"""Evidence-based per-activity academic acceptance without human sign-off.

A passing schema, AI consensus or source keyword is NOT academic correctness.
Only trusted in-process independent verifiers may issue actual PASS evidence.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from app_generator.validation.academic_qa import REQUIRED, Finding, decide
from app_generator.validation.language_qa import check_multilingual_surface
from app_generator.validation.reviewer_source_packets import verified_source_packet
from app_generator.visuals.validation import visual_contract_errors

LANGS=("en","ms","zh")
Verifier=Callable[[dict[str,Any],dict[str,Any]|None],Finding]

def _localized(x:Any) -> bool:
    return (isinstance(x,dict) and all(isinstance(x.get(l),str) and
            bool(x[l].strip()) for l in LANGS))

def _answer_shape_defects(activity:dict[str,Any]) -> list[str]:
    defects=[]
    if activity.get("type")=="mcq":
        key=activity.get("answerKey",{})
        options=key.get("options",[]) if isinstance(key,dict) else []
        ids=[o.get("id") for o in options if isinstance(o,dict)]
        if (not isinstance(options,list) or len(options)<2 or
            len(ids)!=len(options) or len(ids)!=len(set(ids)) or
            key.get("correct") not in ids):
            defects.append("MCQ answer references a missing or duplicate option")
        if not all(_localized(o.get("label")) for o in options if isinstance(o,dict)):
            defects.append("MCQ option lacks EN/MS/ZH localized label")
    elif activity.get("type")=="interactive":
        d=activity.get("interaction")
        if not isinstance(d,dict):
            return ["missing interactive answer structure"]
        items=d.get("items",[])
        ids=[x.get("id") for x in items if isinstance(x,dict)]
        if (not isinstance(items,list) or not items or len(ids)!=len(items) or
            len(set(ids))!=len(ids)):
            return ["interactive item identifiers invalid or duplicate"]
        if any(not _localized(x.get("label")) for x in items if isinstance(x,dict)):
            defects.append("interactive item label missing a locale")
        mode=activity.get("interactionMode")
        if mode=="selection":
            selected=d.get("correctSelections")
            if (not isinstance(selected,list) or not selected or
                len(selected)!=len(set(selected)) or not set(selected)<=set(ids)):
                defects.append("selection key refers to invalid items")
        elif mode=="ordering":
            order=d.get("correctOrder")
            if not isinstance(order,list) or len(order)!=len(ids) or set(order)!=set(ids):
                defects.append("ordering key is not a permutation of all item IDs")
        elif mode in ("classification","matching"):
            targets=d.get("targets",[])
            target_ids=[x.get("id") for x in targets if isinstance(x,dict)]
            assignments=d.get("placements",[])
            if (not isinstance(targets,list) or not targets or
                len(target_ids)!=len(targets) or len(set(target_ids))!=len(target_ids)
                or any(not _localized(x.get("label")) for x in targets if isinstance(x,dict))):
                defects.append("classification/matching target IDs or labels invalid")
            if (not isinstance(assignments,list) or len(assignments)!=len(ids)
                or len({x.get("itemId") for x in assignments if isinstance(x,dict)})!=len(ids)
                or any(not isinstance(x,dict) or x.get("itemId") not in ids
                       or x.get("targetId") not in target_ids for x in assignments)):
                defects.append("classification/matching placements do not cover valid item/target IDs")
        else:
            defects.append("unsupported interactive answer mode")
    else:
        defects.append("unsupported academic activity type")
    return defects

def audit_activity_matrix(
    *, repo_root:Path, package_path:Path, source_pdf:Path,
    source_sha256:str, source_packets:dict[str,Any]|None=None,
    expected_count:int=18,
    trusted_verifiers:Mapping[str,Verifier]|None=None,
) -> dict[str,Any]:
    raw=package_path.read_bytes()
    package_sha=sha256(raw).hexdigest()
    package=json.loads(raw.decode("utf-8"))
    if sha256(source_pdf.read_bytes()).hexdigest()!=source_sha256:
        raise ValueError("controlled PDF differs from authoritative source SHA256")
    acts=package.get("activities",[])
    if not isinstance(acts,list) or len(acts)!=expected_count or expected_count<1:
        raise ValueError("unexpected number of academic activities")
    ids=[a.get("id") if isinstance(a,dict) else None for a in acts]
    if any(not isinstance(id_,str) or not id_ for id_ in ids) or len(set(ids))!=len(ids):
        raise ValueError("missing or duplicate activity identifiers")
    if trusted_verifiers is None:
        trusted_verifiers={}
    if any(gate not in REQUIRED or not callable(f) for gate,f in trusted_verifiers.items()):
        raise ValueError("only executable trusted academic-verifier callbacks supported")
    packets=None
    if source_packets:
        if (source_packets.get("packageSha256")==package_sha and
            source_packets.get("sourceSha256")==source_sha256 and
            isinstance(source_packets.get("packets"),dict)):
            packets=source_packets["packets"]
    all_results=[]
    for a in acts:
        aid=a["id"]
        refs={}
        source=None
        if packets:
            candidate=packets.get(aid)
            if (isinstance(candidate,dict) and
                candidate.get("sourceSha256")==source_sha256 and
                candidate.get("activityId")==aid):
                try:
                    source=verified_source_packet(
                        source_pdf,source_sha256,aid,
                        candidate.get("sourceAnchors",[]),
                    )
                    # A copied or modified source packet cannot silently
                    # replace what was independently extracted from the PDF.
                    if source["sourceEvidence"]!=candidate.get("sourceEvidence"):
                        source=None
                except (ValueError,KeyError,OSError,TypeError):
                    source=None
        findings=[]
        findings.append(Finding("source_fidelity","REVIEW_REQUIRED",
            "deterministic",f"source:{aid}",
            "original source passage location verified, scientific claim interpretation pending"
            if source else "original-source passage not independently verified for exact package"))
        try:
            errors=_answer_shape_defects(a)
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            # Malformed generated JSON must not abort the other activity audits.
            # Only an exception class is persisted, never sensitive content.
            errors=[f"invalid answer structure ({type(exc).__name__})"]
        findings.append(Finding("answer_correctness","FAIL" if errors else "REVIEW_REQUIRED",
            "deterministic",f"answer:{aid}",
            "; ".join(errors) if errors else "answer identifiers structurally consistent, physics of options not fully verified"))
        try:
            vis_errors=visual_contract_errors(repo_root,{**package,"activities":[a]},
                                               label=f"activity:{aid}")
        except (ValueError,OSError,KeyError,TypeError,AttributeError) as exc:
            vis_errors=["visual validation unavailable: "+type(exc).__name__]
        findings.append(Finding("visual_semantics","FAIL" if vis_errors else "REVIEW_REQUIRED",
            "deterministic",f"visual:{aid}",
            "; ".join(vis_errors[:3]) if vis_errors else
            "visual schema valid; rendered geometry and physical scientific meaning require independent review"))
        try:
            findings.append(check_multilingual_surface(a))
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            # A broken nested localization container is a concrete FAIL,
            # rather than discarding the audit of every other activity.
            findings.append(Finding(
                "multilingual_meaning","FAIL","deterministic",f"language:{aid}",
                f"invalid localized structure ({type(exc).__name__})",True))
        findings.append(Finding("physics_consistency","REVIEW_REQUIRED",
            "deterministic",f"physics:{aid}",
            "independent source-grounded scientific proof not yet supplied for this exact activity revision"))
        # An authorized code-level verifier may ADD independent evidence.
        # It cannot override demonstrated deterministic FAIL or masquerade
        # an AI-only response as a numerical/source proof.
        if not any(f.result=="FAIL" for f in findings):
            for gate,checker in trusted_verifiers.items():
                proof=checker(a,source)
                if not isinstance(proof,Finding) or proof.gate!=gate:
                    raise ValueError("trusted verifier returned wrong academic gate")
                if proof.result=="PASS" and gate=="source_fidelity" and source is None:
                    raise ValueError("source fidelity PASS requires independently verified exact PDF passage")
                if proof.result=="PASS":
                    findings=[f for f in findings if f.gate!=gate]
                findings.append(proof)
        decision=decide(findings)
        if decision["academicQA"]=="FAIL":
            action="AUTO_REPAIR"
        elif source is None:
            action="AUTO_SOURCE_CHECK"
        else:
            action="AUTO_RETRY"
        all_results.append({
            "activityId":aid,"type":a["type"],
            "activitySha256":sha256(json.dumps(a,sort_keys=True,ensure_ascii=False,
                separators=(",",":")).encode("utf-8")).hexdigest(),
            "academicQA":decision["academicQA"],
            "gates":decision["gates"],
            "sourcePages":source["verifiedPages"] if source else [],
            "sourceLocationVerified":source is not None,
            "answerStructureErrors":errors,
            "visualContractErrorCount":len(vis_errors),
            "nextAction":action,"humanReviewRequired":False,
            "publicationAuthorized":False,
        })
    statuses={label:sum(x["academicQA"]==label for x in all_results)
              for label in ("PASS","FAIL","REVIEW_REQUIRED")}
    return {
        "packageSha256":package_sha,"sourceSha256":source_sha256,
        "activityCount":len(acts),"counts":statuses,
        "activities":all_results,"academicQA":(
            "FAIL" if statuses["FAIL"] else
            "PASS" if statuses["PASS"]==len(acts) else "REVIEW_REQUIRED"),
        "humanAcademicApprovalRequired":False,"humanReviewed":False,
        "publicationAuthorized":False,
        "meaningOfReviewRequired":"automated source/physics/multilingual/visual follow-up, not mandatory human review",
    }
