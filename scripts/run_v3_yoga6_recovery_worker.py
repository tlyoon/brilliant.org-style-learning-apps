"""One bounded Yoga 6 recovery tick for BOSLA V3.

Default is read-only planning. --diagnose-only uses source-free Gemini
models.get metadata, NOT generation. The --execute path requires the
generated-text-transfer flag, observes every frozen checkpoint/circuit, then
attempts at most ONE new activity. It never replays a submitted request.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.runtime.native_workstation_guard import (
    require_authorized_native_review_host,
)
from app_generator.runtime.v3_course_review import plan_v3_course_review
from app_generator.runtime.v3_gemini_diagnostics import diagnose_model_metadata
from app_generator.runtime.v3_yoga6_recovery import (
    checked_private_root, coordinator_lock, gate_review_plan,
    persist_status, status_from_plan,
)
from scripts.run_v3_native_gemini_review import (
    AUTHORITY, _load_native_config,
)
from scripts import run_v3_native_gemini_review as native

COURSE = ROOT / "content" / "chapter-9"


def _print(data: dict) -> None:
    print(json.dumps(data,sort_keys=True,separators=(",",":")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path)
    parser.add_argument("--diagnose-only", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-generated-text-transfer", action="store_true")
    args = parser.parse_args(argv)
    if args.diagnose_only and args.execute:
        parser.error("choose --diagnose-only or --execute, not both")
    if args.execute and not args.allow_generated_text_transfer:
        _print({"status":"STOP_GENERATED_TEXT_TRANSFER_NOT_AUTHORIZED",
                "publicationAuthorized":False})
        return 2
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        _print({"status":"STOP_LOCALAPPDATA_MISSING",
                "publicationAuthorized":False})
        return 3
    base = Path(local) / "Microvid"
    chosen = args.private_root if args.private_root is not None else (
        base / "BoslaV3ReviewYoga6"
    )
    try:
        private = checked_private_root(chosen,localappdata=Path(local))
        before = plan_v3_course_review(COURSE,ROOT,private_root=private,
                                       continue_independent=True)
        if not (args.execute or args.diagnose_only):
            _print(status_from_plan(before,status="DRY_RUN_NO_PROVIDER_REQUEST"))
            return 0
        # No credential access, SDK setup, or private review state on HP.
        require_authorized_native_review_host(AUTHORITY)
        # Reuse BSA-164's bounded isolated SDK bootstrap on Yoga 6 only.
        # A child is started BEFORE holding the coordinator lock; otherwise
        # its own legitimate lock acquisition would appear to conflict.
        from app_generator.runtime.native_sdk_environment import delegate_to_supported_sdk
        if args.diagnose_only or gate_review_plan(before) == "READY_FOR_SOURCE_FREE_METADATA_CHECK":
            delegated = delegate_to_supported_sdk(
                ROOT, list(argv) if argv is not None else sys.argv[1:],
                entrypoint=Path(__file__))
            if delegated is not None:
                return delegated
        with coordinator_lock(private):
            # Re-plan after obtaining exclusive worker ownership.
            before = plan_v3_course_review(COURSE,ROOT,private_root=private,
                                           continue_independent=True)
            gated = gate_review_plan(before)
            if not args.diagnose_only and gated != "READY_FOR_SOURCE_FREE_METADATA_CHECK":
                receipt = status_from_plan(before,status=gated)
                persist_status(private,receipt)
                _print(receipt)
                return 0
            config = _load_native_config()
            preferred = (before.get("providerCapacity") or {}).get(
                "serverErrorActivitiesHistorical",0)
            diagnostic = diagnose_model_metadata(
                config,preferred_offset=preferred)
            if args.diagnose_only:
                receipt = status_from_plan(
                    before,status="DIAGNOSTIC_"+diagnostic["status"],
                    diagnostic=diagnostic)
                persist_status(private,receipt)
                _print(receipt)
                return 0 if diagnostic["status"]=="READY_SOURCE_FREE_ONLY" else 3
            if diagnostic["status"]!="READY_SOURCE_FREE_ONLY":
                receipt = status_from_plan(
                    before,status=diagnostic["status"],diagnostic=diagnostic)
                persist_status(private,receipt)
                _print(receipt)
                return 3
            index = diagnostic["selectedCandidateIndex"]
            # This is a NEW frozen activity only: normal V3 course dispatcher
            # first enforces immutable per-role claims and source hash scope.
            command = ["--private-root",str(private),"--batch-size","1",
                       "--max-batches","1","--candidate-offset",str(index),
                       "--execute","--allow-generated-text-transfer"]
            output = io.StringIO()
            with redirect_stdout(output):
                native_exit = native.main(command)
            # Avoid returning raw provider replies. Only the verified frozen
            # read-only planner can supply the post-invocation status.
            after = plan_v3_course_review(COURSE,ROOT,private_root=private,
                                          continue_independent=True)
            receipt = status_from_plan(
                after,status=("NEW_ACTIVITY_COMPLETED" if
                    after["activitiesFullyModelReviewed"] >
                    before["activitiesFullyModelReviewed"] else
                    "NO_NEW_FULLY_REVIEWED_ACTIVITY"),
                diagnostic=diagnostic,native_exit_code=native_exit)
            persist_status(private,receipt)
            _print(receipt)
            return 0 if native_exit==0 else 3
    except Exception as exc:
        # No provider text, API secrets, user data or filenames from errors.
        _print({"status":"STOP_YOGA6_RECOVERY_WORKER",
                "reasonClass":type(exc).__name__,"publicationAuthorized":False})
        return 3


if __name__=="__main__":
    raise SystemExit(main())
