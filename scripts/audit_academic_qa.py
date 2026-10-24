"""Read-only academic QA triage on a generated package.

This is NOT scientific review by an LLM or human, and cannot publish content.
Missing source-grounded evidence must produce REVIEW_REQUIRED, never PASS.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from app_generator.validation.academic_qa import Finding, decide
from app_generator.validation.answer_integrity import check_answer_integrity
from app_generator.validation.collision_crosscheck import check_collision_witness
from app_generator.validation.language_qa import check_multilingual_surface
from app_generator.validation.source_identity import verify_source_identity
from app_generator.visuals.validation import visual_contract_errors

def academic_triage(repo: Path, package_path: Path, source_pdf: Path | None = None) -> dict:
    package = json.loads(package_path.read_text(encoding="utf-8"))
    activities = package.get("activities", [])
    if not isinstance(activities, list) or not activities or any(not isinstance(a,dict) for a in activities):
        raise ValueError("nonempty activity package required")
    manifest_name = package.get("sourceManifest")
    if not isinstance(manifest_name,str):
        raise ValueError("sourceManifest missing")
    manifest_path = (repo / manifest_name).resolve()
    if not manifest_path.is_relative_to(repo.resolve()):
        raise ValueError("source manifest path escapes repository")
    findings = [verify_source_identity(manifest_path, source_pdf)]
    rows = []
    visual_errors = visual_contract_errors(repo, package)
    for a in activities:
        checks = [check_answer_integrity(a), check_multilingual_surface(a),
                  check_collision_witness(None, f"activity:{a.get('id','?')}")]
        rows.append({"activityId":a.get("id"), "answer":checks[0].result,
                     "translation":checks[1].result, "physics":checks[2].result})
        findings.extend(checks)
    # The visual contract can expose technical defects but not independently
    # prove that the drawing matches the textbook or answer reasoning.
    if visual_errors:
        findings.append(Finding("visual_semantics","FAIL","deterministic",
                                str(package_path),"visual contract defects: "+"; ".join(visual_errors[:4]),True))
    else:
        findings.append(Finding("visual_semantics","REVIEW_REQUIRED","deterministic",
                                str(package_path),"schema/renderer checks pass; academic meaning not verified",True))
    result = decide(findings)
    result["packageId"] = package.get("packageId")
    result["activityCount"] = len(rows)
    result["activities"] = rows
    result["artifactSha256"] = hashlib.sha256(package_path.read_bytes()).hexdigest()
    result["sourcePdfWasRead"] = bool(source_pdf and source_pdf.is_file())
    result["nextAction"] = ("Correct confirmed defects before any release" if result["academicQA"] == "FAIL" else
        "Supply independent textbook-grounding, answer and multilingual evidence for unresolved gates")
    return result

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package",type=Path,required=True)
    parser.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-pdf",type=Path,default=None)
    args=parser.parse_args()
    try:
        report=academic_triage(args.repo_root.resolve(),args.package.resolve(),args.source_pdf)
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({"academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
                          "error":str(exc)[:600]}))
        return 2
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return {"PASS":0,"FAIL":1,"REVIEW_REQUIRED":2}[report["academicQA"]]

if __name__=="__main__":
    raise SystemExit(main())
