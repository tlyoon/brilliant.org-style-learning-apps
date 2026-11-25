"""BSA240 CI: real source-free Chrome AX tree acceptance with fault injection."""
from __future__ import annotations
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app_generator.runtime.v3_public_pr_accessibility_tree import (
    audit_real_chrome_accessibility_tree,
)
from scripts.check_course_preview_browser import stage_site

PAGES = tuple(("app/index.html",
               f"../content/chapter-9/section-9-{n}/package.json")
              for n in (1, 2, 6))


def run():
    with TemporaryDirectory(prefix="bosla-ax-sourcefree-") as tmp:
        site = Path(tmp)
        stage_site(site)
        result = audit_real_chrome_accessibility_tree(site, PAGES)
        if (result["localeAccessibilityTreeChecks"] != 9
                or result["unnamedControls"] != 0):
            raise ValueError("BSA240_SOURCEFREE_AX_COVERAGE_INCOMPLETE")
        # Real-browser fault injection: replace the production document-language
        # synchronization. The next Chrome run MUST refuse Malay/Chinese.
        app = site / "app" / "app.js"
        code = app.read_text(encoding="utf-8")
        needle = "document.documentElement.lang = requestedLocale;"
        if code.count(needle) != 1:
            raise ValueError("BSA240_CANONICAL_LOCALE_HANDLER_CHANGED")
        app.write_text(code.replace(
            needle, 'document.documentElement.dataset.locale = requestedLocale;'
        ), encoding="utf-8")
        refused = False
        try:
            audit_real_chrome_accessibility_tree(site, PAGES[:1])
        except ValueError as exc:
            refused = "BSA240_DOCUMENT_LANGUAGE_OR_RENDER_MISMATCH" in str(exc)
        if not refused:
            raise ValueError("BSA240_REAL_CHROME_NEGATIVE_CONTROL_NOT_REJECTED")
        print(json.dumps({
            "status": "BSA240_SOURCEFREE_REAL_CHROME_AX_AND_FAULT_INJECTION_PASS",
            **result,
            "faultInjectedLanguageMismatchRejected": True,
            "sourceFreeSyntheticOnly": True,
            "realLearnerScreenReaderWCAGCertified": False,
            "publicationAuthorized": False,
        }, sort_keys=True))


if __name__ == "__main__":
    run()
