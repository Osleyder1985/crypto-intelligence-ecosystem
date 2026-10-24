#!/usr/bin/env python3
"""Inventory captured licence/notice texts for the resolved Dart/Flutter graph."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path


TEXT_MARKERS = ("license", "licence", "copying", "notice", "patent")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._+-]+", "_", value).strip("._") or "package"


def candidates(package: dict, pub_cache: Path, flutter_root: Path | None) -> list[Path]:
    name, version, source = package.get("name", ""), package.get("version", ""), package.get("source", "")
    roots: list[Path] = []
    if source == "hosted" and name and version:
        roots.append(pub_cache / "hosted" / "pub.dev" / f"{name}-{version}")
    elif source == "sdk" and flutter_root and name:
        roots.append(flutter_root / "packages" / name)
        if name == "sky_engine":
            roots.append(flutter_root / "bin" / "cache" / "pkg" / "sky_engine")
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for item in root.iterdir():
            if item.is_file() and any(marker in item.name.casefold() for marker in TEXT_MARKERS):
                found.append(item)
        # A small number of packages put licence files in a dedicated directory.
        licence_dir = root / "licenses"
        if licence_dir.is_dir():
            found.extend(p for p in licence_dir.iterdir() if p.is_file())
    # SDK packages can be covered by the SDK repository's top-level licence.
    if not found and source == "sdk" and flutter_root:
        sdk_license = flutter_root / "LICENSE"
        if sdk_license.is_file():
            found.append(sdk_license)
    return sorted(set(found), key=lambda p: p.name.casefold())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dependencies_json", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--copy-dir", type=Path, required=True)
    args = parser.parse_args()
    graph = json.loads(args.dependencies_json.read_text(encoding="utf-8"))
    packages = graph.get("packages", [])
    pub_cache = Path(os.environ.get("PUB_CACHE", Path.home() / ".pub-cache"))
    root_value = os.environ.get("FLUTTER_ROOT")
    flutter_root = Path(root_value) if root_value else None
    args.copy_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for package in packages:
        if package.get("source") == "root":
            continue
        name, version = str(package.get("name", "")), str(package.get("version", ""))
        files = candidates(package, pub_cache, flutter_root)
        records = []
        for file_path in files:
            digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
            destination = args.copy_dir / safe_name(f"{name}-{version}") / safe_name(file_path.name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, destination)
            records.append({
                "filename": file_path.name,
                "sha256": digest,
                "bytes": file_path.stat().st_size,
                "copied_to": str(destination).replace("\\", "/"),
            })
        rows.append({
            "name": name,
            "version": version,
            "source": package.get("source"),
            "kind": package.get("kind"),
            "license_text_files": records,
            "status": "text-captured" if records else "manual-review-required",
        })

    unresolved = [r for r in rows if r["status"] == "manual-review-required"]
    report = {
        "schema_version": "1.0",
        "package_count": len(rows),
        "packages_with_license_or_notice_text": len(rows) - len(unresolved),
        "manual_review_required_count": len(unresolved),
        "manual_review_required": [{"name": r["name"], "version": r["version"], "source": r["source"]} for r in unresolved],
        "packages": rows,
        "limitations": [
            "This inventories local licence/notice files and hashes; it does not infer SPDX identifiers or approve legal compliance.",
            "Missing local files must be reviewed against the exact upstream package release before production distribution.",
            "A captured licence file does not prove all third-party attribution and notice obligations have been fulfilled."
        ]
    }
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "packages"}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
