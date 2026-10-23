import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_browser_visual import stage_bundle, local_server, capture_review_frame


ROOT = Path(__file__).resolve().parents[1]


class BrowserBundleTests(unittest.TestCase):
    def test_stages_only_private_test_assets_and_does_not_mutate_package(self):
        with tempfile.TemporaryDirectory() as dirname:
            scratch = Path(dirname)
            source = scratch / "source.json"
            source.write_text(json.dumps({"activities": []}), encoding="utf-8")
            before = source.read_bytes()
            output = scratch / "staged"
            output.mkdir()
            stage_bundle(ROOT, source, output)
            self.assertEqual(before, source.read_bytes())
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('data-package-url="package.json"', index)
            self.assertTrue((output / "domain-renderers.js").is_file())
            self.assertTrue((output / "domain-styles.css").is_file())
            self.assertEqual(json.loads((output / "package.json").read_text(encoding="utf-8")), {"activities": []})

    def test_review_screenshot_evidence_is_hashed_and_never_approved(self):
        class FakeFigure:
            screenshot_as_png = bytes.fromhex("89504E470D0A1A0A") + b"fixture"
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            result = capture_review_frame(FakeFigure(), root, "motion/a", "ms", 390, 1)
            data = (root / result["file"]).read_bytes()
            self.assertEqual(len(data), result["bytes"])
            self.assertEqual(result["reviewStatus"], "unreviewed")
            self.assertEqual(64, len(result["sha256"]))
            self.assertNotIn("/", result["file"])

    def test_local_server_is_bound_to_loopback(self):
        with tempfile.TemporaryDirectory() as dirname:
            with local_server(Path(dirname)) as url:
                self.assertTrue(url.startswith("http://127.0.0.1:"), url)


if __name__ == "__main__":
    unittest.main()
