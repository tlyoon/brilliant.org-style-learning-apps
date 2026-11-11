import json
import base64
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.audit_browser_visual import stage_bundle, local_server, capture_review_frame
from tests.test_private_browser_visual_evidence import png_bytes


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

    def test_staged_browser_uses_package_declared_domain_assets(self):
        """Normal visual-audit staging must match trusted release domain assets."""
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname) / "repo"
            shutil.copytree(ROOT / "app", root / "app")
            shutil.copytree(ROOT / "domains", root / "domains")
            alt = root / "domains" / "alternate-domain"
            shutil.copytree(root / "domains" / "university-level physics", alt)
            manifest_path = alt / "domain.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update({
                "id": "alternate-domain",
                "displayName": "Alternate Domain",
                "subject": "alternate-subject",
                "academicLevel": "university",
                "profileVersion": "9.9.9",
            })
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            renderer = alt / manifest["visuals"]["rendererScript"]
            renderer.write_text("// ALTERNATE-BROWSER-RENDERER\n" +
                                renderer.read_text(encoding="utf-8"), encoding="utf-8")
            stylesheet = alt / manifest["visuals"]["stylesheet"]
            stylesheet.write_text("/* ALTERNATE-BROWSER-STYLE */\n" +
                                  stylesheet.read_text(encoding="utf-8"), encoding="utf-8")
            registry_path = root / "domains" / "registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["domains"].append({"id": "alternate-domain",
                                        "path": "alternate-domain"})
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            pkg = Path(dirname) / "synthetic-package.json"
            identity = {"id": "alternate-domain", "profileVersion": "9.9.9",
                        "subject": "alternate-subject", "academicLevel": "university"}
            pkg.write_text(json.dumps({"activities": [], "domain": identity}),
                           encoding="utf-8")
            output = Path(dirname) / "browser"
            output.mkdir()
            stage_bundle(root, pkg, output)
            self.assertIn("ALTERNATE-BROWSER-RENDERER",
                          (output / "domain-renderers.js").read_text(encoding="utf-8"))
            self.assertIn("ALTERNATE-BROWSER-STYLE",
                          (output / "domain-styles.css").read_text(encoding="utf-8"))
            identity["profileVersion"] = "9.9.8"
            pkg.write_text(json.dumps({"activities": [], "domain": identity}),
                           encoding="utf-8")
            refused = Path(dirname) / "untrusted"
            refused.mkdir()
            with self.assertRaises(ValueError):
                stage_bundle(root, pkg, refused)
            self.assertEqual([], list(refused.iterdir()),
                             "stale domain identity must fail before staging bytes")

    def test_review_screenshot_evidence_is_hashed_and_never_approved(self):
        class FakeDriver:
            def execute_script(self, _code, _figure):
                return {"x":0,"y":550,"width":400,"height":150}
            def execute_cdp_cmd(self, name, args):
                assert name == "Page.captureScreenshot"
                assert args["captureBeyondViewport"] is True
                assert args["clip"]["y"] == 550
                return {"data":base64.b64encode(png_bytes()).decode("ascii")}
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            result = capture_review_frame(
                FakeDriver(), object(), root, "motion/a", "ms", 390, 1)
            data = (root / result["file"]).read_bytes()
            self.assertEqual(len(data), result["bytes"])
            self.assertEqual((400,150),(result["imageWidth"],result["imageHeight"]))
            self.assertTrue(result["completeFigureCapture"])
            self.assertEqual(result["reviewStatus"], "unreviewed")
            self.assertEqual(64, len(result["sha256"]))
            self.assertNotIn("/", result["file"])

    def test_clipped_browser_frame_is_rejected(self):
        class Driver:
            def execute_script(self, *_args):
                return {"x":0,"y":450,"width":400,"height":250}
            def execute_cdp_cmd(self, *_args):
                return {"data":base64.b64encode(png_bytes()).decode("ascii")}
        with tempfile.TemporaryDirectory() as dirname:
            with self.assertRaisesRegex(ValueError,"cropped"):
                capture_review_frame(Driver(), object(), Path(dirname),
                                     "a","en",1280,1)

    def test_local_server_is_bound_to_loopback(self):
        with tempfile.TemporaryDirectory() as dirname:
            with local_server(Path(dirname)) as url:
                self.assertTrue(url.startswith("http://127.0.0.1:"), url)


if __name__ == "__main__":
    unittest.main()
