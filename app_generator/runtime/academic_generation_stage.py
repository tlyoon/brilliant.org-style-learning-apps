"""Automatic, nonblocking post-generation AI academic QA stage.

Missing source packets or unavailable independent browser sessions create
machine-actionable pending work, never a request for human academic signoff.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.filesystem.outputs import write_json_atomic
from app_generator.gemini.academic_reviewers import IndependentReviewerFactory
from app_generator.gemini.reviewer_ownership_gate import reviewer_ownership_preflight
from app_generator.runtime.autonomous_academic import review_batch_autonomously
from app_generator.runtime.run_context import RunContext
from app_generator.runtime.academic_repair_stage import dispatch_repair_queue
from app_generator.runtime.bounded_recovery_stage import maybe_run_bounded_recovery
from app_generator.runtime.academic_source_provision import provision_run_source_packets
from app_generator.validation.source_passages import extract_pages
from app_generator.validation.autonomous_ai_review import canonical_digest
from app_generator.validation.reviewer_source_packets import verified_source_packet

NEUTRAL_CHAT = "https://gemini.google.com/app"


def run_academic_stage(
    config: Any,
    context: RunContext,
    package_file: Path,
    source_pdf: Path | None,
    *,
    reviewer_factory_type=IndependentReviewerFactory,
) -> dict[str, Any]:
    if context.validation.resolve().is_relative_to(config.repo_root.resolve()):
        raise ValueError("academic source evidence cannot be stored in public repository")
    pkg_bytes=package_file.read_bytes()
    package_sha=sha256(pkg_bytes).hexdigest()
    package=json.loads(pkg_bytes.decode("utf-8"))
    activities=package.get("activities", [])
    # Legacy generator fixtures and incomplete recovery may temporarily
    # contain no learner-facing activities. Record a private deferred
    # machine check instead of failing an otherwise safe local run.
    if not activities:
        result={
            "packageSha256":package_sha,"sourceSha256":None,
            "activitiesTotal":0,"sourceReady":0,
            "queue":[{"activityId":"PACKAGE","nextAction":"AUTO_SOURCE_CHECK",
                      "reason":"no academic activities available for independent review"}],
            "humanAcademicApprovalRequired":False,"academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False,
        }
        write_json_atomic(context.validation/"autonomous-academic-queue.json",result)
        return result
    if not isinstance(activities,list) or any(
        not isinstance(a,dict) or not isinstance(a.get("id"),str) or not a["id"]
        for a in activities
    ):
        raise ValueError("installed package lacks identified academic activities")
    ids=[a["id"] for a in activities]
    if len(set(ids))!=len(ids):
        raise ValueError("duplicated installed academic activity identifiers")
    packet_path=context.validation/"academic-review-source-packets.json"
    provision={"status":"NO_PRIVATE_PROVENANCE_REGISTRY","packetCreated":False}
    if hasattr(config,"state_dir"):
        try:
            provision=provision_run_source_packets(config,context,package_file,source_pdf)
        except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError) as exc:
            provision={"status":"AUTO_SOURCE_CHECK","packetCreated":False,
                       "errorType":type(exc).__name__}
    queue=[]
    eligible=[]
    contexts={}
    source_sha=None
    if packet_path.is_file():
        try:
            packets=json.loads(packet_path.read_text(encoding="utf-8"))
        except (ValueError,OSError,TypeError):
            packets={}
        if (packets.get("packageSha256")!=package_sha or
            not isinstance(packets.get("packets"),dict)):
            # Stale source evidence is a source-recovery action, not a PASS.
            packets={}
        else:
            source_sha=packets.get("sourceSha256")
            page_cache=None
            if source_pdf is not None and source_pdf.is_file():
                try:
                    if sha256(source_pdf.read_bytes()).hexdigest()==source_sha:
                        page_cache=extract_pages(source_pdf)
                except (ValueError,OSError):
                    page_cache=None
            for a in activities:
                packet=packets["packets"].get(a["id"])
                if (isinstance(packet,dict) and packet.get("sourceSha256")==source_sha and
                    packet.get("activityId")==a["id"] and
                    isinstance(packet.get("sourceEvidence"),str) and
                    len(packet["sourceEvidence"])>=40 and
                    isinstance(packet.get("verifiedPages"),list) and
                    packet["verifiedPages"]):
                    # The received private packet is still untrusted.
                    # Revalidate its literal quote against the exact PDF
                    # before any new AI submission, never just hash JSON.
                    if page_cache is not None:
                        try:
                            trusted=verified_source_packet(
                                source_pdf,source_sha,a["id"],
                                packet.get("sourceAnchors",[]),
                                extractor=lambda _:page_cache,
                            )
                        except (ValueError,OSError):
                            trusted=None
                        if (trusted is not None and
                            trusted["sourceEvidence"]==packet["sourceEvidence"] and
                            trusted["passageSha256"]==packet.get("passageSha256")):
                            eligible.append(a)
                            contexts[a["id"]]=trusted
    for id_ in ids:
        if id_ not in contexts:
            queue.append({"activityId":id_,"nextAction":"AUTO_SOURCE_CHECK",
                          "reason":"source passage absent or stale; automatically regenerate source packet"})
    if source_sha and (source_pdf is None or not source_pdf.is_file()
                       or sha256(source_pdf.read_bytes()).hexdigest()!=source_sha):
        queue=[{"activityId":id_,"nextAction":"AUTO_SOURCE_CHECK",
                "reason":"controlled local PDF not available for independent review"} for id_ in ids]
        eligible=[]
    if eligible and config.llm_backend=="gemini_browser" and config.browser_mode=="controlled":
        profiles=[config.chrome_profile_dir/"academic-reviewers"/role/"gemini-browser"
                  for role in ("physics","semantics")]
        profiles_exist=all(p.is_dir() for p in profiles)
        ownership=(reviewer_ownership_preflight(config.chrome_profile_dir,config.repo_root)
                   if profiles_exist else None)
        if profiles_exist and ownership["canAttemptIndependentBrowserReview"]:
            review_config=replace(config,gem_url=NEUTRAL_CHAT,gem_edit_url=NEUTRAL_CHAT)
            try:
                with reviewer_factory_type(review_config,source_pdf) as reviewer_pool:
                    def sessions(activity_id:str):
                        reviewer_pool.close()
                        return reviewer_pool.open_pair(activity_id)
                    report=review_batch_autonomously(
                        context,{"activities":eligible},
                        package_sha256=package_sha,source_sha256=source_sha,
                        authorized_source=contexts,reviewer_factory=sessions,
                    )
                # Bind model objections back to the actual installed
                # activity, not model-generated/reconstructed question text.
                for reviewed in report["receipts"]:
                    actual=next((a for a in eligible if a["id"]==reviewed["activityId"]),None)
                    if actual is None or canonical_digest(actual)!=reviewed["activityCanonicalSha256"]:
                        raise ValueError("AI repair claim does not match exact installed activity")
                    reviewed["originalActivity"]=actual
                queue.extend(report["followups"])
                queue.extend(dispatch_repair_queue(
                    review_config,context,report,contexts,source_pdf,
                ))
            except Exception as exc:
                # In-flight requests are preserved by RunContext. Do not
                # automatically submit again after provider state ambiguity.
                queue.extend({
                    "activityId":a["id"],"nextAction":"AUTO_RETRY",
                    "reason":"reconcile independent browser academic session: "+type(exc).__name__,
                } for a in eligible)
        else:
            queue.extend({
                "activityId":a["id"],"nextAction":"AUTO_RETRY",
                "reason":("dedicated independent browser profiles are not provisioned"
                          if not profiles_exist else
                          "dedicated reviewer Chrome profiles occupied or ownership unknown; defer safely"),
            } for a in eligible)
    elif eligible:
        queue.extend({
            "activityId":a["id"],"nextAction":"AUTO_RETRY",
            "reason":"configured provider is not the independently provisioned non-API Gemini browser",
        } for a in eligible)
    output={
        "packageSha256":package_sha,
        "sourceSha256":source_sha,
        "activitiesTotal":len(ids),
        "sourceReady":len(eligible),
        "queue":queue,
        "automaticSourceProvisioning":provision,
        "humanAcademicApprovalRequired":False,
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
    }
    # Optional private exact-baseline recovery is a separate bounded action.
    # It NEVER overwrites the original package or turns provider absence into PASS.
    try:
        recovery=maybe_run_bounded_recovery(
            run=context,repository=config.repo_root,
            package_file=package_file,source_pdf=source_pdf,
        )
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
        recovery={"state":"BLOCKED","nextAction":"AUTO_SOURCE_CHECK",
                  "errorClass":type(exc).__name__,"academicQA":"REVIEW_REQUIRED",
                  "publicationAuthorized":False}
    if recovery is not None:
        output["boundedRecovery"]=recovery
        output["queue"].append({
            "activityId":recovery.get("activityId","BOUND_RECOVERY"),
            "nextAction":recovery["nextAction"],
            "reason":"controlled private rollback needs a separate independent review",
        })
    write_json_atomic(context.validation/"autonomous-academic-queue.json",output)
    return output
