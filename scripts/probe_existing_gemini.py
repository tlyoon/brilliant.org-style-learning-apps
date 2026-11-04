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
from app_generator.gemini.existing_login_reviewers import existing_profile_in_use
from app_generator.gemini import selectors
from app_generator.browser.common import find_all
from app_generator.gemini.conversation import (
    _response_text, _complete_json_frame, _generation_signals,
)
from app_generator.generation.extraction import parse_json_response

def privacy_safe_response_diagnostics(driver) -> dict:
    """Count completion signals without persisting response or chat text.

    Only call inside a newly created owned review tab. Failure to inspect
    remains unknown and must never be interpreted as successful delivery.
    """
    try:
        responses=find_all(driver,selectors.MODEL_RESPONSES)
        lengths=[]
        parseable=0
        for element in responses:
            try:
                content=_response_text(driver,element)
                if content:
                    lengths.append(len(content))
                    frame=_complete_json_frame(content)
                    if frame is not None:
                        try:
                            if isinstance(parse_json_response(frame),dict):
                                parseable+=1
                        except (ValueError,TypeError,KeyError):
                            pass
            except Exception:
                continue
        active,complete=_generation_signals(driver)
        return {
            "status":"OBSERVED_COUNTS_ONLY",
            "visibleResponseCount":len(responses),
            "nonemptyResponseCount":len(lengths),
            "longestResponseCharacters":max(lengths,default=0),
            "parseableJsonFrameCount":parseable,
            "generationActive":bool(active),
            "responseCompleteSignal":bool(complete),
        }
    except Exception:
        return {"status":"UNAVAILABLE"}

ROLES=("physics","semantics")
NEUTRAL="https://gemini.google.com/app"


def _save_state(dest:Path, data:dict) -> None:
    temp=dest/"state.tmp"
    temp.write_bytes((json.dumps(data,indent=2,sort_keys=True,ensure_ascii=True)+"\n").encode("utf-8"))
    temp.replace(dest/"state.json")


def probe(config:Path, output_dir:Path,
          *, chrome_factory=ChromeSession,
          verifier_factory=GoogleAccountVerifier,
          page_factory=GemConversationPage,
          profile_busy=existing_profile_in_use) -> dict:
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
    # Ownership is a prerequisite, not a post-submission diagnostic:
    # never connect to a possibly independently owned authoring browser.
    # Do not create even a PREPARED request claim when the profile is busy.
    if profile_busy(profile):
        raise ValueError("existing authorized Chrome profile is busy; no probe request submitted")
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
    phase="CHROME_START"
    try:
        driver=browser.start()
        phase="INITIAL_GEMINI_OR_RESTORED_TAB"
        # Chrome may restore an unrelated start page despite the requested
        # neutral URL. Protect ALL restored tabs before opening anything else.
        # Never navigate, close, or reuse a pre-existing authoring tab.
        protected=set(driver.window_handles)
        if not protected:
            raise ValueError("neutral probe missing protected starting tab")
        u=urlparse(driver.current_url)
        if u.scheme!="https" or u.netloc!="gemini.google.com":
            # Limited to NEW, exclusively owned tabs before any account
            # verification, source upload or model request.
            # Never touch restored/author tabs or retry remote prompts.
            for attempt in range(2):
                driver.switch_to.new_window("tab")
                handle=driver.current_window_handle
                if (not handle or handle in protected or handle in owned):
                    raise ValueError("neutral account-verification tab is not exclusively owned")
                owned.append(handle)
                phase="FRESH_NEUTRAL_TAB_NAVIGATION"
                driver.get(NEUTRAL)
                u=urlparse(driver.current_url)
                if u.scheme=="https" and u.netloc=="gemini.google.com":
                    break
                # Retain this newly owned disposable tab until cleanup.
                # Closing it here can leave Selenium with no active window
                # (NoSuchWindowException) for the next new_window call.
                # Never select or inspect a protected restored author tab.
            if u.scheme!="https" or u.netloc!="gemini.google.com":
                raise ValueError("fresh neutral account-verification tab did not open Gemini")
        # Verify only after the active tab is genuinely on Gemini.
        phase="VISIBLE_ACCOUNT_VERIFICATION"
        verifier_factory(driver,cfg.login_name,12).verify()
        result["status"]="ACCOUNT_VERIFIED"
        _save_state(dest,result)
        for role in ROLES:
            phase="FRESH_ROLE_TAB_CREATION"
            driver.switch_to.new_window("tab")
            handle=driver.current_window_handle
            if handle in protected or handle in owned:
                raise ValueError("new probe tab was not isolated from prior tabs")
            owned.append(handle)
            page=page_factory(driver,NEUTRAL,cfg.ui_timeout_seconds,
                              cfg.response_timeout_seconds)
            phase="FRESH_ROLE_CONVERSATION_NAVIGATION"
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
                # A request may have been accepted after this line even if
                # local capture later fails. Never automatically replay it.
                phase="NEUTRAL_REQUEST_OR_CAPTURE"
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
                             responseCaptured=False,
                             privacySafeUiDiagnostics=privacy_safe_response_diagnostics(driver))
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
        # Only code-owned phase constants. Never log exception text, model
        # response, account identifier, restored URLs or credential state.
        result["failurePhase"]=phase
        result["remoteRequestPossiblySubmitted"]=bool(result["roles"])
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
