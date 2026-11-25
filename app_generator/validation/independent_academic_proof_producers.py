"""BSA256 V28: five *bounded* independently executed academic evidence producers.

All claims are deliberately scoped to what exact source/version and executable
formal models establish. Natural language semantics, unknown translations, and
rendered pixels must remain REVIEW_REQUIRED, never inferred from consistency.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
import re
from pathlib import Path
from typing import Any

from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _source_activity_anchors,
)
from app_generator.validation.bounded_symbolic_qa import (
    audit_bounded_symbolic_recovery,
)
from app_generator.validation.full_semantic_proof_queue import (
    plan_full_semantic_proofs,
)
from app_generator.validation.language_qa import _learner_visible_localized_fields
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA, _CANDIDATE_SHA, _mcq_cases,
    bounded_section91_science_audit,
)
from app_generator.validation.source_passages import extract_pages

_LANGS=("en","ms","zh")
# Unicode \w swallows Chinese references such as '第9.1节'; only ASCII
# variable-name boundaries should suppress a numeric token.
_NUMERIC=re.compile(r"(?<![0-9A-Za-z_])\d+(?:\.\d+)?(?![0-9A-Za-z_])")


def _digest(value: Any)->str:
    return sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,
        separators=(",",":")).encode("utf8")).hexdigest()


def audit_diagram_vector_physics(spec:dict[str,Any])->dict[str,Any]:
    """Independent formal vector model for a cart-style interactive diagram.

    Requires source binding by the caller. This does NOT observe the browser or
    establish that visually rendered arrows equal the declared specification.
    """
    if not isinstance(spec,dict) or spec.get("template")!="mechanics.cart_collision_1d":
        raise ValueError("BSA256_DIAGRAM_MODEL_NOT_RENDERABLE_CART_TEMPLATE")
    p=spec.get("semanticParameters")
    if (not isinstance(p,dict) or p.get("phase")!="before"
            or p.get("track_orientation") not in ("horizontal","left-to-right")):
        raise ValueError("BSA256_DIAGRAM_WRONG_PHASE_OR_ORIENTATION")
    entities=spec.get("entities")
    vectors=spec.get("vectors")
    if (not isinstance(entities,list) or len(entities)!=2
            or not isinstance(vectors,list) or len(vectors)!=2):
        raise ValueError("BSA256_DIAGRAM_REQUIRES_TWO_CARTS_AND_VELOCITIES")
    def positive(x):
        if type(x) not in (int,float,str):
            raise ValueError("BSA256_DIAGRAM_NONNUMERIC_MAGNITUDE")
        try:
            v=Fraction(str(x))
        except (ValueError,ZeroDivisionError) as exc:
            raise ValueError("BSA256_DIAGRAM_NONNUMERIC_MAGNITUDE") from exc
        if not 0<v<=100000:
            raise ValueError("BSA256_DIAGRAM_NONPOSITIVE_OR_UNBOUNDED_VALUE")
        return v
    ids=[]
    masses={}
    for ent in entities:
        if not isinstance(ent,dict) or ent.get("kind")!="cart":
            raise ValueError("BSA256_DIAGRAM_NOT_TWO_CARTS")
        ident=ent.get("id")
        if not isinstance(ident,str) or not ident or ident in masses:
            raise ValueError("BSA256_DIAGRAM_DUPLICATE_ENTITY")
        ids.append(ident)
        masses[ident]=positive(ent.get("properties",{}).get("mass"))
    momentum={}
    for v in vectors:
        if not isinstance(v,dict) or v.get("quantity")!="velocity":
            raise ValueError("BSA256_DIAGRAM_NOT_VELOCITY_ARROW")
        ident=v.get("entityId")
        direction=v.get("direction")
        if ident not in masses or ident in momentum or direction not in ("left","right"):
            raise ValueError("BSA256_DIAGRAM_WRONG_ARROW_ENTITY_OR_DIRECTION")
        speed=positive(v.get("relativeMagnitude"))
        momentum[ident]=masses[ident]*speed*(1 if direction=="right" else -1)
    if set(momentum)!=set(ids):
        raise ValueError("BSA256_DIAGRAM_INCOMPLETE_VELOCITY_ROSTER")
    return {
        "status":"BOUNDED_VECTOR_ARROW_MOMENTUM_MODEL_EXECUTED",
        "sourceLaw":"p=m*v",
        "modelSha256":_digest(spec),
        "signedInitialMomenta":[str(momentum[x]) for x in ids],
        "netInitialMomentum":str(sum(momentum.values(),Fraction(0))),
        "oppositeDirections":momentum[ids[0]]*momentum[ids[1]]<0,
        "sourceFigurePixelSemanticsVerified":False,
        "renderedPixelGeometryVerified":False,
        "completeAcademicPASS":False,
    }


def audit_five_proof_channels(
    *,source_pdf:Path,source_sha:str,candidate_path:Path,
)->dict[str,Any]:
    """Recompute five evidence channels from real SHA-bound original source.

    A missing visual cannot be replaced with a guessed generic diagram.
    Results must remain evidence-specific, not full five-gate academic PASS.
    """
    if (source_sha!=_SOURCE_SHA or not source_pdf.is_file()
            or source_pdf.is_symlink()
            or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
            or not candidate_path.is_file() or candidate_path.is_symlink()
            or sha256(candidate_path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA256_SINGLE_SOURCE_OR_REVISED_PACKAGE_SHA_CHANGED")
    package=json.loads(candidate_path.read_text(encoding="utf8"))
    acts=package["activities"]
    if len(acts)!=18 or len({a["id"] for a in acts})!=18:
        raise ValueError("BSA256_CHANGED_SOURCE_ACTIVITIES")
    # Producer 1: exact physical PDF passage locations, not semantic approval.
    pages=extract_pages(source_pdf)
    anchors=_source_activity_anchors(pages=pages,activities=acts)
    if len(anchors)!=18 or not all(x["uniquePagePassageLocated"] for x in anchors):
        raise ValueError("BSA256_SOURCE_PASSAGE_WITNESS_INCOMPLETE")
    # Producer 2: executable independent source-axiom, answer/physics model.
    science=bounded_section91_science_audit(
        source_pdf=source_pdf,source_sha=source_sha,package_file=candidate_path)
    if (science["independentlyReextractedTextbookPhysicsPremises"]!=9
            or science["boundedFormalAnswerItemWitnesses"]!=68
            or len(science["activityProofs"])!=18):
        raise ValueError("BSA256_FORMAL_EXPLANATION_PROOFS_INCOMPLETE")
    # Producer 3: 27 finite, exact rational countermodels for wrong MCQ choices.
    truth=_mcq_cases()
    mcq=[a for a in acts if a["type"]=="mcq"]
    if len(mcq)!=9 or len(truth)!=9:
        raise ValueError("BSA256_MCQS_AND_PROPOSITION_MODELS_INCOMPLETE")
    falsified=[]
    for a in mcq:
        model=truth[a["id"]]
        key=a["answerKey"]
        selected=key["correct"]
        ids=[o["id"] for o in key["options"]]
        if (len(ids)!=4 or len(set(ids))!=4
                or set(ids)!=set(model) or
                {k for k,v in model.items() if v}!={selected}):
            raise ValueError("BSA256_MC_Q_DISTRACTOR_MODEL_CONTRADICTION")
        falsified.append({"activityId":a["id"],"correct":selected,
            "falsifiedAlternatives":sorted(k for k,v in model.items() if not v),
            "propositionTruthModelSha256":_digest(model)})
    if sum(len(x["falsifiedAlternatives"]) for x in falsified)!=27:
        raise ValueError("BSA256_27_COUNTERMODELS_MISSING")
    # Producer 4: every actual translated surface re-read, strict bounded
    # literal formula matching; never assert natural language equivalence.
    localized=0;numeric_same=0;numeric_ambiguous=0
    for a in acts:
        for path,triple in _learner_visible_localized_fields(a):
            if any(not isinstance(triple.get(l),str) or not triple[l].strip()
                   for l in _LANGS):
                raise ValueError("BSA256_INCOMPLETE_TRILINGUAL_TEXT")
            localized+=1
            nums=[Counter(_NUMERIC.findall(triple[l])) for l in _LANGS]
            if nums[0]==nums[1]==nums[2]:
                numeric_same+=1
            else:
                numeric_ambiguous+=1
    symbols=audit_bounded_symbolic_recovery(acts)
    if (localized!=222
            or symbols["priorAmbiguousSymbolicFields"]!=
                symbols["boundedParserFalsePositivesResolved"]+
                symbols["remainingAmbiguousSymbolicFields"]
            or symbols["independentRemainingPriorReviewFlags"]<
                symbols["remainingAmbiguousSymbolicFields"]):
        raise ValueError("BSA256_TRILINGUAL_OR_SYMBOLIC_PROOFS_CHANGED")
    # Producer 5: perform actual model checks for every declared diagram, or
    # report a verifiable *absence* (never claim pixels or diagrams proven).
    visuals=[a for a in acts if a.get("visualSpec")]
    diagram_models=[audit_diagram_vector_physics(a["visualSpec"])
                    for a in visuals]
    queue=plan_full_semantic_proofs(package=package,source_sha256=source_sha)
    if (queue["taskCount"]!=429 or
            queue["taskCounts"]["VISUAL_COVERAGE_NEEDS_SOURCE"]!=18
            or visuals or diagram_models):
        raise ValueError("BSA256_SELECTED_CASE_VISUAL_NEEDS_SOURCE")
    # Bind each independently executed *bounded* witness to the exact
    # scientific-review task IDs; no queued explanation or diagram becomes
    # academically passed merely because a model/anchor exists.
    anchors_by={row["activityId"]:row for row in anchors}
    formal_by={row["activityId"]:row for row in science["activityProofs"]}
    false_by={row["activityId"]:row for row in falsified}
    task_rows=[]
    for activity in acts:
        aid=activity["id"]
        tasks=[t for t in queue["tasks"] if t["activityId"]==aid]
        by_kind={kind:[t for t in tasks if t["kind"]==kind]
                 for kind in queue["taskCounts"]}
        if (len(by_kind["ORIGINAL_SOURCE_FIDELITY"])!=1
                or len(by_kind["VISUAL_COVERAGE_NEEDS_SOURCE"])!=1
                or len(by_kind["TRILINGUAL_MEANING_EQUIVALENCE"])<1
                or sum(map(len,by_kind.values()))!=len(tasks)):
            raise ValueError("BSA256_PER_ACTIVITY_PROOF_TASK_BINDING_CHANGED")
        fake=false_by.get(aid)
        if ((activity["type"]=="mcq")!=(fake is not None)):
            raise ValueError("BSA256_PER_ACTIVITY_MCQ_MODEL_MISSING")
        task_rows.append({
            "activityId":aid,
            "activitySha256":_digest(activity),
            "sourceTaskId":by_kind["ORIGINAL_SOURCE_FIDELITY"][0]["taskId"],
            "sourcePhysicalPage":anchors_by[aid]["physicalPage"],
            "sourceQuoteSha256":anchors_by[aid]["passageSha256"],
            "formalSolutionSha256":formal_by[aid]["independentFormalSolutionSha256"],
            "boundedFormalWitnessCount":formal_by[aid][
                "exactRationalAndDimensionalWitnesses"],
            "mcqFalseChoicesProven":len(fake["falsifiedAlternatives"]) if fake else 0,
            "mcqCountermodelSha256":fake["propositionTruthModelSha256"] if fake else None,
            "explanationProofTaskIdsSha256":_digest(
                [t["taskId"] for t in by_kind["COMPLETE_SCIENTIFIC_MEANING"]]),
            "trilingualProofTaskIdsSha256":_digest(
                [t["taskId"] for t in by_kind["TRILINGUAL_MEANING_EQUIVALENCE"]]),
            "visualCoverageTaskId":by_kind["VISUAL_COVERAGE_NEEDS_SOURCE"][0]["taskId"],
            "visualSpecAvailable":False,
            "completeSemanticAcceptance":False,
            "publicationAuthorized":False,
        })
    if (len(task_rows)!=18
            or sum(r["boundedFormalWitnessCount"] for r in task_rows)!=68
            or sum(r["mcqFalseChoicesProven"] for r in task_rows)!=27):
        raise ValueError("BSA256_INCOMPLETE_ACTIVITY_SCOPED_PROOF_ROWS")
    return {
        "status":"BSA256_FIVE_INDEPENDENT_BOUNDED_PRODUCERS_EXECUTED",
        "sourceSha256":source_sha,"candidateSha256":_CANDIDATE_SHA,
        "sourceFidelity":{"pageAnchorsReextracted":18,
            "sourcePages":len(pages),"anchorRowsSha256":_digest(anchors),
            "fullSourceStatementMeaningProven":False},
        "scientificExplanations":{"textbookAxiomsReextracted":9,
            "formalAnswerModelsChecked":18,"boundedMathWitnesses":68,
            "formalProofRowsSha256":_digest(science["activityProofs"]),
            "fullExplanationClauseTruthProven":False},
        "mcqIncorrectChoices":{"correctMCQKeysVerified":9,
            "falseMCQAlternativeCountermodels":27,
            "countermodelRowsSha256":_digest(falsified),
            "allDistractorNaturalLanguageSemanticsProven":False},
        "englishMalayChinese":{"localizedSurfacesInspected":localized,
            "matchingNumericLiteralSurfaces":numeric_same,
            "numericLiteralReviewNeeded":numeric_ambiguous,
            "strictFormulaLiteralMatches":symbols["boundedParserFalsePositivesResolved"],
            "unresolvedSymbolicFields":symbols["remainingAmbiguousSymbolicFields"],
            "fullTrilingualMeaningProven":False},
        "interactiveDiagrams":{"declaredDiagramsFound":0,
            "boundedDiagramModelsExecuted":0,
            "sourceGroundedVisualNecessityTasksOpen":18,
            "sourceSectionMentionsFigure91":bool(re.search(
                r"Figure\s+9\.1",pages[0],re.I)),
            "renderedVisualScienceApproved":False},
        "originalIndependentSemanticTasksPending":429,
        "fullSourceBoundTaskRosterSha256":_digest(queue["tasks"]),
        "perActivityBoundedProofRowsSha256":_digest(task_rows),
        "perActivityBoundedProofRows":task_rows,
        "completeAcademicProofGatesStillOpen":90,
        "formalAcademicPASS":0,
        "providerCalls":0,"additionalTextbooks":0,
        "publicationAuthorized":False,
    }
