"""BOSLA BSA237 V16: source-pinned public draft PR security/a11y preflight.

Read-only technical evidence, NOT a full penetration test, WCAG certification,
academic acceptance, independent reviewer approval, merge or publication.
Runs after a genuine signed V15 within the normal Yoga6 worker.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import tempfile

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import (
    _REMOTE, _MAIN, _REPO, _ls_remote, _preflight as _v13_preflight,
)
from app_generator.runtime.v3_public_pr_independent_browser_acceptance import (
    _verify_v13, _check_pr_snapshot, _check_pr_diff, _read_gh_json,
    _V14, _STATUS as _V14_STATUS,
)
from app_generator.runtime.v3_global_post_pr_readonly_roadmap import (
    _V15, _STATUS as _V15_STATUS,
)

_V16 = "V16_PR_SECURITY_ACCESSIBILITY_PREFLIGHT.json"
_STATUS = "SOURCE_PINNED_PR_SECURITY_A11Y_TECHNICAL_PREFLIGHT_NO_RELEASE"
_SECTIONS = ("section-9-1", "section-9-2", "section-9-6")
_LANGUAGES = ("en", "ms", "zh")
_FILES = ("index.html", "app/app.js", "app/domain-renderers.js",
          "app/domain-styles.css", "app/styles.css",
          "app/visual-renderers.js", "content/package.json")
_UNSAFE_JS = (
    r"\.innerHTML\s*=", r"\.outerHTML\s*=", r"\bdocument\.write\s*\(",
    r"\beval\s*\(", r"\bnew\s+Function\s*\(",
    r"\blocalStorage\s*\.\s*setItem\s*\(",
    r"\bsessionStorage\s*\.\s*setItem\s*\(",
)


class _Markup(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.nodes = []
    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


def _check_page(markup: str) -> None:
    parsed = _Markup()
    parsed.feed(markup)
    if not (
        any(t == "html" and a.get("lang") == "en" for t, a in parsed.nodes)
        and any(t == "main" for t, _ in parsed.nodes)
        and any(t == "meta" and a.get("name") == "viewport"
                for t, a in parsed.nodes)
        and any(t == "select" and a.get("id") == "locale"
                and a.get("aria-label") for t, a in parsed.nodes)
        and any(t == "section" and a.get("id") == "app"
                and a.get("aria-live") == "polite"
                for t, a in parsed.nodes)
    ):
        raise ValueError("V16_REQUIRED_DOCUMENT_ACCESSIBILITY_STRUCTURE_MISSING")
    for t, attrs in parsed.nodes:
        if any(k.startswith("on") for k in attrs):
            raise ValueError("V16_INLINE_EVENT_HANDLER_REFUSED")
        for k in ("src", "href"):
            value = attrs.get(k, "")
            if re.match(r"(?i)^(https?:|data:|javascript:|//)", value):
                raise ValueError("V16_EXTERNAL_OR_ACTIVE_RESOURCE_REFUSED")
    src = [a.get("src") for t, a in parsed.nodes if t == "script"]
    if src != ["app/domain-renderers.js", "app/visual-renderers.js",
               "app/app.js"]:
        raise ValueError("V16_SCRIPT_ALLOWLIST_MISMATCH")


def _check_package(raw: str) -> dict:
    obj = json.loads(raw)
    if not isinstance(obj, dict) or obj.get("status") != "draft":
        raise ValueError("V16_PUBLIC_PACKAGE_STATUS_NOT_DRAFT")
    acts = obj.get("activities")
    if not isinstance(acts, list) or len(acts) != 18:
        raise ValueError("V16_EXPECTED_18_ACTIVITIES_MISSING")
    seen = set()
    for activity in acts:
        if not isinstance(activity, dict) or not isinstance(activity.get("id"), str):
            raise ValueError("V16_ACTIVITY_ID_INVALID")
        if activity["id"] in seen:
            raise ValueError("V16_ACTIVITY_ID_DUPLICATE")
        seen.add(activity["id"])
        accessibility = activity.get("accessibilityText")
        if not isinstance(accessibility, dict) or any(
            not isinstance(accessibility.get(lang), str)
            or not accessibility[lang].strip()
            for lang in _LANGUAGES
        ):
            raise ValueError("V16_TRILINGUAL_ACCESSIBILITY_TEXT_MISSING")
    return {"activityCount": len(acts),
            "nonemptyTrilingualAccessibilityCount": len(acts),
            "packageStatus": "draft"}


def audit_public_checkout(checkout: Path, expected_paths: list[str]) -> dict:
    """Audit all 21 pinned modified PR files; no source text in receipt."""
    expected = [f"{section}/{f}" for section in _SECTIONS for f in _FILES]
    if len(expected_paths) != 21 or set(expected_paths) != set(expected):
        raise ValueError("V16_EXACT_21_PATH_SCOPE_REQUIRED")
    result = []
    for section in _SECTIONS:
        folder = checkout / section
        parts = {}
        for filename in _FILES:
            path = folder / filename
            if path.is_symlink() or not path.is_file():
                raise ValueError("V16_MISSING_OR_LINKED_PUBLIC_FILE")
            parts[filename] = path.read_text(encoding="utf-8")
        _check_page(parts["index.html"])
        for name in ("app/app.js", "app/domain-renderers.js",
                     "app/visual-renderers.js"):
            if any(re.search(pattern, parts[name]) for pattern in _UNSAFE_JS):
                raise ValueError("V16_POTENTIALLY_UNSAFE_DYNAMIC_JS_SINK")
        if "fetch(packageUrl)" not in parts["app/app.js"]:
            raise ValueError("V16_LOCAL_PACKAGE_FETCH_NOT_CONFIRMED")
        # BSA239: a locale control is not accessible when translations
        # render but the HTML document continues advertising English.
        if "document.documentElement.lang = requestedLocale" not in parts["app/app.js"]:
            raise ValueError("V16_TRANSLATED_DOCUMENT_LANGUAGE_NOT_SYNCHRONIZED")
        css = parts["app/styles.css"] + parts["app/domain-styles.css"]
        if ":focus-visible" not in css:
            raise ValueError("V16_KEYBOARD_FOCUS_STYLE_MISSING")
        if "prefers-reduced-motion" not in css:
            raise ValueError("V16_REDUCED_MOTION_STYLE_MISSING")
        package = _check_package(parts["content/package.json"])
        result.append({"section": section, **package,
                       "documentLandmarksPresent": True,
                       "keyboardFocusRulePresent": True,
                       "reducedMotionRulePresent": True,
                       "unsafeJsSinkPatternDetected": False})
    return {"changedFileCount": len(expected),
            "sections": result, "totalActivities": 54}


def run_public_pr_security_accessibility(
    repo: Path, private: Path, ready: dict, v9: dict, v11: dict,
    v12: dict, v13_result: dict, v14_result: dict, v15_result: dict,
) -> dict:
    folder, _, _, branch, expected_paths = _v13_preflight(
        repo, private, ready, v9, v11, v12)
    v13 = _verify_v13(folder, v13_result, ready)
    v14 = _trusted_json(folder / _V14)
    v15 = _trusted_json(folder / _V15)
    if (v14 != v14_result or v14.get("status") != _V14_STATUS
            or v14.get("realChromeRoutesPassed") != 9
            or v14.get("actualRemoteGitHubDiffPaths") != expected_paths
            or v15 != v15_result
            or v15.get("status") != _V15_STATUS
            or v15.get("integritySha256") != _hash({
                k: v for k, v in v15.items() if k != "integritySha256"})
            or v15.get("gitHead") != ready["gitHead"]
            or v15.get("sourceV14ReceiptSha256") != v14.get("integritySha256")
            or v15.get("taskDispatchCount") != 3
            or v15.get("quarantinedTaskIds") != []
            or v15.get("nextTaskDispatchActuallyExecuted") is not True
            or any(v15.get(k) is not False for k in
                   ("publicMergeExecuted", "publicDeployExecuted",
                    "publicationAuthorized"))):
        raise ValueError("V16_GENUINE_SIGNED_V15_REQUIRED")
    if _ls_remote("main") != _MAIN or (
        _ls_remote(branch) != v13["publicReviewBranchSha"]
    ):
        raise ValueError("V16_PUBLIC_BASE_OR_PR_BRANCH_CHANGED")
    n = v13["publicPullRequestNumber"]
    _check_pr_snapshot(_read_gh_json(f"pulls/{n}"), v13)
    paths = _check_pr_diff(
        _read_gh_json(f"pulls/{n}/files?per_page=100"), v13)
    if paths != expected_paths:
        raise ValueError("V16_PUBLIC_PR_DIFF_CHANGED")
    with tempfile.TemporaryDirectory(prefix="bosla-v16-", dir=private) as tmp:
        checkout = Path(tmp) / "public-pr"
        run = subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch,
             _REMOTE, str(checkout)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=90, check=False)
        if run.returncode:
            raise ValueError("V16_SOURCE_PINNED_READONLY_CLONE_FAILED")
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout,
                             capture_output=True, text=True, check=True,
                             encoding="utf-8", timeout=20).stdout.strip()
        if sha != v13["publicReviewBranchSha"]:
            raise ValueError("V16_PUBLIC_CLONE_HEAD_CHANGED")
        audit = audit_public_checkout(checkout, paths)
    payload = {
        "contract": "BOSLA_V16_SOURCE_PINNED_PR_SECURITY_A11Y_PREFLIGHT",
        "status": _STATUS,
        "gitHead": ready["gitHead"],
        "sourceV15ReceiptSha256": v15["integritySha256"],
        "publicPrNumber": n,
        "publicPrHeadSha": v13["publicReviewBranchSha"],
        "publicPrDraft": True,
        "technicalEvidence": audit,
        "fullSecurityAssessmentComplete": False,
        "screenReaderWCAGCertificationComplete": False,
        "independentScientificAcceptanceComplete": False,
        "publicationAuthorized": False,
        "publicMergeExecuted": False,
        "publicDeployExecuted": False,
        "schedulerReinstalled": False,
        "nextEligibleMilestone": "INDEPENDENT_SCREENREADER_SECURITY_AND_ACADEMIC_RELEASE_GATES",
    }
    return _v6_checkpoint(folder / _V16, payload)
