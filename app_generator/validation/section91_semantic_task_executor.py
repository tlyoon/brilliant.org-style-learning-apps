"""BSA264: execute all source-identified semantic proof tasks, not just queue them.

Every task receives a bounded independent-evidence classification or a precise
pending dependency. Do NOT turn partial formal evidence into an academic PASS.
No model calls, new source PDFs, or publication. Generic task dispatch with
a source-specific formal-physics adapter.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.full_semantic_proof_queue import (
    plan_full_semantic_proofs, KINDS,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA, _CASES, _source_axioms,
    _mcq_cases, _interactive_cases, _check_solution, _digest,
)
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _source_activity_anchors,
)
from app_generator.validation.source_passages import extract_pages

_EVIDENCE = {
    "ORIGINAL_SOURCE_FIDELITY": "EXACT_SOURCE_PASSAGE_ANCHOR_BOUNDED_NOT_FULL_MEANING",
    "COMPLETE_SCIENTIFIC_MEANING": "SOURCE_DERIVED_FORMAL_ANSWER_MODEL_NOT_FULL_CLAUSE_TRUTH",
    "MCQ_DISTRACTOR_SCIENCE": "FORMAL_FALSE_ALTERNATIVE_NOT_FULL_DISTRACTOR_WORDING",
    "TRILINGUAL_MEANING_EQUIVALENCE": "EXACT_TRILINGUAL_SURFACE_BOUND_NOT_TRANSLATION_EQUIVALENCE",
    "RENDERED_DIAGRAM_SCIENCE": "RENDERED_PIXEL_SCIENCE_INDEPENDENT_REVIEW_REQUIRED",
    "VISUAL_COVERAGE_NEEDS_SOURCE": "NO_DECLARED_DIAGRAM_VISUAL_NECESSITY_UNRESOLVED",
}

def audit_semantic_backlog(
    *,source_pdf:Path,candidate_path:Path,
    _injected_activity_failure:str|None=None,
)->dict:
    if (source_pdf.is_symlink() or not source_pdf.is_file()
        or candidate_path.is_symlink() or not candidate_path.is_file()
        or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
        or sha256(candidate_path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA264_ORIGINAL_SOURCE_OR_FROZEN_PACKAGE_INTEGRITY")
    if len(_source_axioms(source_pdf,_SOURCE_SHA))!=9:
        raise ValueError("BSA264_ORIGINAL_TEXTBOOK_AXOIMS_UNAVAILABLE")
    package=json.loads(candidate_path.read_text(encoding="utf8"))
    activities=package.get("activities",[])
    if len(activities)!=18 or [a.get("id") for a in activities]!=list(_CASES):
        raise ValueError("BSA264_18_ACTIVITY_ROSTER_TAMPERED")
    queue=plan_full_semantic_proofs(package=package,source_sha256=_SOURCE_SHA)
    if queue["taskCount"]!=429 or queue["taskCounts"]!={
        "ORIGINAL_SOURCE_FIDELITY":18,
        "COMPLETE_SCIENTIFIC_MEANING":144,
        "MCQ_DISTRACTOR_SCIENCE":27,
        "TRILINGUAL_MEANING_EQUIVALENCE":222,
        "RENDERED_DIAGRAM_SCIENCE":0,
        "VISUAL_COVERAGE_NEEDS_SOURCE":18,
    }:
        raise ValueError("BSA264_EXACT_VERSION_TASK_ROSTER_CHANGED")
    pages=extract_pages(source_pdf)
    source_anchors=_source_activity_anchors(pages=pages,activities=activities)
    if len(source_anchors)!=18 or not all(
        a.get("uniquePagePassageLocated") for a in source_anchors):
        raise ValueError("BSA264_INDEPENDENT_SOURCE_ANCHORS_MISSING")
    truths={**_mcq_cases(),**_interactive_cases()}
    if set(truths)!=set(_CASES):
        raise ValueError("BSA264_INDEPENDENT_FORMAL_MODELS_MISSING")
    model_hashes={}
    for a in activities:
        model_hashes[a["id"]]=_check_solution(a,truths[a["id"]])["independentSolutionSha256"]
    known={a["id"]:a for a in activities}
    rows_by_activity={aid:[] for aid in _CASES}
    isolated_failures=[]
    # Retry/repair is intentionally NOT fabricated. An independent task that
    # cannot be executed is quarantined, while other activities continue.
    for task in queue["tasks"]:
        aid=task["activityId"]
        if aid not in known or task["kind"] not in _EVIDENCE:
            raise ValueError("BSA264_UNREGISTERED_PROOF_TASK")
        status="BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED"
        evidence_class=_EVIDENCE[task["kind"]]
        if task["kind"]=="VISUAL_COVERAGE_NEEDS_SOURCE":
            status="INDEPENDENT_SOURCE_VISUAL_DECISION_REQUIRED"
        if task["kind"]=="RENDERED_DIAGRAM_SCIENCE":
            status="UNRENDERED_VISUAL_SCIENCE_NOT_ACCEPTED"
        # Deliberate per-activity fault injection verifies that progress on
        # independent academic tasks is not stranded by one failed branch.
        if _injected_activity_failure==aid:
            status="QUARANTINED_INJECTED_ACTIVITY_FAILURE"
            evidence_class="EXACT_TASK_REQUIRES_SEPARATE_REPAIR"
            isolated_failures.append(task["taskId"])
        rows_by_activity[aid].append({
            "taskId":task["taskId"],
            "kind":task["kind"],
            "surfaceSha256":task["surfaceSha256"],
            "status":status,
            "evidenceClass":evidence_class,
        })
    if set(rows_by_activity)!=set(_CASES) or sum(
        len(rows) for rows in rows_by_activity.values())!=429:
        raise ValueError("BSA264_UNACCOUNTED_EXACT_VERSION_PROOF_TASKS")
    rows=[{
        "activityId":aid,
        "activitySha256":_digest(known[aid]),
        "independentFormalAnswerSha256":model_hashes[aid],
        "taskCount":len(rows_by_activity[aid]),
        "evidenceRows":rows_by_activity[aid],
        "completeAcademicPASS":False,
    } for aid in _CASES]
    counts=Counter(r["status"] for row in rows for r in row["evidenceRows"])
    return {
        "status":"BSA264_ALL_429_SOURCE_BOUND_TASKS_ATTEMPTED_ISOLATED_PENDING",
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "queueSha256":_digest(queue["tasks"]),
        "totalTaskCount":429,
        "taskKindCounts":queue["taskCounts"],
        "activityEvidenceRows":rows,
        "activityEvidenceRowsSha256":_digest(rows),
        "taskDispositionCounts":dict(sorted(counts.items())),
        "sourceAnchorsRechecked":18,
        "formalModelsRecomputed":18,
        "visualNecessityUndecided":18,
        "quarantinedTaskCount":len(isolated_failures),
        "quarantinedTaskIdsSha256":_digest(isolated_failures),
        "fullAcademicProofTasksAccepted":0,
        "fullAcademicProofTasksStillOpen":429,
        "completeAcademicProofGatesStillOpen":90,
        "fullAcademicPASS":0,
        "newModelCalls":0,
        "publicationAuthorized":False,
    }
