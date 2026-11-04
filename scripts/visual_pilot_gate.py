"""Read-only technical evidence summary for a bounded visual learning pilot.

A technical pass never implies permission to publish. Human/source/real
browser review gates remain explicitly unfulfilled unless independently
documented elsewhere, outside this script's authority.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.audit_visual_run import audit_run


REVIEW_GATES = (
    "source-grounded_academic_review",
    "actual_browser_pixel_quality",
    "keyboard_screenreader_mobile_review",
    "learner_activity_review_and_approval",
)


def summarize(phase: str, contract: dict, renderer: dict) -> dict:
    contract_ok = contract.get("outcome") == "contract_pass"
    semantic_ok = renderer.get("status") == "semantic_render_pass"
    completed = phase == "COMPLETE"
    return {
        "runPhase": phase,
        "technicalEvidenceReady": completed and contract_ok and semantic_ok,
        "contract": contract,
        "semanticRenderer": renderer,
        "pendingIndependentGates": list(REVIEW_GATES),
        "publicationAuthorized": False,
        "deploymentCompleted": False,
    }


def evaluate(repo_root: Path, run_root: Path, *, node: str = "node") -> dict:
    state_file = run_root / "state/run-state.json"
    if not state_file.is_file():
        raise ValueError("saved run state is required")
    state = json.loads(state_file.read_text(encoding="utf-8"))
    contract = audit_run(repo_root, run_root)
    rendered = {"status": "not_checked", "issues": []}
    package_files = [
        Path(value) for value in state.get("installed_paths", [])
        if isinstance(value, str) and Path(value).name == "package.json"
    ]
    if state.get("phase") == "COMPLETE" and len(package_files) == 1 and contract.get("outcome") == "contract_pass":
        args = [
            node, str(repo_root / "scripts/audit_visual_rendering.js"),
            "--repo-root", str(repo_root),
            "--package", str(package_files[0]),
        ]
        try:
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=30, check=False,
            )
            rendered = json.loads(result.stdout)
            if result.returncode != 0:
                rendered["status"] = "fail"
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            rendered = {"status": "not_checked", "issues": [str(exc)[:400]]}
    return summarize(str(state.get("phase", "UNKNOWN")), contract, rendered)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], type=Path)
    options = parser.parse_args()
    try:
        report = evaluate(options.repo_root.resolve(), options.run_root.resolve())
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"technicalEvidenceReady": False, "publicationAuthorized": False, "error": str(exc)}))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["technicalEvidenceReady"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
