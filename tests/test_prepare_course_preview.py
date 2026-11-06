"""End-to-end source-free preparation of a local-only instructor preview."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.prepare_course_preview import (
    prepare_local_roster,
    write_local_roster,
    main,
)
from tests.test_course_pilot_readiness import package


def git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        timeout=20,
    )


class LocalPreviewPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        git(self.root, "init", "-q")
        (self.root / ".gitignore").write_text("local-pilot/\n", encoding="utf-8")
        for section in range(1, 7):
            p = self.root / f"content/chapter-9/section-9-{section}/package.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(package(section)), encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "-c", "user.email=ci@example.invalid",
            "-c", "user.name=Source-Free-Test", "commit", "-qm", "six synthetic packages")

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self, sections=None):
        return prepare_local_roster(
            self.root, chapter=9, sections=sections or [1, 2, 3, 4, 5, 6],
            scope_id="sourcefree-pilot-local-instructor-synthetic",
        )

    def test_exact_six_tracked_packages_create_single_ignored_roster(self):
        manifest = self.prepare()
        self.assertEqual(6, len(manifest["cases"]))
        self.assertFalse(manifest["publicationAllowed"])
        output = write_local_roster(self.root, manifest)
        self.assertEqual(self.root / "local-pilot/roster.json", output)
        self.assertEqual(manifest, json.loads(output.read_text(encoding="utf-8")))
        with self.assertRaisesRegex(ValueError, "ALREADY_EXISTS"):
            write_local_roster(self.root, manifest)
        status = subprocess.run(
            ["git", "-C", str(self.root), "status", "--porcelain"],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual("", status.stdout, "private manifest must be gitignored")

    def test_dirty_or_missing_tracked_package_never_creates_roster(self):
        package_path = self.root / "content/chapter-9/section-9-4/package.json"
        package_path.write_text(package_path.read_text(encoding="utf-8") + "\n")
        with self.assertRaisesRegex(ValueError, "FROZEN_COMMIT"):
            self.prepare()
        self.assertFalse((self.root / "local-pilot/roster.json").exists())

    def test_invalid_selection_refused_before_any_roster_write(self):
        for sections in ([1, 2, 3, 4, 5, 5], [1, 2, 3], [1, 2, 3, 4, 5, True]):
            with self.subTest(sections=sections):
                with self.assertRaises(ValueError):
                    self.prepare(sections)
        self.assertFalse((self.root / "local-pilot").exists())

    def test_wrong_package_identity_rejected_even_when_committed(self):
        target = self.root / "content/chapter-9/section-9-3/package.json"
        changed = package(3)
        changed["packageId"] = "chapter-9-section-9-2"
        target.write_text(json.dumps(changed), encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "-c", "user.email=ci@example.invalid",
            "-c", "user.name=Source-Free-Test", "commit", "-qm", "new faulty candidate")
        with self.assertRaisesRegex(ValueError, "STRUCTURALLY_VALID"):
            self.prepare()
        self.assertFalse((self.root / "local-pilot").exists())

    def test_missing_gitignore_guard_prevents_public_roster(self):
        (self.root / ".gitignore").write_text("", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "GIT_REVISION_OR_TRACKED_PACKAGE_UNAVAILABLE"):
            write_local_roster(self.root, self.prepare())
        self.assertFalse((self.root / "local-pilot").exists())

    def test_cli_writes_local_preview_and_refuses_repeat(self):
        from contextlib import redirect_stdout
        from io import StringIO
        args = ["--repo-root", str(self.root), "--chapter", "9",
                "--sections", "1", "2", "3", "4", "5", "6",
                "--scope-id", "sourcefree-pilot-local-instructor-synthetic"]
        with redirect_stdout(StringIO()) as output:
            self.assertEqual(0, main(args))
        parsed = json.loads(output.getvalue())
        self.assertEqual("LOCAL_SOURCEFREE_PREVIEW_ROSTER_CREATED", parsed["status"])
        self.assertFalse(parsed["classroomPilotReady"])
        with redirect_stdout(StringIO()) as repeated:
            self.assertEqual(1, main(args))
        self.assertEqual(
            "STOP_UNSAFE_OR_INCOMPLETE_LOCAL_PREVIEW",
            json.loads(repeated.getvalue())["status"],
        )


if __name__ == "__main__":
    unittest.main()
