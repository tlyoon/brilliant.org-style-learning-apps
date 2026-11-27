"""Bosla Yoga6 persistent, restart-safe autonomous development dispatcher.

Invoked by two owner-approved *new* Windows triggers (logon and 15-minute
recovery tick). Both call the SAME single-flight bounded --once worker.
Unlike source-free status polling, each invocation executes actual eligible
development: exact CI-gated feature-branch promotion, genuine Yoga6 owner
scientific acceptance, or a bounded Codex workspace-write CODE-DEVELOPMENT
session with independent tests and hosted CI handoff. New scientific academic
PASS is only the output of pre-existing independent source-bound owner
verifiers; a Codex patch, unittest or GitHub CI never self-admits scientific
correctness. No outside PDF or automatic public merge/deployment.

The old BoslaYoga6V3Recovery scheduler is retired and is NEVER recreated.
Do not run on Dell-115 / MicroGen_AI_Web. Status/journal are local-only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
try:
    import msvcrt  # Windows only; hosted CI imports for pure unit tests
except ImportError:
    msvcrt = None
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
from typing import Any

from app_generator.runtime.v3_persistent_academic_failure_recovery import (
    owner_recovery_plan,should_skip_unchanged_owner,
    classify_codegen_failure,
)
from app_generator.runtime.v3_isolated_codegen_workspace import (
    build_isolated_coding_snapshot,apply_isolated_patch,
)
from app_generator.runtime.v3_staged_patch_autorepair import (
    repair_staged_blank_eof,
)
from app_generator.runtime.v3_scientific_acceptance_watchdog import (
    observe_signed_horizon, investigate_zero_academic_gain,
)
from app_generator.runtime.v3_owner_child_tree_recovery import (
    windows_kill_tree, recover_previous_owner_tree,
)

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=Path(os.environ.get("LOCALAPPDATA", str(Path.home()/"AppData"/"Local")))/"Microvid"/"BoslaPersistentDevelopment"
STATE=PRIVATE/"state.json"
LOCK=PRIVATE/"single-flight.lock"
JOURNAL=PRIVATE/"events.jsonl"
MAIN_BRANCH="feature/bsa237-v16-pr-security-a11y"
LEGACY_TASK="BoslaYoga6V3Recovery"
PERSISTENT_TASKS=("BoslaPersistentDevelopment-Yoga6",)
FIXED_READY_BRANCH="feature/bsa278-paired-momentum-science"
MAX_CODEX_PER_DAY=12
MAX_CODEX_SECONDS=2700
MAX_OWNER_SECONDS=3600
ALLOWED_PREFIXES=("app_generator/","scripts/","tests/","docs/")
ALLOWED_FILES={"AGENTS.md","README.md"}
FORBIDDEN_PATH_BITS=(".env","secret","credential","token","keyfile","private_source","source.pdf")


def _utc()->str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_json(path:Path,value:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+".new")
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=True)+"\n",encoding="utf8")
    temp.replace(path)


def _read_state()->dict[str,Any]:
    if not STATE.exists():
        return {"schemaVersion":1,"createdAt":_utc(),"cycle":0,
                "integratedBranches":[],"codexDay":"","codexCount":0}
    value=json.loads(STATE.read_text(encoding="utf8"))
    if not isinstance(value,dict) or value.get("schemaVersion")!=1:
        raise ValueError("BSA279_PERSISTED_STATE_SCHEMA_UNTRUSTED")
    return value


def _update(state:dict[str,Any],status:str,**fields:Any)->None:
    state.update(fields)
    state["status"]=status
    state["heartbeatAt"]=_utc()
    _atomic_json(STATE,state)
    JOURNAL.parent.mkdir(parents=True,exist_ok=True)
    with JOURNAL.open("a",encoding="utf8") as out:
        out.write(json.dumps({
            "time":_utc(),"status":status,"cycle":state.get("cycle"),
            "gitHead":state.get("currentHead"),
            "pendingBranch":state.get("pendingBranch"),
        },sort_keys=True)+"\n")


class SingleFlight:
    """OS-owned Windows byte-range lock releases automatically after crash."""
    def __enter__(self):
        PRIVATE.mkdir(parents=True,exist_ok=True)
        self.file=LOCK.open("a+b")
        # Windows byte-range locks can reject a *read* on an already
        # locked byte before LK_NBLCK is reached. Inspect file size via
        # seek, never read the locked byte, and close on every denial.
        try:
            self.file.seek(0,2)
            if self.file.tell()==0:
                self.file.write(b"0")
                self.file.flush()
            self.file.seek(0)
            if msvcrt is None:
                raise OSError("Windows OS byte lock unavailable")
            msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
        except OSError as exc:
            self.file.close()
            raise ValueError(
                "BSA279_ANOTHER_PERSISTENT_WORKER_IS_ACTIVE"
            ) from exc
        return self

    def __exit__(self,*_):
        self.file.seek(0)
        msvcrt.locking(self.file.fileno(),msvcrt.LK_UNLCK,1)
        self.file.close()


def _run(args:list[str],*,cwd:Path=ROOT,timeout:int=40)->subprocess.CompletedProcess:
    return subprocess.run(args,cwd=cwd,text=True,encoding="utf8",
                          errors="replace",capture_output=True,
                          timeout=timeout,check=False)


def _ok(args:list[str],*,cwd:Path=ROOT,timeout:int=40)->str:
    p=_run(args,cwd=cwd,timeout=timeout)
    if p.returncode:
        raise ValueError("BSA279_COMMAND_FAILED:"+args[0]+":"+
                         str(p.returncode)+":"+p.stderr[-400:])
    return p.stdout.strip()


def _head(repo:Path=ROOT)->str:
    v=_ok(["git","rev-parse","HEAD"],cwd=repo)
    if not re.fullmatch(r"[0-9a-f]{40}",v):
        raise ValueError("BSA279_INVALID_GIT_SHA")
    return v


def _branch(repo:Path=ROOT)->str:
    return _ok(["git","branch","--show-current"],cwd=repo)


def _clean(repo:Path=ROOT)->bool:
    return not _ok(["git","status","--porcelain"],cwd=repo)


def _hosted_ci(head:str,branch:str,*,min_runs:int)->str:
    """CI gate is verified from the GitHub CLI *exact* commit, not a label."""
    result=_run(["gh","run","list","--repo",
                 "tlyoon/brilliant.org-style-learning-apps",
                 "--branch",branch,"--limit","20",
                 "--json","headSha,status,conclusion,databaseId"],
                timeout=80)
    if result.returncode:
        return "GH_UNAVAILABLE"
    try:
        matches=[v for v in json.loads(result.stdout)
                 if v.get("headSha")==head]
    except (ValueError,TypeError):
        return "CI_UNREADABLE"
    if len(matches)<min_runs:
        return "CI_AWAITING"
    if any(x.get("status")!="completed" for x in matches):
        return "CI_AWAITING"
    if any(x.get("conclusion")!="success" for x in matches):
        return "CI_FAILED"
    return "CI_SUCCESS"


def _approved_diff(base:str,tip:str)->bool:
    raw=_ok(["git","diff","--name-only",base+".."+tip],timeout=60)
    names=[x.strip().replace("\\","/") for x in raw.splitlines() if x.strip()]
    if not names:
        return False
    for name in names:
        norm=name.lower()
        if (not (name.startswith(ALLOWED_PREFIXES) or name in ALLOWED_FILES)
            or any(bit in norm for bit in FORBIDDEN_PATH_BITS)
            or norm.startswith("docs/owner-five-stage-completion")):
            return False
    return True


def _log_process(state:dict[str,Any],label:str,args:list[str],*,
                 cwd:Path,timeout:int,idle_timeout:int|None=None)->int:
    """BSA286: supervise the entire owned child tree on every exit path.

    The owner process *never* waits indefinitely for a live subprocess in
    finally. Ordinary exceptions trigger tree cleanup before returning to
    the scheduler; crash/power-loss orphans are recovered under singleflight
    on the next cycle with exact PID, command and creation-time checks.
    """
    logdir=PRIVATE/"logs"
    logdir.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile=logdir/(label+"_"+stamp+".log")
    _update(state,"BSA279_"+label+"_RUNNING",currentLog=str(logfile))
    with logfile.open("wb") as output:
        p=subprocess.Popen(args,cwd=cwd,stdout=output,
                           stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
        start=time.monotonic()
        last=start
        last_progress=start
        last_length=0
        completed=False
        kill_requested=False
        state["childPid"]=p.pid
        state["ownerChildStartedAt"]=_utc()
        state["ownerChildLabel"]=label
        state["ownerChildLifecycle"]="RUNNING"
        try:
            _update(state,"BSA286_"+label+"_TREE_OWNED",
                    childPid=p.pid,ownerChildStartedAt=state["ownerChildStartedAt"],
                    ownerChildLabel=label,ownerChildLifecycle="RUNNING")
            while True:
                result=p.poll()
                if result is not None:
                    completed=True
                    break
                now=time.monotonic()
                elapsed=now-start
                length=logfile.stat().st_size
                if length>last_length:
                    last_length=length
                    last_progress=now
                if elapsed>timeout or (
                        idle_timeout is not None and
                        now-last_progress>idle_timeout):
                    stall=elapsed<=timeout
                    try:
                        windows_kill_tree(p.pid)
                        kill_requested=True
                    except ValueError as exc:
                        state["ownerChildCleanupFault"]=str(exc)[:160]
                    state["ownerChildLifecycle"]="STOP_REQUESTED"
                    _update(state,
                        ("BSA283_"+label+"_NO_VERIFIABLE_PROGRESS"
                         if stall else "BSA279_"+label+"_TIMED_OUT"),
                        failedPid=p.pid,elapsedSeconds=int(elapsed),
                        idleSeconds=int(now-last_progress),
                        lastLogBytes=last_length,childPid=p.pid)
                    return 125 if stall else 124
                if now-last>=20:
                    _update(state,"BSA279_"+label+"_RUNNING",
                            elapsedSeconds=int(elapsed),childPid=p.pid,
                            lastLogBytes=last_length,
                            idleSeconds=int(now-last_progress),
                            childProgressObserved=last_length>0)
                    last=now
                time.sleep(2)
        finally:
            # This also runs if the owner heartbeat or filesystem fails.
            # Never issue an unbounded wait on a still-live source subprocess:
            # it can own an entire nested source-free or Chrome worker tree.
            if not completed and not kill_requested:
                try:
                    windows_kill_tree(p.pid)
                    kill_requested=True
                except ValueError as exc:
                    state["ownerChildCleanupFault"]=str(exc)[:160]
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # taskkill can race a still-shutting-down Python wrapper.
                try:
                    windows_kill_tree(p.pid)
                except ValueError as exc:
                    state["ownerChildCleanupFault"]=str(exc)[:160]
                try:
                    p.wait(timeout=4)
                except subprocess.TimeoutExpired as exc:
                    state["ownerChildLifecycle"]="CLEANUP_UNVERIFIED"
                    raise ValueError(
                        "BSA286_OWNER_CHILD_TREE_TERMINATION_UNVERIFIED") from exc
            state["ownerChildLifecycle"]="EXITED"
    _update(state,"BSA279_"+label+"_ENDED",
            exitCode=p.returncode,elapsedSeconds=int(time.monotonic()-start),
            lastLogBytes=last_length,ownerChildLifecycle="EXITED")
    return int(p.returncode)


def _promote_candidate(state:dict[str,Any],branch:str)->bool:
    if branch in state.get("integratedBranches",[]):
        return False
    remote=_run(["git","rev-parse","refs/heads/"+branch],timeout=25)
    if remote.returncode:
        return False
    source_head=remote.stdout.strip()
    main_head=_head()
    # The main feature branch may already contain a pre-certified candidate
    # (for example BSA278 integrated before this persistent runner existed).
    # Don't mistake this ordinary already-promoted state for a divergence,
    # and never replay its cherry-pick.
    cherry=_run(["git","cherry",main_head,branch],timeout=60)
    patch_equivalent=(cherry.returncode==0
        and bool(cherry.stdout.strip())
        and all(line.startswith("- ") for line in cherry.stdout.splitlines()))
    if (source_head==main_head or patch_equivalent
        or _run(["git","merge-base","--is-ancestor",
                 source_head,main_head]).returncode==0):
        state.setdefault("integratedBranches",[]).append(branch)
        _update(state,"BSA279_ALREADY_INTEGRATED_NO_DUPLICATE",
                lastIntegratedBranch=branch)
        return False
    if _branch()!=MAIN_BRANCH or not _clean():
        _update(state,"BSA279_MAIN_UNSAFE_FOR_CODE_PROMOTION")
        return False
    if _run(["git","merge-base","--is-ancestor",main_head,source_head]).returncode:
        _update(state,"BSA279_CANDIDATE_DIVERGED_REQUIRES_RECOVERY",
                rejectedBranch=branch)
        return False
    if not _approved_diff(main_head,source_head):
        _update(state,"BSA279_CANDIDATE_UNAPPROVED_FILE_SCOPE",
                rejectedBranch=branch)
        return False
    ci=_hosted_ci(source_head,branch,min_runs=1)
    if ci!="CI_SUCCESS":
        _update(state,"BSA279_CANDIDATE_"+ci,candidateHead=source_head)
        return False
    # Actual verified change on a development branch, NOT public main/deploy.
    commits=_ok(["git","rev-list","--reverse",main_head+".."+source_head]).splitlines()
    for revision in commits:
        if _run(["git","cherry-pick",revision],timeout=120).returncode:
            # Never automatically reset/discard genuine owner data on conflict.
            _update(state,"BSA279_CHERRY_PICK_CONFLICT_NEEDS_HISTORICAL_REPAIR",
                    failedRevision=revision)
            return False
    if _run(["git","push","origin",
             "HEAD:refs/heads/"+MAIN_BRANCH],timeout=90).returncode:
        _update(state,"BSA279_MAIN_PUSH_UNCERTAIN_VERIFY_BEFORE_RETRY")
        return False
    state.setdefault("integratedBranches",[]).append(branch)
    state.pop("pendingBranch",None)
    _update(state,"BSA279_VERIFIED_DEVELOPMENT_INTEGRATED",
            currentHead=_head(),lastIntegratedBranch=branch,
            lastIntegratedSourceHead=source_head)
    return True


def _promote_known(state:dict[str,Any])->bool:
    # Any approved pending Codex change goes before the prebuilt BSA278 batch.
    pending=state.get("pendingBranch")
    if pending:
        return _promote_candidate(state,pending)
    return _promote_candidate(state,FIXED_READY_BRANCH)


def _safe_last_log(state:dict[str,Any])->str:
    """Read only a bounded private diagnostic tail; never persist source text."""
    raw=state.get("currentLog")
    if not isinstance(raw,str):
        return ""
    path=Path(raw)
    try:
        if not path.resolve().is_relative_to((PRIVATE/"logs").resolve()):
            return ""
        with path.open("rb") as f:
            f.seek(0,2)
            f.seek(max(0,f.tell()-20000))
            return f.read(20000).decode("utf8",errors="replace")
    except (OSError,ValueError):
        return ""


def _failed_owner_decision(
    state:dict[str,Any],*,head:str,exit_code:int,
)->dict[str,Any]:
    plan=owner_recovery_plan(
        state=state,head=head,exit_code=exit_code,
        log_excerpt=_safe_last_log(state))
    _update(state,"BSA280_OWNER_"+plan["mode"],
            currentHead=head,ownerExitCode=exit_code,
            academicFailure=plan)
    return plan


def _owner_stage(state:dict[str,Any])->bool:
    """Actual original-source V36 -> A1..A12 signed independent chain."""
    current=_head()
    state["currentHead"]=current
    if state.get("lastOwnerHead")==current:
        return True
    if should_skip_unchanged_owner(state,current):
        _update(state,"BSA280_UNCHANGED_FAILED_OWNER_NOT_REPLAYED")
        return False
    if _branch()!=MAIN_BRANCH or not _clean():
        _update(state,"BSA279_DIRTY_MAIN_OWNER_NOT_RUN")
        return False
    ci=_hosted_ci(current,MAIN_BRANCH,min_runs=2)
    if ci!="CI_SUCCESS":
        _update(state,"BSA279_MAIN_"+ci,currentHead=current)
        return False
    rc=_log_process(state,"OWNER_REAL_SOURCE_ADMISSION",
                    [sys.executable,"-u","-m",
                     "scripts.auto_advance_bosla_academic_frontier",
                     "--max-steps","8"],cwd=ROOT,timeout=MAX_OWNER_SECONDS,
                    idle_timeout=1200)
    if rc!=0:
        _failed_owner_decision(state,head=current,exit_code=rc)
        return False
    rc=_log_process(state,"OWNER_INDEPENDENT_HORIZON",
                    [sys.executable,"-u","-m",
                     "scripts.show_bosla_long_horizon"],cwd=ROOT,timeout=1300,
                    idle_timeout=900)
    if rc!=0:
        _failed_owner_decision(state,head=current,exit_code=rc)
        return False
    # BSA285: a successful independently signed source-bound verifier is
    # different from CI success, watchdog heartbeat, or growing log bytes.
    # Failure to parse the independent receipt fails closed, never adds PASS.
    try:
        science=observe_signed_horizon(
            state,_safe_last_log(state),head=current,now=_utc(),
            cycle=int(state["cycle"]))
    except (ValueError,KeyError,TypeError) as exc:
        _update(state,"BSA285_INDEPENDENT_SCIENCE_READBACK_UNTRUSTED",
                scienceVerificationError=str(exc)[:250],
                currentHead=current)
        return False
    _update(state,"BSA285_INDEPENDENT_SIGNED_SCIENCE_COUNT_OBSERVED",
            scienceAcceptance=science)
    state.pop("academicFailure",None)
    state["lastOwnerHead"]=current
    _update(state,"BSA279_ORIGINAL_TEXTBOOK_OWNER_SIGNED_ACCEPTANCE_VERIFIED",
            currentHead=current)
    return True


def _daily_budget(state:dict[str,Any])->bool:
    day=datetime.now().strftime("%Y-%m-%d")
    if state.get("codexDay")!=day:
        state["codexDay"]=day
        state["codexCount"]=0
    return int(state.get("codexCount",0))<MAX_CODEX_PER_DAY


def _dev_worktree(state:dict[str,Any])->tuple[str,Path]:
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    branch="feature/bosla-auto-"+stamp
    dest=PRIVATE/"worktrees"/("bosla-"+stamp)
    dest.parent.mkdir(parents=True,exist_ok=True)
    _ok(["git","worktree","add","-b",branch,str(dest),"HEAD"],timeout=90)
    return branch,dest


def _codex_prompt()->str:
    return (
        "You are the bounded engineering worker for BOSLA, the brilliant.org-"
        "style learning app on Yoga6, NOT MicroGen_AI_Web. Authorized goal: "
        "AUTONOMOUS SUBSTANTIVE CODE DEVELOPMENT using original instructor "
        "selected Serway textbook only. Begin by reading AGENTS.md, "
        "docs/CONTEXT_INDEX.md, docs/AUTONOMOUS_DEVELOPMENT_CONTINUATION.md, "
        "docs/recurrence_registry.json and relevant past failure fixes. "
        "Identify the next missing SOURCE-BOUND INDEPENDENT SCIENTIFIC "
        "EXPLANATION, TRILINGUAL MEANING, MCQ DISTRACTOR, or INTERACTIVE "
        "DIAGRAM proof mechanism. Implement a *genuine working proof "
        "producer* and its acceptance, not another no-op scheduler, metadata "
        "report or source-quote inventory. Advance all obvious safe steps. "
        "For each blocker use historical failure review -> targeted fix -> "
        "actual source-bound test -> adversarial/fault-injection regression -> "
        "executable recovery-registry integration -> normal continuation. "
        "Keep original Serway PDF private; NEVER download or upload another "
        "PDF or expose full textbook in Git. Do not initiate paid Gemini "
        "requests, replay uncertain model calls or alter historical signed "
        "A1-A12 evidence. No public PR merge, public deploy, new scheduled "
        "task, git commit/push/checkout/reset, or changes outside this "
        "sandboxed worktree; the host coordinator performs Git and CI. "
        "Never waive exact-source, scientific, trilingual, figure or release "
        "gates or falsely claim that all 90 activities pass. Make actual "
        "verified code and tests, update recurrence registry/ledger/checkpoint "
        "consistently, run focused tests. On unresolved proof isolate the "
        "specific task and work on other eligible mechanisms. Do not stop "
        "merely to ask the user for an obvious next step. Limit this run to "
        "one coherent, testable integrated development change; exit cleanly "
        "with evidence of files changed and tests run. "
    )



def _finalize_staged_patch(
    state:dict[str,Any],*,branch:str,worktree:Path,
)->bool:
    """Host-only source-safe gates after model patch or deterministic repair."""
    # Stage first, then scope-review before any commit; never trust a model's
    # claim of passing independent science or grant PASS from CI.
    _ok(["git","add","--all"],cwd=worktree)
    files=_ok(["git","diff","--cached","--name-only"],cwd=worktree).splitlines()
    if (not files or any(
            not (f.startswith(ALLOWED_PREFIXES) or f in ALLOWED_FILES)
            or any(bit in f.lower() for bit in FORBIDDEN_PATH_BITS)
            for f in files)):
        _update(state,"BSA279_CODEX_UNAPPROVED_PATCH_QUARANTINED",
                devBranch=branch,changedPaths=files)
        return False
    if not any(f.startswith(("app_generator/","scripts/"))
               and f.endswith((".py",".js",".ts",".tsx"))
               for f in files):
        _update(state,"BSA279_CODEX_DOCS_ONLY_NOT_DEVELOPMENT",
                devBranch=branch,changedPaths=files,
                codexRepairRequired=True)
        return False
    # BSA282 deterministic historical repair: only Git-reported terminal
    # empty lines of *approved staged source files*, no physics or metadata.
    # No new model request, no removal of actual code, no false academic PASS.
    staged_gate=_run(["git","diff","--cached","--check"],cwd=worktree)
    if staged_gate.returncode:
        decision=repair_staged_blank_eof(worktree)
        if decision["status"]=="REPAIRED_EXACT_BLANK_LINES_AT_EOF":
            _update(state,"BSA282_KNOWN_EOF_BLANK_LINES_AUTO_REPAIRED",
                    devBranch=branch,
                    autoRepairPaths=decision["fixedFiles"],
                    autoRepairDigests=decision["beforeAfterSha256"],
                    codexRepairRequired=True)
        if _run(["git","diff","--cached","--check"],cwd=worktree).returncode:
            _update(state,"BSA282_UNRESOLVED_NONTRIVIAL_PATCH_WHITESPACE",
                    devBranch=branch,codexRepairRequired=True,
                    autoRepairClass=decision["status"])
            return False
    # Regression contract and original content integrity are mandatory.
    for label,cmd in (
        ("CONTRACT",[sys.executable,"scripts/check_regression_contract.py"]),
        ("CONTENT",[sys.executable,"scripts/validate_content.py"]),
        ("ACADEMIC_TESTS",[sys.executable,"-m","unittest",
           "tests.test_v46_generic_academic_proof_registry",
           "tests.test_v49_si_unit_science_batch",
           "tests.test_v50_bosla_autonomous_academic_advance",
           "tests.test_v51_newton_force_science_batch",
           "tests.test_v52_paired_glider_source_science",
           "tests.test_v53_paired_glider_signed_admission","-q"]),
    ):
        # Existing tests from repository branch may be extended by Codex.
        code=_log_process(state,"CODEX_"+label,cmd,
                          cwd=worktree,timeout=300)
        if code:
            _update(state,"BSA279_CODEX_TESTS_FAIL_KEEP_PATCH",
                    failedTest=label,devBranch=branch,
                    codexRepairRequired=True)
            return False
    _ok(["git","commit","-m","Bosla autonomous science proof development: "+
         datetime.now().strftime("%Y-%m-%d")],cwd=worktree,timeout=80)
    tip=_head(worktree)
    if _run(["git","push","--set-upstream","origin",branch],
            cwd=worktree,timeout=120).returncode:
        _update(state,"BSA279_CODEX_REMOTE_CI_HANDOFF_UNVERIFIED",
                devBranch=branch,devHead=tip)
        return False
    state["pendingBranch"]=branch
    _update(state,"BSA279_NEW_SOURCE_CODE_COMMITTED_CI_DISPATCHED",
            pendingHead=tip,devBranch=branch,
            codexRepairRequired=False)
    return True


def _codex_stage(state:dict[str,Any],*,repair:bool=False)->bool:
    # BSA282 prevents an infinite Codex loop on an *old* Git commit.
    # Preserve the complete existing staged patch and its history without
    # rebasing/overwriting the newer, independently admitted academic code.
    # A new owner-head worktree is created automatically in the SAME cycle.
    if state.get("codexRepairRequired") is True:
        old_branch=state.get("devBranch")
        old_location=state.get("devWorktree")
        if (isinstance(old_branch,str)
            and isinstance(old_location,str)
            and Path(old_location).is_dir()
            and _branch(Path(old_location))==old_branch):
            prior=Path(old_location)
            original_head=_head(prior)
            latest_head=_head()
            if original_head!=latest_head:
                # No patch content is deleted or imported across a scientific
                # revision. A subsequent model works from latest verified
                # HEAD; older changes remain available for targeted review.
                diverged=_run([
                    "git","merge-base","--is-ancestor",
                    original_head,latest_head],cwd=prior)
                if diverged.returncode:
                    _update(state,"BSA282_DIVERGED_OLD_PATCH_QUARANTINED",
                            oldRepairBranch=old_branch,
                            oldRepairHead=original_head,
                            currentHead=latest_head,
                            codexRepairRequired=False)
                else:
                    staged=_ok(["git","diff","--cached","--name-only"],
                               cwd=prior).splitlines()
                    state.setdefault("quarantinedStalePatches",[]).append({
                        "branch":old_branch,"head":original_head,
                        "worktree":old_location,"changedPaths":staged,
                        "reason":"NEWER_OWNER_ACADEMIC_HEAD_ALREADY_INTEGRATED",
                    })
                    state["codexRepairRequired"]=False
                    state.pop("devBranch",None)
                    state.pop("devWorktree",None)
                    _update(state,"BSA282_STALE_PATCH_QUARANTINED_NEW_HEAD_RETRY",
                            currentHead=latest_head,
                            staleCodePreserved=True,
                            oldRepairHead=original_head,
                            oldRepairBranch=old_branch)
            elif state.get("status") in (
                "BSA279_CODEX_PATCH_WHITESPACE_FAILURE",
                "BSA282_UNRESOLVED_NONTRIVIAL_PATCH_WHITESPACE",
            ):
                # Repair and finish the saved candidate WITHOUT a fresh
                # model call or spending a bounded Codex request.
                decision=repair_staged_blank_eof(prior)
                if decision["status"]=="REPAIRED_EXACT_BLANK_LINES_AT_EOF":
                    _update(state,"BSA282_RESUMED_SAVED_PATCH_NO_MODEL_CALL",
                            devBranch=old_branch,
                            autoRepairPaths=decision["fixedFiles"],
                            autoRepairDigests=decision["beforeAfterSha256"],
                            codexRepairRequired=True)
                    return _finalize_staged_patch(
                        state,branch=old_branch,worktree=prior)
    if state.get("pendingBranch") and not repair:
        _update(state,"BSA279_WAITING_FOR_PENDING_BRANCH_CI")
        return False
    if not _daily_budget(state):
        _update(state,"BSA279_BOUNDED_DAILY_MODEL_BUDGET_REACHED")
        return False
    if time.time()<float(state.get("codexQuarantinedUntilEpoch",0)):
        _update(state,"BSA280_REPEATED_CODEX_ENV_FAILURE_IN_COOLDOWN")
        return False
    executable=shutil.which("codex.cmd") or shutil.which("codex")
    if not executable:
        _update(state,"BSA279_CODE_DEVELOPMENT_AGENT_UNAVAILABLE")
        return False
    if not _clean() or _branch()!=MAIN_BRANCH:
        _update(state,"BSA279_OWNER_CODE_NOT_STABLE_FOR_CODEX")
        return False
    # Preserve and repair the SAME isolated code change after a CI or
    # deterministic local-test failure. Never drop unfinished code and
    # blindly generate another unrelated branch on the next scheduled tick.
    reuse=repair or state.get("codexRepairRequired") is True
    if reuse:
        branch=state.get("pendingBranch") or state.get("devBranch")
        location=state.get("devWorktree")
        if (not isinstance(branch,str) or not isinstance(location,str)
            or not Path(location).is_dir()
            or _branch(Path(location))!=branch):
            _update(state,"BSA279_REPAIR_WORKTREE_NOT_AUTHENTIC")
            return False
        worktree=Path(location)
    else:
        branch,worktree=_dev_worktree(state)
    state["codexCount"]=int(state.get("codexCount",0))+1
    prompt=_codex_prompt()
    if isinstance(state.get("academicFailure"),dict):
        issue=state["academicFailure"]
        if issue.get("mode")=="DISPATCH_INDEPENDENT_SOURCE_SAFE_CODE_REPAIR":
            prompt+=(
                " OWNER ACADEMIC FAILURE RECOVERY: classification "
                +str(issue.get("classification"))+
                ". The prior owner source-bound admission did NOT PASS. "
                " Implement and test the missing code/verification handler "
                " without altering or re-signing ANY academic evidence. "
                " The owner will rerun authentic CI and science on the "
                " next committed head. "
            )
    science_stall=state.get("scienceStall")
    if isinstance(science_stall,dict) and science_stall.get("triggered"):
        prompt+=(
            " BSA285 INDEPENDENT SCIENTIFIC ACCEPTANCE STALL: a separately "
            "verified original Serway horizon receipt has not increased "
            "the academically accepted 429-task count. This is NOT normal "
            "progress merely because logs, CI or source-free tests pass. "
            "Review earlier source-proof and admission implementations; "
            "finish the specific missing real-source scientific proof "
            "producer AND its signed owner admission + independent "
            "cross-Git-head readback. Add falsification and restart tests, "
            "integrate the remedy, and advance to the next genuinely "
            "unaccepted task. Never fabricate the next accepted count or "
            "turn a generated witness into an academic PASS. "
        )
    if reuse:
        prompt+=(
            " INCIDENT REPAIR, NOT A NEW UNRELATED TASK: inspect the "
            "existing modified files and prior exact-hosted-CI/test "
            "failure on this same branch. Look up historical fixes, "
            "produce the targeted correction, run actual tests, add "
            "fault-injection and integrate the fix into the executable "
            "recovery registry. Do not replay an uncertain Gemini "
            "request or assume the prior failed model output succeeded."
        )
    # The Windows elevated workspace-write helper previously failed in
    # Git-linked LOCALAPPDATA worktrees. Use an *unlinked*, source-tracked
    # 10MB snapshot, exactly as the earlier standalone Codex write test did.
    # The owner host checks and adopts only an allowlisted delta into Git.
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot=PRIVATE/"coding-snapshots"/("safe-"+stamp+"-"+
                                       branch.rsplit("/",1)[-1])
    baseline=build_isolated_coding_snapshot(
        repo=worktree,snapshot=snapshot)
    _update(state,"BSA280_ISOLATED_GITLESS_CODE_WORKSPACE_READY",
            devBranch=branch,devWorktree=str(worktree),
            codexSnapshot=str(snapshot),copiedSourceFiles=len(baseline),
            codexCount=state["codexCount"],codexRepairRequired=reuse)
    prompt+=(
        " You are editing a disposable, Git-less copy of the Bosla "
        "tracked repository. The host will compare files against a "
        "read-only hash manifest, apply only approved source changes "
        "into the authenticated Git worktree, run tests and then commit. "
        " Do not expect git commands to work here. The original textbook "
        "PDF is private and deliberately absent; do not fabricate source "
        "passages or academic acceptance. MCQ05 A13-A15 already have signed "
        "source-bound science receipts; choose genuinely NEW remaining "
        "academic proof tasks on the CURRENT Git head, not previously "
        "accepted tasks or source-free metadata. Write real proof producer "
        "code with adversarial negative tests and never claim science PASS "
        "from model output or CI alone. "
    )
    out=PRIVATE/"codex-last-message.txt"
    args=[str(executable),"exec","--sandbox","workspace-write",
          "--cd",str(snapshot),"--skip-git-repo-check",
          "-c","approval_policy=\"never\"",
          "--output-last-message",str(out),prompt]
    rc=_log_process(state,"CODEX_TARGETED_REPAIR" if reuse
                    else "CODEX_ACTUAL_CODE_DEVELOPMENT",args,
                    cwd=snapshot,timeout=MAX_CODEX_SECONDS)
    try:
        adopted=apply_isolated_patch(
            repo=worktree,snapshot=snapshot,baseline=baseline)
    except (OSError,ValueError) as exc:
        _update(state,"BSA280_UNSAFE_SNAPSHOT_QUARANTINED",
                devBranch=branch,patchErrorCode=str(exc),
                codexRepairRequired=False)
        return False
    if rc!=0 or not adopted:
        classification=classify_codegen_failure(
            exit_code=rc,log_excerpt=_safe_last_log(state),
            changed_files=bool(adopted))
        prior=state.get("codexFailure",{})
        attempts=(int(prior.get("count",0))+1
                  if isinstance(prior,dict)
                  and prior.get("classification")==classification else 1)
        state["codexFailure"]={
            "classification":classification,"count":attempts,
            "head":_head(),"academicPASS":False}
        if attempts>=2 and classification in (
                "CODEX_LOCAL_SANDBOX_WRITE_OR_EXEC_FAILURE",
                "CODEX_NO_CHANGE_NOT_ACADEMIC_PROGRESS"):
            # Retry only after a bounded cooldown or environment revision,
            # rather than spend twelve model sessions on the same denial.
            state["codexQuarantinedUntilEpoch"]=time.time()+3600
        _update(state,"BSA280_"+classification,
                devBranch=branch,modelExitCode=rc,
                codexRepairRequired=bool(adopted))
        return False
    state.pop("codexFailure",None)
    state.pop("codexQuarantinedUntilEpoch",None)
    changed=_ok(["git","status","--porcelain"],cwd=worktree)
    if not changed:
        _update(state,"BSA280_SNAPSHOT_IMPORTED_NO_GIT_DELTA",
                devBranch=branch,codexRepairRequired=False)
        return False
    return _finalize_staged_patch(state,branch=branch,worktree=worktree)


def cycle(*,codegen:bool=True)->dict[str,Any]:
    if os.environ.get("COMPUTERNAME","").upper()!="YOGA6":
        raise ValueError("BSA279_BOSLA_OWNER_YOGA6_ONLY")
    with SingleFlight():
        state=_read_state()
        # BSA286: a stopped coordinator may have left a nested academic
        # worker alive. Clear ONLY exact saved process identity first.
        try:
            old_child=recover_previous_owner_tree(
                state,expected_python=ROOT/".venv"/"Scripts"/"python.exe")
        except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
            _update(state,"BSA286_ORPHAN_IDENTITY_PROBE_SAFETY_STOP",
                    lastErrorClass=type(exc).__name__,lastErrorCode=str(exc)[:250])
            return state
        if not old_child["safe"]:
            _update(state,"BSA286_OWNER_ORPHAN_IDENTITY_SAFETY_STOP",
                    orphanRecovery=old_child)
            return state
        if old_child["status"]=="BSA286_STALE_OWNER_TREE_REAPED":
            _update(state,"BSA286_AUTHENTIC_STALE_OWNER_TREE_REAPED",
                    orphanRecovery=old_child)
        state["cycle"]=int(state.get("cycle",0))+1
        state["currentHead"]=_head()
        _update(state,"BSA279_PERSISTENT_DEVELOPMENT_CYCLE_STARTED",
                cycleStartedAt=_utc())
        # BSA285: independent scholarly throughput is not log throughput.
        # Inspect the previously independently verified signed baseline on
        # every normal scheduler entry, including CI and code-repair cycles.
        diagnostic=investigate_zero_academic_gain(
            state,now=_utc(),cycle=int(state["cycle"]))
        if diagnostic.get("triggered"):
            state["scienceStall"]=diagnostic
            _update(state,"BSA285_INDEPENDENT_SCIENCE_STALL_INVESTIGATION",
                    scienceStall=diagnostic)
        try:
            if _branch()!=MAIN_BRANCH:
                _update(state,"BSA279_WRONG_BOSLA_FEATURE_BRANCH")
                return state
            promoted=_promote_known(state)
            state["currentHead"]=_head()
            if promoted:
                # The same cycle cannot sign science before new exact CI.
                _update(state,"BSA279_NEW_CODE_PROMOTED_WAIT_HOSTED_CI")
                return state
            # A CI-pending generated branch is *not* bypassed for more
            # speculative code creation: finish its hosted review first.
            if state.get("pendingBranch"):
                branch=state["pendingBranch"]
                candidate=_head(Path(state["devWorktree"])) if (
                    isinstance(state.get("devWorktree"),str)
                    and Path(state["devWorktree"]).is_dir()
                ) else state.get("pendingHead","")
                ci=_hosted_ci(candidate,branch,min_runs=1)
                if ci=="CI_FAILED" and codegen:
                    _update(state,"BSA279_FAILED_CI_TARGETED_REPAIR_DISPATCHED",
                            pendingBranch=branch,failedCandidateHead=candidate)
                    _codex_stage(state,repair=True)
                else:
                    _update(state,"BSA279_CANDIDATE_"+ci,
                            pendingBranch=branch)
                return state
            owner_ok=_owner_stage(state)
            if not owner_ok:
                # Never fabricate PASS from a failed original source.
                # A genuinely defective or missing engineering proof
                # handler must nonetheless be repaired INDEPENDENTLY.
                issue=state.get("academicFailure")
                if (codegen and isinstance(issue,dict)
                    and issue.get("head")==state.get("currentHead")
                    and issue.get("mode")==
                       "DISPATCH_INDEPENDENT_SOURCE_SAFE_CODE_REPAIR"):
                    _update(state,
                        "BSA280_ACADEMIC_FAILURE_ISOLATED_CODE_REPAIR_DISPATCH",
                        academicFailure=issue)
                    _codex_stage(state)
                return state
            if codegen:
                _codex_stage(state)
            else:
                _update(state,"BSA279_PERSISTENCE_SELFTEST_OWNER_OK",
                        lastOwnerHead=state.get("lastOwnerHead"))
            return state
        except (ValueError,OSError,subprocess.TimeoutExpired) as exc:
            _update(state,"BSA279_CLASSIFIED_RETRYABLE_OR_SAFETY_BOUNDARY",
                    lastErrorCode=str(exc)[:450],
                    lastErrorClass=type(exc).__name__)
            return state


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once",action="store_true")
    group.add_argument("--status",action="store_true")
    group.add_argument("--lock-probe",action="store_true")
    parser.add_argument("--skip-codegen",action="store_true")
    args=parser.parse_args(argv)
    if args.status:
        print(json.dumps({"taskNames":PERSISTENT_TASKS,
                          "state":_read_state()},sort_keys=True))
        return 0
    if args.lock_probe:
        try:
            with SingleFlight():
                print(json.dumps({"status":"BSA279_SINGLE_FLIGHT_ACQUIRED"}))
            return 0
        except ValueError as exc:
            print(json.dumps({"status":"BSA279_SINGLE_FLIGHT_REJECTED",
                              "code":str(exc)}))
            return 2
    try:
        outcome=cycle(codegen=not args.skip_codegen)
        print(json.dumps({"status":outcome.get("status"),
                          "cycle":outcome.get("cycle"),
                          "gitHead":outcome.get("currentHead"),
                          "pendingBranch":outcome.get("pendingBranch"),
                          "lastOwnerHead":outcome.get("lastOwnerHead"),
                          "heartbeatAt":outcome.get("heartbeatAt")},sort_keys=True))
        # A retryable owner/CI block should not be silently reported as
        # scientific success. Task Scheduler will safely re-enter next tick.
        return 0 if outcome.get("status","").startswith("BSA279_") else 2
    except (ValueError,OSError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status":"BSA279_PERSISTENCE_LAUNCH_FAILURE",
                          "errorCode":str(exc)[:400],
                          "errorClass":type(exc).__name__},sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())
