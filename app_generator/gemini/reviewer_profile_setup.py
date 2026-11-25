"""Provision separate ordinary Chrome sign-in windows for academic reviewers.

Never reuses browser cookies or the author's profile. No Selenium connection,
model request, textbook upload, credential read, or publication is performed.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from app_generator.browser.chrome import ChromeSession
from app_generator.config import GeneratorConfig

NEUTRAL_GEMINI = "https://gemini.google.com/app"
ROLES = ("physics", "semantics")


def _profile_base(config: GeneratorConfig) -> Path:
    if config.browser_mode != "controlled":
        raise ValueError("independent sign-in requires controlled Chrome mode")
    base=config.chrome_profile_dir
    if not base.is_absolute():
        raise ValueError("independent Chrome profile root must be absolute")
    if base.resolve().is_relative_to(config.repo_root.resolve()):
        raise ValueError("independent sign-in profiles cannot be stored in Git checkout")
    return base


def role_browser_config(config: GeneratorConfig, role: str) -> GeneratorConfig:
    if role not in ROLES:
        raise ValueError("only independently assigned reviewer roles can sign in")
    _profile_base(config)
    # This is a reviewer-only override, never mutate generator settings.
    return replace(
        config,
        chrome_profile_dir=config.chrome_profile_dir / "academic-reviewers" / role,
        gem_url=NEUTRAL_GEMINI,
        gem_edit_url=NEUTRAL_GEMINI,
        llm_backend="gemini_browser",
    )


def inspect_reviewer_profiles(config: GeneratorConfig) -> dict[str, Any]:
    _profile_base(config)
    details=[]
    for role in ROLES:
        cfg=role_browser_config(config,role)
        location=cfg.chrome_profile_dir/"gemini-browser"
        has_directory=location.is_dir()
        # Chrome preferences are not proof of login, and are never opened.
        initialized=(location/"Default"/"Preferences").is_file()
        details.append({
            "role":role,
            "profileExists":has_directory,
            "chromeInitialized":initialized,
            "authenticated":False,
            "requiresLoginVerification":True,
        })
    return {
        "status":"PREFLIGHT_ONLY",
        "backend":"gemini_browser",
        "usingPaidApi":False,
        "profiles":details,
        "distinctProfiles":True,
        "browserResponseCaptured":False,
        "fullAcademicReviewVerified":False,
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
    }


def open_missing_signin_windows(
    config: GeneratorConfig,
    *,
    launcher: Callable[[GeneratorConfig], Any] = ChromeSession,
) -> dict[str, Any]:
    """Only open distinct absent Chrome profiles; never replace existing ones.

    No attempt is made to sign in on behalf of an owner; the user must
    authenticate in each dedicated window using Google's normal UI.
    """
    status=inspect_reviewer_profiles(config)
    launched=[]
    skipped=[]
    for role in ROLES:
        cfg=role_browser_config(config,role)
        location=cfg.chrome_profile_dir/"gemini-browser"
        if location.exists():
            skipped.append(role)
            continue
        if location.parent.exists() and any(location.parent.iterdir()):
            # A partly provisioned reviewer root needs investigation.
            raise ValueError(f"{role} reviewer directory contains unexpected files")
        browser=launcher(cfg)
        browser.open_window()
        launched.append(role)
    status=inspect_reviewer_profiles(config)
    return {
        **status,
        "status":"SIGNIN_WINDOWS_OPENED" if launched else "SIGNIN_PROFILES_ALREADY_EXIST",
        "launchedRoles":launched,
        "skippedExistingRoles":skipped,
        "requiresOwnerLogin":bool(launched),
        "browserResponseCaptured":False,
        "publicationAuthorized":False,
    }
