"""Local, metadata-only execution recovery CLI; never runs any QA job.

All emitted JSON is descriptive evidence/state, not a command or an access grant.
Each transition creates a *new* private file; no existing file is overwritten.
A denied operation stays terminal for the checkpoint's exact source/package IDs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.execution_access_recovery import (
    DENIAL_CLASSES, TASK_DEPENDENCIES, TOOL_CLASSES, add_event,
    new_checkpoint, safe_plan,
)


def _save_new(path: Path, state: dict) -> None:
    dest = path.resolve()
    if dest.is_relative_to(ROOT.resolve()) or not dest.parent.is_dir() or dest.exists():
        raise ValueError("new private output outside repository required")
    # Exclusive create prevents overwriting an old evidence checkpoint.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(state, stream, indent=2, ensure_ascii=True)
        stream.write("\n")


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    fresh = sub.add_parser("init", help="create a blank, version-bound checkpoint")
    fresh.add_argument("--source-sha256", required=True)
    fresh.add_argument("--package-sha256", required=True)
    fresh.add_argument("--out", required=True, type=Path)
    for cmd in ("deny", "receipt"):
        item = sub.add_parser(cmd, help="record an externally determined outcome")
        item.add_argument("--state", type=Path, required=True)
        item.add_argument("--out", type=Path, required=True)
        item.add_argument("--task", choices=tuple(TASK_DEPENDENCIES), required=True)
        item.add_argument("--event-id", required=True)
        if cmd == "deny":
            item.add_argument("--denial-class", choices=tuple(sorted(DENIAL_CLASSES)), required=True)
            item.add_argument("--tool-class", choices=tuple(sorted(TOOL_CLASSES)), required=True)
        else:
            item.add_argument("--receipt-sha256", required=True)
    plan = sub.add_parser("plan", help="show independent work without executing it")
    plan.add_argument("--state", type=Path, required=True)
    ns = parser.parse_args(args)
    try:
        if ns.action == "init":
            state = new_checkpoint(ns.source_sha256, ns.package_sha256)
            _save_new(ns.out, state)
            result = safe_plan(state)
        else:
            state_path = ns.state.resolve()
            if not state_path.is_file() or state_path.is_relative_to(ROOT.resolve()):
                raise ValueError("only private external checkpoint inputs are accepted")
            state = json.loads(ns.state.read_text(encoding="utf-8"))
            if ns.action == "deny":
                state = add_event(
                    state, task_id=ns.task, event_id=ns.event_id,
                    outcome="BLOCKED_EXTERNAL", denial_class=ns.denial_class,
                    tool_class=ns.tool_class)
                _save_new(ns.out, state)
            elif ns.action == "receipt":
                state = add_event(
                    state, task_id=ns.task, event_id=ns.event_id,
                    outcome="RECEIPT_RECORDED", receipt_sha256=ns.receipt_sha256)
                _save_new(ns.out, state)
            result = safe_plan(state)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError) as exc:
        # Deliberately no echo of file paths, command arguments, or private data.
        print(json.dumps({"status": "BLOCKED", "errorClass": type(exc).__name__,
                          "externalAuthorizationGranted": False,
                          "publicationAuthorized": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
