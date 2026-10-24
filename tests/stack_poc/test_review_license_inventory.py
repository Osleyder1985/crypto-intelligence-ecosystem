import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "stack_poc" / "review_license_inventory.py"


class LicenceInventoryReviewTests(unittest.TestCase):
    def run_review(self, rows):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        source = Path(temp.name) / "inventory.json"
        output = Path(temp.name) / "review.json"
        source.write_text(json.dumps(rows), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(source), str(output)],
            check=True, capture_output=True, text=True,
        )
        return json.loads(output.read_text(encoding="utf-8")), completed.stdout

    def test_version_bound_license_text_override_is_applied(self):
        report, _ = self.run_review([{
            "Name": "CacheControl", "Version": "0.14.4",
            "License-Metadata": "UNKNOWN", "License-Classifier": "UNKNOWN",
            "LicenseText": "Licensed under the Apache License, Version 2.0",
            "LicenseFile": "/package/LICENSE", "NoticeFile": "UNKNOWN",
            "NoticeText": "UNKNOWN", "URL": "https://pypi.org/project/CacheControl/",
        }])
        package = report["packages"][0]
        self.assertEqual(package["license_expression"], "Apache-2.0")
        self.assertEqual(package["status"], "identified-from-versioned-license-text")
        self.assertEqual(report["manual_review_required"], 0)

    def test_version_pinned_upstream_license_text_resolves_missing_installed_text(self):
        report, _ = self.run_review([{
            "Name": "packageurl-python", "Version": "0.17.6",
            "License-Metadata": "MIT", "License-Classifier": "MIT License",
            "LicenseText": "UNKNOWN", "LicenseFile": "UNKNOWN",
            "NoticeFile": "UNKNOWN", "NoticeText": "UNKNOWN",
            "URL": "https://github.com/package-url/packageurl-python",
        }])
        package = report["packages"][0]
        self.assertEqual(package["license_expression"], "MIT")
        self.assertEqual(package["status"], "identified-from-versioned-upstream-license-text")
        self.assertTrue(package["license_text_present"])
        self.assertEqual(package["license_source_url"], "https://raw.githubusercontent.com/package-url/packageurl-python/v0.17.6/mit.LICENSE")
        self.assertEqual(report["identified_from_versioned_upstream_license_text"], 1)
        self.assertEqual(report["manual_review_required"], 0)

    def test_starlette_1100_license_is_pinned_to_tagged_three_clause_bsd_text(self):
        report, _ = self.run_review([{
            "Name": "starlette", "Version": "1.10.0",
            "License-Metadata": "UNKNOWN", "License-Classifier": "UNKNOWN",
            "LicenseText": "UNKNOWN", "LicenseFile": "UNKNOWN",
            "NoticeFile": "UNKNOWN", "NoticeText": "UNKNOWN",
            "URL": "https://github.com/Kludex/starlette",
        }])
        package = report["packages"][0]
        self.assertEqual(package["license_expression"], "BSD-3-Clause")
        self.assertEqual(package["status"], "identified-from-versioned-license-text")
        self.assertIn("starlette/blob/1.10.0/LICENSE.md", package["basis"])

    def test_override_does_not_carry_forward_to_unreviewed_version(self):
        report, _ = self.run_review([{
            "Name": "CacheControl", "Version": "99.0.0",
            "License-Metadata": "UNKNOWN", "License-Classifier": "UNKNOWN",
            "LicenseText": "some unreviewed licence text",
            "LicenseFile": "/package/LICENSE", "NoticeFile": "UNKNOWN",
            "NoticeText": "UNKNOWN", "URL": "https://pypi.org/project/CacheControl/",
        }])
        package = report["packages"][0]
        self.assertEqual(package["status"], "manual-review-required")
        self.assertIsNone(package["license_expression"])

    def test_declared_license_without_captured_text_stays_unresolved(self):
        report, _ = self.run_review([{
            "Name": "example", "Version": "1.0",
            "License-Metadata": "MIT", "License-Classifier": "MIT License",
            "LicenseText": "UNKNOWN", "LicenseFile": "UNKNOWN",
            "NoticeFile": "UNKNOWN", "NoticeText": "UNKNOWN", "URL": "https://example.invalid",
        }])
        package = report["packages"][0]
        self.assertEqual(package["status"], "manual-review-required")
        self.assertFalse(package["license_text_present"])
        self.assertEqual(report["missing_license_text_count"], 1)

    def test_aligned_metadata_is_not_misrepresented_as_text_review(self):
        report, _ = self.run_review([{
            "Name": "example", "Version": "1.0",
            "License-Metadata": "MIT", "License-Classifier": "MIT License",
            "LicenseText": "MIT License text", "LicenseFile": "/package/LICENSE",
            "NoticeFile": "UNKNOWN", "NoticeText": "UNKNOWN", "URL": "https://example.invalid",
        }])
        package = report["packages"][0]
        self.assertEqual(package["status"], "metadata-aligned-review-required")
        self.assertEqual(report["metadata_aligned_review_required"], 1)


if __name__ == "__main__":
    unittest.main()
