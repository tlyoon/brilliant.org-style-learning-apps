"""Run Python regression test modules with explicit time limits and diagnostics.

This opt-in diagnostic runner does not alter the authoritative CI unittest suite.
Each test_*.py module runs in a fresh interpreter, so a blocked module can be
identified without holding the entire test run indefinitely. No services or
protected project artifacts are accessed by this wrapper itself.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
COUNT_RE = re.compile(r"Ran (\d+) tests? in")


def _stop_tree(proc: subprocess.Popen[str]) -> str:
    if proc.poll() is None:
        if os.name == "nt":
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True, timeout=5, check=False)
            except (OSError, subprocess.TimeoutExpired):
                pass
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if proc.poll() is None:
            proc.kill()
    try:
        output, _ = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        output, _ = proc.communicate()
    return output or ""


def run_module(file: Path, *, timeout_seconds: float, python: str) -> dict:
    if timeout_seconds <= 0 or timeout_seconds > 900:
        raise ValueError("module timeout must be in (0, 900] seconds")
    started = time.monotonic()
    cmd = [python, "-m", "unittest", "discover", "-s", str(file.parent),
           "-p", file.name, "-v"]
    proc = subprocess.Popen(
        cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, errors="replace",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        start_new_session=os.name != "nt",
    )
    try:
        output, _ = proc.communicate(timeout=timeout_seconds)
        status = "PASS" if proc.returncode == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        output, status = _stop_tree(proc), "TIMEOUT"
    match = COUNT_RE.search(output)
    return {
        "module": file.name, "status": status,
        "seconds": round(time.monotonic() - started, 2),
        "tests": int(match.group(1)) if match else None,
        # Never echo arbitrary test output from a success. Failure output
        # is deliberately bounded for local diagnostics only.
        "diagnostic": output[-800:] if status != "PASS" else "",
    }


def run_suite(test_dir: Path, *, pattern: str = "test_*.py",
              timeout_seconds: float = 120.0, python: str = sys.executable,
              fail_fast: bool = False, limit: int | None = None) -> list[dict]:
    if (not pattern.startswith("test_") or not pattern.endswith(".py") or
        "/" in pattern or "\\" in pattern or ".." in pattern):
        raise ValueError("only test_*.py filename patterns are allowed")
    if timeout_seconds <= 0 or timeout_seconds > 900:
        raise ValueError("module timeout must be in (0, 900] seconds")
    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    test_dir = test_dir.resolve()
    if not test_dir.is_dir():
        raise ValueError("test directory missing")
    files = sorted(f for f in test_dir.glob(pattern)
                   if f.is_file() and f.name.startswith("test_") and
                   f.suffix == ".py")
    if not files:
        raise ValueError("no matching Python test modules")
    results = []
    for file in files[:limit]:
        result = run_module(file, timeout_seconds=timeout_seconds, python=python)
        results.append(result)
        print(f"{result['status']:7} {file.name} "
              f"({result['tests'] if result['tests'] is not None else '?'} tests, "
              f"{result['seconds']:.2f}s)", flush=True)
        if result["diagnostic"]:
            print(result["diagnostic"], flush=True)
        if fail_fast and result["status"] != "PASS":
            break
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-dir", type=Path, default=ROOT / "tests")
    parser.add_argument("--pattern", default="test_*.py")
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args()
    try:
        results = run_suite(args.test_dir, pattern=args.pattern,
                            timeout_seconds=args.timeout_seconds,
                            fail_fast=args.fail_fast, limit=args.limit)
    except (ValueError, OSError) as exc:
        print(f"BLOCKED {type(exc).__name__}: {str(exc)[:200]}")
        return 2
    passed = sum(x["status"] == "PASS" for x in results)
    failed = sum(x["status"] == "FAIL" for x in results)
    timed_out = sum(x["status"] == "TIMEOUT" for x in results)
    print(f"SUMMARY modules={len(results)} pass={passed} fail={failed} "
          f"timeout={timed_out}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
