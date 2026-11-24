"""BSA258: restart-safe V30 real Chrome screenshot pixels, successor to signed V29.

Only executes after genuine signed V28->V29 proof; stores exactly three
private PNGs, a screenshot manifest, and a signed bounded final receipt.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_public_nonmerging_draft_pr import _preflight
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.runtime.v3_post_v28_source_visual_pilot import (
    _V29,_V29_DRAFT,_V29_GEOMETRY,_STATUS29,
)
from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,
)
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_exact_revised_review_reconciliation import _CANDIDATE
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json

_V30_PRE="V30_ACTUAL_BROWSER_PIXEL_PRE_CALL.json"
_V30_RASTER="V30_PRIVATE_REAL_CHROME_SCREENSHOT_PIXEL_RESULT.json"
_V30="V30_SOURCE_PINNED_ACTUAL_BROWSER_PIXELS_NO_ACADEMIC_PASS.json"
_STATUS30="V30_REAL_BROWSER_SOURCE_BOUND_THREE_LOCALE_PIXELS_PRIVATE_NO_RELEASE"


def run_post_v29_real_browser_pixels(
    repo:Path,private:Path,ready:dict[str,Any],
    v9:dict,v11:dict,v12:dict,v29_result:dict[str,Any],
)->dict[str,Any]:
    folder,_,_,_,_=_preflight(repo,private,ready,v9,v11,v12)
    v29=_signed(folder,_V29,ready)
    draft=_signed(folder,_V29_DRAFT,ready)
    dom=_signed(folder,_V29_GEOMETRY,ready)
    if (v29!=v29_result or v29.get("status")!=_STATUS29
            or v29.get("privateDraftSha256")!=draft.get("integritySha256")
            or v29.get("realSvgGeometryReceiptSha256")!=dom.get("integritySha256")
            or v29.get("actualRenderedSvgArrowsVerified")!=6
            or v29.get("completeAcademicProofGatesStillOpen")!=90
            or v29.get("independentMeaningMicroproofsPending")!=429
            or v29.get("fullAcademicPASS")!=0
            or v29.get("newModelCalls")!=0
            or v29.get("publicationAuthorized") is not False
            or v29.get("sourceSha256")!=_SOURCE_SHA
            or v29.get("revisedCandidateSha256")!=_CANDIDATE_SHA
            or draft.get("sourceSha256")!=_SOURCE_SHA
            or draft.get("candidateSha256")!=_CANDIDATE_SHA):
        raise ValueError("BSA258_SIGNED_EXACT_SOURCE_V29_NOT_VERIFIED")
    source=_trusted_json(private/_SOURCE_BINDING)
    pdf=Path(source["sourcePdf"])
    original=folder/_CANDIDATE
    if (pdf.is_symlink() or not pdf.is_file()
            or sha256(pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
            or original.is_symlink() or not original.is_file()
            or sha256(original.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA258_ORIGINAL_SERWAY_PDF_OR_REVISED_SOURCE_CHANGED")
    identity={
        "gitHead":ready["gitHead"],
        "proposalSha256":ready["proposalSha256"],
        "sourceSha256":_SOURCE_SHA,
        "revisedCandidateSha256":_CANDIDATE_SHA,
        "sourceV29ReceiptSha256":v29["integritySha256"],
        "sourceV29PrivateDraftSha256":draft["integritySha256"],
        "sourceV29DomReceiptSha256":dom["integritySha256"],
    }
    _v6_checkpoint(folder/_V30_PRE,{
        **identity,"status":"V30_PRIVATE_RENDERED_BROWSER_PIXEL_PRE_CALL",
        "newProviderCalls":0,"publicationAuthorized":False,
        "outsideSourcePdfsRequired":False,
    })
    screenshot_dir=folder/"private-v30-browser-evidence"
    if screenshot_dir.is_symlink():
        raise ValueError("BSA258_PRIVATE_SCREENSHOT_FOLDER_SYMLINK")
    screenshot_dir.mkdir(parents=True,exist_ok=True)
    args=[
        sys.executable,str(repo/"scripts"/"check_v30_private_browser_velocity_pixels.py"),
        "--draft",str(folder/_V29_DRAFT),
        "--output-dir",str(screenshot_dir),
    ]
    checked=subprocess.run(args,cwd=repo,capture_output=True,text=True,
                           timeout=100,check=False)
    if checked.returncode!=0:
        raise ValueError("BSA258_REAL_CHROME_SCREENSHOT_PIXELS_FAILED")
    raster=json.loads(checked.stdout)
    if (raster.get("status")!=
            "BSA258_V30_ACTUAL_HEADLESS_CHROME_RASTER_VECTORS_CHECKED_PRIVATE"
            or raster.get("actualBrowserPixelForPrivateDiagramVerified") is not True
            or raster.get("realBrowserScreenshotsProduced")!=3
            or raster.get("realBrowserRasterOppositeVelocityArrowsVerified")!=6
            or raster.get("independentOriginalFigurePixelEquivalenceProven") is not False
            or raster.get("fullTrilingualScientificMeaningProven") is not False
            or raster.get("fullSourceScientificMeaningProven") is not False
            or raster.get("fullAcademicPASS")!=0
            or raster.get("newProviderCalls")!=0
            or raster.get("publicationAuthorized") is not False
            or len(raster.get("screenshots",[]))!=3):
        raise ValueError("BSA258_SCREENSHOT_RESULT_FALSELY_ACADEMIC_ACCEPTED")
    for locale,row in zip(("en","ms","zh"),raster["screenshots"],strict=True):
        expected="V30_PRIVATE_BROWSER_SCREENSHOT_"+locale+".png"
        path=screenshot_dir/expected
        if (row.get("locale")!=locale
                or row.get("privateScreenshotFilename")!=expected
                or path.is_symlink() or not path.is_file()
                or row.get("privateScreenshotSha256")!=
                    sha256(path.read_bytes()).hexdigest()
                or row.get("privateScreenshotBytes")!=path.stat().st_size
                or not (2000<=path.stat().st_size<=400000)):
            raise ValueError("BSA258_BROWSER_REAL_PIXEL_RECEIPT_OR_PNG_MISMATCH")
    raster_signed=_v6_checkpoint(folder/_V30_RASTER,{
        **identity,**raster,"publicationAuthorized":False,
    })
    return _v6_checkpoint(folder/_V30,{
        **identity,"status":_STATUS30,
        "sourceV30RasterReceiptSha256":raster_signed["integritySha256"],
        "realChromeScreenshotPixelEvidenceCount":3,
        "realChromeScreenshotVelocityArrowsVerified":6,
        "privatePedagogicalVisualRasterVerified":True,
        "independentSourceFigureExactPixelMatch":False,
        "fullIndependentTextbookExplanationProofsPassed":0,
        "completeAcademicProofGatesStillOpen":90,
        "independentMeaningMicroproofsPending":429,
        "fullAcademicPASS":0,"newModelCalls":0,
        "publicationAuthorized":False,
        "outsideTextbookPdfsRequired":False,
        "nextEligibleMilestone":"BOUNDED_INDEPENDENT_MCQ_TRILINGUAL_SEMANTIC_WITNESSES",
    })
