"""BSA311: executable CI-to-next-work continuation policy for Bosla Yoga6.

Scheduled development must not stop at a normal code-patch/CI boundary.
Only verified external CI readiness permits further owner stages. A genuine
failure is quarantined; original textbook review and child process safety
remain fully enforced by the normal owner cycle.
"""
from __future__ import annotations
from pathlib import Path
import re
from typing import Any

_SHA=re.compile(r"[0-9a-f]{40}\Z")
_BRANCH=re.compile(r"feature/[a-zA-Z0-9_.\-/]{4,120}\Z")
CI_WAIT={"BSA279_NEW_SOURCE_CODE_COMMITTED_CI_DISPATCHED",
         "BSA279_NEW_CODE_PROMOTED_WAIT_HOSTED_CI",
         "BSA279_CANDIDATE_CI_AWAITING",
         "BSA279_MAIN_CI_AWAITING"}
REPAIR_READY={"BSA279_CODEX_TESTS_FAIL_KEEP_PATCH",
              "BSA279_CODEX_CONTRACT_FAIL_KEEP_PATCH",
              "BSA279_CODEX_PATCH_WHITESPACE_FAILURE",
              "BSA279_FAILED_CI_TARGETED_REPAIR_DISPATCHED"}

def ci_gate(state:dict[str,Any],*,main_branch:str)->tuple[str,str,int]|None:
    """Return exact Git SHA, branch and minimum checks; never infer PASS."""
    pending=state.get("pendingBranch")
    if pending:
        path=state.get("devWorktree")
        if (not isinstance(path,str) or not isinstance(pending,str)
            or not _BRANCH.fullmatch(pending)
            or not Path(path).is_dir()):
            raise ValueError("BSA311_UNTRUSTED_CANDIDATE_GATE")
        # The caller, under the owner lock, will recheck this worktree's
        # exact commit; never use a bare branch name as CI evidence.
        return (path,pending,1)
    if state.get("status") in (
        "BSA279_NEW_CODE_PROMOTED_WAIT_HOSTED_CI",
        "BSA279_MAIN_CI_AWAITING",
    ):
        head=state.get("currentHead")
        if not isinstance(head,str) or not _SHA.fullmatch(head):
            raise ValueError("BSA311_UNTRUSTED_OWNER_CI_SHA")
        return head,main_branch,2
    return None

def decide_next(status:str,*,pending_branch:str|None,
                recovery_attempts:int)->str:
    """Explicit recovery decision; no uncontrolled model retry loop."""
    if not isinstance(status,str):
        return "BSA311_STOP_UNTRUSTED_CYCLE_RESULT"
    if status in CI_WAIT or pending_branch:
        return "BSA311_WAIT_EXACT_GIT_COMMIT_CI"
    if status in REPAIR_READY:
        return ("BSA311_DISPATCH_EXISTING_TARGETED_RECOVERY"
                if recovery_attempts<2 else
                "BSA311_STOP_REPEATED_UNVERIFIED_REPAIR")
    if status.startswith("BSA279_") and (
        status.endswith("_CI_AWAITING")
        or status=="BSA279_NEW_CODE_PROMOTED_WAIT_HOSTED_CI"):
        return "BSA311_WAIT_EXACT_GIT_COMMIT_CI"
    # Ineligible states stop only this attempt. The existing persistent
    # scheduler re-enters on its next trigger; do not fake an acceptance.
    return "BSA311_STOP_UNRESOLVED_OR_SAFETY_BOUNDARY"
