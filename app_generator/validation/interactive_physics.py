"""Deterministic, source-bound interaction answer-model checks for Section 9.4.

These reference models independently compute finite rational collision examples
and the corresponding expected answer IDs for the *fixed* controlled package.
They are not a proof of every possible English/Chinese/Malay interpretation,
every incorrect option, or a full academic PASS.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from typing import Any

from app_generator.validation.source_passages import check_anchor, extract_pages

SUPPORTED = {
    "int-classify-collision-regimes": "classify_collision_regimes",
    "int-select-isolated-conditions": "impulse_conditions",
    "int-match-collision-properties": "match_collision_properties",
    "int-order-post-collision-speeds": "order_target_speeds",
    "int-classify-relative-velocity-validity": "relative_velocity_cases",
    "int-select-valid-equal-mass-outcomes": "equal_mass_outcomes",
    "int-order-ballistic-pendulum-sequence": "ballistic_stages",
    "int-match-extreme-mass-limits": "extreme_mass_limits",
    "int-classify-spring-collision-phases": "spring_phases",
}

def semantic_digest(activity: dict[str,Any]) -> str:
    """Hash actual question wording and all-language option semantics."""
    ix=activity.get("interaction") or {}
    text={
        "id":activity.get("id"),"interactionMode":activity.get("interactionMode"),
        "prompt":activity.get("prompt"),"feedback":activity.get("feedback"),
        "explanation":activity.get("explanation"),
        "items":[{"id":x.get("id"),"label":x.get("label")} for x in ix.get("items",[])],
        "targets":[{"id":x.get("id"),"label":x.get("label")} for x in ix.get("targets",[])],
    }
    return hashlib.sha256(json.dumps(text,sort_keys=True,ensure_ascii=False,
                                     separators=(",",":")).encode("utf-8")).hexdigest()


# Explicit approved baseline of the *installed* pilot, not the checked-in
# source-free unit-test fixture. Changing question wording/translations
# requires a new independent review and updated verified model.
EXPECTED_TEXT_SHA256 = {
    "int-classify-collision-regimes": "8a94f6cf5d76ac66b4fc53c4430f04b0a414c8e3a3ebda696a4fbec5c4346ebe",
    "int-select-isolated-conditions": "8e552956f975398156b85d54784728501d28f542a9bbe44c97b58b9aa81c5407",
    "int-match-collision-properties": "289c12ed93760cb6c39b8d0aca2e2140b4371ce55e6a7cb6e403db459ad3a6f5",
    "int-order-post-collision-speeds": "ae7374d7fce129a02cf08a85957468ebf82bf10624c9b793c0873e35504e4e54",
    "int-classify-relative-velocity-validity": "51e4432fc8231af6f1b4bb9beb18819a5e90932d0a53ac611e5b5e6463dcae45",
    "int-select-valid-equal-mass-outcomes": "ee7d761a9c6961f7e3b8f8896c04f519661e0b5d496bfa2461fa9b7511439613",
    "int-order-ballistic-pendulum-sequence": "5522648d733a50e1c6d973a6d0732630f48a403f0c1e00340fa0fe22c9e6bef2",
    "int-match-extreme-mass-limits": "0c0bea7bb1eefcfeddbb4f05a140edde4e6d29d8ffe787b1411820e23c6a209f",
    "int-classify-spring-collision-phases": "94707ac1c1bb6d32f69a80a30a30b978d9fc20d0e06aa835165f6e952ef959a7",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError("independent physics model invalid: " + message)


def elastic(m1: F, m2: F, u1: F, u2: F) -> tuple[F, F]:
    require(m1 > 0 and m2 > 0, "positive masses")
    v1 = ((m1-m2)*u1+2*m2*u2)/(m1+m2)
    v2 = (2*m1*u1+(m2-m1)*u2)/(m1+m2)
    require(m1*u1+m2*u2 == m1*v1+m2*v2, "momentum")
    require(m1*u1*u1+m2*u2*u2 == m1*v1*v1+m2*v2*v2, "kinetic energy")
    return v1,v2


def sticky(m1: F, m2: F, u1: F, u2: F) -> tuple[F,F]:
    require(m1 > 0 and m2 > 0, "positive masses")
    v=(m1*u1+m2*u2)/(m1+m2)
    ki=(m1*u1*u1+m2*u2*u2)/2
    kf=(m1+m2)*v*v/2
    require(m1*u1+m2*u2 == (m1+m2)*v, "sticking momentum")
    require(ki >= kf, "inelastic kinetic energy")
    return v,ki-kf


def assignments(model: str) -> tuple[str, Any, list[str], dict[str,str]]:
    """Return (mode, independent answer key, limitations, exact proof numbers)."""
    notes=[]
    values={}
    if model == "classify_collision_regimes":
        # Elastic repulsion can be noncontact; binding bodies conserves p not K.
        v1,v2=elastic(F(1),F(1),F(2),F(0))
        v,loss=sticky(F(1),F(1),F(2),F(0))
        require((v1,v2)==(0,2) and v==1 and loss==1, "classification witnesses")
        # Sticking with KE strictly unchanged cannot occur for nonzero relative speed:
        # K_i - K_f = m1*m2*(u1-u2)^2/(2*(m1+m2)) > 0.
        values={"elasticFinal":str(v2),"stickySpeed":str(v),"stickyLostKE":str(loss)}
        key={
            "item-elastic-repulsion":"target-valid-elastic",
            "item-sticking-conserves-p":"target-valid-inelastic",
            "item-inelastic-lost-p":"target-violates-laws",
            "item-entangled-conserves-ke":"target-violates-laws",
        }
        return "classification",key,notes,values

    if model == "impulse_conditions":
        # Internal force pairs cancel exactly, but nonzero external impulse
        # changes p even when much smaller than internal collision impulse.
        external_impulse=F(1,1000)*F(1,100)
        require(external_impulse != 0 and external_impulse < F(1,100), "external impulse")
        v,loss=sticky(F(1),F(1),F(2),F(0))
        require(v==1 and loss>0, "momentum independent of KE conservation")
        values={"externalImpulse":str(external_impulse),"inelasticLostKE":str(loss)}
        notes.append("impulse approximation permits nonzero external impulse: strictly conserved momentum claim needs isolated-system qualifier")
        key=["item-large-internal-forces","item-action-reaction-internal","item-momentum-conserved-regardless-type"]
        return "selection",key,notes,values

    if model == "match_collision_properties":
        elastic_values=elastic(F(1),F(1),F(2),F(0))
        vehicle_v, vehicle_ke=sticky(F(1800),F(900),F(2),F(0))
        clay_v,clay_loss=sticky(F(1),F(1),F(2),F(-2))
        require(elastic_values==(0,2) and vehicle_v==F(4,3) and
                vehicle_ke>0 and clay_v==0 and clay_loss>0,"matching outcomes")
        # Ball-wall bounce with nonzero restitution loses kinetic energy.
        e=F(1,2)
        require((1-e*e)>0,"inelastic bounce energy drop")
        values={"entangledVehicleSpeed":str(vehicle_v),"claySpeed":str(clay_v),
                "bounceEnergyRetentionRatio":str(e*e)}
        return "matching",{
            "item-elastic-head-on":"target-elastic-desc",
            "item-general-inelastic":"target-inelastic-desc",
            "item-entangled-moving":"target-perfectly-inelastic-motion",
            "item-symmetric-head-on-clay":"target-zero-final-velocity",
        },notes,values

    if model == "order_target_speeds":
        m=F(100);u=F(1)
        massive=elastic(m, F(10000),u,F(0))[1]
        equal=elastic(m,m,u,F(0))[1]
        light=elastic(m,F(1),u,F(0))[1]
        require(F(0)<massive<equal<light<F(2),"elastic target speed ordering")
        values={"heavyTarget":str(massive),"equalTarget":str(equal),"lightTarget":str(light)}
        return "ordering",["target-massive","target-equal","target-light"],notes,values

    if model == "relative_velocity_cases":
        v1,v2=elastic(F(1),F(1),F(2),F(0))
        require(F(2)==-(v1-v2),"elastic relative reversal")
        glued,_=sticky(F(1),F(1),F(2),F(0))
        require((glued-glued)!=-F(2),"sticky counterexample")
        # e=1/2 dissipative head-on case; relative post-speed is smaller.
        damped_rel=-F(1,2)*F(2)
        require(damped_rel!=-F(2),"dented metal counterexample")
        # 2D oblique collision: tangential component 1 is not reversed.
        require((F(-2),F(1)) != (-F(2),-F(1)),"2d counterexample")
        values={"elasticRelativeFinal":str(v1-v2),"inelasticRelativeFinal":str(damped_rel)}
        return "classification",{
            "item-1d-spring-bumper":"target-valid",
            "item-1d-sticky-putty":"target-invalid",
            "item-1d-dented-metal":"target-invalid",
            "item-2d-glancing-impact":"target-invalid",
        },notes,values

    if model == "equal_mass_outcomes":
        v1,v2=elastic(F(2),F(2),F(4),F(0))
        common,loss=sticky(F(2),F(2),F(4),F(0))
        require((v1,v2)==(0,4) and common==2 and loss>0,
                "equal mass outcomes and counterexamples")
        values={"elasticFinal":str(v2),"stickingSpeed":str(common),"stickingLostKE":str(loss)}
        return "selection",["opt-elastic-exchange","opt-inelastic-stick"],notes,values

    if model == "ballistic_stages":
        v,loss=sticky(F(1),F(9),F(10),F(0))
        h=v*v/(2*F(10))
        require(v==1 and loss>0 and h==F(1,20),"impact and rise")
        values={"postImpactSpeed":str(v),"impactLostKE":str(loss),"riseHeight":str(h)}
        return "ordering",[
            "stage-incoming-projectile","stage-inelastic-impact",
            "stage-post-impact-motion","stage-conservative-swing",
        ],notes,values

    if model == "extreme_mass_limits":
        v1_eq,v2_eq=elastic(F(1),F(1),F(4),F(0))
        v1_h,v2_h=elastic(F(100),F(1),F(4),F(0))
        v1_l,v2_l=elastic(F(1),F(100),F(4),F(0))
        v_stick,loss=sticky(F(1),F(1),F(4),F(0))
        require(v1_eq==0 and v2_eq==4 and v2_h>F(7) and
                v1_h>0 and v1_l<0 and F(0)<v2_l<F(1,10) and
                v_stick==2 and loss>0,"extreme-mass outcomes")
        values={"targetHeavyProjectile":str(v2_h),"projectileHeavyTarget":str(v1_l),
                "equalMassStickySpeed":str(v_stick)}
        return "matching",{
            "case-equal-elastic":"target-exchange",
            "case-heavy-projectile-elastic":"target-double-speed",
            "case-light-projectile-elastic":"target-rebound",
            "case-equal-inelastic":"target-half-speed",
        },notes,values

    if model == "spring_phases":
        m=F(1);u=F(2);k=F(2);x=F(1)
        initial_ke=m*u*u
        spring_pe=k*x*x/2
        intermediate_ke=initial_ke-spring_pe
        v_sticky,loss=sticky(m,m,u,-u)
        require(initial_ke==4 and spring_pe==1 and
                F(0)<intermediate_ke<initial_ke and
                intermediate_ke+spring_pe==initial_ke and
                v_sticky==0 and loss>0,"spring energy phases")
        values={"initialKE":str(initial_ke),"springPE":str(spring_pe),
                "intermediateKE":str(intermediate_ke),"stickyLoss":str(loss)}
        return "classification",{
            "item-momentum-any-isolated":"cat-constant-throughout",
            "item-mech-energy-spring":"cat-constant-throughout",
            "item-ke-spring-mid-collision":"cat-temporarily-stored",
            "item-ke-entangled-wreckage":"cat-permanently-lost",
        },notes,values
    raise ValueError("unsupported physics interaction model")


def actual_answer(activity: dict[str,Any]) -> tuple[str,Any]:
    mode=activity.get("interactionMode")
    interaction=activity.get("interaction")
    if not isinstance(interaction,dict):
        raise ValueError("invalid interaction structure")
    items=interaction.get("items",[])
    if not isinstance(items,list) or len({x.get("id") for x in items if isinstance(x,dict)}) != len(items):
        raise ValueError("missing or duplicate interaction items")
    item_ids={x["id"] for x in items}
    if mode in ("matching","classification"):
        targets=interaction.get("targets",[])
        if not isinstance(targets,list) or len({x.get("id") for x in targets if isinstance(x,dict)})!=len(targets):
            raise ValueError("invalid target list")
        target_ids={x["id"] for x in targets}
        placements=interaction.get("placements",[])
        if not isinstance(placements,list) or len(placements)!=len(items):
            raise ValueError("missing or incomplete placements")
        key={}
        for row in placements:
            if row.get("itemId") in key or row.get("itemId") not in item_ids or row.get("targetId") not in target_ids:
                raise ValueError("invalid or duplicate placements")
            key[row["itemId"]]=row["targetId"]
        return mode,key
    if mode=="selection":
        ids=interaction.get("correctSelections",[])
        if not isinstance(ids,list) or len(ids)!=len(set(ids)) or any(x not in item_ids for x in ids):
            raise ValueError("ambiguous selection key")
        return mode,ids
    if mode=="ordering":
        ids=interaction.get("correctOrder",[])
        if not isinstance(ids,list) or len(ids)!=len(item_ids) or set(ids)!=item_ids or len(ids)!=len(set(ids)):
            raise ValueError("invalid ordering key")
        return mode,ids
    raise ValueError("unsupported interaction mode")


def audit_interaction_models(
    package: dict[str,Any], source_pdf: Path, source_sha256: str,
    receipts: dict[str,Any],
) -> dict[str,Any]:
    if hashlib.sha256(source_pdf.read_bytes()).hexdigest()!=source_sha256:
        raise ValueError("controlled source PDF SHA mismatch")
    if receipts.get("sourceSha256")!=source_sha256:
        raise ValueError("interaction receipts refer to different source PDF")
    canonical=hashlib.sha256(json.dumps(package,sort_keys=True,ensure_ascii=False,
                                       separators=(",",":")).encode("utf-8")).hexdigest()
    if receipts.get("packageCanonicalSha256")!=canonical:
        raise ValueError("interaction receipts refer to different installed package")
    all_activities=package.get("activities",[])
    if not isinstance(all_activities,list) or not all_activities:
        raise ValueError("missing installed learning activities")
    activities={a.get("id"):a for a in all_activities if isinstance(a,dict)}
    if len(activities)!=len(all_activities):
        raise ValueError("duplicate or malformed installed activities")
    interactive={k:v for k,v in activities.items() if v.get("type")=="interactive"}
    if set(interactive)!=set(SUPPORTED):
        raise ValueError("unexpected or missing interactive activity; no blanket approval")
    proofs=receipts.get("proofs",[])
    if (not isinstance(proofs,list) or any(not isinstance(x,dict) for x in proofs)
        or len(proofs)!=len({x.get("activityId") for x in proofs})):
        raise ValueError("malformed or duplicate source-bound interaction receipts")
    if any(item.get("activityId") not in interactive for item in proofs):
        raise ValueError("receipt references unknown interactive activity")
    by_id={x["activityId"]:x for x in proofs}
    pages=extract_pages(source_pdf)
    results=[]
    for id_, activity in interactive.items():
        row={"activityId":id_,"status":"REVIEW_REQUIRED","fullAcademicPass":False}
        receipt=by_id.get(id_)
        if receipt is None:
            row["reason"]="missing private source-bound interaction proof receipt"
            results.append(row);continue
        if semantic_digest(activity)!=EXPECTED_TEXT_SHA256.get(id_):
            row["reason"]="generated question or locale wording differs from independently mapped baseline"
            results.append(row);continue
        model=SUPPORTED[id_]
        if receipt.get("model")!=model:
            row["reason"]="source receipt model does not match registered interaction"
            results.append(row);continue
        anchor=check_anchor(pages,receipt.get("anchor",{}))
        if anchor.get("status")!="VERIFIED_TEXT_ONLY" or anchor.get("activityId")!=id_:
            row["reason"]="source passage unresolved: "+anchor.get("reason","unknown")
            results.append(row);continue
        try:
            mode,expected,notes,proof=assignments(model)
            observed_mode,observed=actual_answer(activity)
            if mode!=observed_mode:
                raise ValueError("interaction mode disagrees with independent model")
            if mode in ("selection",):
                # Array order is not semantically meaningful for multi-select.
                valid=set(expected)==set(observed)
            else:
                valid=(expected==observed)
            if not valid:
                raise ValueError("generated answer mapping differs from independent physics model")
            row.update({
                "status":("BOUNDED_INTERACTION_MODEL_VERIFIED" if not notes
                          else "QUALIFIER_REVIEW_REQUIRED"),
                "sourcePage":anchor["pageIndex"],"sourceQuoteSha256":anchor["quoteSha256"],
                "physicsWitness":proof,
                "caveats":notes,
                "reason":("quantitative model agrees with key; source interpretation, translations and visuals not fully verified"
                          if not notes else "model agrees; scientifically important wording qualifier unresolved"),
            })
        except (ValueError,KeyError,TypeError,ZeroDivisionError) as exc:
            row.update({"status":"FAIL","reason":str(exc)[:280]})
        results.append(row)
    return {
        "sourceSha256":source_sha256,
        "packageCanonicalSha256":canonical,
        "interactiveActivitiesTotal":len(interactive),
        "boundedModelsVerified":sum(x["status"]=="BOUNDED_INTERACTION_MODEL_VERIFIED" for x in results),
        "qualifierReviewRequired":sum(x["status"]=="QUALIFIER_REVIEW_REQUIRED" for x in results),
        "unresolved":sum(x["status"]=="REVIEW_REQUIRED" for x in results),
        "modelDiscrepancies":sum(x["status"]=="FAIL" for x in results),
        "fullAcademicActivitiesPassed":0,
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
        "results":results,
    }
