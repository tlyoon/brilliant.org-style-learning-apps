import tempfile
import unittest
from pathlib import Path

from scripts.build_public_release import build


ROOT = Path(__file__).resolve().parents[1]


class PublicReleaseTests(unittest.TestCase):
    def test_bundle_contains_only_runtime_files_for_section_1_1(self):
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
                "content/chapter-1/section-1-1/package.json",
            }, actual_files)
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="app/styles.css"', index)
            self.assertIn('src="app/app.js"', index)
            self.assertIn('data-package-url="./content/chapter-1/section-1-1/package.json"', index)

    def test_refuses_to_overwrite_an_existing_bundle(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            (output / "existing.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                build(output)
            self.assertEqual("keep", (output / "existing.txt").read_text(encoding="utf-8"))

    def test_bundle_uses_the_current_section_1_1_package(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output)
            self.assertEqual(
                (ROOT / "content" / "chapter-1" / "section-1-1" / "package.json").read_text(encoding="utf-8"),
                (output / "content" / "chapter-1" / "section-1-1" / "package.json").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
