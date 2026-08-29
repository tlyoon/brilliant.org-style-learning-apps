import tempfile
import unittest
from pathlib import Path

from scripts.build_public_release import build


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "content" / "chapter-1" / "section-1-1" / "package.json"


class PublicReleaseTests(unittest.TestCase):
    def test_bundle_contains_only_runtime_files_for_selected_package(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output, PACKAGE)
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
                "content/package.json",
            }, actual_files)
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="app/styles.css"', index)
            self.assertIn('src="app/app.js"', index)
            self.assertIn('data-package-url="./content/package.json"', index)
            self.assertNotIn("Section 1.1", index)

    def test_refuses_to_overwrite_an_existing_bundle(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            (output / "existing.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                build(output, PACKAGE)
            self.assertEqual("keep", (output / "existing.txt").read_text(encoding="utf-8"))

    def test_bundle_uses_the_explicit_selected_package(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "release"
            build(output, PACKAGE)
            self.assertEqual(
                PACKAGE.read_text(encoding="utf-8"),
                (output / "content" / "package.json").read_text(encoding="utf-8"),
            )

    def test_refuses_a_package_outside_repository_content(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            outside = Path(temporary_directory) / "package.json"
            outside.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                build(Path(temporary_directory) / "release", outside)


if __name__ == "__main__":
    unittest.main()
