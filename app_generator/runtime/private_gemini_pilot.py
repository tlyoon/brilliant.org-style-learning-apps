"""Controlled one-activity Gemini academic pilot with exact private sources.

Fails closed when dedicated reviewer profiles are absent. No cookies, sessions,
private PDFs or source passages are copied into the Git checkout.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.config import GeneratorConfig
from app_generator.gemini.academic_reviewers import IndependentReviewerFactory
from app_generator.runtime.autonomous_academic import review_batch_autonomously
from app_generator.runtime.run_context import RunContext
from app_generator.validation.reviewer_source_packets import verified_source_packet
from app_generator.validation.impulse_v3_audit import audit_v3

NEUTRAL_GEM_URL="https://gemini.google.com/app"
ACTIVITY_ID="int-select-isolated-conditions"


def exact_v3_context(v3_package:Path,v3_review:Path,v2_package:Path,
                     v2_review:Path,source_pdf:Path,
                     original_anchor:dict[str,Any]) -> dict[str,Any]:
    audit=audit_v3(v3_package,v3_review,v2_package,v2_review,source_pdf)
    source_sha=audit["sourceSha256"]
    if original_anchor.get("activityId")!=ACTIVITY_ID:
        raise ValueError("original source anchor does not address requested v3 activity")
    packet=verified_source_packet(source_pdf,source_sha,ACTIVITY_ID,[original_anchor])
    # Independent literal re-location is not proof of new semantic meaning.
    packet["sourceInterpretationVerified"]=False
    packet["derivedFromPriorAnchorOnly"]=True
    return packet


def readiness(config:GeneratorConfig,package:Path,
              source_pdf:Path,source_context:dict[str,Any],
              *, existing_login:bool=False) -> dict[str,Any]:
    if config.browser_mode!="controlled" or config.llm_backend!="gemini_browser":
        raise ValueError("pilot needs isolated, non-API controlled Gemini browser mode")
    if sha256(source_pdf.read_bytes()).hexdigest()!=source_context.get("sourceSha256"):
        raise ValueError("pilot source PDF hash does not match verified passage")
    if source_context.get("activityId")!=ACTIVITY_ID or not source_context.get("sourceEvidence"):
        raise ValueError("source passage not present for controlled pilot activity")
    pkg=json.loads(package.read_text(encoding="utf-8"))
    if sum(a.get("id")==ACTIVITY_ID for a in pkg.get("activities",[]))!=1:
        raise ValueError("pilot activity missing or duplicated")
    expected_paths=[
        config.chrome_profile_dir/"academic-reviewers"/role/"gemini-browser"
        for role in ("physics","semantics")
    ]
    if existing_login:
        # Existing authorized original Chrome profile is an eligible
        # candidate only. Its authentication is verified LIVE by
        # ExistingLoginReviewerFactory, not inferred from Preferences.
        root=config.chrome_profile_dir/"gemini-browser"
        provisioned=[root.is_dir(),(root/"Default"/"Preferences").is_file()]
    else:
        provisioned=[path.is_dir() for path in expected_paths]
    return {
        "sourceSha256":source_context["sourceSha256"],
        "packageSha256":sha256(package.read_bytes()).hexdigest(),
        "activityId":ACTIVITY_ID,
        "distinctReviewerProfilesProvisioned":provisioned if not existing_login else [False,False],
        "existingAuthorizedProfileEvidence":provisioned if existing_login else [],
        "reviewerIsolation":"separate_new_conversations_same_google_account" if existing_login else "separate_browser_profiles",
        "independentGoogleAccounts":False if existing_login else None,
        "readyToAttemptBrowserReview":all(provisioned),
        "authenticated":False,  # directory presence alone proves no login
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
    }


def run_private_pilot(
    config:GeneratorConfig,package:Path,source_pdf:Path,source_context:dict[str,Any],
    *,
    run_directory:Path,
    reviewer_factory_type=IndependentReviewerFactory,
    existing_login:bool=False,
) -> dict[str,Any]:
    preflight=readiness(config,package,source_pdf,source_context,
                        existing_login=existing_login)
    if not preflight["readyToAttemptBrowserReview"]:
        return {**preflight,"status":"BLOCKED_NO_INDEPENDENT_BROWSER_PROFILE",
                "aiReviewedActivities":0,
                "nextAction":"Provision two independently authenticated review profiles without copying author session; meanwhile continue safe coding."}
    if run_directory.exists():
        raise ValueError("private pilot run directory already exists")
    if run_directory.resolve().is_relative_to(config.repo_root.resolve()):
        raise ValueError("private Gemini review receipts must remain outside repository")
    # Reviewers must be independent of the author's customized Gem.
    review_config=replace(config,gem_url=NEUTRAL_GEM_URL,
                          gem_edit_url=NEUTRAL_GEM_URL)
    activity=next(a for a in json.loads(package.read_text(encoding="utf-8"))["activities"]
                  if a["id"]==ACTIVITY_ID)
    with reviewer_factory_type(review_config,source_pdf) as reviewers:
        ctx=RunContext.create(run_directory)
        report=review_batch_autonomously(
            ctx,{"activities":[activity]},
            package_sha256=preflight["packageSha256"],
            source_sha256=preflight["sourceSha256"],
            authorized_source={ACTIVITY_ID:source_context},
            reviewer_factory=reviewers.open_pair,
        )
    return {**preflight,"status":"AI_REVIEW_ATTEMPTED",
            "aiReviewedActivities":report["aiReviewedActivities"],
            "nextActions":report["followupCounts"],"academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False}
