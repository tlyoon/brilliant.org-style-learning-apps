"""Automatic private repair dispatch for independently flagged academic errors.

One repair session per bounded attempt. It never installs a candidate and
requires fresh independent reviewer revalidation of any generated revision.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable

from app_generator.gemini.academic_reviewers import (
    DirectGeminiReviewer, ReviewerBrowser,
)
from app_generator.runtime.run_context import RunContext
from app_generator.validation.autonomous_repair import propose_private_repair

NEUTRAL_CHAT="https://gemini.google.com/app"

def dispatch_repair_queue(
    config:Any,run:RunContext,review_report:dict[str,Any],
    source_contexts:dict[str,dict[str,Any]],source_pdf:Path,
    *, repair_browser_factory:Callable[...,Any]=ReviewerBrowser,
    attempt:int=1,
) -> list[dict[str,Any]]:
    receipts=review_report.get("receipts",[])
    package_sha=review_report.get("packageSha256")
    if not isinstance(receipts,list) or not isinstance(package_sha,str):
        raise ValueError("independent model receipt report not available")
    if source_pdf is None or not source_pdf.is_file():
        raise ValueError("controlled source PDF required for repair")
    results=[]
    for record in receipts:
        if record.get("nextAction")!="AUTO_REPAIR":
            continue
        activity_id=record.get("activityId")
        if not isinstance(activity_id,str) or activity_id not in source_contexts:
            raise ValueError("repair source is missing for a recorded activity")
        source=source_contexts[activity_id]
        if source.get("sourceSha256")!=review_report.get("sourceSha256"):
            raise ValueError("wrong original textbook source for repair")
        gates=record.get("gates",{})
        objections=[
            x.get("issue")
            for v in gates.values() for x in v.get("reports",[])
            if x.get("verdict")=="CONTRADICTED" and isinstance(x.get("issue"),str)
            and len(x.get("issue").strip())>=12
        ]
        if not objections:
            results.append({"activityId":activity_id,"nextAction":"AUTO_SOURCE_CHECK",
                            "reason":"contradiction lacks a concrete reviewed issue"})
            continue
        profile=config.chrome_profile_dir/"academic-reviewers"/"repair"/"gemini-browser"
        if not profile.is_dir():
            results.append({"activityId":activity_id,"nextAction":"AUTO_RETRY",
                            "reason":"dedicated independent repair browser profile not available"})
            continue
        activity=record.get("originalActivity")
        # A stored AI report contains only the source-bound activity ID+hash.
        # The caller must independently supply the *actual* exact activity.
        if not isinstance(activity,dict) or activity.get("id")!=activity_id:
            results.append({"activityId":activity_id,"nextAction":"AUTO_SOURCE_CHECK",
                            "reason":"exact original activity required for repair"})
            continue
        private_dir=(run.validation/"academic-repair-candidates"/
                     (sha256(activity_id.encode("utf-8")).hexdigest()[:12]+f"-{attempt:02d}"))
        browser=repair_browser_factory("repair",
            replace(config,gem_url=NEUTRAL_CHAT,gem_edit_url=NEUTRAL_CHAT),source_pdf)
        try:
            browser.open()
            response=propose_private_repair(
                run=run,activity=activity,source=source,
                objections=objections,package_sha256=package_sha,
                model=DirectGeminiReviewer(browser.client),attempt=attempt,
                private_dir=private_dir,
            )
            results.append({"activityId":activity_id,
                            "nextAction":response["status"],
                            "candidateSha256":response.get("candidateSha256"),
                            "independentReverificationRequired":True})
        except Exception as exc:
            # Provider may have received an in-flight request; only a
            # source-/request-bound checkpoint may authorize a replay.
            results.append({"activityId":activity_id,"nextAction":"AUTO_RETRY",
                            "reason":"reconcile repair session: "+type(exc).__name__})
        finally:
            browser.close()
    return results
