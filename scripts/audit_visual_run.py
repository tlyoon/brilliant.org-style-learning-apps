"""Read-only offline validation of a saved visual-generation run.

This checks deterministic contracts only. A pass is NOT evidence of rendered
pixel quality, source accuracy, academic review, or publication approval.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from app_generator.errors import ResponseContractError
from app_generator.generation.extraction import parse_json_response
from app_generator.visuals.generation import attach_visual_documents


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def audit_run(repo_root: Path, run_root: Path) -> dict[str, object]:
    report: dict[str, object] = {
        "outcome": "incomplete",
        "verification": "offline_deterministic_contract_only",
        "run": run_root.name,
        "candidateActivities": 0,
        "visualPlans": 0,
        "visualSpecs": 0,
        "issues": [],
        "publicationVerified": False,
        "renderedPixelsVerified": False,
    }
    issues: list[str] = []
    try:
        packages = sorted((run_root / "candidate/content").rglob("package.json"))
        if len(packages) != 1:
            raise ValueError(f"expected exactly one saved candidate package, found {len(packages)}")
        pkg = _read(packages[0])
        report["candidateActivities"] = len(pkg.get("activities", []))
        plans = _read(run_root / "batches/visual-plans.json")
        report["visualPlans"] = len(plans.get("activities", []))
        batches = run_root / "batches"
        complete = batches / "visual-specs.json"
        partial = batches / "visual-specs-validated.json"
        repaired = batches / "visual-specs-repair.response.txt"
        state_path = run_root / "state/run-state.json"
        state = _read(state_path) if state_path.is_file() else {}
        if state.get("phase") == "COMPLETE":
            installed = [
                Path(path) for path in state.get("installed_paths", [])
                if isinstance(path, str) and Path(path).name == "package.json"
            ]
            if len(installed) != 1:
                raise ValueError("completed run must identify exactly one installed package")
            actual = _read(installed[0])
            original = deepcopy(actual)
            extracted_plans = []
            extracted_specs = []
            for item in original["activities"]:
                if "visualPlan" in item:
                    extracted_plans.append({"activityId": item["id"], "visualPlan": item.pop("visualPlan")})
                if "visualSpec" in item:
                    extracted_specs.append({"activityId": item["id"], "visualSpec": item.pop("visualSpec")})
            report["candidateActivities"] = len(actual["activities"])
            report["visualPlans"] = len(extracted_plans)
            report["visualSpecs"] = len(extracted_specs)
            rebuilt = attach_visual_documents(
                repo_root, original, {"activities": extracted_plans},
                {"activities": extracted_specs},
            )
            if rebuilt["activities"] != actual["activities"]:
                raise ValueError("installed activity visuals do not round-trip through validation")
            if {item["activityId"] for item in extracted_plans} != {
                item.get("activityId") for item in plans["activities"]
            }:
                raise ValueError("installed visual plans do not match run plan IDs")
            report["source"] = "completed_run_installed_package"
            report["outcome"] = "contract_pass"
            return report
        if complete.is_file():
            specs = _read(complete)
        elif partial.is_file() and repaired.is_file():
            accepted = _read(partial)
            reply = parse_json_response(repaired.read_text(encoding="utf-8"))
            if not isinstance(reply, dict) or not isinstance(reply.get("activities"), list):
                raise ValueError("saved visual-spec repair response is malformed")
            specs = {"activities": accepted["activities"] + reply["activities"]}
        elif partial.is_file():
            specs = _read(partial)
        else:
            raise ValueError("no saved visual-specifications or repair evidence")
        report["visualSpecs"] = len(specs.get("activities", []))
        result = attach_visual_documents(repo_root, pkg, plans, specs)
        if len(result["activities"]) != report["candidateActivities"]:
            raise ValueError("audited package activity count unexpectedly changed")
        report["outcome"] = "contract_pass"
    except (OSError, ValueError, KeyError, TypeError, ResponseContractError, json.JSONDecodeError) as exc:
        issues.append(f"{type(exc).__name__}: {str(exc)[:1500]}")
    report["issues"] = issues
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], type=Path)
    args = parser.parse_args()
    report = audit_run(args.repo_root.resolve(), args.run_root.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["outcome"] == "contract_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
