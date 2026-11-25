"""Owner-authorized NEW four-activity revised 9.1 Gemini V3 model assessment.

Default: read-only exact signed V22 dry-run, ZERO model calls.
--execute requires owner standing consent, generated-text-only transfer,
verified Yoga6 host, compatible pinned SDK, source-free metadata reachability,
genuine independent reviewer contexts, immutable PRE_CALL claims and no replay.

Not the frozen original Section9.1 campaign; no source PDF upload, no merge,
no academic source/semantic PASS merely from model votes.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from app_generator.runtime.v3_revised91_fresh_model_reviews import (
    fresh_revised91_inputs, advance_bounded_revised91,
)
from app_generator.runtime.v3_standing_paid_science import authorize_standing
from scripts.run_v3_native_gemini_review import AUTHORITY,_load_native_config


def _out(record:dict)->None:
    print(json.dumps(record,sort_keys=True,separators=(",",":"),
                     ensure_ascii=True))


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-head",required=True)
    parser.add_argument("--proposal-sha",required=True)
    parser.add_argument("--private-root",type=Path)
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--allow-generated-text-transfer",action="store_true")
    parser.add_argument("--max-activities",type=int,default=4)
    parser.add_argument("--max-seconds",type=int,default=900)
    args=parser.parse_args(argv)
    try:
        if not os.environ.get("LOCALAPPDATA"):
            raise ValueError("V23_OWNER_LOCALAPPDATA_REQUIRED")
        private=(args.private_root if args.private_root is not None else
                 Path(os.environ["LOCALAPPDATA"])/"Microvid"/"BoslaV3ReviewYoga6")
        plan=fresh_revised91_inputs(
            repo=ROOT,private=private,source_head=args.source_head,
            proposal_sha=args.proposal_sha)
        roster=[{"activityId":a["activityId"],
                 "reviewSliceSha256":a["sha"]}
                for a in plan["stagedReviewInputs"]]
        if not args.execute:
            _out({
                "status":"V23_FOUR_FRESH_REVISED_91_SOURCE_BOUND_DRY_RUN",
                "sourceHead":args.source_head,
                "candidateSha256":plan["revisedCandidateSha256"],
                "newIndependentReviewInputs":roster,
                "newGeminiCalls":0,
                "publicationAuthorized":False,
            })
            return 0
        authorize_standing(execute=True,
                           transfer=args.allow_generated_text_transfer,
                           activities=args.max_activities,
                           seconds=args.max_seconds)
        from app_generator.runtime.native_workstation_guard import (
            require_authorized_native_review_host,
        )
        require_authorized_native_review_host(AUTHORITY)
        from app_generator.runtime.native_sdk_environment import (
            delegate_to_supported_sdk,
        )
        delegated=delegate_to_supported_sdk(
            ROOT,list(argv) if argv is not None else sys.argv[1:],
            entrypoint=Path(__file__))
        if delegated is not None:
            return delegated
        # This is source-free metadata GET only, not proof of quota; the
        # first paid provider role itself is governed by V3 PRE_CALL.
        from app_generator.runtime.v3_gemini_diagnostics import (
            diagnose_model_metadata,
        )
        from app_generator.runtime.v3_authorized_review import (
            advance_v3_generated_text,
        )
        from app_generator.gemini.v3_native_api_reviewers import (
            V3NativeGeminiApiSessions,
        )
        config=_load_native_config()
        metadata=diagnose_model_metadata(config,
            preferred_offset=0,max_candidates=2)
        if (metadata.get("status")!="READY_SOURCE_FREE_ONLY"
                or type(metadata.get("selectedCandidateIndex")) is not int
                or metadata["selectedCandidateIndex"] not in range(8)):
            _out({"status":"V23_STOP_SOURCE_FREE_PROVIDER_PREFLIGHT",
                  "reasonClass":metadata.get("status"),
                  "newGeminiCalls":0,"publicationAuthorized":False})
            return 3
        selected=metadata["selectedCandidateIndex"]
        def review_one(raw:bytes,aid:str,evidence:Path)->dict:
            with V3NativeGeminiApiSessions(
                config,operation_authorized=True,
                generated_content_transfer_allowed=True,
                candidate_offset=selected,
            ) as factory:
                sessions=factory.open_pair(aid)
                return advance_v3_generated_text(
                    raw,sessions,private_root=evidence,
                    generated_content_transfer_allowed=True,
                    max_activities=1,
                )
        report=advance_bounded_revised91(
            repo=ROOT,private=private,source_head=args.source_head,
            proposal_sha=args.proposal_sha,
            execute=True,transfer=True,
            max_activities=args.max_activities,
            max_seconds=args.max_seconds,review_one=review_one,
        )
        _out(report)
        return 0 if report["status"]=="V23_NEW_REVISED_91_BOUNDED_REVIEW_ATTEMPT_RECONCILED" else 3
    except Exception as exc:
        # No raw exception messages: they may contain model content,
        # API key detail, local paths or source text.
        _out({"status":"V23_STOP_REVISED_91_NO_UNSAFE_REPLAY",
              "reasonClass":type(exc).__name__,
              "publicationAuthorized":False})
        return 3


if __name__=="__main__":
    raise SystemExit(main())
