"""Source-bound exact-rational counterexamples for every fixed MCQ option.

Finite witnesses do not verify whole-label semantics, locale translations,
contact-force propagation, figures, or formal academic accuracy.
"""
from __future__ import annotations
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.answer_integrity import check_answer_integrity
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.physics_proofs import KNOWN_CASES
from app_generator.validation.physics_receipt_generation import generate_bounded_physics_receipts

# Fixed original 27 distractor identities; correct keys sourced from KNOWN_CASES.
COUNTEREXAMPLES: dict[str, dict[str, str | None]] = {
 "mcq-collision-types-concept":{
  "opt-both-conserved":"inelastic","opt-ke-conserved-momentum-decreases":"inelastic",
  "opt-neither-conserved":"inelastic"},
 "mcq-impulse-approximation-basis":{
  "opt-external-forces-vanish":"external","opt-inelastic-breaks-momentum":"sticky",
  "opt-equal-masses-required":"unequal"},
 "mcq-perfectly-inelastic-outcome":{
  "opt-sticking-stops-dead":"sticky","opt-elastic-because-smooth":"sticky",
  "opt-general-inelastic-only":"sticky"},
 "mcq-equal-mass-elastic-transfer":{
  "opt-exchange-universal":"sticky","opt-equal-share":"elastic",
  "opt-rebound-both":"elastic"},
 "mcq-relative-velocity-scope":{
  "opt-universal-1d":"relative_sticky","opt-all-elastic-2d":"oblique",
  "opt-inelastic-sticky":"relative_sticky"},
 "mcq-extreme-mass-heavy-target":{
  "opt-ke-conserved":"heavy","opt-rebound-speed":"heavy",
  "opt-half-speed":"heavy"},
 "mcq-ballistic-pendulum-stages":{
  "opt-direct-energy":"ballistic","opt-momentum-lost-claim":"ballistic",
  "opt-rebound-condition":"elastic"},
 "mcq-newton-cradle-multi-ball":{
  "opt-ke-always":"cradle","opt-momentum-lost":"cradle",
  "opt-force-transmission":None},
 "mcq-spring-collision-intermediate":{
  "opt-ke-always-conserved":"spring","opt-momentum-not-conserved":"spring",
  "opt-both-decreased":"spring"},
}


def witness(case: str) -> dict[str, str]:
    """Compute exact finite collision laws, fail closed on inconsistent cases."""
    def check(ok: bool) -> None:
        if not ok:raise ValueError("invalid independent exact collision witness")
    if case=="inelastic":
        m1=m2=F(1); u=F(2); e=F(1,2)
        v1=(m1-e*m2)*u/(m1+m2);v2=m1*(1+e)*u/(m1+m2)
        p=m1*u;p1=m1*v1+m2*v2
        ki=m1*u*u/2;kf=(m1*v1*v1+m2*v2*v2)/2
        check(p==p1 and 0<kf<ki and v2-v1==e*u)
        data={"momentumBefore":p,"momentumAfter":p1,"keBefore":ki,"keAfter":kf}
    elif case=="external":
        j_internal=F(1000)*F(1,100)
        j_external=F(1)*F(1,100)
        check(j_external>0 and j_internal/j_external==1000)
        data={"internalImpulse":j_internal,"externalImpulse":j_external}
    elif case in ("sticky","relative_sticky"):
        m=F(2);u=F(4);v=m*u/(2*m)
        ki=m*u*u/2;kf=2*m*v*v/2
        check(v==2 and m*u==2*m*v and 0<kf<ki and (v-v)!=-u)
        data={"commonVelocity":v,"keBefore":ki,"keAfter":kf,
              "relativeBefore":u,"relativeAfter":F(0)}
    elif case=="unequal":
        m,M,u=F(1),F(5),F(4)
        v=m*u/(m+M)
        check(m!=M and (m+M)*v==m*u and (m+M)*v*v/2<m*u*u/2)
        data={"massRatio":m/M,"postImpactCommonVelocity":v}
    elif case=="elastic":
        m,u=F(2),F(4);v1,v2=F(0),u
        check(m*u==m*v1+m*v2 and m*u*u==m*v1*v1+m*v2*v2)
        data={"incidentAfter":v1,"targetAfter":v2,"initialSpeed":u}
    elif case=="oblique":
        # Elastic equal masses: (1,0)+(0,0) -> (1/2,1/2)+(1/2,-1/2).
        a=(F(1,2),F(1,2));b=(F(1,2),-F(1,2))
        p=(a[0]+b[0],a[1]+b[1])
        ki=F(1,2);kf=sum(v*v for v in (*a,*b))/2
        rel=(a[0]-b[0],a[1]-b[1])
        check(p==(1,0) and kf==ki and rel!=(-F(1),F(0)))
        data={"relativeAfterX":rel[0],"relativeAfterY":rel[1],"ke":kf}
    elif case=="heavy":
        m,M,u=F(1),F(100),F(5);v=m*u/(m+M)
        fraction=m/(m+M)
        check(M>=100*m and 0<v<u/2 and (m+M)*v==m*u and fraction==F(1,101))
        data={"commonVelocity":v,"kineticEnergyRetained":fraction}
    elif case=="ballistic":
        m,M,u,g=F(1),F(9),F(10),F(10)
        v=m*u/(m+M);ki=m*u*u/2;kf=(m+M)*v*v/2
        h=v*v/(2*g)
        check(v==1 and 0<kf<ki and m*u==(m+M)*v and (m+M)*g*h==kf)
        data={"momentumBefore":m*u,"momentumAfter":(m+M)*v,
              "keBefore":ki,"keAfter":kf,"postImpactHeight":h}
    elif case=="cradle":
        m,u=F(1),F(6);half=u/2
        pi=m*u;pf=2*m*half
        ki=m*u*u/2;kf=2*m*half*half/2
        check(pi==pf and kf==ki/2 and 0<kf<ki)
        data={"momentumBefore":pi,"momentumAfter":pf,"keBefore":ki,"keAfter":kf}
    elif case=="spring":
        m,u,k,x=F(2),F(3),F(2),F(2)
        p=m*u-m*u;ki=m*u*u;pe=k*x*x/2;k_mid=ki-pe
        check(p==0 and 0<k_mid<ki and k_mid+pe==ki)
        data={"momentum":p,"mechanicalEnergy":ki,"intermediateKE":k_mid,
              "springPotential":pe}
    else:raise ValueError("unsupported exact physics counterexample")
    return {key:str(value) for key,value in data.items()}


def audit_source_bound_all_mcq_options(*,package_file:Path,source_pdf:Path,
                                       source_packets_file:Path)->dict[str,Any]:
    source=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=source_packets_file,expected_count=18)
    raw=package_file.read_bytes()
    if (source["newlyReverifiedSourceActivities"]!=18 or
        source["packageSha256"]!=sha256(raw).hexdigest() or
        source["publicationAuthorized"] is not False):
        raise ValueError("controlled original source identity is not verified")
    receipt,existing=generate_bounded_physics_receipts(
        package_file,source_pdf,source_packets_file)
    if (existing["boundedPropositionsVerified"]!=9 or
        existing["failedWitnesses"]!=0 or existing["unresolvedReceipts"]!=0 or
        existing["publicationAuthorized"] is not False or
        receipt["sourceSha256"]!=source["sourceSha256"] or
        {r["activityId"] for r in existing["proofs"]
         if r["status"]=="BOUNDED_PROPOSITION_VERIFIED"}!=set(KNOWN_CASES)):
        raise ValueError("nine exact-source chosen-answer physics proofs incomplete")
    content=json.loads(raw.decode("utf-8"))
    mcqs={a["id"]:a for a in content["activities"] if a["type"]=="mcq"}
    if len(mcqs)!=9 or set(mcqs)!=set(KNOWN_CASES)!=set(COUNTEREXAMPLES):
        raise ValueError("source-bound MCQ activity roster changed")
    results=[]
    for aid,activity in mcqs.items():
        structural=check_answer_integrity(activity)
        if structural.result=="FAIL":
            raise ValueError("MCQ option text or identity not structurally valid")
        key=activity["answerKey"]
        chosen_model,chosen_id=KNOWN_CASES[aid]
        if key["correct"]!=chosen_id:
            raise ValueError("correct option differs from exact physics witness")
        expected=COUNTEREXAMPLES[aid]
        option_ids=[opt["id"] for opt in key["options"]]
        if (len(option_ids)!=4 or len(set(option_ids))!=4 or
            len(expected)!=3 or set(option_ids)!={chosen_id,*expected}):
            raise ValueError("original four-option physics roster altered")
        for oid in option_ids:
            if oid==chosen_id:
                kind="SELECTED_BOUNDED_PHYSICS_WITNESS"
                scenario=chosen_model; evidence={}
            else:
                scenario=expected[oid]
                if scenario is None:
                    kind="UNRESOLVED_CONTACT_FORCE_PROPAGATION"
                    scenario="OUTSIDE_POINT_MASS_COLLISION_MODEL"
                    evidence={}
                else:
                    kind="RATIONAL_COUNTEREXAMPLE_FOR_MAPPED_OPTION_ID"
                    evidence=witness(scenario)
                    if not evidence:raise ValueError("counterexample produced no witness")
            results.append({"activityId":aid,"optionId":oid,
                "boundedResult":kind,"witnessCase":scenario,
                "exactValues":evidence,"optionMeaningVerified":False})
    outcome={
        "sourceBoundSelectedOptionWitnesses":sum(
          x["boundedResult"]=="SELECTED_BOUNDED_PHYSICS_WITNESS" for x in results),
        "rationalCounterexamplesForDistractorIds":sum(
          x["boundedResult"]=="RATIONAL_COUNTEREXAMPLE_FOR_MAPPED_OPTION_ID" for x in results),
        "unresolvedPhysicalDistractors":sum(
          x["boundedResult"]=="UNRESOLVED_CONTACT_FORCE_PROPAGATION" for x in results),
    }
    if len(results)!=36 or outcome!={"sourceBoundSelectedOptionWitnesses":9,
        "rationalCounterexamplesForDistractorIds":26,
        "unresolvedPhysicalDistractors":1}:
        raise ValueError("bounded option coverage incomplete")
    return {"status":"SOURCE_BOUND_36_OPTION_BOUNDED_PHYSICS_REVIEW_ONLY",
        "sourceSha256":source["sourceSha256"],"packageSha256":source["packageSha256"],
        "originalSourceActivitiesReverified":18,"mcqActivitiesChecked":9,
        "mcqOptionsChecked":len(results),**outcome,
        "optionWordMeaningVerified":False,"multilingualMeaningVerified":False,
        "figureScientificSemanticsVerified":False,
        "academicQA":"REVIEW_REQUIRED","formalAcademicPASS":0,
        "publicationAuthorized":False,"options":results}
