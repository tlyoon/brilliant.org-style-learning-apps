"""Source-bound technical screenshot evidence coverage for private academic queue.

Browser/PNG checks certify capture identity, existence and nonblank pixels only.
They never certify diagram physics, accessibility or EN/MS/ZH semantics.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.private_visual_pixel_integrity import audit_private_visual_pixel_integrity

_EXPECTED_LOCALES=frozenset(("en","ms","zh"))
_EXPECTED_WIDTHS=frozenset((390,1280))


def audit_source_bound_visual_readiness(
    *, package_file:Path, source_pdf:Path,
    browser_evidence_dir:Path, academic_queue:dict[str,Any],
) -> dict[str,Any]:
    package_bytes=package_file.read_bytes()
    source_bytes=source_pdf.read_bytes()
    psha=sha256(package_bytes).hexdigest()
    ssha=sha256(source_bytes).hexdigest()
    if (not source_bytes.startswith(b"%PDF-") or
        not isinstance(academic_queue,dict) or
        academic_queue.get("status")!="SOURCE_BOUND_AUTONOMOUS_ACADEMIC_REVIEW_QUEUE" or
        academic_queue.get("packageSha256")!=psha or
        academic_queue.get("sourceSha256")!=ssha or
        academic_queue.get("publicationAuthorized") is not False):
        raise ValueError("visual evidence must match controlled original-source academic queue")
    package=json.loads(package_bytes.decode("utf-8"))
    activities=package.get("activities")
    queued=academic_queue.get("activities")
    if (not isinstance(activities,list) or not isinstance(queued,list) or
        len(activities)!=academic_queue.get("activityCount") or
        len(queued)!=len(activities)):
        raise ValueError("academic queue does not cover exact package activities")
    ids=[a.get("id") for a in activities if isinstance(a,dict)]
    queue_ids=[a.get("activityId") for a in queued if isinstance(a,dict)]
    if (len(ids)!=len(activities) or len(set(ids))!=len(ids) or
        len(queue_ids)!=len(ids) or len(set(queue_ids))!=len(ids) or
        set(ids)!=set(queue_ids) or
        any(row.get("publicationAuthorized") is not False for row in queued)):
        raise ValueError("visual-to-academic activity identities mismatch")
    visuals={a["id"] for a in activities if a.get("visualSpec")}
    if not visuals:
        raise ValueError("no visual activities in original package")
    # Independently re-read real PNGs, hashes, controlled source, and RGB data.
    receipt=audit_private_visual_pixel_integrity(
        package_file=package_file,source_pdf=source_pdf,
        evidence_dir=browser_evidence_dir,
        expected_package_sha256=psha,expected_source_sha256=ssha,
    )
    if (receipt.get("packageSha256")!=psha or receipt.get("sourceSha256")!=ssha or
        receipt.get("pixelQualityReviewed") is not False or
        receipt.get("academicAccuracyReviewed") is not False or
        receipt.get("publicationAuthorized") is not False or
        receipt.get("technicalPixelIntegrityChecked") is not True):
        raise ValueError("screenshot receipt cannot imply visual scientific approval")
    checks=receipt.get("checks")
    if not isinstance(checks,list):
        raise ValueError("browser screenshot checks absent")
    expected={(aid,lang,width) for aid in visuals
              for lang in _EXPECTED_LOCALES for width in _EXPECTED_WIDTHS}
    actual=[]
    for check in checks:
        if not isinstance(check,dict):
            raise ValueError("invalid technical screenshot receipt")
        actual.append((check.get("activityId"),check.get("locale"),check.get("viewportWidth")))
    if len(actual)!=len(expected) or len(set(actual))!=len(actual) or set(actual)!=expected:
        raise ValueError("visual screenshots lack full locale and mobile/desktop coverage")
    rows=[]
    for row in queued:
        aid=row["activityId"]
        rows.append({
            "activityId":aid,"academicPriority":row["priority"],
            "visualSpecPresent":aid in visuals,
            "technicalVisualCapturesVerified":6 if aid in visuals else 0,
            "technicalPixelIntegrityVerified":aid in visuals,
            "scientificVisualSemanticsVerified":False,
            "trilingualVisualMeaningVerified":False,
            "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
        })
    return {
        "status":"EXACT_SOURCE_TECHNICAL_VISUAL_COVERAGE_ONLY",
        "sourceSha256":ssha,"packageSha256":psha,
        "activityCount":len(ids),"visualActivities":len(visuals),
        "screenshotCapturesVerified":len(actual),
        "sourceVerifiedBrowserReceipt":receipt.get("sourceIdentityStatus"),
        "desktopAndMobileTrilingualScreenshotsCovered":True,
        "scientificVisualSemanticsVerified":False,
        "academicAccuracyReviewed":False,
        "academicQA":"REVIEW_REQUIRED",
        "formalAcademicPASSCount":0,
        "publicationAuthorized":False,
        "activities":rows,
    }
