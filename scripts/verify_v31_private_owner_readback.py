"""BSA258/259 independent readback of owner Yoga6 NORMAL V1-V31 receipts.

Does NOT rerun/rewrite the worker or the screenshots. Uses stdlib PNG pixel
decoding separate from Chrome's JavaScript screenshot raster checker, plus
reopening the genuine original single Serway textbook PDF and frozen candidate.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v28_source_visual_pilot import _V29,_STATUS29
from app_generator.runtime.v3_post_v29_real_browser_pixels import (
    _V30,_V30_RASTER,_STATUS30,
)
from app_generator.runtime.v3_post_v30_bounded_mcq_semantics import (
    _V31,_V31_WITNESS,_STATUS31,
)
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.validation.section91_formal_physics import _SOURCE_SHA,_CANDIDATE_SHA
from app_generator.validation.section91_bounded_semantic_witness import (
    source_bound_four_choice_witness,
)
from app_generator.validation.private_raster_pixels import validate_private_raster_png

PROPOSAL="738a612d6d192cae715858c226bf0f952ceeb0a2df823502d15a387448b968b0"


def main()->None:
    head=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,check=True,
                        capture_output=True,text=True,timeout=15).stdout.strip()
    local=os.environ.get("LOCALAPPDATA")
    if not local or len(head)!=40:
        raise ValueError("BSA258_INDEPENDENT_OWNER_HEAD_INVALID")
    private=Path(local)/"Microvid"/"BoslaV3ReviewYoga6"
    folder=private/"owner-five-stage-completion"/head/PROPOSAL
    ready={"gitHead":head,"proposalSha256":PROPOSAL}
    v29=_signed(folder,_V29,ready)
    v30=_signed(folder,_V30,ready)
    raster=_signed(folder,_V30_RASTER,ready)
    v31=_signed(folder,_V31,ready)
    witness=_signed(folder,_V31_WITNESS,ready)
    if (v29.get("status")!=_STATUS29
            or v30.get("status")!=_STATUS30
            or v31.get("status")!=_STATUS31
            or v30.get("sourceV29ReceiptSha256")!=v29["integritySha256"]
            or v30.get("sourceV30RasterReceiptSha256")!=raster["integritySha256"]
            or v31.get("sourceV30ReceiptSha256")!=v30["integritySha256"]
            or v31.get("sourceV31LocalizedWitnessSha256")!=witness["integritySha256"]
            or any(v.get("fullAcademicPASS")!=0 or
                   v.get("publicationAuthorized") is not False
                   for v in (v29,v30,v31,witness))
            or v31.get("completeAcademicProofGatesStillOpen")!=90
            or v31.get("independentMeaningMicroproofsPending")!=429
            or v31.get("newModelCalls")!=0):
        raise ValueError("BSA259_INDEPENDENT_SIGNED_CHAIN_OR_ACADEMIC_GATE_BAD")
    binding=_trusted_json(private/_SOURCE_BINDING)
    source_pdf=Path(binding["sourcePdf"])
    candidate=folder/_CANDIDATE
    if (source_pdf.is_symlink() or not source_pdf.is_file()
            or candidate.is_symlink() or not candidate.is_file()
            or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
            or sha256(candidate.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA259_ORIGINAL_SELECTED_TEXTBOOK_DRIFT")
    evidence=source_bound_four_choice_witness(
        source_pdf=source_pdf,package_file=candidate)
    if (evidence["localizedRoleWitnesses"]!=witness["localizedRoleWitnesses"]
            or evidence["mathematicallyCounterexampledFalseChoices"]!=3
            or evidence["independentlyCheckedOptionLocales"]!=12):
        raise ValueError("BSA259_INDEPENDENT_MCQ_SOURCE_WITNESS_MISMATCH")
    rows=[]
    expected_rows=raster.get("screenshots")
    if not isinstance(expected_rows,list) or len(expected_rows)!=3:
        raise ValueError("BSA258_INDEPENDENT_SCREENSHOT_ROSTER_WRONG")
    for locale,row in zip(("en","ms","zh"),expected_rows,strict=True):
        filename="V30_PRIVATE_BROWSER_SCREENSHOT_"+locale+".png"
        if row.get("locale")!=locale or row.get("privateScreenshotFilename")!=filename:
            raise ValueError("BSA258_INDEPENDENT_LANGUAGE_PIXEL_ROSTER_DRIFT")
        saved=folder/"private-v30-browser-evidence"/filename
        pixels=validate_private_raster_png(saved)
        if (pixels["pngSha256"]!=row["privateScreenshotSha256"]
                or row.get("realScreenshotRaster",{}).get("screenshotWidth")!=640
                or row.get("realScreenshotRaster",{}).get("screenshotHeight")!=360):
            raise ValueError("BSA258_INDEPENDENT_ACTUAL_PNG_SHA_OR_SIZE_DRIFT")
        rows.append({"locale":locale,"sha256":pixels["pngSha256"],
                     "verifiedRasterArrows":pixels["verifiedOppositeVelocityArrows"],
                     "independentArrowPixels":{
                         "left":pixels["independentLeftwardArrowPixels"],
                         "right":pixels["independentRightwardArrowPixels"]}})
    print(json.dumps({
        "status":"BSA259_INDEPENDENT_ORIGINAL_SERWAY_V30_V31_REAL_PNG_PASS",
        "gitHead":head,
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "signedV29Sha256":v29["integritySha256"],
        "signedV30Sha256":v30["integritySha256"],
        "signedV31Sha256":v31["integritySha256"],
        "privateBrowserScreenshotReadbackCount":len(rows),
        "independentlyDecodedRasterArrows":sum(
            r["verifiedRasterArrows"] for r in rows),
        "sourceBoundSemanticRoleChecksReverified":
            evidence["independentlyCheckedLocalizedRoleTexts"],
        "sourceBoundMcqFalseOptionCounterexamples":3,
        "fullAcademicPASS":0,
        "completeAcademicGatesStillOpen":90,
        "fullMeaningMicroproofsPending":429,
        "newModelCalls":0,
        "publicationAuthorized":False,
        "privatePixelEvidence":rows,
    },ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    main()
