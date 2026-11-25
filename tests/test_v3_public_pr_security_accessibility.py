"""Source-free adversarial tests for BSA237 V16 (not release approval)."""
from __future__ import annotations
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_public_pr_security_accessibility as m


HTML = """<!doctype html><html lang="en"><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
</head><body><main>
<select id="locale" aria-label="Language"></select>
<section id="app" aria-live="polite"></section></main>
<script src="app/domain-renderers.js"></script>
<script src="app/visual-renderers.js"></script>
<script src="app/app.js"></script></body></html>"""


class PublicSecurityA11yUnitTests(unittest.TestCase):
    def test_expected_markup(self):
        m._check_page(HTML)

    def test_missing_keyboard_label_fails(self):
        with self.assertRaisesRegex(ValueError, "STRUCTURE"):
            m._check_page(HTML.replace(' aria-label="Language"', ""))

    def test_inline_handler_fails(self):
        with self.assertRaisesRegex(ValueError, "INLINE_EVENT"):
            m._check_page(HTML.replace("<main>", '<main onclick="x()">'))

    def test_remote_resource_fails(self):
        with self.assertRaisesRegex(ValueError, "EXTERNAL_OR_ACTIVE"):
            m._check_page(HTML.replace('src="app/app.js"', 'src="https://example.org/js"'))

    def test_script_allowlist_fails(self):
        with self.assertRaisesRegex(ValueError, "SCRIPT_ALLOWLIST"):
            m._check_page(HTML.replace('src="app/app.js"', 'src="untrusted.js"'))

    def test_activity_data(self):
        a = [{"id": f"a{x}", "accessibilityText": {
            "en": "description", "ms": "keterangan", "zh": "描述"}}
             for x in range(18)]
        self.assertEqual(m._check_package(json.dumps({
            "status": "draft", "activities": a}))["activityCount"], 18)
        a[0]["accessibilityText"]["ms"] = ""
        with self.assertRaisesRegex(ValueError, "TRILINGUAL"):
            m._check_package(json.dumps({"status": "draft", "activities": a}))

    def test_published_status_rejected(self):
        with self.assertRaisesRegex(ValueError, "STATUS"):
            m._check_package(json.dumps({"status": "published", "activities": []}))

    def test_duplicate_activity_ids_rejected(self):
        a = [{"id": "same", "accessibilityText": {
            k: "text" for k in m._LANGUAGES}} for _ in range(18)]
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            m._check_package(json.dumps({"status": "draft", "activities": a}))

    def _fixture(self, root: Path):
        activities = [{"id": str(i), "accessibilityText": {
            "en": "text", "ms": "teks", "zh": "文字"}} for i in range(18)]
        for section in m._SECTIONS:
            p = root / section
            (p / "app").mkdir(parents=True)
            (p / "content").mkdir()
            for name in m._FILES:
                f = p / name
                if name == "index.html":
                    text = HTML
                elif name.endswith("package.json"):
                    text = json.dumps({"status": "draft", "activities": activities})
                elif name == "app/app.js":
                    text = ("const response = await fetch(packageUrl);\n"
                            "document.documentElement.lang = requestedLocale;\n")
                elif name.endswith(".css"):
                    text = ":focus-visible {outline: 2px solid black}\n@media(prefers-reduced-motion:reduce) {}"
                else:
                    text = "const good = true;"
                f.write_text(text, encoding="utf-8")

    def test_actual_checkout_shape(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            paths = [f"{s}/{f}" for s in m._SECTIONS for f in m._FILES]
            report = m.audit_public_checkout(root, paths)
            self.assertEqual(report["changedFileCount"], 21)
            self.assertEqual(report["totalActivities"], 54)

    def test_outside_scope_and_missing_file_fail(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            paths = [f"{s}/{f}" for s in m._SECTIONS for f in m._FILES]
            with self.assertRaisesRegex(ValueError, "SCOPE"):
                m.audit_public_checkout(root, paths[:-1] + ["outside/private"])
            (root / "section-9-2" / "app" / "styles.css").unlink()
            with self.assertRaisesRegex(ValueError, "MISSING"):
                m.audit_public_checkout(root, paths)

    def test_injected_dynamic_sink_fails(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            target = root / "section-9-6" / "app" / "app.js"
            target.write_text("x.innerHTML = y; fetch(packageUrl);", encoding="utf-8")
            paths = [f"{s}/{f}" for s in m._SECTIONS for f in m._FILES]
            with self.assertRaisesRegex(ValueError, "UNSAFE"):
                m.audit_public_checkout(root, paths)

    def test_missing_dynamic_document_language_update_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            target = root / "section-9-2" / "app" / "app.js"
            target.write_text("const response = await fetch(packageUrl);\n",
                              encoding="utf-8")
            paths = [f"{s}/{f}" for s in m._SECTIONS for f in m._FILES]
            with self.assertRaisesRegex(ValueError, "LANGUAGE_NOT_SYNCHRONIZED"):
                m.audit_public_checkout(root, paths)

    def test_no_release_side_effect_in_technical_audit(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            paths = [f"{s}/{f}" for s in m._SECTIONS for f in m._FILES]
            audit = m.audit_public_checkout(root, paths)
            self.assertNotIn("publicationAuthorized", audit)
            self.assertNotIn("academicPass", audit)


    def test_tampered_v15_prevents_any_remote_operations(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = [f"{s}/{f}" for s in m._SECTIONS for f in m._FILES]
            ready = {"gitHead": "a" * 40}
            v14 = {"status":m._V14_STATUS,
                   "realChromeRoutesPassed":9,
                   "actualRemoteGitHubDiffPaths":expected,
                   "integritySha256":"1" * 64}
            v15 = {"status":m._V15_STATUS,
                   "gitHead":"a" * 40,
                   "sourceV14ReceiptSha256":"1" * 64,
                   "taskDispatchCount":3,
                   "quarantinedTaskIds":[],
                   "nextTaskDispatchActuallyExecuted":True,
                   "publicMergeExecuted":False,
                   "publicDeployExecuted":False,
                   "publicationAuthorized":False,
                   "integritySha256":"f" * 64}
            def read_receipt(path):
                return v15 if str(path).endswith(m._V15) else v14
            with (patch.object(m,"_v13_preflight",
                       return_value=(root,{},{},"testbranch",expected)),
                  patch.object(m,"_verify_v13",
                       return_value={"publicReviewBranchSha":"2"*40}),
                  patch.object(m,"_trusted_json",side_effect=read_receipt),
                  patch.object(m,"_ls_remote") as network,
                  patch.object(m,"_read_gh_json") as github):
                with self.assertRaisesRegex(ValueError,
                                            "V16_GENUINE_SIGNED_V15_REQUIRED"):
                    m.run_public_pr_security_accessibility(
                        root,root,ready,{}, {}, {}, {}, v14, v15)
                network.assert_not_called()
                github.assert_not_called()

if __name__ == "__main__":
    unittest.main()
