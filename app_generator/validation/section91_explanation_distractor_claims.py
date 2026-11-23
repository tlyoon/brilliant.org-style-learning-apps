"""BSA253: original-textbook-bound explanation/distractor/EN-MS-ZH triage.

Reusable typed-scientific alignment engine + exact domain-scoped V25 physics
models. No generic model vote can prove that every explanatory clause is true.
Full semantic QA remains unproven when a symbolic expression or physical
meaning is ambiguous, especially across languages.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.section91_formal_physics import (
    _CANDIDATE_SHA, _SOURCE_SHA, bounded_section91_science_audit,
)
from app_generator.validation.typed_scientific_semantic_alignment import (
    audit_reusable_scientific_alignment, _digest,
)


def audit_source_bound_explanation_distractors(
    *,source_pdf:Path, source_sha:str, candidate_path:Path,
)->dict[str,Any]:
    """Produce *bounded* source and exact-answer-backed claims, never PASS."""
    if (source_sha!=_SOURCE_SHA or candidate_path.is_symlink()
            or not candidate_path.is_file()
            or sha256(candidate_path.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA253_SOURCE_OR_REVISED_CANDIDATE_CHANGED")
    math=bounded_section91_science_audit(
        source_pdf=source_pdf,source_sha=source_sha,
        package_file=candidate_path)
    package=json.loads(candidate_path.read_bytes())
    alignment=audit_reusable_scientific_alignment(package["activities"])
    math_map={q["activityId"]:q for q in math["activityProofs"]}
    if (math["boundedFormalAnswerItemWitnesses"]!=68
            or len(math_map)!=18
            or alignment["activitiesChecked"]!=18
            or any(q["activityCanonicalSha256"]!=
                   math_map[q["activityId"]]["activityCanonicalSha256"]
                   for q in alignment["rows"])):
        raise ValueError("BSA253_SCIENTIFIC_FORMAL_PROOF_SCOPE_DRIFT")
    hard_defects=sum(
        sum(f["kind"].startswith("DETERMINISTIC_")
            for f in row["issues"])
        for row in alignment["rows"])
    # A verified formula/key contradiction is a genuine defect. Missing
    # lexical cues or different written notations are ONLY review items.
    if hard_defects:
        raise ValueError("BSA253_DETERMINISTIC_EXPLANATORY_SCIENCE_DEFECT")
    count=sum(int(a.get("type")=="mcq") for a in package["activities"])
    visuals=sum(bool(a.get("visualSpec")) for a in package["activities"])
    return {
        "status":"BSA253_EXACT_SOURCE_EXPLANATION_DISTRACTOR_TRILINGUAL_TRIAGE_NO_RELEASE",
        "sourceSha256":source_sha,
        "candidateSha256":_CANDIDATE_SHA,
        "originalTextbookPremisesReverified":math[
            "independentlyReextractedTextbookPhysicsPremises"],
        "sourceBoundFormalAnswerWitnessesRecomputed":68,
        "completeMCQCorrectAndDistractorTruthModels":count,
        "completeInteractiveFormalSolutions":18-count,
        "localisedFieldsExamined":alignment["surfacesChecked"],
        "scientificMathBearingFields":alignment["mathBearingSurfaces"],
        "scientificExpressionOccurrences":alignment["mathExpressionOccurrences"],
        "unresolvedSemanticAlignmentReviewItems":alignment["issues"],
        "unambiguousScienceOrAnswerContradictions":hard_defects,
        "visualSpecsInPilot":visuals,
        "diagramSemanticClaimsMade":False,
        "fullEnglishExplanationsProven":False,
        "fullDistractorNaturalLanguageMeaningProven":False,
        "fullEN_MS_ZHSemanticEquivalenceProven":False,
        "formalAcademicPASS":0,
        "fullAcademicProofGatesOpen":90,
        "newProviderCalls":0,
        "outsideTextbooksUsed":False,
        "publicationAuthorized":False,
        "rows":[{
            "activityId":row["activityId"],
            "activityCanonicalSha256":row["activityCanonicalSha256"],
            "localizedFieldsChecked":row["localizedSurfacesChecked"],
            "mathBearingFields":row["crossLocaleMathBearingFieldsChecked"],
            "trilingualReviewIssues":row["issueCount"],
            "deterministicDefect":False,
            "boundedAnswerPhysicsEvidenceSha256":math_map[
                row["activityId"]]["independentFormalSolutionSha256"],
            "completeSemanticEquivalenceProven":False,
            "publicationAuthorized":False,
            "issueCategories":sorted({x["reason"] for x in row["issues"]}),
        } for row in alignment["rows"]],
    }
