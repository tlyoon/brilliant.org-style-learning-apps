"""BSA253 reusable, exact-version full-semantics evidence task enumeration.

A task is a demand for real independent proof, NEVER a completed proof.
No source passages, model calls, private generated text, release or publication.
The same deterministic queue applies to any textbook-based Bosla package.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

LANGS = ("en", "ms", "zh")
SHA = re.compile(r"[0-9a-f]{64}\Z")
EXPLANATORY = frozenset((
    "prompt", "answerLogic", "explanation", "feedback", "hint", "hints",
    "accessibilityText", "prerequisiteRecovery", "rationale",
))
KINDS = (
    "ORIGINAL_SOURCE_FIDELITY", "COMPLETE_SCIENTIFIC_MEANING",
    "MCQ_DISTRACTOR_SCIENCE", "TRILINGUAL_MEANING_EQUIVALENCE",
    "RENDERED_DIAGRAM_SCIENCE",
    "VISUAL_COVERAGE_NEEDS_SOURCE",
)


def _digest(data: Any) -> str:
    return sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode("utf8")).hexdigest()


def _localized(node: Any, path: tuple[str, ...] = ()):
    if isinstance(node, dict):
        if any(lang in node for lang in LANGS):
            if (not all(isinstance(node.get(lang), str)
                        and node[lang].strip() for lang in LANGS)):
                raise ValueError("BSA253_INCOMPLETE_TRILINGUAL_SURFACE")
            yield path, {lang: node[lang] for lang in LANGS}
        for key, value in node.items():
            if key not in LANGS:
                yield from _localized(value, (*path, str(key)))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _localized(value, (*path, str(i)))


def plan_full_semantic_proofs(*, package: dict[str, Any],
                              source_sha256: str) -> dict[str, Any]:
    """Build content-free proof queue from a fully pinned activity revision.

    Scientific text and diagram PASS is impossible from this queue alone.
    A later independent examiner must inspect real source, rendered pixels,
    and exact translated meanings, then emit separately checked evidence.
    """
    if not isinstance(source_sha256, str) or not SHA.fullmatch(source_sha256):
        raise ValueError("BSA253_INVALID_ORIGINAL_SOURCE_IDENTITY")
    if not isinstance(package, dict):
        raise ValueError("BSA253_INVALID_PACKAGE")
    acts = package.get("activities")
    if not isinstance(acts, list) or not acts:
        raise ValueError("BSA253_EMPTY_ACTIVITY_ROSTER")
    package_sha = _digest(package)
    ids = [a.get("id") if isinstance(a, dict) else None for a in acts]
    if (any(not isinstance(aid, str) or not aid for aid in ids)
            or len(ids) != len(set(ids))):
        raise ValueError("BSA253_INVALID_ACTIVITY_IDENTITIES")
    all_tasks = []
    for a in acts:
        aid = a["id"]
        activity_sha = _digest(a)
        tasks = []

        def add(kind: str, path: str, digest: str):
            payload = (source_sha256, package_sha, aid, activity_sha,
                       kind, path, digest)
            tasks.append({
                "taskId": _digest(payload),
                "activityId": aid,
                "activitySha256": activity_sha,
                "kind": kind,
                "surfacePath": path,
                "surfaceSha256": digest,
                "status": "REVIEW_REQUIRED",
            })

        add("ORIGINAL_SOURCE_FIDELITY", "$activity", activity_sha)
        surfaces = list(_localized(a))
        if not surfaces:
            raise ValueError("BSA253_NO_LOCALIZED_LEARNER_CONTENT")
        for path, value in surfaces:
            display = "/".join(path)
            digest = _digest(value)
            add("TRILINGUAL_MEANING_EQUIVALENCE", display, digest)
            if path and path[0] in EXPLANATORY:
                add("COMPLETE_SCIENTIFIC_MEANING", display, digest)

        if a.get("type") == "mcq":
            key = a.get("answerKey")
            if not isinstance(key, dict) or not isinstance(key.get("options"), list):
                raise ValueError("BSA253_MC_Q_ANSWER_STRUCTURE_REQUIRED")
            options = key["options"]
            ids_ = [o.get("id") if isinstance(o, dict) else None for o in options]
            if (len(options) < 2 or any(not isinstance(i, str) or not i for i in ids_)
                    or len(set(ids_)) != len(ids_)
                    or key.get("correct") not in ids_):
                raise ValueError("BSA253_MC_Q_CORRECT_DISTRACTOR_IDENTITY_INVALID")
            for i, opt in enumerate(options):
                if opt["id"] != key["correct"]:
                    label = opt.get("label")
                    if (not isinstance(label, dict)
                            or any(not isinstance(label.get(lang), str)
                                   or not label[lang].strip() for lang in LANGS)):
                        raise ValueError("BSA253_DISTRACTOR_TRANSLATION_MISSING")
                    add("MCQ_DISTRACTOR_SCIENCE",
                        f"answerKey/options/{i}/label", _digest(label))
        if a.get("visualSpec") is not None:
            visual = a["visualSpec"]
            if not isinstance(visual, dict) or not visual:
                raise ValueError("BSA253_INVALID_DIAGRAM_SPEC")
            add("RENDERED_DIAGRAM_SCIENCE", "visualSpec", _digest(visual))
        else:
            # Absence of a declared diagram is NOT evidence that one is
            # scientifically unnecessary. Every activity needs source-bound
            # visual coverage determination, even when visualSpec is absent.
            add("VISUAL_COVERAGE_NEEDS_SOURCE", "visualSpec:$absent",
                _digest({"declaredVisualSpec": False}))
        if len({t["taskId"] for t in tasks}) != len(tasks):
            raise ValueError("BSA253_DUPLICATE_SEMANTIC_PROOF_TASK")
        all_tasks.extend(tasks)
    counts = Counter(t["kind"] for t in all_tasks)
    return {
        "status": "BSA253_INDEPENDENT_FULL_SEMANTIC_PROOFS_QUEUED",
        "sourceSha256": source_sha256,
        "packageSha256": package_sha,
        "activityCount": len(acts),
        "activityIds": ids,
        "taskCount": len(all_tasks),
        "taskCounts": {kind: counts[kind] for kind in KINDS},
        "tasks": all_tasks,
        "academicPASS": 0,
        "academicQA": "REVIEW_REQUIRED",
        "newProviderCalls": 0,
        "sourcePdfUploaded": False,
        "publicationAuthorized": False,
    }


def verify_semantic_queue(*, package: dict[str, Any], source_sha256: str,
                          queue: dict[str, Any]) -> None:
    """Verify complete exact regenerated inventory (not academic truth)."""
    expected = plan_full_semantic_proofs(
        package=package, source_sha256=source_sha256)
    if queue != expected:
        raise ValueError("BSA253_STALE_OR_FORGED_SEMANTIC_EVIDENCE_QUEUE")
