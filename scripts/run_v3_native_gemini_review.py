"""Independent local BOSLA V3 native Gemini API review runner.

Dry-run default: NO credentials, NO Google requests, NO browser and no write.
For a user-owned, independently permitted native Google API workflow, run
locally with BOTH --execute and --allow-generated-text-transfer. Do NOT invoke
this program via ChatGPT remote tools to replay a previously denied operation.

The existing V3 engine handles immutable package hashes, two Gemini roles,
private checkpoints, one-activity smoke, finite batches, and no replay.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.gemini.v3_native_api_reviewers import V3NativeGeminiApiSessions
from app_generator.project import load_project_identity
from app_generator.config import load_config
from app_generator.runtime.v3_course_review import (
    advance_v3_course_review, plan_v3_course_review,
)
from scripts import sync_configured_workstation as configured

AUTHORITY = ROOT / "config" / "configure_project.toml"


def _load_native_config():
    """Reuse the canonical nonsecret config authority; no source is uploaded."""
    identity = load_project_identity(AUTHORITY)
    configured.configure_core()
    materialized = configured.core.render_project_config(
        AUTHORITY.read_bytes(), repo_root=ROOT,
        state_root=identity.state_root,
    )
    with tempfile.TemporaryDirectory() as folder:
        local = Path(folder) / "gemini-native-v3.toml"
        local.write_text(materialized, encoding="utf-8")
        cfg = load_config(local, cli_overrides={"llm_backend": "gemini_api"})
    if cfg.llm_backend != "gemini_api" or cfg.repo_root.resolve() != ROOT.resolve():
        raise ValueError("V3_NATIVE_CONFIG_REPO_OR_PROVIDER_CHANGED")
    return cfg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--course-dir", type=Path,
                    default=Path("content/chapter-9"))
    ap.add_argument("--private-root", type=Path)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--max-batches", type=int, default=1)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--allow-generated-text-transfer", action="store_true")
    args = ap.parse_args(argv)
    if not (1 <= args.batch_size <= 6 and 1 <= args.max_batches <= 108):
        ap.error("batch-size must be 1..6 and max-batches 1..108")
    source = (ROOT / args.course_dir).resolve()
    if (not source.is_relative_to((ROOT / "content").resolve())
        or source.name != "chapter-9"
        or args.course_dir.is_symlink()):
        ap.error("only the frozen local content/chapter-9 course is allowed")
    if args.private_root is None:
        identity = load_project_identity(AUTHORITY)
        private = identity.state_root / "v3-native-review"
    else:
        private = args.private_root.expanduser().resolve()
    if (not private.is_absolute()
        or private == ROOT.resolve()
        or private.is_relative_to(ROOT.resolve())
        or private.is_symlink()):
        ap.error("private-root must be outside this Git repository")
    # The default is an entirely offline, read-only plan.
    before = plan_v3_course_review(source, ROOT, private_root=private)
    if not args.execute:
        print(json.dumps({**before, "nativeMode": "DRY_RUN_NO_MODEL_CALL"},
                         sort_keys=True))
        return 0
    if not args.allow_generated_text_transfer:
        print(json.dumps({
            "status": "STOP_GENERATED_TEXT_TRANSFER_NOT_AUTHORIZED",
            "publicationAuthorized": False,
        }, sort_keys=True))
        return 2
    if before["dispatchStatus"] != "READY_FOR_AUTHORIZED_REVIEW_SESSIONS":
        print(json.dumps(before,sort_keys=True))
        return 0
    batches = 0
    try:
        # BSA-20261114-164: recover a stale/missing google-genai SDK in an
        # isolated, pinned local venv BEFORE any review claim or model call.
        from app_generator.runtime.native_sdk_environment import delegate_to_supported_sdk
        delegated = delegate_to_supported_sdk(
            ROOT, list(argv) if argv is not None else sys.argv[1:])
        if delegated is not None:
            return delegated
        cfg = _load_native_config()
        current = before
        reviewed = 0
        for _ in range(args.max_batches):
            if current["dispatchStatus"] != "READY_FOR_AUTHORIZED_REVIEW_SESSIONS":
                break
            # Native API roles are one-shot per activity. Each CLI batch may
            # group 1..6 independent, immutable single-activity invocations.
            # A FAIL/UNCERTAIN halts before opening any later SDK client.
            for _ in range(args.batch_size):
                if current["dispatchStatus"] != "READY_FOR_AUTHORIZED_REVIEW_SESSIONS":
                    break
                factory = V3NativeGeminiApiSessions(
                    cfg, operation_authorized=True,
                    generated_content_transfer_allowed=True,
                )
                after = advance_v3_course_review(
                    source, ROOT, private_root=private,
                    session_factory=factory,
                    external_operation_authorized=True,
                    generated_content_transfer_allowed=True,
                    max_activities=1,
                )
                reviewed += 1
                if (after.get("activitiesAssessedRows", 0) <=
                        current.get("activitiesAssessedRows", 0)):
                    raise ValueError("V3_NATIVE_NO_PROGRESS_STOP")
                current = after
            batches += 1
        print(json.dumps({**current, "nativeMode": "EXECUTED_ACTUAL_GEMINI_API",
                          "batchesExecuted": batches,
                          "activitiesAttempted": reviewed},sort_keys=True))
        return 0 if current["dispatchStatus"] in (
            "READY_FOR_AUTHORIZED_REVIEW_SESSIONS",
            "PENDING_DETERMINISTIC_RELEASE_EVIDENCE",
        ) else 3
    except Exception as exc:
        # Output no credential, source JSON, provider error body, or tokens.
        print(json.dumps({"status": "STOP_NATIVE_GEMINI_REVIEW",
                          "reasonClass": type(exc).__name__,
                          "batchesExecuted": batches,
                          "publicationAuthorized": False},sort_keys=True))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
