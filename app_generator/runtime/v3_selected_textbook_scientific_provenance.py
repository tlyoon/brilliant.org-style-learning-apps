"""BSA244 V18: real single-textbook local academic evidence, NEVER release.

A source match is not scientific meaning. The six exact arithmetic witnesses
do not certify every answer, multilingual translation or visual meaning.
No provider, outside PDF retrieval, or private passage text leaves Yoga6.
"""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight as _v13_preflight
from app_generator.runtime.v3_science_c3_independent_dispatch import _V17
from app_generator.validation.source_passages import check_anchor, extract_pages
from app_generator.validation.academic_coverage_gate import (
    _canonical_activity_sha, audit_academic_coverage,
)
from app_generator.validation.academic_qa import REQUIRED

_V18 = "V18_SELECTED_TEXTBOOK_REAL_SOURCE_SCIENTIFIC_PROVENANCE.json"
_STATUS = "V18_SINGLE_TEXTBOOK_REAL_PDF_EVIDENCE_VERIFIED_SCIENCE_STILL_PARTIAL"
_CONTRACT = "BOSLA_V18_SELECTED_TEXTBOOK_SOURCE_BOUND_SCIENCE_V1"
_SOURCE_BINDING = "bosla-selected-textbook-source-binding.json"
_SOURCE_MANIFEST = Path("content/source-manifests/chapter-9-section-9-1.json")
_PACKAGE = Path("content/chapter-9/section-9-1/package.json")
_SECTION = "9.1"
_REQUIRED_COUNT = 18
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_WORDS = re.compile(r"[a-z]{4,}")
_STOP = frozenset(
    "the and from that with into each both where while these those this which "
    "given does what when many same object objects linear momentum system "
    "physical quantity newton definition correct correctly force velocity "
    "chapter section compare answer describes because rather than energy"
    .split()
)

# These are bounded source-grounded key checks for the *existing* Serway 9.1
# pilot, not generic claims of full 18-activity academic correctness.
_MCQS: dict[str, tuple[str, tuple[str, ...]]] = {
    "act-mcq-01-vector-nature":
        ("opt-a", ("equal momentum magnitudes", "opposite directions", "vector")),
    "act-mcq-02-si-units":
        ("opt-a", ("kg", "m/s", "ml/t", "vector")),
    "act-mcq-03-net-force-definition":
        ("opt-a", ("net force equals", "rate", "momentum changes")),
    "act-mcq-04-two-particle-opposite-momentum":
        ("opt-a", ("momentum is zero", "kinetic energy is positive")),
    "act-mcq-07-equal-ke-momentum-relation":
        ("opt-transport-greater", ("greater momentum magnitude",)),
}


def _tokens(value: str) -> set[str]:
    return set(_WORDS.findall(value.casefold())) - _STOP


def _source_candidates(pages: tuple[str, ...]) -> list[tuple[int, str, set[str]]]:
    candidates = []
    for number, page in enumerate(pages, 1):
        for block in re.split(r"\n[ \t]*\n", page):
            clean = re.sub(r"\s+", " ", block).strip()
            if len(clean) < 85 or "\ufffd" in clean:
                continue
            for position in range(0, len(clean), 550):
                quote = clean[position:position + 550].strip()
                if 85 <= len(quote) <= 550 and len(quote.split()) >= 12:
                    candidates.append((number, quote, _tokens(quote)))
    return candidates


def _source_activity_anchors(
    *, pages: tuple[str, ...], activities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates = _source_candidates(pages)
    if not candidates:
        raise ValueError("V18_SELECTED_TEXTBOOK_UNUSABLE_LOCAL_PDF_TEXT")
    result = []
    for activity in activities:
        data = activity.get("prompt")
        explanation = activity.get("explanation")
        if not isinstance(data, dict) or not isinstance(explanation, dict):
            raise ValueError("V18_SOURCE_ACTIVITY_NOT_TRANSLATED")
        prompt = data.get("en")
        explanation_text = explanation.get("en")
        objective = activity.get("objective")
        if (not isinstance(prompt, str) or not isinstance(explanation_text, str)
                or not isinstance(objective, str)):
            raise ValueError("V18_SOURCE_ACTIVITY_ENGLISH_UNREADABLE")
        terms = _tokens(" ".join((prompt, explanation_text, objective)))
        if len(terms) < 5:
            raise ValueError("V18_SOURCE_ACTIVITY_RELEVANCE_TERMS_MISSING")
        ranked = sorted(
            ((len(terms & words), page, quote)
             for page, quote, words in candidates),
            key=lambda row: (-row[0], row[1], row[2]),
        )
        score, page_index, quote = ranked[0]
        if score < 4:
            raise ValueError("V18_SOURCE_ACTIVITY_RELEVANCE_INSUFFICIENT")
        checked = check_anchor(pages, {
            "activityId": activity["id"], "pageIndex": page_index,
            "quotedText": quote,
        })
        if checked.get("status") != "VERIFIED_TEXT_ONLY":
            raise ValueError("V18_SOURCE_PAGE_ANCHOR_NOT_INDEPENDENTLY_VERIFIED")
        result.append({
            "activityId": activity["id"],
            "activitySha256": _hash(activity),
            "physicalPage": page_index,
            "passageSha256": checked["quoteSha256"],
            "uniquePagePassageLocated": True,
            "overlapWords": score,
            "scientificMeaningVerified": False,
            "academicQA": "REVIEW_REQUIRED",
        })
    return result


def _bounded_math_witnesses() -> dict[str, bool]:
    """Independent exact arithmetic examples, not proof of every answer."""
    masses = (Fraction(1, 2), Fraction(3), Fraction(17, 2))
    velocities = (Fraction(2), Fraction(5, 3), Fraction(11))
    one = all(m * v > 0 for m in masses for v in velocities)
    two = all(m * v + m * (-v) == 0
              for m in masses for v in velocities)
    three = all((m * v) ** 2 == 2 * m * (m * v * v / 2)
                for m in masses for v in velocities)
    four = all(2 * big_k * big_m > 2 * big_k * small_m
               for big_m, small_m, big_k in (
                   (Fraction(8), Fraction(2), Fraction(3)),
                   (Fraction(20), Fraction(1), Fraction(1, 2)),
               ))
    five = all(m * (v + acceleration * duration) - m * v ==
               (m * acceleration) * duration
               for m in masses for v in velocities
               for acceleration, duration in (
                   (Fraction(3, 5), Fraction(2)),
                   (Fraction(-2), Fraction(1, 4)),
               ))
    six = all(((p1 + impulse) + (p2 - impulse)) == p1 + p2
              for p1, p2, impulse in (
                  (Fraction(1), Fraction(-2), Fraction(5, 4)),
                  (Fraction(0), Fraction(7), Fraction(-3, 8)),
              ))
    return {
        "positive_momentum_magnitude_for_positive_mass_speed": one,
        "equal_opposite_momenta_cancel": two,
        "momentum_kinetic_energy_relation": three,
        "greater_mass_greater_momentum_at_equal_ke": four,
        "newton_force_impulse_momentum_change": five,
        "equal_opposite_internal_impulses_conserve_system_momentum": six,
    }


def _bounded_mcq_labels(activities: list[dict[str, Any]]) -> list[str]:
    by_id = {a["id"]: a for a in activities}
    checked = []
    for aid, (expected_key, phrases) in _MCQS.items():
        a = by_id.get(aid)
        if not isinstance(a, dict) or a.get("type") != "mcq":
            raise ValueError("V18_SCIENCE_BOUNDED_PILOT_MCQ_MISSING")
        key = a.get("answerKey")
        if not isinstance(key, dict) or key.get("correct") != expected_key:
            raise ValueError("V18_SCIENCE_BOUNDED_PILOT_CORRECT_CHOICE_CHANGED")
        choices = key.get("options")
        if not isinstance(choices, list):
            raise ValueError("V18_SCIENCE_BOUNDED_PILOT_CHOICES_MISSING")
        selected = [x for x in choices if isinstance(x, dict)
                    and x.get("id") == expected_key]
        if len(selected) != 1 or not isinstance(selected[0].get("label"), dict):
            raise ValueError("V18_SCIENCE_BOUNDED_PILOT_LABEL_MISSING")
        english = selected[0]["label"].get("en")
        if not isinstance(english, str) or any(
                phrase not in english.casefold() for phrase in phrases):
            raise ValueError("V18_SCIENCE_BOUNDED_PILOT_CORRECT_PHYSICS_DISAGREES")
        checked.append(aid)
    return checked


def verify_real_selected_source(
    *, repo: Path, source_pdf: Path, expected_source_sha: str,
    package_file: Path | None = None,
) -> dict[str, Any]:
    """Read exactly one explicitly bound instructor source on owner Yoga6."""
    repo = repo.resolve(strict=True)
    if (not isinstance(expected_source_sha, str)
            or not _SHA.fullmatch(expected_source_sha)):
        raise ValueError("V18_SELECTED_TEXTBOOK_INVALID_BINDING_SHA")
    if (source_pdf.is_symlink() or not source_pdf.is_file() or
            source_pdf.resolve().is_relative_to(repo)):
        raise ValueError("V18_SELECTED_TEXTBOOK_PRIVATE_SOURCE_REQUIRED")
    source_pdf = source_pdf.resolve(strict=True)
    if source_pdf.name.casefold() != "source.pdf":
        raise ValueError("V18_SELECTED_TEXTBOOK_SELECTED_FILENAME_MISMATCH")
    if source_pdf.parent.name != _SECTION or source_pdf.parent.parent.name != "9":
        raise ValueError("V18_SELECTED_TEXTBOOK_WRONG_TOPIC")
    manifest_file = repo / _SOURCE_MANIFEST
    package_file = package_file or repo / _PACKAGE
    manifest = json.loads(manifest_file.read_text(encoding="utf8"))
    raw = package_file.read_bytes()
    package = json.loads(raw.decode("utf8"))
    entries = manifest.get("sources")
    if (not isinstance(entries, list) or len(entries) != 1
            or entries[0].get("role") != "primary"
            or entries[0].get("controlledFilename") != source_pdf.name
            or entries[0].get("sha256") != expected_source_sha
            or manifest.get("sha256") != expected_source_sha
            or package.get("packageId") != "chapter-9-section-9-1"):
        raise ValueError("V18_SELECTED_TEXTBOOK_MANIFEST_SOURCE_IDENTITY_MISMATCH")
    with source_pdf.open("rb") as file:
        if file.read(5) != b"%PDF-":
            raise ValueError("V18_SELECTED_TEXTBOOK_SOURCE_PDF_MAGIC_INVALID")
    h = sha256(source_pdf.read_bytes()).hexdigest()
    if h != expected_source_sha:
        raise ValueError("V18_SELECTED_TEXTBOOK_REAL_PDF_SHA_CHANGED")
    activities = package.get("activities")
    if (not isinstance(activities, list) or len(activities) != _REQUIRED_COUNT
            or any(not isinstance(a, dict)
                   or not isinstance(a.get("id"), str) for a in activities)
            or len({a["id"] for a in activities}) != _REQUIRED_COUNT):
        raise ValueError("V18_SELECTED_TEXTBOOK_EXACT_18_ROSTER_REQUIRED")
    pages = extract_pages(source_pdf)
    if not 1 <= len(pages) <= 15:
        raise ValueError("V18_SELECTED_TEXTBOOK_UNEXPECTED_SECTION_LENGTH")
    # Local extracted text must contain the source's defining science domain,
    # not just a selected filename/sha. The source itself stays private.
    lower = "\n".join(pages).casefold()
    if any(term not in lower for term in (
            "linear momentum", "mass and velocity", "kinetic energy",
            "second law", "third law", "isolated")):
        raise ValueError("V18_SELECTED_TEXTBOOK_EXPECTED_SOURCE_SCIENCE_ABSENT")
    anchors = _source_activity_anchors(pages=pages, activities=activities)
    math = _bounded_math_witnesses()
    if not all(math.values()):
        raise ValueError("V18_SELECTED_TEXTBOOK_DETERMINISTIC_PHYSICS_WITNESS_FAILED")
    bounded = _bounded_mcq_labels(activities)
    if package_file.read_bytes() != raw or sha256(source_pdf.read_bytes()).hexdigest() != h:
        raise ValueError("V18_SELECTED_TEXTBOOK_SOURCE_CHANGED_DURING_AUDIT")
    return {
        "status": "REAL_SELECTED_TEXTBOOK_SOURCE_AND_BOUNDED_PHYSICS_CHECKED",
        "section": _SECTION,
        "sourceSha256": h,
        "sourceManifestSha256": sha256(manifest_file.read_bytes()).hexdigest(),
        "packageSha256": sha256(raw).hexdigest(),
        "selectedSourcePDFCount": 1,
        "selectedPhysicalPdfPages": len(pages),
        "activityCount": len(anchors),
        "physicalPageAnchorsReextracted": len(anchors),
        "pageSpecificSourceLocationsVerified": len(anchors),
        "sourceAnchors": anchors,
        "independentExactArithmeticWitnesses": math,
        "independentExactArithmeticWitnessCount": len(math),
        "boundedMCQKeyAndEnglishAnswerPatternVerified": bounded,
        "boundedMCQPatternCount": len(bounded),
        "fullAnswerScienceReviewCompleted": False,
        "fullTrilingualMeaningReviewCompleted": False,
        "fullRenderedVisualScienceReviewCompleted": False,
        "academicQA": "REVIEW_REQUIRED",
        "formalAcademicPassCount": 0,
        "independentScientificAcceptanceComplete": False,
        "publicationAuthorized": False,
        "newPdfDownloads": 0,
        "additionalExternalPdfCount": 0,
        "newModelCalls": 0,
        "newSourcePdfUploads": 0,
    }


def _selected_textbook_academic_gap_audit(
    *, repo: Path, source_sha256: str,
) -> dict[str, Any]:
    """Actually run the existing exact-source/package independent gap gate.

    A source passage locator is NOT independent scientific semantic proof.
    No status is fabricated and no model review is replayed.
    """
    raw = (repo / _PACKAGE).read_bytes()
    package = json.loads(raw.decode("utf8"))
    items = package["activities"]
    matrix = {
        "packageSha256": sha256(raw).hexdigest(),
        "sourceSha256": source_sha256,
        "activityCount": len(items),
        "academicQA": "REVIEW_REQUIRED",
        "publicationAuthorized": False,
        "counts": {"PASS": 0, "FAIL": 0, "REVIEW_REQUIRED": len(items)},
        "activities": [{
            "activityId": a["id"], "activitySha256": _canonical_activity_sha(a),
            "sourceLocationVerified": False,
            "gates": {gate: "REVIEW_REQUIRED" for gate in REQUIRED},
            "academicQA": "REVIEW_REQUIRED",
            "publicationAuthorized": False,
        } for a in items],
    }
    report = audit_academic_coverage(
        package_bytes=raw, matrix=matrix, source_sha256=source_sha256,
    )
    outstanding = sum(report["perGateOutstanding"].values())
    if (report["formalAcademicPassCount"] != 0
            or report["academicQA"] != "REVIEW_REQUIRED"
            or report["activityCount"] != _REQUIRED_COUNT
            or outstanding != _REQUIRED_COUNT * len(REQUIRED)
            or report["publicationAuthorized"] is not False):
        raise ValueError("V18_BOGUS_INDEPENDENT_SCIENCE_ACCEPTANCE")
    return {
        "status": "18_REAL_91_TEXTBOOK_ACTIVITIES_90_ACADEMIC_GATE_PROOFS_OPEN",
        "packageSha256": report["packageSha256"],
        "sourceSha256": report["sourceSha256"],
        "activityCount": report["activityCount"],
        "unverifiedGateInstances": outstanding,
        "perGateOutstanding": report["perGateOutstanding"],
        "formalAcademicPASS": False, "academicQA": "REVIEW_REQUIRED",
        "publicationAuthorized": False, "modelCalls": 0,
    }


def run_post_v17_selected_textbook(
    repo: Path, private: Path, ready: dict,
    v9: dict, v11: dict, v12: dict, v17: dict,
) -> dict[str, Any]:
    """Normal V17 -> V18 dispatch with private signed pre-call/result."""
    folder, _, _, _, _ = _v13_preflight(repo, private, ready, v9, v11, v12)
    historical = _trusted_json(folder / _V17)
    if (historical != v17
            or historical.get("status") != "V17_REAL_SCIENCE_C3_GAP_AUDITS_EXECUTED_NO_RELEASE"
            or historical.get("gitHead") != ready.get("gitHead")
            or historical.get("proposalSha256") != ready.get("proposalSha256")
            or historical.get("quarantinedTaskIds") != []
            or historical.get("historicalC3") != "FAILED_LIMITED_CAMPAIGN"
            or historical.get("publicationAuthorized") is not False
            or historical.get("integritySha256") != _hash({
                k: v for k, v in historical.items() if k != "integritySha256"
            })):
        raise ValueError("V18_GENUINE_SIGNED_V17_REQUIRED")
    identity = {
        "gitHead": ready["gitHead"],
        "proposalSha256": ready["proposalSha256"],
        "sourceV17ReceiptSha256": historical["integritySha256"],
    }
    detail = None
    task_result = None
    _v6_checkpoint(folder / "V18_SELECTED_TEXTBOOK_SCIENCE_PRE_CALL.json", {
        **identity, "state": "PRE_CALL_LOCAL_ONE_SOURCE_ONLY",
        "pdfUploadsAllowed": False, "externalPdfDownloadsAllowed": False,
        "modelCallsAllowed": False, "publicationAuthorized": False,
    })
    try:
        binding_file = private / _SOURCE_BINDING
        binding = _trusted_json(binding_file)
        if binding.get("integritySha256") != _hash({
                k: v for k, v in binding.items()
                if k != "integritySha256"
        }):
            raise ValueError("V18_SELECTED_TEXTBOOK_PRIVATE_BINDING_TAMPERED")
        source_path = Path(binding["sourcePdf"])
        source_root = Path(binding["sourceRoot"])
        expected = binding["sourceSha256"]
        if (binding.get("contract") != "BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1"
                or binding.get("section") != _SECTION
                or binding.get("sourceFilename") != "source.pdf"
                or binding.get("externalFallbackAllowed") is not False
                or binding.get("sourcePdfUploaded") is not False
                or not source_root.is_dir()
                or source_path.resolve() != (
                    source_root / "9" / _SECTION / "source.pdf").resolve()
                or source_path.is_symlink()):
            raise ValueError("V18_LOCAL_TEXTBOOK_BINDING_MISMATCH")
        audit = verify_real_selected_source(
            repo=repo, source_pdf=source_path,
            expected_source_sha=expected)
        detail = _v6_checkpoint(folder / "V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json", {
            **identity, "state": "ONE_REAL_TEXTBOOK_SOURCE_AUDIT_COMPLETE",
            "audit": audit, "publicationAuthorized": False,
        })
        # v7.1 actual same-run downstream dispatch, not a checkpoint label.
        _v6_checkpoint(folder / "V18_ACADEMIC_GAP_AUDIT_PRE_CALL.json", {
            **identity, "state": "PRE_CALL_READONLY_REAL_ACADEMIC_GAP_AUDIT",
            "sourceV18AuditReceiptSha256": detail["integritySha256"],
            "modelCallsAllowed": False, "publicationAuthorized": False,
        })
        gaps = _selected_textbook_academic_gap_audit(
            repo=repo, source_sha256=audit["sourceSha256"])
        task_result = _v6_checkpoint(folder / "V18_ACADEMIC_GAP_AUDIT_RESULT.json", {
            **identity, "state": "REAL_SOURCE_BOUND_ACADEMIC_GAP_AUDIT_COMPLETE",
            "sourceV18AuditReceiptSha256": detail["integritySha256"],
            "result": gaps, "publicationAuthorized": False,
        })
        state = _STATUS
    except Exception as exc:
        if detail is None:
            detail = _v6_checkpoint(folder / "V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json", {
                **identity, "state": "SELECTED_SOURCE_AUDIT_QUARANTINED",
                "errorClass": type(exc).__name__,
                "publicationAuthorized": False,
            })
        else:
            task_result = _v6_checkpoint(folder / "V18_ACADEMIC_GAP_AUDIT_RESULT.json", {
                **identity, "state": "REAL_ACADEMIC_GAP_AUDIT_QUARANTINED",
                "sourceV18AuditReceiptSha256": detail["integritySha256"],
                "errorClass": type(exc).__name__,
                "publicationAuthorized": False,
            })
        state = "V18_REAL_SELECTED_TEXTBOOK_SOURCE_AUDIT_QUARANTINED"
    return _v6_checkpoint(folder / _V18, {
        **identity, "contract": _CONTRACT, "status": state,
        "resultSha256": detail["integritySha256"],
        "resultState": detail["state"],
        "nextTaskDispatchActuallyExecuted": state == _STATUS,
        "academicGapAuditReceiptSha256": (
            task_result["integritySha256"] if task_result else None),
        "realSingleTextbookPdfOpened": state == _STATUS,
        "historicalC3": "FAILED_LIMITED_CAMPAIGN",
        "additionalExternalPdfsRequired": False,
        "newModelCalls": 0, "newOutsidePdfDownloads": 0,
        "newSourcePdfUploads": 0,
        "independentScientificAcceptanceComplete": False,
        "publicationAuthorized": False,
        "publicMergeExecuted": False, "publicDeployExecuted": False,
        "nextEligibleMilestone":
            "INDEPENDENT_ACTIVITY_SEMANTIC_VISUAL_MULTILINGUAL_REVIEW_ON_SELECTED_TEXTBOOK",
    })
