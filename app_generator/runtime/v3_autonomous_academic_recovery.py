"""BSA251 / V24: executable academic recovery loop in ordinary Yoga6 worker.

History FIRST, not an unbounded generic agent. This bounded dispatcher
executes real independent source, domain, arithmetic, numeric and reviewer
provenance verifiers, classifies proof gaps separately from repairable defects,
and writes a signed version-bound continuation queue. On repeated execution,
the same evidence and actions are rechecked without new model requests.

The historical recurrence registry is DATA, not Python to eval/import.
Approved handlers below are statically wired, tied to resolved IDs, and
never upgrade a source-page/AI-consensus/negative-pattern check to full PASS.
Unknown defects and genuinely missing proof stop explicitly, rather than
reporting pipeline success or demanding a human by default.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import (
    _V21, _RESULT21, _signed, independently_rebind_revision,
)
from app_generator.runtime.v3_exact_revised_review_reconciliation import (
    _V22, _RESULT22, _STATUS22, _CANDIDATE,
)
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _PACKAGE, _SOURCE_BINDING, _bounded_math_witnesses, _bounded_mcq_labels,
)
from app_generator.runtime.v3_malay_auto_revision import _RECEIPT as _MALAY_REPAIR
from app_generator.runtime.v3_revised91_fresh_model_reviews import (
    fresh_revised91_inputs,
)
from app_generator.runtime.v3_section96_authorized_revised_qa import (
    unsent_revised_input, read_prior_two_role_science,
)
from app_generator.runtime.v3_standing_paid_science import (
    section91_evidence, verified_section91_standing_passes,
)
from app_generator.validation.academic_acceptance_matrix import audit_activity_matrix
from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.multilingual_numeric_triage import _scan_activity

_V24 = "V24_AUTONOMOUS_ACADEMIC_RECOVERY_DISPATCH.json"
_PRE = "V24_ACADEMIC_RECOVERY_PRE_CALL.json"
_RESULT = "V24_ACADEMIC_RECOVERY_EXECUTED_EVIDENCE_QUEUE.json"
_STATUS = "V24_BOUNDED_HISTORY_FIRST_ACADEMIC_DISPATCH_EXECUTED_PROOFS_OPEN"
_MAX_ROUNDS = 2

# A fixed, auditable execution table: registry strings are never executable.
# A remedy marked disabled/retired cannot be silently invoked.
_DISPATCH = {
    "VERIFY_SELECTED_SOURCE": (
        "BSA-20261122-248",
        "app_generator/runtime/v3_revised_source_proof_rebinding.py",
    ),
    "VERIFY_DOMAIN_AND_ANSWER_SHAPES": (
        "BSA-20261122-247",
        "app_generator/runtime/v3_historical_academic_audit.py",
    ),
    "VERIFY_BOUNDED_PHYSICS": (
        "BSA-20261122-244",
        "app_generator/runtime/v3_selected_textbook_scientific_provenance.py",
    ),
    "VERIFY_NUMERIC_TRANSLATIONS": (
        "BSA-20261122-248",
        "app_generator/runtime/v3_revised_source_proof_rebinding.py",
    ),
    "RECONCILE_HISTORIC_REVIEW_CLAIMS": (
        "BSA-20261122-249",
        "app_generator/runtime/v3_exact_revised_review_reconciliation.py",
    ),
    "RECONCILE_NEW_REVISED_REVIEW_CLAIMS": (
        "BSA-20261122-250",
        "app_generator/runtime/v3_revised91_fresh_model_reviews.py",
    ),
}
_GATE_ACTIONS = {
    "source_fidelity": "REQUIRES_INDEPENDENT_TEXTBOOK_MEANING_PROOF",
    "answer_correctness": "REQUIRES_FULL_KEY_DISTRACTOR_INTERACTION_PROOF",
    "physics_consistency": "REQUIRES_COMPLETE_SOURCE_BOUND_PHYSICS_PROOF",
    "visual_semantics": "REQUIRES_INDEPENDENT_RENDERED_PHYSICAL_VISUAL_PROOF",
    "multilingual_meaning": "REQUIRES_EN_MS_ZH_SEMANTIC_EQUIVALENCE_PROOF",
}


def _approved_history(repo: Path) -> dict[str, str]:
    """Read actual registry and require all reviewed remedy IDs enabled."""
    path = repo / "docs" / "recurrence_registry.json"
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError("V24_HISTORY_REGISTRY_UNSAFE_OR_MISSING")
    register = json.loads(path.read_text(encoding="utf8"))
    entries = register.get("incidents") if isinstance(register, dict) else None
    if not isinstance(entries, list):
        raise ValueError("V24_HISTORY_REGISTRY_INVALID")
    by_id = {x.get("id"): x for x in entries if isinstance(x,dict)}
    if len(by_id) != len(entries):
        raise ValueError("V24_HISTORY_INCIDENT_DUPLICATE")
    for action,(ident, runtime) in _DISPATCH.items():
        row = by_id.get(ident)
        if (not isinstance(row,dict) or row.get("status") != "resolved"
                or not isinstance(row.get("automaticRemedy"),dict)
                or row["automaticRemedy"].get("runtimePath") != runtime
                or not (repo / runtime).is_file()):
            raise ValueError("V24_HISTORICAL_REMEDY_RETIRED_OR_UNVERIFIED_"+action)
    return {name:ident for name,(ident,_) in _DISPATCH.items()}


def _safe_gate_queue(report: dict, activities: list[dict],
                     *, prior_review: dict[str, str],
                     action_history: dict[str,str]) -> list[dict]:
    """Return actionable metadata for all 18 x 5 gates, never private text."""
    rows = report.get("activities")
    if not isinstance(rows,list) or len(rows)!=18:
        raise ValueError("V24_EXACT_18_ACADEMIC_ROWS_REQUIRED")
    by_id = {a["id"]:a for a in activities}
    if len(by_id)!=18:
        raise ValueError("V24_DUPLICATED_ACTIVITIES")
    queue=[]
    for row in rows:
        aid = row.get("activityId")
        if aid not in by_id or row.get("activitySha256") != sha256(
            json.dumps(by_id[aid],sort_keys=True,ensure_ascii=False,
                       separators=(",",":")).encode("utf8")).hexdigest():
            raise ValueError("V24_REVIEW_RESULT_ACTIVITY_VERSION_DRIFT")
        states = row.get("gates",{})
        if set(states)!=set(REQUIRED):
            raise ValueError("V24_MISSING_ACADEMIC_GATE")
        for gate in REQUIRED:
            observed=states[gate]
            if observed not in ("PASS","FAIL","REVIEW_REQUIRED"):
                raise ValueError("V24_UNRECOGNIZED_GATE_STATE")
            if observed=="PASS":
                # Only original independent trusted checker can issue PASS.
                action="PROOF_ALREADY_VERIFIED"
                recovery_id=None
                cls="VERIFIED"
            elif observed=="FAIL":
                # Known Malay repair is in V20, not a generic text rewrite.
                # A new FAIL on the REVISED package cannot borrow that repair.
                action="STOP_EXACT_VERSION_UNHANDLED_DETERMINISTIC_FAILURE"
                recovery_id=action_history["VERIFY_DOMAIN_AND_ANSWER_SHAPES"]
                cls="DETERMINISTIC_DEFECT"
            else:
                action=_GATE_ACTIONS[gate]
                recovery_id={
                    "source_fidelity":"VERIFY_SELECTED_SOURCE",
                    "answer_correctness":"VERIFY_DOMAIN_AND_ANSWER_SHAPES",
                    "physics_consistency":"VERIFY_BOUNDED_PHYSICS",
                    "visual_semantics":"VERIFY_DOMAIN_AND_ANSWER_SHAPES",
                    "multilingual_meaning":"VERIFY_NUMERIC_TRANSLATIONS",
                }[gate]
                recovery_id=action_history[recovery_id]
                cls="MISSING_INDEPENDENT_PROOF"
            queue.append({
                "activityId":aid,
                "exactActivitySha256":row["activitySha256"],
                "gate":gate,
                "gateState":observed,
                "failureClass":cls,
                "nextAction":action,
                "historicalRemedyId":recovery_id,
                "historicalReviewStatus":prior_review[aid],
                "publicationAuthorized":False,
            })
    if len(queue)!=90 or len({
        (x["activityId"],x["gate"]) for x in queue})!=90:
        raise ValueError("V24_GATES_INCOMPLETE_OR_DUPLICATED")
    return queue


def _review_inventory(repo: Path, private: Path,
                      source_head: str, proposal_sha: str,
                      activities: list[dict]) -> dict[str,str]:
    """Read exact immutable old and NEW V3 reviews; NEVER submit requests."""
    plan=fresh_revised91_inputs(repo=repo,private=private,
        source_head=source_head,proposal_sha=proposal_sha)
    changed = {x["activityId"]:x for x in plan["stagedReviewInputs"]}
    old = section91_evidence(repo/"content"/"chapter-9",repo,private)
    historic = verified_section91_standing_passes(
        repo/"content"/"chapter-9",repo,private)
    if (len(historic)!=17 or old.get("oldUncertainIndex")!=0
            or len(changed)!=4):
        raise ValueError("V24_OLD_AND_NEW_REVIEW_HISTORY_DRIFT")
    old_status={
        row["activityId"]:"HISTORIC_IDENTICAL_MODEL_EVIDENCE_ONLY"
        for row in historic if row["activityId"] not in changed
    }
    if len(old_status)!=13:
        raise ValueError("V24_HISTORICAL_MODEL_MATCH_COUNT_CHANGED")
    first_id=activities[0]["id"]
    if first_id in old_status or first_id in changed:
        raise ValueError("V24_ORIGINAL_UNCERTAIN_ZERO_NOT_QUARANTINED")
    statuses={first_id:"ORIGINAL_UNCERTAIN_NO_REPLAY",**old_status}
    for aid,entry in changed.items():
        if unsent_revised_input(private,entry["sha"]):
            status="NEW_MODEL_REVIEW_NOT_YET_SUBMITTED"
        else:
            # An ambiguous or partially submitted previous claim must stop;
            # it cannot be retried or silently called a PASS.
            saved=read_prior_two_role_science(private,entry)
            status=("NEW_MODEL_CONSENSUS_ADVISORY_ONLY" if saved["pass"]
                    else "NEW_MODEL_REPAIR_REQUIRED" if saved["repair"]
                    else "NEW_MODEL_ROLE_UNCERTAIN_NO_REPLAY")
        statuses[aid]=status
    if set(statuses)!={a["id"] for a in activities}:
        raise ValueError("V24_REVIEW_PROVENANCE_ROSTER_WRONG")
    return statuses


def execute_academic_evidence_cycle(
    *, repo: Path, pdf: Path, source_sha: str, original: dict,
    revised: dict, original_sha: str, revised_sha: str,
    original_anchors: list[dict], changed_ids: set[str],
    previous_review: dict[str,str], history: dict[str,str],
    revised_path: Path,
) -> dict[str, Any]:
    """Apply reviewed deterministic handlers then stop at a *true* fixed point.

    Convergence means no more supported source-free checks are eligible.
    It emphatically does NOT mean all 90 proofs are complete.
    """
    original_activity=original.get("activities")
    revised_activity=revised.get("activities")
    if (not isinstance(original_activity,list) or len(original_activity)!=18
            or not isinstance(revised_activity,list) or len(revised_activity)!=18):
        raise ValueError("V24_EXACT_ORIGINAL_AND_REVISED_ACTIVITY_ROSTER_REQUIRED")
    if (revised_path.is_symlink() or not revised_path.is_file()
            or sha256(revised_path.read_bytes()).hexdigest()!=revised_sha
            or sha256(pdf.read_bytes()).hexdigest()!=source_sha):
        raise ValueError("V24_REAL_REVISED_PACKAGE_OR_SOURCE_CHANGED")
    if set(previous_review)!={a["id"] for a in revised_activity}:
        raise ValueError("V24_REVIEW_HISTORY_DOES_NOT_COVER_CANDIDATE")
    records=[]
    prior_digest=None
    actual_queue=None
    metrics=None
    for round_index in range(1,_MAX_ROUNDS+1):
        packets,changed=independently_rebind_revision(
            pdf=pdf,source_sha=source_sha,original=original,candidate=revised,
            original_sha=original_sha,candidate_sha=revised_sha,
            original_anchors=original_anchors,
            expected_changed_ids=changed_ids,
        )
        if set(changed)!=changed_ids or len(packets["packets"])!=18:
            raise ValueError("V24_CHANGED_SOURCE_PACKET_SCOPE_MISMATCH")
        report=audit_activity_matrix(
            repo_root=repo,package_path=revised_path,source_pdf=pdf,
            source_sha256=source_sha,source_packets=packets,expected_count=18,
        )
        if (report.get("packageSha256")!=revised_sha
                or report.get("sourceSha256")!=source_sha
                or report.get("publicationAuthorized") is not False
                or len(report.get("activities",[]))!=18
                or not all(x.get("sourceLocationVerified") is True
                           for x in report["activities"])):
            raise ValueError("V24_REAL_ACADEMIC_CHECK_WRONG_SOURCE_VERSION")
        math = _bounded_math_witnesses()
        keys = _bounded_mcq_labels(revised_activity)
        if (len(math)!=6 or not all(math.values()) or len(keys)!=5):
            raise ValueError("V24_HISTORICAL_BOUNDED_PHYSICS_PROOF_FAILED")
        fields=0
        flagged=0
        for activity in revised_activity:
            checked,flags=_scan_activity(activity)
            fields+=checked
            flagged+=len(flags)
        actual_queue=_safe_gate_queue(
            report,revised_activity,prior_review=previous_review,
            action_history=history)
        count={label:sum(row["gateState"]==label for row in actual_queue)
               for label in ("PASS","FAIL","REVIEW_REQUIRED")}
        metrics={
            "evidenceSlotsEvaluated":len(actual_queue),
            "gateCounts":count,
            "distinctOriginalPdfPassagesReverified":len(packets["packets"]),
            "boundedExactMathIdentities":len(math),
            "boundedMCQEnglishKeyChecks":len(keys),
            "numericLocaleFieldsChecked":fields,
            "numericLocaleDifferenceFlags":flagged,
            "verifiedHistoricalRemedies":sorted(set(history.values())),
            "originalUncertainReviewerReplayed":False,
            "paidModelCalls":0,
            "publicationAuthorized":False,
        }
        digest=_hash({
            "candidatePackageSha256":revised_sha,
            "selectedSourceSha256":source_sha,
            "verifiedAcademicGates":actual_queue,
            "recheckedIndependentEvidence":metrics,
        })
        records.append({
            "round":round_index,
            "evidenceDigestSha256":digest,
            "pendingProofRequirements":count["REVIEW_REQUIRED"],
            "deterministicFailures":count["FAIL"],
            "realHistoricalHandlersExecuted":len(_DISPATCH),
        })
        if digest==prior_digest:
            break
        prior_digest=digest
    if (len(records)!=2
            or records[0]["evidenceDigestSha256"]!=records[1]["evidenceDigestSha256"]
            or metrics is None or actual_queue is None):
        raise ValueError("V24_BOUNDED_AUTONOMOUS_RECOVERY_NOT_AT_FIXED_POINT")
    if sha256(revised_path.read_bytes()).hexdigest()!=revised_sha:
        raise ValueError("V24_REVISED_CONTENT_DRIFT_AFTER_RECOVERY")
    deterministic=metrics["gateCounts"]["FAIL"]
    pending=metrics["gateCounts"]["REVIEW_REQUIRED"]
    state=("STOP_UNHANDLED_VERSIONED_DETERMINISTIC_DEFECT"
           if deterministic else
           "STOP_INDEPENDENT_ACADEMIC_PROOFS_NOT_YET_SUPPLIED"
           if pending else "ALL_TRUSTED_ACADEMIC_GATES_VERIFIED_NO_RELEASE")
    return {
        "status":state,
        "roundsCompleted":len(records),
        "fixedPointReached":True,
        "candidatePackageSha256":revised_sha,
        "sourceSha256":source_sha,
        "independentProofGaps":pending,
        "newDeterministicDefectSlots":deterministic,
        "formalAcademicPassedActivities":report["counts"]["PASS"],
        "verifierActionsActuallyExecuted":list(_DISPATCH),
        "iterations":records,
        "rechecked":metrics,
        "nextEvidenceWorkQueue":actual_queue,
        "publicationAuthorized":False,
    }


def _persist_private_gate_queues(
    folder:Path, identity:dict, outcome:dict,
) -> list[dict[str,Any]]:
    """5 separate immutable, signed source-free workqueues, each <12 KB.

    Historical V6 checkpoint readers intentionally cap each artifact at
    12000 bytes. A monolithic 90-task receipt would exceed that safety cap,
    so retain independent gate files and a digest-only aggregate manifest.
    """
    tasks=outcome.get("nextEvidenceWorkQueue")
    if not isinstance(tasks,list) or len(tasks)!=90:
        raise ValueError("V24_PRIVATE_NINETY_PROOF_QUEUE_REQUIRED")
    source=outcome["sourceSha256"]
    candidate=outcome["candidatePackageSha256"]
    manifest=[]
    for gate in REQUIRED:
        subset=[item for item in tasks if item.get("gate")==gate]
        if len(subset)!=18:
            raise ValueError("V24_INCOMPLETE_PER_GATE_RECOVERY_QUEUE")
        saved=_v6_checkpoint(
            folder/f"V24_GATE_{gate.upper()}_PROOF_TASKS.json",{
                **identity,
                "status":"V24_IMMUTABLE_PRIVATE_EVIDENCE_TASKS",
                "sourceSha256":source,
                "revisedCandidateSha256":candidate,
                "gate":gate,
                "proofTasks":subset,
                "publicationAuthorized":False,
            })
        manifest.append({
            "gate":gate,
            "taskCount":len(subset),
            "signedQueueSha256":saved["integritySha256"],
        })
    return manifest


def run_post_v22_autonomous_academic_recovery(
    repo:Path, private:Path, ready:dict, v9:dict, v11:dict, v12:dict,
    v22:dict,
) -> dict:
    """Execute bounded history-first source-free academic loop after V22.

    Every normal worker restart re-evaluates exact PDF, candidate hashes,
    historical two-role model claims and independent negative/proof checks.
    Persist only signed metadata. Never call a provider or publish.
    """
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    signed22=_signed(folder,_V22,ready)
    result22=_signed(folder,_RESULT22,ready)
    signed21=_signed(folder,_V21,ready)
    result21=_signed(folder,_RESULT21,ready)
    repair=_signed(folder,_MALAY_REPAIR,ready)
    source18=_signed(folder,"V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json",ready)
    if (signed22!=v22 or signed22.get("status")!=_STATUS22
            or signed22.get("resultSha256")!=result22["integritySha256"]
            or signed22.get("sourceV21ReceiptSha256")!=signed21["integritySha256"]
            or signed21.get("resultSha256")!=result21["integritySha256"]
            or result22.get("revisedCandidateSha256")!=
                result21.get("revisedCandidateSha256")
            or signed22.get("oldUncertainRoleReplayed") is not False
            or signed22.get("newGeminiCalls")!=0
            or signed22.get("formalAcademicPASS")!=0
            or result22.get("newReviewPairsRequired")!=4
            or result22.get("advisoryHistoricallyVerifiedIdenticalRolePairs")!=13
            or result21.get("revisedPrivateSourceLocationsVerified")!=18
            or result21.get("sourceSha256")!=source18["audit"]["sourceSha256"]
            or repair.get("newPrivateCandidateSha256")!=
                result21["revisedCandidateSha256"]):
        raise ValueError("V24_AUTHENTIC_SIGNED_V18_V22_CHAIN_REQUIRED")
    binding=_trusted_json(private/_SOURCE_BINDING)
    pdf=Path(binding["sourcePdf"])
    root=Path(binding["sourceRoot"])
    source_sha=binding.get("sourceSha256")
    if (binding.get("integritySha256")!=_hash({
            k:v for k,v in binding.items() if k!="integritySha256"})
            or binding.get("contract")!=
               "BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1"
            or binding.get("section")!="9.1"
            or binding.get("externalFallbackAllowed") is not False
            or binding.get("sourcePdfUploaded") is not False
            or pdf.is_symlink() or not pdf.is_file()
            or pdf.resolve()!=(root/"9"/"9.1"/"source.pdf").resolve()
            or pdf.resolve().is_relative_to(repo.resolve())
            or sha256(pdf.read_bytes()).hexdigest()!=source_sha
            or source_sha!=result22.get("sourceSha256")):
        raise ValueError("V24_EXACT_ONE_ORIGINAL_TEXTBOOK_SOURCE_REQUIRED")
    original_path=repo/_PACKAGE
    revised_path=folder/_CANDIDATE
    if revised_path.is_symlink() or not revised_path.is_file():
        raise ValueError("V24_REVISED_PRIVATE_CANDIDATE_MISSING")
    original_raw=original_path.read_bytes()
    revised_raw=revised_path.read_bytes()
    original_sha=sha256(original_raw).hexdigest()
    revised_sha=sha256(revised_raw).hexdigest()
    if (original_sha!=source18["audit"]["packageSha256"]
            or revised_sha!=result22["revisedCandidateSha256"]
            or revised_sha!=repair["newPrivateCandidateSha256"]):
        raise ValueError("V24_CANDIDATE_VERSION_INVALID_OR_DRIFTED")
    original=json.loads(original_raw.decode("utf8"))
    revised=json.loads(revised_raw.decode("utf8"))
    history=_approved_history(repo)
    # Signed, crash-safe pre-call receipt precedes any subsequent recheck;
    # V24 does not invoke a provider, so a crash cannot replay model claims.
    identity={
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceV22ReceiptSha256":signed22["integritySha256"],
        "sourceV21ReceiptSha256":signed21["integritySha256"],
    }
    _v6_checkpoint(folder/_PRE,{
        **identity,"status":"PRE_CALL_FIXED_HISTORY_DISPATCH_NO_PROVIDER",
        "sourceSha256":source_sha,
        "candidatePackageSha256":revised_sha,
        "allowedHistoryIncidentIds":sorted(set(history.values())),
        "providerRequestsAllowed":False,
        "publicationAuthorized":False,
    })
    reviews=_review_inventory(repo,private,ready["gitHead"],
                              ready["proposalSha256"],revised["activities"])
    outcome=execute_academic_evidence_cycle(
        repo=repo,pdf=pdf,source_sha=source_sha,original=original,
        revised=revised,original_sha=original_sha,revised_sha=revised_sha,
        revised_path=revised_path,
        original_anchors=source18["audit"]["sourceAnchors"],
        changed_ids=set(repair["affectedOriginalActivityIds"]),
        previous_review=reviews,history=history,
    )
    if (outcome["newDeterministicDefectSlots"]!=0
            or outcome["formalAcademicPassedActivities"]!=0
            or outcome["independentProofGaps"]!=90
            or outcome["publicationAuthorized"] is not False):
        raise ValueError("V24_UNEXPECTED_SOURCE_OR_ACADEMIC_PROOF_STATE")
    gate_manifest=_persist_private_gate_queues(folder,identity,outcome)
    bounded_outcome={
        k:v for k,v in outcome.items() if k!="nextEvidenceWorkQueue"
    }
    result=_v6_checkpoint(folder/_RESULT,{
        **identity,
        **bounded_outcome,
        "status":"REAL_HISTORY_FIRST_ACADEMIC_PROOF_QUEUE_EXECUTED",
        "perGateSignedWorkQueueReceipts":gate_manifest,
        "completeWorkQueueDigestSha256":_hash(outcome["nextEvidenceWorkQueue"]),
        "oldRoleClaimsReplayed":False,
        "privatePdfUploaded":False,
        "publicationAuthorized":False,
    })
    return _v6_checkpoint(folder/_V24,{
        **identity,
        "status":_STATUS,
        "resultSha256":result["integritySha256"],
        "historicalRemedyHandlersActuallyExecuted":len(_DISPATCH),
        "genuineTextbookPageRechecks":18,
        "completeAcademicProofGapsStillOpen":90,
        "autoRecoveryRounds":outcome["roundsCompleted"],
        "academicFixedPointReached":True,
        "externalGeminiCalls":0,
        "academicPASS":0,
        "publicationAuthorized":False,
        "nextAction":"SOURCE_BOUND_INDEPENDENT_PER_GATE_PROOF_IMPLEMENTATION",
    })
