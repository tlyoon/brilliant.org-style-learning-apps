"""Live no-source, no-API Gemini roundtrip with existing Google sign-in.

One invocation owns one immutable private report directory. In case of
possible submission timeout, preserve AMBIGUOUS; NEVER automatically retry.
No source PDF, teaching material, credentials, cookies, tokens or authoring
conversation content enters the neutral probe.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from app_generator.browser.account import GoogleAccountVerifier
from app_generator.browser.chrome import ChromeSession
from app_generator.config import load_config
from app_generator.gemini.conversation import GemConversationPage
from app_generator.generation.extraction import parse_json_response

ROLES=("physics","semantics")
NEUTRAL="https://gemini.google.com/app"


def _save_state(dest:Path, data:dict) -> None:
    temp=dest/"state.tmp"
    temp.write_bytes((json.dumps(data,indent=2,sort_keys=True,ensure_ascii=True)+"\n").encode("utf-8"))
    temp.replace(dest/"state.json")


def probe(config:Path, output_dir:Path,
          *, chrome_factory=ChromeSession,
          verifier_factory=GoogleAccountVerifier,
          page_factory=GemConversationPage) -> dict:
    cfg=replace(load_config(config),gem_url=NEUTRAL,gem_edit_url=NEUTRAL,
                llm_backend="gemini_browser",
                response_timeout_seconds=90,ui_timeout_seconds=24)
    root=cfg.repo_root.resolve()
    dest=output_dir.resolve()
    if dest.is_relative_to(root) or dest.is_relative_to(ROOT.resolve()):
        raise ValueError("browser probe receipt cannot be inside Git")
    if dest.exists():
        raise ValueError("previous real request claim already exists; never resubmit")
    profile=cfg.chrome_profile_dir/"gemini-browser"
    if cfg.browser_mode!="controlled" or not profile.is_dir():
        raise ValueError("only previously-authorized existing controlled Chrome profile")
    dest.mkdir(parents=True,exist_ok=False)
    result={
        "status":"PREPARED","reviewerMode":"same_authorized_login_separate_new_chats",
        "providerAccountsIndependent":False,
        "sourcePdfUploaded":False,"promptContainsSource":False,
        "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
        "roles":{},
    }
    _save_state(dest,result)
    browser=chrome_factory(cfg)
    driver=None
    owned=[]
    try:
        driver=browser.start()
        u=urlparse(driver.current_url)
        if u.scheme!="https" or u.netloc!="gemini.google.com":
            raise ValueError("existing Chrome did not open neutral Gemini")
        verifier_factory(driver,cfg.login_name,12).verify()
        protected=set(driver.window_handles)
        result["status"]="ACCOUNT_VERIFIED"
        _save_state(dest,result)
        for role in ROLES:
            driver.switch_to.new_window("tab")
            handle=driver.current_window_handle
            if handle in protected or handle in owned:
                raise ValueError("new probe tab was not isolated from prior tabs")
            owned.append(handle)
            page=page_factory(driver,NEUTRAL,cfg.ui_timeout_seconds,
                              cfg.response_timeout_seconds)
            page.open_new()
            if urlparse(driver.current_url).netloc!="gemini.google.com":
                raise ValueError("new probe conversation left Gemini")
            if role=="physics":
                prompt=("Answer the arithmetic expression 2+2. "
                        "Return only BEGIN_JSON then a JSON object with "
                        'keys role="physics", sum=4 then END_JSON. '
                        "No source documents are being supplied.")
            else:
                prompt=("Translate the English word 'momentum' to Malay "
                        "and Simplified Chinese. Return only BEGIN_JSON "
                        "then a JSON object with keys role=\"semantics\", "
                        "\"ms\" and \"zh\" containing your translations, "
                        "then END_JSON. No source documents are being supplied.")
            stage={"state":"POSSIBLY_SENT","promptSha256":sha256(prompt.encode()).hexdigest(),
                   "responseCaptured":False}
            result["roles"][role]=stage
            result["status"]="IN_FLIGHT"
            _save_state(dest,result)
            try:
                raw=page.ask(prompt)
                parsed=parse_json_response(raw)
                if not isinstance(parsed,dict) or parsed.get("role")!=role:
                    raise ValueError("unexpected role in source-free model answer")
                if role=="physics":
                    if parsed.get("sum")!=4:
                        raise ValueError("arithmetic response invalid")
                else:
                    if not isinstance(parsed.get("ms"),str) or not isinstance(parsed.get("zh"),str):
                        raise ValueError("multilingual probe response invalid")
                stage.update(state="COMPLETE_CAPTURED",
                             responseSha256=sha256(raw.encode("utf-8")).hexdigest(),
                             responseCaptured=True,
                             validRoleAndShape=True)
                result["status"]="PARTIAL_COMPLETE"
            except Exception as exc:
                stage.update(state="AMBIGUOUS",
                             errorType=type(exc).__name__,
                             responseCaptured=False)
                result["status"]="REQUIRES_RECONCILIATION"
                _save_state(dest,result)
                break
            _save_state(dest,result)
        if all(result["roles"].get(r,{}).get("state")=="COMPLETE_CAPTURED" for r in ROLES):
            result["status"]="NEUTRAL_TWO_CONTEXTS_CONFIRMED"
        _save_state(dest,result)
    except Exception as exc:
        result["status"]="BLOCKED_BEFORE_OR_DURING_PROBE"
        result["errorType"]=type(exc).__name__
        _save_state(dest,result)
    finally:
        if driver is not None:
            for handle in owned:
                try:
                    if handle in driver.window_handles:
                        driver.switch_to.window(handle)
                        driver.close()
                except Exception:
                    pass
        try:
            browser.close()
        except Exception:
            result["cleanupStatus"]="BROWSER_CLOSE_UNVERIFIED"
            _save_state(dest,result)
    return {
        "status":result["status"],
        "roleResults":{key:{"state":v["state"],"responseCaptured":v["responseCaptured"]}
                       for key,v in result["roles"].items()},
        "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
        "privateReceipt":str(dest/"state.json"),
        "providerAccountsIndependent":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    try:
        outcome=probe(args.config,args.out)
        print(json.dumps(outcome,indent=2))
        return 0 if outcome["status"]=="NEUTRAL_TWO_CONTEXTS_CONFIRMED" else 2
    except (ValueError,OSError,TypeError) as exc:
        print(json.dumps({"status":"BLOCKED",
                          "errorType":type(exc).__name__,
                          "publicationAuthorized":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
