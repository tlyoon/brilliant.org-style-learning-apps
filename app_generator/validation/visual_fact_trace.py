"""Source-bound five-diagram fact trace and historical screenshot coverage.

This binds original PDF passages, declared visual scientific fact IDs, existing
bounded mechanics checks and PRIVATE historical 3-locale x 2-viewport screenshot
receipts. It does NOT inspect the historical PNG pixels again and does not
establish full figure or translation semantics. No original content is output.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.bounded_diagram_physics import check_bounded_diagram_physics

# Explicit independently tracked fact/provenance policy for the fixed pilot.
# These identifiers are model metadata, not quotations from the source.
FACTS={
 "mcq-collision-types-concept":(
  2,(("collision-isolated-momentum-conservation","source_fact",("cart-1","cart-2")),
     ("inelastic-kinetic-energy-loss","source_fact",("cart-1","cart-2")))),
 "mcq-perfectly-inelastic-outcome":(
  2,(("perfectly-inelastic-definition","source_fact",("cart-1","cart-2")),
     ("common-final-velocity-formula","source_fact",("cart-1","cart-2")))),
 "mcq-equal-mass-elastic-transfer":(
  4,(("equal-mass-elastic-exchange","source_fact",("cart-1","cart-2")),
     ("inelastic-velocity-sharing","source_fact",("cart-1","cart-2")))),
 "mcq-extreme-mass-heavy-target":(
  2,(("extreme-mass-limit-heavy-target","source_fact",("cart-1","cart-2")),
     ("inelastic-kinetic-energy-dissipation","source_fact",("cart-1","cart-2")))),
 "mcq-spring-collision-intermediate":(
  9,(("energy-storage-intermediate-state","source_fact",("kinetic","elastic","intermediate-state")),
     ("spring-collision-isolated-system","source_fact",("mechanical-energy-conservation",)),
     ("relative-energy-normalization","pedagogical_simplification",("initial-state","intermediate-state")))),
}
_LANGS=("en","ms","zh")
_VIEWPORTS=(390,1280)


def audit_source_visual_fact_trace(
    *,package_file:Path,source_pdf:Path,packets_file:Path,
    historical_pixel_receipt:Path,
)->dict[str,Any]:
    original=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=packets_file,expected_count=18)
    raw=package_file.read_bytes()
    if (original.get("newlyReverifiedSourceActivities")!=18 or
        original.get("packageSha256")!=sha256(raw).hexdigest() or
        original.get("publicationAuthorized") is not False):
        raise ValueError("original PDF or private package source identity mismatch")
    pkg=json.loads(raw.decode("utf-8"))
    visual={a["id"]:a for a in pkg["activities"] if a.get("visualSpec")}
    if len(visual)!=5 or set(visual)!=set(FACTS):
        raise ValueError("visual source-grounding activity roster changed")
    source_rows={q["activityId"]:q for q in original["activityEvidence"]}
    if len(source_rows)!=18:
        raise ValueError("original source packet evidence incomplete")
    evidence=[]
    total_facts=simplifications=0
    for aid,activity in visual.items():
        original_page,expected=FACTS[aid]
        actual_pages=source_rows[aid]["verifiedPhysicalPdfPages"]
        if actual_pages!=[original_page]:
            raise ValueError("original source page for visual changed")
        spec=activity["visualSpec"]
        actual=spec.get("grounding")
        if not isinstance(actual,list) or len(actual)!=len(expected):
            raise ValueError("visual fact grounding roster changed")
        seen=set()
        valid_refs={x["id"] for x in spec.get("entities",[])}
        valid_refs.update(x["id"] for x in spec.get("states",[]))
        valid_refs.add("mechanical-energy-conservation")
        for fact,policy in zip(actual,expected):
            if not isinstance(fact,dict):
                raise ValueError("malformed source-grounded visual fact")
            fields=(fact.get("factId"),fact.get("origin"),
                    tuple(fact.get("appliesTo",[])))
            if fields!=policy or fields[0] in seen:
                raise ValueError("visual fact identity or source/pedagogical provenance changed")
            if any(ref not in valid_refs for ref in fields[2]):
                raise ValueError("source fact references unknown rendered entity/state")
            seen.add(fields[0])
            total_facts+=1
            simplifications+=int(fields[1]=="pedagogical_simplification")
        proof=check_bounded_diagram_physics(activity)
        evidence.append({
            "activityId":aid,
            "originalPhysicalPdfPage":original_page,
            "declaredSourceFactIdsCrossChecked":len(expected),
            "boundedVisualModelChecked":proof["boundedPhysicalCheck"],
            "specificOriginalFigurePixelSemanticsVerified":False,
            "translatedVisualMeaningVerified":False,
        })
    if total_facts!=11 or simplifications!=1:
        raise ValueError("source visual fact policy or normalization drift")
    pixel=json.loads(historical_pixel_receipt.read_text(encoding="utf-8"))
    if (pixel.get("packageSha256")!=original["packageSha256"] or
        pixel.get("sourceSha256")!=original["sourceSha256"] or
        pixel.get("publicationAuthorized") is not False or
        pixel.get("technicalPixelIntegrityChecked") is not True or
        pixel.get("academicAccuracyReviewed") is not False or
        pixel.get("pixelQualityReviewed") is not False or
        pixel.get("screenCapturesChecked")!=30):
        raise ValueError("historical screenshot identity/limitations are invalid")
    rows=pixel.get("checks")
    expected={(a,l,w) for a in FACTS for l in _LANGS for w in _VIEWPORTS}
    if not isinstance(rows,list) or len(rows)!=30:
        raise ValueError("full historical visual screenshot roster missing")
    seen=set()
    for check in rows:
        if not isinstance(check,dict):
            raise ValueError("invalid screenshot receipt")
        key=(check.get("activityId"),check.get("locale"),
             check.get("viewportWidth"))
        if key in seen:
            raise ValueError("duplicate historical screenshot receipt")
        seen.add(key)
        if (type(check.get("distinctSampleColors")) is not int or
            check["distinctSampleColors"]<3 or
            type(check.get("nonwhitePixelPercent")) not in (int,float) or
            not 1<=check["nonwhitePixelPercent"]<=100 or
            type(check.get("width")) is not int or check["width"]<100 or
            type(check.get("height")) is not int or check["height"]<100):
            raise ValueError("untrustworthy historical screenshot metadata")
    if seen!=expected:
        raise ValueError("historical screenshot language/viewport coverage mismatch")
    return {
        "status":"SOURCE_BOUND_DECLARED_VISUAL_FACT_TRACE_ONLY",
        "sourceSha256":original["sourceSha256"],
        "packageSha256":original["packageSha256"],
        "allOriginalSourceActivitiesReverified":18,
        "visualActivitiesChecked":5,
        "declaredFactIdentifiersCrossChecked":total_facts,
        "declaredPedagogicalSimplifications":simplifications,
        "boundedVisualPhysicsModelsRechecked":5,
        "historicalTechnicalScreenshotReceiptsCrossChecked":30,
        "historicalScreenshotPixelsRehashedInThisRun":False,
        "sourcePassageSemanticsApproved":False,
        "figurePixelScientificMeaningApproved":False,
        "threeLanguageVisualMeaningApproved":False,
        "academicQA":"REVIEW_REQUIRED",
        "formalAcademicPASS":0,
        "publicationAuthorized":False,
        "visualResults":evidence,
    }
