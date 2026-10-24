import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "stack_poc" / "inventory_dart_licenses.py"


class DartLicenceInventoryTests(unittest.TestCase):
    def test_captures_and_hashes_license_text_and_marks_missing_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "pub-cache"
            flutter_root = root / "flutter-sdk"
            flutter_root.mkdir()
            sdk_license_text = "Flutter SDK license text\\n"
            (flutter_root / "LICENSE").write_text(sdk_license_text, encoding="utf-8")
            package = cache / "hosted" / "pub.dev" / "sample_pkg-1.2.3"
            package.mkdir(parents=True)
            license_text = "MIT License\nCopyright (c) Example\n"
            (package / "LICENSE").write_text(license_text, encoding="utf-8")
            graph = {
                "packages": [
                    {"name": "sample_pkg", "version": "1.2.3", "source": "hosted", "kind": "direct"},
                    {"name": "missing_pkg", "version": "4.5.6", "source": "hosted", "kind": "transitive"},
                    {"name": "flutter_test", "version": "0.0.0", "source": "sdk", "kind": "dev"},
                    {"name": "app", "version": "0.1.0", "source": "root", "kind": "root"},
                ]
            }
            graph_path = root / "deps.json"
            output_path = root / "report.json"
            copy_dir = root / "captured"
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            env = dict(os.environ)
            env["PUB_CACHE"] = str(cache)
            env["FLUTTER_ROOT"] = str(flutter_root)
            subprocess.run(
                [sys.executable, str(SCRIPT), str(graph_path), str(output_path), "--copy-dir", str(copy_dir)],
                check=True, capture_output=True, text=True, env=env,
            )
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["package_count"], 3)
            self.assertEqual(report["packages_with_license_or_notice_text"], 2)
            self.assertEqual(report["manual_review_required_count"], 1)
            captured = report["packages"][0]
            self.assertEqual(captured["status"], "text-captured")
            self.assertEqual(captured["license_text_files"][0]["sha256"], hashlib.sha256(license_text.encode()).hexdigest())
            copied = copy_dir / "sample_pkg-1.2.3" / "LICENSE"
            self.assertEqual(copied.read_text(encoding="utf-8"), license_text)
            missing = report["packages"][1]
            self.assertEqual(missing["status"], "manual-review-required")
            sdk_package = report["packages"][2]
            self.assertEqual(sdk_package["name"], "flutter_test")
            self.assertEqual(sdk_package["status"], "text-captured")
            sdk_copy = copy_dir / "flutter_test-0.0.0" / "LICENSE"
            self.assertEqual(sdk_copy.read_text(encoding="utf-8"), sdk_license_text)


if __name__ == "__main__":
    unittest.main()
