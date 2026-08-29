import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_section_8_1_public_release import (
    build,
    section_eight_three_package,
    version_one_package,
)


ROOT = Path(__file__).resolve().parents[1]


class SectionEightOnePublicReleaseTests(unittest.TestCase):
    def test_bundle_contains_only_dual_version_runtime_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output)
            actual_files = {
                path.relative_to(output).as_posix()
                for path in output.rglob("*")
                if path.is_file()
            }
            self.assertEqual({
                ".nojekyll",
                "index.html",
                "app/app.js",
                "app/styles.css",
                "v1/index.html",
                "v2/index.html",
                "section-8-3/index.html",
                "content/v1/package.json",
                "content/v2/package.json",
                "content/section-8-3/package.json",
            }, actual_files)

    def test_both_draft_versions_are_distinct_and_complete(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output)
            version_one = json.loads((output / "content/v1/package.json").read_text(encoding="utf-8"))
            version_two = json.loads((output / "content/v2/package.json").read_text(encoding="utf-8"))
            self.assertNotEqual(version_one, version_two)
            for package in (version_one, version_two):
                self.assertEqual("chapter-8-section-8-1", package["packageId"])
                self.assertEqual("draft", package["status"])
                self.assertEqual(18, len(package["activities"]))

    def test_version_one_is_the_immutable_historical_package(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output)
            self.assertEqual(
                version_one_package(),
                (output / "content/v1/package.json").read_bytes(),
            )

    def test_version_two_uses_the_current_main_package(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output)
            self.assertEqual(
                (ROOT / "content/chapter-8/section-8-1/package.json").read_bytes(),
                (output / "content/v2/package.json").read_bytes(),
            )

    def test_section_eight_three_uses_the_current_draft_package(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output)
            deployed = json.loads(
                (output / "content/section-8-3/package.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                section_eight_three_package(),
                (output / "content/section-8-3/package.json").read_bytes(),
            )
            self.assertEqual("chapter-8-section-8-3", deployed["packageId"])
            self.assertEqual("draft", deployed["status"])
            self.assertEqual(18, len(deployed["activities"]))

    def test_landing_and_version_pages_keep_draft_review_labelling(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output)
            landing = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="v1/"', landing)
            self.assertIn('href="v2/"', landing)
            self.assertIn('href="section-8-3/"', landing)
            self.assertIn("none are approved for publication", landing)
            for version in ("v1", "v2"):
                page = (output / version / "index.html").read_text(encoding="utf-8")
                self.assertIn("Draft review prototype", page)
                self.assertIn(f'data-package-url="../content/{version}/package.json"', page)
            section_eight_three = (output / "section-8-3/index.html").read_text(encoding="utf-8")
            self.assertIn("Draft review prototype", section_eight_three)
            self.assertIn(
                'data-package-url="../content/section-8-3/package.json"',
                section_eight_three,
            )

    def test_refuses_to_overwrite_an_existing_bundle(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            (output / "existing.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                build(output)
            self.assertEqual("keep", (output / "existing.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
