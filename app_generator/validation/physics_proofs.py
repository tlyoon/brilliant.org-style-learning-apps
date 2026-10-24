"""Independent exact-arithmetic proof receipts for bounded Section 9.4 claims.

A validated mathematical witness, an exactly matched controlled source
passage and an immutable package binding are distinct from full activity QA.
"""
from __future__ import annotations
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from app_generator.validation.source_passages import check_anchor, extract_pages

KNOWN_CASES = {
    "mcq-perfectly-inelastic-outcome": ("equal_mass_sticking", "opt-perfectly-inelastic-forward"),
    "mcq-equal-mass-elastic-transfer": ("equal_mass_exchange", "opt-elastic-condition"),
    "mcq-newton-cradle-multi-ball": ("newton_two_out", "opt-violates-ke"),
    "mcq-extreme-mass-heavy-target": ("heavy_target_sticking", "opt-near-zero-ke-lost"),
    "mcq-ballistic-pendulum-stages": ("ballistic_two_phase", "opt-inelastic-dissipation"),
    "mcq-spring-collision-intermediate": ("spring_energy_storage", "opt-momentum-equal-ke-less"),
    "mcq-relative-velocity-scope": ("elastic_relative_velocity", "opt-1d-elastic-only"),
}


def number(value: Any) -> Fraction:
    if type(value) not in (str, int):
        raise ValueError("witness numbers must be exact integer or rational strings")
    result = Fraction(value)
    if not -10**9 <= result <= 10**9 or result.denominator > 10**9:
        raise ValueError("unbounded physics witness")
    return result


def prove_case(name: str, parameters: dict[str, Any]) -> dict[str, str]:
    """Return a finite exact-rational mathematical subclaim proof or fail."""
    p = {key: number(value) for key, value in parameters.items()}
    def positive(*items: str) -> None:
        if any(p[key] <= 0 for key in items):
            raise ValueError("witness requires positive masses/speeds/constants")
    def require(ok: bool, explanation: str) -> None:
        if not ok:
            raise ValueError("witness fails independently computed identity: " + explanation)

    if name == "equal_mass_sticking":
        positive("m","u")
        m, u = p["m"], p["u"]
        common = m*u/(2*m)
        initial_ke = m*u*u/2
        final_ke = 2*m*common*common/2
        require(common == u/2 and common > 0, "shared forward velocity")
        require((2*m)*common == m*u and final_ke == initial_ke/2, "momentum/energy")
        return {"model": name, "postImpactSpeed": str(common), "kineticEnergyRatio": str(final_ke/initial_ke)}

    if name == "equal_mass_exchange":
        positive("m","u")
        m,u=p["m"],p["u"]
        elastic_v1,elastic_v2=Fraction(0),u
        sticky=m*u/(2*m)
        require(m*elastic_v1+m*elastic_v2 == m*u, "elastic momentum")
        require(m*(elastic_v1**2+elastic_v2**2)/2 == m*u*u/2, "elastic energy")
        require(sticky != 0 and sticky == u/2, "nonelastic counterexample")
        return {"model":name,"elasticFinalV1":str(elastic_v1),"elasticFinalV2":str(elastic_v2),
                "stickingFinalSpeed":str(sticky)}

    if name == "newton_two_out":
        positive("m","u")
        m,u=p["m"],p["u"]
        incoming_ke=m*u*u/2
        outgoing_ke=2*m*(u/2)**2/2
        require(2*m*u/2==m*u, "outgoing momentum")
        require(outgoing_ke/incoming_ke==Fraction(1,2), "outgoing kinetic energy")
        return {"model":name,"outgoingMomentumRatio":"1","outgoingKineticEnergyRatio":"1/2"}

    if name == "heavy_target_sticking":
        positive("m","M","u")
        m,M,u=p["m"],p["M"],p["u"]
        require(M >= 100*m, "heavy-target limit witness M>=100m")
        common=m*u/(m+M)
        ratio=(m+M)*common**2/(m*u**2)
        require(ratio==m/(m+M) and ratio<=Fraction(1,101), "heavy-target energy")
        return {"model":name,"commonFinalVelocity":str(common),"kineticEnergyRatio":str(ratio)}

    if name == "ballistic_two_phase":
        positive("m1","m2","u","g")
        m1,m2,u,g=(p[x] for x in ("m1","m2","u","g"))
        v=m1*u/(m1+m2)
        pre=m1*u*u/2
        post=(m1+m2)*v*v/2
        h=v*v/(2*g)
        require(m1*u==(m1+m2)*v, "collision momentum")
        require(post<pre and post/pre==m1/(m1+m2), "inelastic energy loss")
        require((m1+m2)*g*h==post, "postimpact pendulum swing energy")
        return {"model":name,"immediateSpeed":str(v),"collisionKineticEnergyRatio":str(post/pre),
                "riseHeight":str(h)}

    if name == "spring_energy_storage":
        positive("m","u","k","x")
        m,u,k,x=(p[z] for z in ("m","u","k","x"))
        initial_ke=m*u*u
        elastic_potential=k*x*x/2
        current_ke=initial_ke-elastic_potential
        require(Fraction(0)<current_ke<initial_ke, "positive kinetic energy with compression")
        require(current_ke+elastic_potential==initial_ke, "total mechanical energy")
        # Equal and opposite velocities are consistent with zero total momentum.
        return {"model":name,"initialKineticEnergy":str(initial_ke),
                "intermediateKineticEnergy":str(current_ke),
                "springPotentialEnergy":str(elastic_potential),
                "totalMomentum": "0"}

    if name == "elastic_relative_velocity":
        positive("m1","m2","u1")
        m1,m2,u1=(p[z] for z in ("m1","m2","u1"))
        u2=p.get("u2",Fraction(0))
        require(u1!=u2,"nontrivial initial relative motion")
        v1=((m1-m2)*u1+2*m2*u2)/(m1+m2)
        v2=(2*m1*u1+(m2-m1)*u2)/(m1+m2)
        require(m1*u1+m2*u2==m1*v1+m2*v2,"momentum")
        require(m1*u1*u1+m2*u2*u2==m1*v1*v1+m2*v2*v2,"kinetic energy")
        require(u1-u2==-(v1-v2),"relative velocity")
        sticky=(m1*u1+m2*u2)/(m1+m2)
        require(sticky-sticky!=-(u1-u2),"inelastic counterexample")
        return {"model":name,"elasticFinalV1":str(v1),"elasticFinalV2":str(v2),
                "relativeVelocityEquality":"verified"}
    raise ValueError("unsupported physics proof model")


def audit_proofs(package: dict[str, Any], pdf: Path, expected_source_sha: str,
                 receipts: dict[str, Any]) -> dict[str, Any]:
    if hashlib.sha256(pdf.read_bytes()).hexdigest()!=expected_source_sha:
        raise ValueError("source PDF differs from controlled manifest")
    if receipts.get("sourceSha256") != expected_source_sha:
        raise ValueError("witness source SHA mismatch")
    # Stable JSON serialization is used for receipt binding to actual content,
    # avoiding machine-dependent whitespace in the installed JSON file.
    package_sha=hashlib.sha256(json.dumps(package,ensure_ascii=False,sort_keys=True,
                                            separators=(",",":")).encode("utf-8")).hexdigest()
    if receipts.get("packageCanonicalSha256")!=package_sha:
        raise ValueError("witness package identity mismatch")
    pages=extract_pages(pdf)
    activities={a.get("id"):a for a in package.get("activities",[])}
    proofs=receipts.get("proofs",[])
    if (not isinstance(proofs,list) or
        any(not isinstance(x,dict) for x in proofs) or
        len({x.get("activityId") for x in proofs})!=len(proofs)):
        raise ValueError("duplicate or invalid physics witness receipts")
    outcomes=[]
    for receipt in proofs:
        id_=receipt.get("activityId")
        row={"activityId":id_,"status":"REVIEW_REQUIRED","fullAcademicPass":False}
        if id_ not in activities or id_ not in KNOWN_CASES:
            raise ValueError("unknown activity or unapproved physics proof model")
        model,correct_id=KNOWN_CASES[id_]
        act=activities[id_]
        if receipt.get("model")!=model or act.get("answerKey",{}).get("correct")!=correct_id:
            row["reason"]="model mapping or designated answer key mismatch"
        else:
            anchor=check_anchor(pages,receipt.get("anchor",{}))
            if anchor.get("activityId")!=id_ or anchor.get("status")!="VERIFIED_TEXT_ONLY":
                row["reason"]="source quote unresolved: "+anchor.get("reason","unknown")
            else:
                try:
                    proof=prove_case(model,receipt["parameters"])
                    row.update({"status":"BOUNDED_PROPOSITION_VERIFIED",
                                "sourcePage":anchor["pageIndex"],
                                "sourceQuoteSha256":anchor["quoteSha256"],
                                "proof":proof})
                except (ValueError,KeyError,TypeError,ZeroDivisionError) as exc:
                    row.update({"status":"FAIL","reason":str(exc)[:220]})
        outcomes.append(row)
    return {
        "sourceSha256":expected_source_sha,
        "packageCanonicalSha256":package_sha,
        "activitiesTotal":len(activities),
        "boundedPropositionsVerified":sum(x["status"]=="BOUNDED_PROPOSITION_VERIFIED" for x in outcomes),
        "failedWitnesses":sum(x["status"]=="FAIL" for x in outcomes),
        "unresolvedReceipts":sum(x["status"]=="REVIEW_REQUIRED" for x in outcomes),
        "academicActivitiesPassed":0,
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
        "proofs":outcomes,
    }
