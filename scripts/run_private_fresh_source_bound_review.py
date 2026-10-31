"""Launch NEW private, source-bound Gemini academic reviewer conversations.

Requires prior two-context no-source neutral preflight and never allows
replaying existing immutable academic reviewer claims. No paid API or Git
publication. All substantive review evidence stays inside the private run.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.config import load_config
from app_generator.gemini.existing_login_reviewers import (
    ExistingLoginReviewerFactory, existing_profile_in_use,
)
from app_generator.runtime.run_context import RunContext
from app_generator.validation.autonomous_ai_review import review_activity
from app_generator.validation.fresh_academic_review_admission import admit_fresh_academic_review

GATES = ("source_fidelity", "answer_correctness", "physics_consistency",
         "visual_semantics", "multilingual_meaning")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "package", "pdf", "packets", "priority-queue",
                 "neutral-receipt", "private-evidence-root", "run-id",
                 "activity-id", "claim-prefix"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    try:
        cfg = replace(
            load_config(Path(args.config)), repo_root=ROOT,
            browser_mode="controlled", llm_backend="gemini_browser",
            gem_url="https://gemini.google.com/app",
            gem_edit_url="https://gemini.google.com/app",
            git_publish=False, git_auto_merge=False, public_deploy=False,
            response_timeout_seconds=90, ui_timeout_seconds=30,
            max_gemini_session_restarts=0,
        )
        prepared = admit_fresh_academic_review(
            package_file=Path(args.package), source_pdf=Path(args.pdf),
            packets_file=Path(args.packets),
            priority_queue_file=Path(args.priority_queue),
            neutral_receipt_file=Path(args.neutral_receipt),
            private_evidence_root=Path(args.private_evidence_root),
            run_id=args.run_id, activity_id=args.activity_id,
            claim_prefix=args.claim_prefix, repository_root=ROOT,
        )
        if args.preflight_only:
            print(json.dumps({"status":"FRESH_SOURCE_REVIEW_PREFLIGHT_PASS",
                              "activityId":args.activity_id,
                              "academicQA":"REVIEW_REQUIRED",
                              "publicationAuthorized":False}))
            return 0
        if existing_profile_in_use(cfg.chrome_profile_dir / "gemini-browser"):
            raise ValueError("authorized Chrome profile is in use")
        target = prepared["privateRunDirectory"]
        # Atomically reserve a never-used run before any browser request.
        target.mkdir(parents=True, exist_ok=False)
        context = RunContext.create(target.parent, args.run_id)
        context.save_stage("review-readiness", {
            "activityId":args.activity_id,
            "sourceSha256":prepared["sourceSha256"],
            "packageSha256":prepared["packageSha256"],
            "verifiedPhysicalPages":prepared["sourceContext"]["verifiedPages"],
            "claimPrefix":args.claim_prefix, "academicQA":"REVIEW_REQUIRED",
            "publicationAuthorized":False,
        })
        try:
            with ExistingLoginReviewerFactory(cfg, Path(args.pdf)) as factory:
                sessions=factory.open_pair(args.activity_id)
                result=review_activity(
                    prepared["activity"],prepared["sourceContext"],sessions,
                    package_sha256=prepared["packageSha256"],
                    source_sha256=prepared["sourceSha256"],gates=GATES,
                    checkpoint=context,claim_prefix=args.claim_prefix,
                )
            context.save_stage("all5-gate-result",result)
            print(json.dumps({
                "status":"PRIVATE_NEW_REVIEW_RECORDED",
                "activityId":args.activity_id,"nextAction":result["nextAction"],
                "aiReviewed":result["aiReviewed"],
                "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
            }))
            return 0
        except Exception as exc:
            # Never log untrusted model text, URLs or exception messages.
            context.save_stage("review-failure",{
                "errorType":type(exc).__name__,
                "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
            })
            print(json.dumps({
                "status":"REVIEW_BLOCKED_OR_AMBIGUOUS",
                "errorType":type(exc).__name__,
                "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
            }))
            return 2
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"BLOCKED_BEFORE_REVIEW_SUBMISSION",
                          "errorType":type(exc).__name__,
                          "academicQA":"REVIEW_REQUIRED",
                          "publicationAuthorized":False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
