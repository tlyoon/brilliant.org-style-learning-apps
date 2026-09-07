import unittest
from types import SimpleNamespace

from app_generator.errors import NoAvailableJob
from app_generator.runtime.targeting import (
    normalize_target_subchapter_id,
    restrict_inventory_to_subchapter,
)


class TargetedAutoInventoryTests(unittest.TestCase):
    def sources(self):
        return (
            SimpleNamespace(subchapter_id="8.5", job_key="job-85"),
            SimpleNamespace(subchapter_id="8.6", job_key="job-86"),
            SimpleNamespace(subchapter_id="8.7", job_key="job-87"),
        )

    def test_no_target_preserves_full_auto_inventory(self):
        sources = self.sources()
        self.assertEqual(sources, restrict_inventory_to_subchapter(sources, None))

    def test_explicit_target_returns_only_requested_section(self):
        result = restrict_inventory_to_subchapter(self.sources(), "8.6")
        self.assertEqual(["8.6"], [source.subchapter_id for source in result])

    def test_path_style_target_uses_terminal_section_id(self):
        self.assertEqual("8.6", normalize_target_subchapter_id(r"8\8.6"))
        result = restrict_inventory_to_subchapter(self.sources(), r"8\8.6")
        self.assertEqual(["8.6"], [source.subchapter_id for source in result])

    def test_missing_target_does_not_fall_through_to_another_section(self):
        with self.assertRaisesRegex(NoAvailableJob, "Target section 9.9"):
            restrict_inventory_to_subchapter(self.sources(), "9.9")


if __name__ == "__main__":
    unittest.main()
