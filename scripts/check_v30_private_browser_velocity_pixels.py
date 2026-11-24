"""BSA258: real headless Chrome raster/pixel proof for frozen private V29 diagram.

Uses *production* physics renderer + stylesheet and selenium screenshots.
Source-free and localhost/network-free (data: document), keeps PNGs private.
A pixel proof of a pedagogical velocity drawing is NOT textbook figure
equivalence, natural language semantic acceptance, or release permission.
"""
from __future__ import annotations

import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
RENDERER = REPO/"domains"/"university-level physics"/"visuals"/"physics-renderers.js"
CSS = REPO/"domains"/"university-level physics"/"visuals"/"physics-styles.css"

_PIXEL_JS = """
const png=arguments[0], cb=arguments[arguments.length-1];
const picture=new Image();
picture.onerror=()=>cb({error:"BSA258_SCREENSHOT_DECODE_FAILED"});
picture.onload=()=>{
 try {
  const canvas=document.createElement("canvas");
  canvas.width=picture.naturalWidth;canvas.height=picture.naturalHeight;
  const ctx=canvas.getContext("2d",{willReadFrequently:true});
  ctx.drawImage(picture,0,0);
  const at=(x,y)=>Array.from(ctx.getImageData(x,y,1,1).data);
  const patch=(x,y)=> {
   const pts=[];
   for(let dx=-3;dx<=3;dx++) for(let dy=-2;dy<=2;dy++)
     pts.push(at(x+dx,y+dy));
   return pts;
  };
  cb({width:canvas.width,height:canvas.height,
      leftArrowPatch:patch(150,191),rightArrowPatch:patch(480,191),
      leftBackground:at(150,145),rightBackground:at(480,145)});
 } catch(e) {cb({error:String(e)});}
};
picture.src="data:image/png;base64,"+png;
"""

def _same_color(pixel: list[int], expected: tuple[int,int,int]) -> bool:
    return (len(pixel)==4 and pixel[3]>=245
            and all(abs(pixel[i]-expected[i])<=36 for i in range(3)))

def verify_browser_raster_pixels(samples:dict[str,Any]) -> dict[str,Any]:
    """Fail closed if screenshot bytes do not visibly contain two CSS-colored arrows."""
    if samples.get("error") or (samples.get("width"),samples.get("height"))!=(640,360):
        raise ValueError("BSA258_REAL_BROWSER_RASTER_SIZE_OR_DECODE_INVALID")
    left=samples.get("leftArrowPatch")
    right=samples.get("rightArrowPatch")
    if not (isinstance(left,list) and isinstance(right,list)
            and len(left)==35 and len(right)==35
            and all(isinstance(px,list) for px in left+right)):
        raise ValueError("BSA258_MISSING_REAL_RASTER_PATCH_PIXELS")
    # Production stylesheet colors: first solid leftward arrow and
    # second dashed rightward arrow. Look at a small patch, not one fragile pixel.
    green=(23,107,81)
    orange=(217,119,6)
    count_left=sum(_same_color(x,green) for x in left)
    count_right=sum(_same_color(x,orange) for x in right)
    if (count_left<9 or count_right<9
            or _same_color(samples.get("leftBackground",[]),green)
            or _same_color(samples.get("rightBackground",[]),orange)):
        raise ValueError("BSA258_SCREENSHOT_DOES_NOT_SHOW_OPPOSING_COLORED_VELOCITY_ARROWS")
    return {"leftRasterGreenPixels":count_left,
            "rightRasterOrangePixels":count_right,
            "screenshotWidth":640,"screenshotHeight":360}

def run_browser_raster_check(draft:Path,output_dir:Path)->dict[str,Any]:
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    if (draft.is_symlink() or not draft.is_file()
            or draft.stat().st_size>12000
            or output_dir.is_symlink()
            or not output_dir.is_dir()):
        raise ValueError("BSA258_PRIVATE_SIGNED_SOURCE_INPUT_OR_OUTPUT_MISSING")
    document=json.loads(draft.read_text(encoding="utf8"))
    if (document.get("status")!=
            "BSA257_PRIVATE_ONE_SOURCE_GROUNDED_VISUAL_DRAFT_NO_RELEASE"
            or document.get("activityId")!="act-mcq-01-vector-nature"
            or document.get("sourceSha256")!=
                "cdbea066436ace273b94aedc2eb1b22f94d0fd5b0b3f810d6bfc27469a5e7b50"
            or document.get("candidateSha256")!=
                "454715ec1a3e23ce19099d4f1ed56babb1de3c8561473b9072c6e01ffbae9c38"
            or document.get("fullAcademicPASS")!=0
            or document.get("publicationAuthorized") is not False
            or document.get("spec",{}).get("template")!=
                "mechanics.opposite_velocity_pair_1d"):
        raise ValueError("BSA258_SOURCE_PINNED_V29_VISUAL_REQUIRED")
    original=json.dumps(document["spec"],ensure_ascii=False)
    if not RENDERER.is_file() or not CSS.is_file():
        raise ValueError("BSA258_PRODUCTION_RENDERER_STYLES_MISSING")
    js=RENDERER.read_text(encoding="utf8")
    css=CSS.read_text(encoding="utf8")
    screenshot_rows=[]
    opt=webdriver.ChromeOptions()
    opt.add_argument("--headless=new")
    opt.add_argument("--disable-extensions")
    opt.add_argument("--no-first-run")
    opt.add_argument("--disable-background-networking")
    opt.add_argument("--window-size=1000,720")
    opt.add_argument("--force-device-scale-factor=1")
    opt.add_argument("--hide-scrollbars")
    opt.page_load_strategy="eager"
    browser=webdriver.Chrome(options=opt)
    try:
        browser.set_page_load_timeout(20)
        browser.set_script_timeout(20)
        browser.get("data:text/html,<html><head><meta charset='utf-8'></head><body></body></html>")
        browser.execute_script(
            "const s=document.createElement('style');"
            "s.textContent=arguments[0];document.head.append(s);",css)
        browser.execute_script(js)
        if not browser.execute_script(
                "return window.DomainVisuals.supportedTemplates."
                "includes('mechanics.opposite_velocity_pair_1d')"):
            raise ValueError("BSA258_PRODUCTION_TEMPLATE_NOT_LOADED")
        for locale in ("en","ms","zh"):
            browser.execute_script(
                """
                document.body.replaceChildren();
                const s=JSON.parse(arguments[0]);
                const fig=window.DomainVisuals.renderVisualSpec(s,{
                    locale:arguments[1],document});
                fig.style.width="640px";fig.style.margin="0";fig.style.border="0";
                fig.style.boxShadow="none";fig.style.borderRadius="0";
                document.body.style.margin="0";
                document.body.append(fig);
                """,original,locale)
            figure=browser.find_element(By.CSS_SELECTOR,
                                        'figure[data-template="mechanics.opposite_velocity_pair_1d"]')
            svg=figure.find_element(By.CSS_SELECTOR,"svg.physics-visual__svg")
            proof=browser.execute_script(
                """
                const f=document.querySelector('figure');
                const s=f.querySelector('svg');
                const a=s.querySelector('[data-semantic-id="velocity-a"]');
                const b=s.querySelector('[data-semantic-id="velocity-b"]');
                const lines=[a,b];
                return {label:f.getAttribute('aria-label'),
                  renderer:f.getAttribute('data-renderer-version'),
                  template:f.getAttribute('data-template'),
                  svgSize:[s.getBoundingClientRect().width,s.getBoundingClientRect().height],
                  bodyCount:s.querySelectorAll('g.physics-visual__body').length,
                  arrowCount:s.querySelectorAll('line.physics-visual__vector').length,
                  arrows:lines.map(n=>n?{x1:+n.getAttribute('x1'),
                     x2:+n.getAttribute('x2'),y1:+n.getAttribute('y1'),
                     y2:+n.getAttribute('y2'),
                     stroke:getComputedStyle(n).stroke,
                     strokeWidth:getComputedStyle(n).strokeWidth,
                     opacity:getComputedStyle(n).opacity}:null),
                  visible: getComputedStyle(s).visibility,
                  actualLabelText:Array.from(s.querySelectorAll(
                       'text.physics-visual__entity-label')).map(n=>n.textContent)
                };
                """)
            vectors=proof["arrows"]
            if (proof["label"]!=document["spec"]["accessibility"]["description"][locale]
                    or proof["template"]!="mechanics.opposite_velocity_pair_1d"
                    or proof["renderer"]!="1.0.0"
                    or proof["svgSize"]!=[640,360]
                    or proof["arrowCount"]!=2 or proof["bodyCount"]!=2
                    or proof["visible"]!="visible"
                    or proof["actualLabelText"]!=[
                        e["label"][locale] for e in document["spec"]["entities"]]
                    or any(a is None or a["opacity"]=="0" for a in vectors)
                    or not (vectors[0]["x2"]<vectors[0]["x1"]
                            and vectors[1]["x2"]>vectors[1]["x1"]
                            and abs((vectors[0]["x2"]-vectors[0]["x1"])
                                    +(vectors[1]["x2"]-vectors[1]["x1"]))<1e-8)
                    or any(a["y1"]!=a["y2"] for a in vectors)):
                raise ValueError("BSA258_REAL_CHROME_DOM_OR_SOURCE_VISUAL_MISMATCH_"+locale)
            screenshot=svg.screenshot_as_png
            if not screenshot.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("BSA258_CHROME_SCREENSHOT_INVALID_PNG")
            samples=browser.execute_async_script(
                _PIXEL_JS,base64.b64encode(screenshot).decode("ascii"))
            verified=verify_browser_raster_pixels(samples)
            target=output_dir/("V30_PRIVATE_BROWSER_SCREENSHOT_"+locale+".png")
            if target.is_symlink() or target.exists():
                # This is a private, deterministic exact-head verification output,
                # NOT the immutable source or frozen candidate.
                if target.is_symlink():
                    raise ValueError("BSA258_SCREENSHOT_TARGET_SYMLINK")
            target.write_bytes(screenshot)
            screenshot_rows.append({
                "locale":locale,
                "privateScreenshotFilename":target.name,
                "privateScreenshotSha256":sha256(screenshot).hexdigest(),
                "privateScreenshotBytes":len(screenshot),
                "sourceRenderedLabelsMatch":True,
                "realBrowserComputedArrowStroke":True,
                "realBrowserDirectionalSvgGeometry":True,
                "realScreenshotRaster":verified,
            })
    finally:
        browser.quit()
    return {
        "status":"BSA258_V30_ACTUAL_HEADLESS_CHROME_RASTER_VECTORS_CHECKED_PRIVATE",
        "realBrowserScreenshotsProduced":3,
        "realBrowserRasterOppositeVelocityArrowsVerified":6,
        "actualBrowserPixelForPrivateDiagramVerified":True,
        "independentOriginalFigurePixelEquivalenceProven":False,
        "fullSourceScientificMeaningProven":False,
        "fullTrilingualScientificMeaningProven":False,
        "fullAcademicPASS":0,
        "newProviderCalls":0,
        "publicationAuthorized":False,
        "productionRendererSha256":sha256(RENDERER.read_bytes()).hexdigest(),
        "productionStylesSha256":sha256(CSS.read_bytes()).hexdigest(),
        "screenshots":screenshot_rows,
    }

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--draft",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(run_browser_raster_check(args.draft,args.output_dir),
                     sort_keys=True,ensure_ascii=False))
if __name__=="__main__":
    main()
