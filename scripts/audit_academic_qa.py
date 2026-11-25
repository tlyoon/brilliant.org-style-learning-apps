"""Read-only academic QA triage on a generated package.

This is NOT scientific review by an LLM or human, and cannot publish content.
Missing source-grounded evidence must produce REVIEW_REQUIRED, never PASS.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app_generator.validation.academic_qa import Finding, decide
from app_generator.validation.answer_integrity import check_answer_integrity
from app_generator.validation.collision_crosscheck import check_collision_witness
from app_generator.validation.language_qa import check_multilingual_surface
from app_generator.validation.source_identity import verify_source_identity
from app_generator.validation.physics_proofs import audit_proofs
from app_generator.validation.interactive_physics import audit_interaction_models
from app_generator.validation.impulse_semantics import audit_impulse_candidate
from app_generator.validation.impulse_v3_audit import audit_v3
from app_generator.visuals.validation import visual_contract_errors

def academic_triage(
    repo: Path, package_path: Path, source_pdf: Path | None = None,
    *, physics_receipts: dict | None = None, interaction_receipts: dict | None = None,
    impulse_review_path: Path | None = None,
    impulse_v3_review: Path | None = None,
    impulse_v3_parent: Path | None = None,
    impulse_v3_parent_review: Path | None = None,
) -> dict:
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
    if impulse_review_path is not None and impulse_v3_review is not None:
        raise ValueError("conflicting v2 and v3 academic evidence options")
    if physics_receipts is not None:
        if not source_pdf or not source_pdf.is_file():
            raise ValueError("bounded physics proofs require the exact controlled source PDF")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (len(manifest.get("sources",[])) != 1 or
            manifest["sources"][0].get("sha256") != manifest.get("sha256")):
            raise ValueError("academic QA source manifest is ambiguous")
        evidence = audit_proofs(package, source_pdf, manifest["sha256"], physics_receipts)
        result["boundedPhysicsEvidence"] = evidence
        # Even six rigorous bounded witnesses do not verify all questions,
        # misleading distractors, translations, or the visual semantics.
        result["academicQA"] = (
            "FAIL" if result["academicQA"] == "FAIL" or evidence["failedWitnesses"]
            else result["academicQA"]
        )
        result["publicationAuthorized"] = False
    if interaction_receipts is not None:
        if not source_pdf or not source_pdf.is_file():
            raise ValueError("interactive physics models require controlled source PDF")
        manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
        if (len(manifest.get("sources",[])) != 1 or
            manifest["sources"][0].get("sha256") != manifest.get("sha256")):
            raise ValueError("academic QA source manifest ambiguous for interactive evidence")
        evidence=audit_interaction_models(package,source_pdf,manifest["sha256"],
                                          interaction_receipts)
        result["interactivePhysicsEvidence"]=evidence
        if evidence["modelDiscrepancies"]:
            result["academicQA"]="FAIL"
        # Bounded physics models never by themselves imply correctness of
        # question prose, distractor meaning, visual content or translations.
        result["publicationAuthorized"]=False
    if impulse_review_path is not None:
        if source_pdf is None or not source_pdf.is_file():
            raise ValueError("controlled source PDF is required for impulse semantic evidence")
        # Independently verify that the evaluated file is exactly the
        # source-version-bound private candidate, not any other installed
        # package, before attaching an optional semantic/distractor receipt.
        screening=audit_impulse_candidate(package_path,impulse_review_path,source_pdf)
        result["trilingualDistractorEvidence"]=screening
        result["publicationAuthorized"]=False
        # Bounded lexical/physics evidence cannot confer full academic PASS.
        if result["academicQA"]=="PASS":
            result["academicQA"]="REVIEW_REQUIRED"
    if impulse_v3_review is not None:
        if not source_pdf or not source_pdf.is_file():
            raise ValueError("controlled source PDF required for v3 academic evidence")
        if not impulse_v3_parent or not impulse_v3_parent_review:
            raise ValueError("exact private v2 package and review receipt required for v3")
        result["impulseV3Evidence"]=audit_v3(
            package_path,impulse_v3_review,impulse_v3_parent,
            impulse_v3_parent_review,source_pdf,
        )
        if result["academicQA"]=="PASS":
            result["academicQA"]="REVIEW_REQUIRED"
        result["publicationAuthorized"]=False
    result["nextAction"] = ("Correct confirmed defects before any release" if result["academicQA"] == "FAIL" else
        "Supply independent textbook-grounding, answer and multilingual evidence for unresolved gates")
    return result

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package",type=Path,required=True)
    parser.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-pdf",type=Path,default=None)
    parser.add_argument("--physics-receipts",type=Path,default=None,
                        help="private source-bound exact-arithmetic proof receipts")
    parser.add_argument("--interaction-receipts",type=Path,default=None,
                        help="private source-bound interactive answer model receipts")
    parser.add_argument("--impulse-review",type=Path,default=None,
                        help="private v2 candidate review.json for bounded multilingual/distractor checks")
    parser.add_argument("--impulse-v3-review",type=Path,default=None)
    parser.add_argument("--impulse-v3-parent",type=Path,default=None)
    parser.add_argument("--impulse-v3-parent-review",type=Path,default=None)
    args=parser.parse_args()
    try:
        receipt_data=(json.loads(args.physics_receipts.read_text(encoding="utf-8"))
                      if args.physics_receipts else None)
        interactions=(json.loads(args.interaction_receipts.read_text(encoding="utf-8"))
                      if args.interaction_receipts else None)
        report=academic_triage(args.repo_root.resolve(),args.package.resolve(),args.source_pdf,
                               physics_receipts=receipt_data,interaction_receipts=interactions,
                               impulse_review_path=args.impulse_review,
                               impulse_v3_review=args.impulse_v3_review,
                               impulse_v3_parent=args.impulse_v3_parent,
                               impulse_v3_parent_review=args.impulse_v3_parent_review)
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({"academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
                          "error":str(exc)[:600]}))
        return 2
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return {"PASS":0,"FAIL":1,"REVIEW_REQUIRED":2}[report["academicQA"]]

if __name__=="__main__":
    raise SystemExit(main())
