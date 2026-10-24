#!/usr/bin/env python3
"""Produce a conservative, version-bound review of pip-licenses JSON inventory."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Curated from the exact installed distribution's captured LICENSE text.
# Keep versions pinned here: a new version must be reviewed rather than inheriting
# an unverified licence classification.
TEXT_OVERRIDES = {
    ("cachecontrol", "0.14.4"): ("Apache-2.0", "LICENSE text states Apache License 2.0"),
    ("pygments", "2.21.0"): ("BSD-2-Clause", "LICENSE text has the two-clause BSD conditions"),
    ("annotated-doc", "0.0.5"): ("MIT", "LICENSE text identifies The MIT License"),
    ("anyio", "4.15.1"): ("MIT", "LICENSE text identifies The MIT License"),
    ("fastapi", "0.158.1"): ("MIT", "LICENSE text identifies The MIT License"),
    ("idna", "3.20"): ("BSD-3-Clause", "LICENSE text has the three-clause BSD conditions"),
    ("msgpack", "1.2.3"): ("Apache-2.0", "LICENSE text states Apache License 2.0"),
    ("opentelemetry-api", "1.45.1"): ("Apache-2.0", "LICENSE text identifies Apache License 2.0"),
    ("packaging", "26.3"): ("Apache-2.0 OR BSD-2-Clause", "LICENSE text explicitly permits either LICENSE.APACHE or LICENSE.BSD; contribution terms are dual"),
    ("pydantic", "2.14.1"): ("MIT", "LICENSE text identifies The MIT License"),
    ("pydantic_core", "2.50.1"): ("MIT", "LICENSE text identifies The MIT License"),
    ("pyparsing", "3.3.3"): ("MIT", "LICENSE text matches the MIT permission and disclaimer"),
    ("starlette", "1.9.0"): ("BSD-3-Clause", "LICENSE text has the three-clause BSD conditions"),
    ("typing-inspection", "0.4.4"): ("MIT", "LICENSE text identifies The MIT License"),
    ("urllib3", "2.8.0"): ("MIT", "LICENSE text identifies The MIT License"),
}


def known(value: object) -> bool:
    return isinstance(value, str) and value.strip() and value.strip().upper() != "UNKNOWN"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: review_license_inventory.py INPUT.json OUTPUT.json", file=sys.stderr)
        return 2
    inventory = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    reviewed = []
    for item in inventory:
        name = str(item.get("Name", ""))
        version = str(item.get("Version", ""))
        key = (name.casefold(), version)
        metadata = item.get("License-Metadata", "UNKNOWN")
        classifier = item.get("License-Classifier", "UNKNOWN")
        text_present = known(item.get("LicenseText"))
        file_present = known(item.get("LicenseFile"))
        notice_present = known(item.get("NoticeText")) or known(item.get("NoticeFile"))
        expression = None
        basis = None
        status = "manual-review-required"

        if key in TEXT_OVERRIDES:
            expression, basis = TEXT_OVERRIDES[key]
            status = "identified-from-versioned-license-text"
        elif known(metadata) and known(classifier):
            expression = str(metadata)
            basis = "package metadata and PyPI classifier both declare a licence; text not independently normalized here"
            status = "metadata-aligned-review-required"
        elif known(metadata):
            expression = str(metadata)
            basis = "package metadata declares a licence; classifier is unknown"
            status = "metadata-review-required"
        elif known(classifier):
            expression = str(classifier)
            basis = "PyPI classifier declares a licence; metadata is unknown"
            status = "classifier-review-required"

        if not text_present:
            status = "manual-review-required"
            basis = (basis + "; " if basis else "") + "installed distribution did not provide licence text in inventory"
        reviewed.append({
            "name": name,
            "version": version,
            "license_expression": expression,
            "basis": basis,
            "status": status,
            "license_text_present": bool(text_present),
            "license_file_present": bool(file_present),
            "separate_notice_present": bool(notice_present),
            "metadata_license": metadata,
            "classifier_license": classifier,
            "package_url": item.get("URL"),
        })

    unresolved = [x for x in reviewed if x["status"] == "manual-review-required"]
    summary = {
        "schema_version": "1.0",
        "inventory_count": len(reviewed),
        "identified_from_versioned_license_text": sum(x["status"] == "identified-from-versioned-license-text" for x in reviewed),
        "metadata_aligned_review_required": sum(x["status"] == "metadata-aligned-review-required" for x in reviewed),
        "metadata_review_required": sum(x["status"] == "metadata-review-required" for x in reviewed),
        "classifier_review_required": sum(x["status"] == "classifier-review-required" for x in reviewed),
        "manual_review_required": len(unresolved),
        "missing_license_text_count": sum(not x["license_text_present"] for x in reviewed),
        "missing_separate_notice_count": sum(not x["separate_notice_present"] for x in reviewed),
        "unresolved_packages": [{"name": x["name"], "version": x["version"], "metadata_license": x["metadata_license"], "classifier_license": x["classifier_license"], "license_text_present": x["license_text_present"], "license_file_present": x["license_file_present"]} for x in unresolved],
        "packages": reviewed,
        "limitations": [
            "This is an inventory triage report, not legal advice or a formal legal approval.",
            "Version-specific text overrides must be re-reviewed when package versions change.",
            "Missing separate NOTICE files do not by themselves prove a violation; distribution obligations must be checked against each licence text and the intended product distribution.",
            "Packages marked for manual review must be resolved before production ratification."
        ]
    }
    Path(sys.argv[2]).write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "packages"}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
