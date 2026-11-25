import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.errors import ValidationFailure

from scripts.build_public_release import build


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "content" / "chapter-1" / "section-1-1" / "package.json"


class PublicReleaseTests(unittest.TestCase):
    def test_bundle_contains_only_runtime_files_for_selected_package(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output, PACKAGE, local_preview=True)
            actual_files = {
                path.relative_to(output).as_posix()
                for path in output.rglob("*")
                if path.is_file()
            }

            self.assertEqual({
                ".nojekyll",
                "index.html",
                "app/app.js",
                "app/domain-renderers.js",
                "app/visual-renderers.js",
                "app/styles.css",
                "app/domain-styles.css",
                "content/package.json",
            }, actual_files)
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="app/styles.css"', index)
            self.assertIn('href="app/domain-styles.css"', index)
            self.assertIn('src="app/domain-renderers.js"', index)
            self.assertIn('src="app/visual-renderers.js"', index)
            self.assertIn('src="app/app.js"', index)
            self.assertIn('data-package-url="./content/package.json"', index)
            self.assertNotIn("Section 1.1", index)

    def test_refuses_to_overwrite_an_existing_bundle(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            (output / "existing.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                build(output, PACKAGE, local_preview=True)
            self.assertEqual("keep", (output / "existing.txt").read_text(encoding="utf-8"))

    def test_bundle_uses_the_explicit_selected_package(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output, PACKAGE, local_preview=True)
            self.assertEqual(
                PACKAGE.read_text(encoding="utf-8"),
                (output / "content" / "package.json").read_text(encoding="utf-8"),
            )

    def test_default_builder_blocks_unverified_public_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundle"
            with self.assertRaisesRegex(ValueError, "private academic validation"):
                build(output, PACKAGE)
            self.assertFalse(output.exists(), "must not write even an index file")

    def test_explicit_preview_has_visible_warning_and_noindex(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "preview"
            build(output, PACKAGE, local_preview=True)
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("LOCAL DRAFT PREVIEW", index)
            self.assertIn("NOT APPROVED FOR PUBLICATION", index)
            self.assertIn('content="noindex, nofollow"', index)
            self.assertEqual(PACKAGE.read_bytes(), (output / "content/package.json").read_bytes())

    def test_public_mode_requires_independent_academic_gate_not_cached_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "evidence"
            evidence.mkdir()
            unreviewed = ROOT / "content/chapter-9/section-9-4/package.json"
            fake_receipt = {"academicQA": "PASS", "artifactSha256":
                            hashlib.sha256(unreviewed.read_bytes()).hexdigest()}
            (evidence / "academic-release-gate.json").write_text(json.dumps(fake_receipt))
            output = Path(tmp) / "publication"
            with self.assertRaisesRegex(ValidationFailure,
                                        "pending complete V3 AI"):
                build(output, unreviewed, validation_dir=evidence)
            self.assertFalse(output.exists(), "forged receipt cannot create a public bundle")
            # The shared current V3 gate rejects legacy faux PASS; historical
            # original-source/browser campaign stops are independently kept.
            stored = json.loads((evidence / "academic-release-gate.json").read_text())
            self.assertEqual(fake_receipt, stored)

    def test_release_mode_accepts_only_exact_sha_from_same_academic_gate(self):
        # Synthetic PASS stub tests wiring, not actual academic approval.
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "evidence"
            output = Path(tmp) / "bundle"
            with patch("scripts.build_public_release.enforce_academic_release_gate",
                       return_value={"artifactSha256": "0" * 64, "academicQA": "PASS"}):
                with self.assertRaisesRegex(ValueError, "does not match bundled"):
                    build(output, PACKAGE, validation_dir=evidence)
            self.assertFalse(output.exists())
            expected = hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
            with patch("scripts.build_public_release.enforce_academic_release_gate",
                       return_value={"artifactSha256": expected, "academicQA": "PASS"}) as gate:
                build(output, PACKAGE, validation_dir=evidence)
            gate.assert_called_once_with(ROOT, PACKAGE, evidence)
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("LOCAL DRAFT PREVIEW", index)
            self.assertEqual(PACKAGE.read_bytes(), (output / "content/package.json").read_bytes())

    def test_frozen_chapter9_public_build_stops_before_academic_gate_or_write(self):
        """Alternative builder requires actual V3 AI receipts; no historic replay."""
        frozen = ROOT / "content/chapter-9/section-9-4/package.json"
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "offrepo-evidence"
            evidence.mkdir()
            output = Path(tmp) / "bundle"
            with self.assertRaisesRegex(ValidationFailure,
                                        "pending complete V3 AI"):
                build(output, frozen, validation_dir=evidence)
            self.assertFalse(output.exists(),
                             "no public files without verified current V3 receipt")

    def test_private_receipts_cannot_be_staged_inside_public_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundle"
            with self.assertRaisesRegex(ValueError, "must not be inside"):
                build(output, PACKAGE, validation_dir=output / "evidence")
            self.assertFalse(output.exists())

    def test_refuses_a_package_outside_repository_content(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            outside = Path(temporary_directory) / "package.json"
            outside.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                build(Path(temporary_directory) / "release", outside)


if __name__ == "__main__":
    unittest.main()
