"""Read-only V3 course-level acceptance visibility across exact package bytes.

This is not a new reviewer, model transport, browser pilot or release authority.
It is an evidence inventory; missing or conflicting private evidence never
becomes an inferred model verdict. No state is created or modified.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from app_generator.validation.autonomous_completion import (
    package_identity, assessment_progress,
)

# Support the repository's canonical section-9-1 layout as well as
# portable synthetic section-1 fixtures without hardcoding chapter numbers.
_SECTION = re.compile(r"section-(?:[0-9]+-)?([0-9]+)\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")


def _approved_frozen_scope(
    chapter: Path, root: Path, expected_sections: int,
) -> dict[int, tuple[str, int]] | None:
    """Read existing immutable candidate identities, never historical V2 gates.

    A chapter-N directory may carry an acceptance_closure_chapterN.json
    frozen-candidate roster. It is a source for *scope and exact package
    identity only*: no former academic, human, rights or publication gate
    is inherited by V3. No roster means no implicit subset authorization.
    """
    m=re.fullmatch(r"chapter-([1-9][0-9]*)",chapter.name)
    if m is None:
        return None
    manifest=root/"docs"/("acceptance_closure_chapter"+m.group(1)+".json")
    if not manifest.exists():
        return None
    if (manifest.is_symlink() or not manifest.is_file()
        or manifest.stat().st_size > 150_000):
        raise ValueError("V3_UNSAFE_FROZEN_SCOPE_MANIFEST")
    data=json.loads(manifest.read_text(encoding="utf-8"))
    if (not isinstance(data,dict)
        or data.get("project")!="BOSLA"
        or data.get("contract")!="FINAL_ACCEPTANCE_NO_REPEAT_V2"
        or not isinstance(data.get("policy"),dict)
        or data["policy"].get("frozen") is not True
        or not isinstance(data.get("frozenCandidates"),list)
        or len(data["frozenCandidates"])!=expected_sections):
        raise ValueError("V3_INVALID_FROZEN_SCOPE_MANIFEST")
    result={}
    for candidate in data["frozenCandidates"]:
        if not isinstance(candidate,dict):
            raise ValueError("V3_INVALID_FROZEN_SCOPE_CANDIDATE")
        label=candidate.get("section")
        prefix=m.group(1)+"."
        suffix=label[len(prefix):] if isinstance(label,str) and label.startswith(prefix) else ""
        digest=candidate.get("packageSha256")
        count=candidate.get("activityCount")
        if (not suffix.isdecimal() or not suffix or str(int(suffix))!=suffix
            or int(suffix)<1 or int(suffix) in result
            or not isinstance(digest,str) or not _HASH.fullmatch(digest)
            or type(count) is not int or count<1):
            raise ValueError("V3_INVALID_FROZEN_SCOPE_CANDIDATE")
        result[int(suffix)]=(digest,count)
    return result


def course_readiness(
    chapter_dir: Path, repo_root: Path, *,
    private_root: Path | None = None, expected_sections: int = 6,
    section_numbers: tuple[int, ...] | None = None,
) -> dict:
    """Audit exactly the selected course's existing package/checkpoint roster.

    Only reads direct section-N/package.json children within repo content.
    Optional private checkpoint root must be outside the repo checkout and
    follows the already established authorized V3 session-run convention.
    """
    if type(expected_sections) is not int or not 1 <= expected_sections <= 200:
        raise ValueError("V3_INVALID_EXPECTED_SECTIONS")
    if not isinstance(repo_root, Path) or not isinstance(chapter_dir, Path):
        raise ValueError("V3_INVALID_COURSE_ROOT")
    root=repo_root.resolve(strict=True)
    content=(root/"content").resolve(strict=True)
    if chapter_dir.is_symlink() or not chapter_dir.is_dir():
        raise ValueError("V3_UNSAFE_CHAPTER_DIRECTORY")
    chapter=chapter_dir.resolve(strict=True)
    if not chapter.is_relative_to(content) or chapter == content:
        raise ValueError("V3_COURSE_NOT_UNDER_CONTENT")
    if private_root is not None:
        if not isinstance(private_root,Path) or not private_root.is_absolute() or private_root.is_symlink():
            raise ValueError("V3_UNSAFE_PRIVATE_ASSESSMENT_ROOT")
        private=private_root.resolve()
        if private == root or private.is_relative_to(root):
            raise ValueError("V3_UNSAFE_PRIVATE_ASSESSMENT_ROOT")
    else:
        private=None
    sections=[]
    for directory in chapter.iterdir():
        m=_SECTION.fullmatch(directory.name)
        if m is None:
            continue
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("V3_UNSAFE_SECTION_DIRECTORY")
        sections.append((int(m.group(1)),directory))
    if len({number for number,_ in sections})!=len(sections):
        raise ValueError("V3_DUPLICATE_COURSE_SECTION")
    sections.sort()
    # Validate an explicit claim before comparing it to frozen identities:
    # bools, lists and duplicate ordinals cannot masquerade as approval.
    if section_numbers is not None and (
        not isinstance(section_numbers,tuple)
        or len(section_numbers)!=expected_sections
        or any(type(i) is not int or i<1 for i in section_numbers)
        or len(set(section_numbers))!=len(section_numbers)
    ):
        raise ValueError("V3_INVALID_EXPLICIT_COURSE_SCOPE")
    frozen=_approved_frozen_scope(chapter,root,expected_sections)
    if frozen is not None:
        # Recover the complete approved set automatically on every normal
        # run. An explicit override is an assertion, never permission to
        # expand or substitute a different six-section campaign.
        if section_numbers is not None and set(section_numbers)!=set(frozen):
            raise ValueError("V3_SECTION_OVERRIDE_CONFLICTS_WITH_FROZEN_SCOPE")
        section_numbers=tuple(frozen)
    if section_numbers is not None:
        # For other scopes an explicitly supplied subset remains possible,
        # but it cannot override an existing frozen-candidate manifest.
        if (not isinstance(section_numbers,tuple)
            or len(section_numbers)!=expected_sections
            or any(type(i) is not int or i<1 for i in section_numbers)
            or len(set(section_numbers))!=len(section_numbers)):
            raise ValueError("V3_INVALID_EXPLICIT_COURSE_SCOPE")
        by_number=dict(sections)
        if not set(section_numbers).issubset(by_number):
            raise ValueError("V3_MISSING_EXPLICIT_COURSE_SECTION")
        sections=[(number,by_number[number])
                  for number in sorted(section_numbers)]
    elif len(sections)!=expected_sections:
        raise ValueError("V3_INCOMPLETE_COURSE_ROSTER")
    digests=set()
    rows=[]
    for number,section in sections:
        if (frozen is not None and
            section.name != f"section-{chapter.name.split('-')[-1]}-{number}"):
            raise ValueError("V3_FROZEN_SECTION_NAME_MISMATCH")
        package=section/"package.json"
        if (package.is_symlink() or not package.is_file()
            or package.stat().st_size > 2_000_000):
            raise ValueError("V3_MISSING_OR_UNSAFE_COURSE_PACKAGE")
        raw=package.read_bytes()
        digest,activities=package_identity(raw)
        if frozen is not None and (digest,len(activities))!=frozen[number]:
            raise ValueError("V3_FROZEN_PACKAGE_IDENTITY_DRIFT")
        if digest in digests:
            raise ValueError("V3_DUPLICATE_COURSE_PACKAGE")
        digests.add(digest)
        assessment=None
        if private is not None:
            state_dir=private/("v3-generated-"+digest)
            batches=state_dir/"batches"
            stage=batches/("v3-assessment-"+digest+".json")
            if any(path.is_symlink() for path in (state_dir,batches,stage)):
                raise ValueError("V3_UNSAFE_PRIVATE_COURSE_EVIDENCE")
            if stage.exists():
                if not stage.is_file() or stage.stat().st_size > 8_000_000:
                    raise ValueError("V3_UNSAFE_PRIVATE_COURSE_EVIDENCE")
                assessment=json.loads(stage.read_text(encoding="utf-8"))
        # This pre-existing validator rejects stale, forged, mismatched,
        # incomplete and inconsistent model checkpoint aggregates.
        progress=assessment_progress(raw,assessment)
        rows.append({
            "section":section.name,
            "packageSha256":digest,
            "activitiesTotal":len(activities),
            "activitiesAssessedRows":progress["activitiesAssessed"],
            "activitiesFullyModelReviewed":progress["activitiesFullyModelReviewed"],
            "modelConsensusPassActivities":progress["modelConsensusPassActivities"],
            "reviewerRequestsSkippedUnsent":progress["reviewerRequestsSkippedUnsent"],
            "currentTechnicalDisposition":progress["currentTechnicalDisposition"],
        })
    total=sum(row["activitiesTotal"] for row in rows)
    reviewed=sum(row["activitiesFullyModelReviewed"] for row in rows)
    assessed=sum(row["activitiesAssessedRows"] for row in rows)
    consensus=sum(row["modelConsensusPassActivities"] for row in rows)
    pending=any(row["currentTechnicalDisposition"]=="PENDING_AUTOMATED_ASSESSMENT" for row in rows)
    repair=any(row["currentTechnicalDisposition"]=="AUTO_REPAIR_REQUIRED" for row in rows)
    ambiguous=any(row["currentTechnicalDisposition"]=="RECONCILE_AMBIGUOUS_REVIEW" for row in rows)
    disposition=("AUTO_REPAIR_REQUIRED" if repair else
                 "PENDING_AUTOMATED_ASSESSMENT" if pending else
                 "RECONCILE_AMBIGUOUS_REVIEW" if ambiguous else
                 "PENDING_DETERMINISTIC_RELEASE_EVIDENCE")
    return {
        "contract":"AUTONOMOUS_AI_TECHNICAL_COMPLETION_V3",
        "scope":"READ_ONLY_COURSE_EVIDENCE_INVENTORY",
        "scopeSource":("FROZEN_CANDIDATE_MANIFEST" if frozen is not None
                       else "EXPLICIT_OR_COMPLETE_DIRECTORY"),
        "sectionsTotal":len(rows),
        "activitiesTotal":total,
        "activitiesAssessedRows":assessed,
        "activitiesFullyModelReviewed":reviewed,
        "modelConsensusPassActivities":consensus,
        "reviewerRequestsSkippedUnsent":sum(
            row["reviewerRequestsSkippedUnsent"] for row in rows),
        "currentTechnicalDisposition":disposition,
        "courseReleaseReceiptValidated":False,
        "publicationAuthorized":False,
        "sectionProgress":rows,
    }
