"""BSA240 fail-closed, source-free AX tree unit and fault injection tests."""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from app_generator.runtime.v3_public_pr_accessibility_tree import (
    inspect_control_names, audit_real_chrome_accessibility_tree,
)


def node(role, name, ignored=False):
    return {"ignored": ignored,
            "role": {"value": role},
            "name": {"value": name}}


class RealChromeAccessibilityTreeContractTests(unittest.TestCase):
    def test_named_select_and_button_pass(self):
        result = inspect_control_names(
            {"nodes": [node("RootWebArea", ""), node("comboBox", "Language"),
                       node("button", "Semak jawapan")]},
            page="section-9-1/index.html", locale="ms")
        self.assertEqual(result["namedControls"], 2)
        self.assertEqual(result["unnamedControls"], 0)

    def test_missing_select_label_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "BSA240_UNNAMED_ACCESSIBLE_CONTROL"):
            inspect_control_names({"nodes": [
                node("comboBox", ""), node("button", "Check answer")]},
                page="section-9-1/index.html", locale="en")

    def test_empty_button_name_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "BSA240_UNNAMED_ACCESSIBLE_CONTROL"):
            inspect_control_names({"nodes": [
                node("comboBox", "Language"), node("button", "  ")]},
                page="section-9-1/index.html", locale="en")

    def test_ignored_nodes_not_counted(self):
        with self.assertRaisesRegex(ValueError, "BSA240_MISSING_INTERACTIVE_AX_CONTROLS"):
            inspect_control_names({"nodes": [
                node("comboBox", "Language"), node("button", "unused", ignored=True)]},
                page="section-9-2/index.html", locale="zh")

    def test_deny_missing_tree_and_invalid_schema(self):
        for invalid in ({}, {"nodes": []}, {"nodes": "not-list"}):
            with self.subTest(tree=invalid):
                with self.assertRaisesRegex(ValueError, "BSA240_AX_TREE_EMPTY"):
                    inspect_control_names(invalid,
                                         page="section-9-2/index.html", locale="en")

    def test_symlink_and_path_escape_forbidden_before_any_browser(self):
        with TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "page.html").write_text("synthetic", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "BSA240_INVALID_PAGE_PATH"):
                audit_real_chrome_accessibility_tree(
                    site, (("../page.html", ""),))
            with self.assertRaisesRegex(ValueError, "BSA240_UNSAFE_PACKAGE_PATH"):
                audit_real_chrome_accessibility_tree(
                    site, (("page.html", "https://example.org/evil"),))
            with self.assertRaisesRegex(ValueError, "BSA240_INVALID_PAGE_FILE"):
                audit_real_chrome_accessibility_tree(
                    site, (("not-here.html", ""),))

    def test_explicit_empty_page_set_refused(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "BSA240_NO_PAGES"):
                audit_real_chrome_accessibility_tree(Path(tmp), ())


if __name__ == "__main__":
    unittest.main()
