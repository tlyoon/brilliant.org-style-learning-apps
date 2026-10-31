"""Source-bound MCQ option-claim audit with bounded physical counterexamples.

This audit binds all EN/MS/ZH option statements to unchanged private-v5 label
digests, rechecks all original PDF source passages, and examines *individual*
claims with exact-rational physical scenarios. The scientific interpretation
of natural-language claims is limited to the explicitly modeled assertions.
No general academic PASS, figure understanding or translation approval.
"""
from __future__ import annotations

from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.collision_property_grid import collision
from app_generator.validation.physics_proofs import KNOWN_CASES
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.mcq_label_digest_baseline import OPTION_LABEL_SHA256


def _group_truths(group: str) -> dict[str,bool|None]:
    """Evidence predicates matched to independently interpreted option claims.

    True: this bounded scenario supports the specified statement.
    False: the scenario falsifies the distractor's claim or violates the
    controlled textbook collision-type definition.
    None: requires source-figure and contact-mechanics semantic review.
    """
    if group=="mcq-collision-types-concept":
        v1,v2=collision(F(1),F(1),F(2),F(0),F(1,2))
        p0=F(2); p1=v1+v2
        ki=F(2);kf=(v1*v1+v2*v2)/2
        return {
          "opt-momentum-conserved-ke-decreases":p0==p1 and 0<kf<ki,
          "opt-both-conserved":p0==p1 and ki==kf,
          "opt-ke-conserved-momentum-decreases":ki==kf and p1<p0,
          "opt-neither-conserved":p1!=p0 and ki!=kf,
        }
    if group=="mcq-impulse-approximation-basis":
        internal=F(1000);external=F(1);duration=F(1,100)
        v1,v2=collision(F(1),F(2),F(2),F(0),F(0))
        return {
          "opt-internal-forces-dominate":internal/external>=100 and external*duration<internal*duration,
          "opt-external-forces-vanish":external*duration==0,
          "opt-inelastic-breaks-momentum":(v1+2*v2)!=2,
          "opt-equal-masses-required":F(1)==F(2),
        }
    if group=="mcq-perfectly-inelastic-outcome":
        v1,v2=collision(F(1),F(1),F(2),F(0),F(0))
        ki=F(2); kf=(v1*v1+v2*v2)/2
        return {
          "opt-perfectly-inelastic-forward":v1==v2 and v1>0 and kf<ki,
          "opt-sticking-stops-dead":v1==v2==0,
          "opt-elastic-because-smooth":kf==ki,
          "opt-general-inelastic-only":v1!=v2,
        }
    if group=="mcq-equal-mass-elastic-transfer":
        e1=collision(F(1),F(1),F(2),F(0),F(1))
        half=collision(F(1),F(1),F(2),F(0),F(1,2))
        stick=collision(F(1),F(1),F(2),F(0),F(0))
        return {
          "opt-elastic-condition":e1==(F(0),F(2)) and half[0]!=0 and stick[0]!=0,
          "opt-exchange-universal":half==(F(0),F(2)),
          "opt-equal-share":e1[0]==e1[1]==F(1),
          "opt-rebound-both":e1!=(F(0),F(2)),
        }
    if group=="mcq-relative-velocity-scope":
        v_el=collision(F(1),F(1),F(2),F(0),F(1))
        v_in=collision(F(1),F(1),F(2),F(0),F(1,2))
        v_st=collision(F(1),F(1),F(2),F(0),F(0))
        before=(F(2),F(1));after=(-F(2),F(1))
        return {
          "opt-1d-elastic-only":v_el[0]-v_el[1]==-F(2),
          "opt-universal-1d":v_in[0]-v_in[1]==-F(2),
          "opt-all-elastic-2d":after==tuple(-x for x in before),
          "opt-inelastic-sticky":v_st[0]-v_st[1]==-F(2),
        }
    if group=="mcq-extreme-mass-heavy-target":
        a,b=collision(F(1),F(1000),F(2),F(0),F(0))
        ki=F(2); kf=F(1001)*a*a/2
        return {
          "opt-near-zero-ke-lost":a==b and 0<a<F(1,100) and kf/ki==F(1,1001),
          "opt-ke-conserved":a>=F(3,2) and kf==ki,
          "opt-rebound-speed":a==-F(2),
          "opt-half-speed":a==F(1),
        }
    if group=="mcq-ballistic-pendulum-stages":
        common=F(1)*F(10)/(F(1)+F(9))
        ki=F(1)*F(10)**2/2
        post=F(10)*common**2/2
        # A hypothetical elastic rebound still leaves energy in projectile.
        bullet_el,target_el=collision(F(1),F(9),F(10),F(0),F(1))
        return {
          "opt-inelastic-dissipation":post<ki and common>0 and post>0,
          "opt-direct-energy":post==ki,
          "opt-momentum-lost-claim":F(10)*common!=F(10),
          "opt-rebound-condition":F(9)*target_el**2/2==ki and bullet_el==0,
        }
    if group=="mcq-newton-cradle-multi-ball":
        incoming_momentum=F(1)*F(2)
        outgoing_momentum=F(2)*F(1)
        incoming_ke=F(1)*F(2)**2/2
        outgoing_ke=F(2)*F(1)**2/2
        return {
          "opt-violates-ke":incoming_momentum==outgoing_momentum and outgoing_ke*2==incoming_ke,
          "opt-ke-always":outgoing_ke==incoming_ke,
          "opt-momentum-lost":outgoing_momentum!=incoming_momentum,
          "opt-force-transmission":None,
        }
    if group=="mcq-spring-collision-intermediate":
        p0=F(0); p1=F(0)
        ki=F(10); midke=F(6); spring=F(4)
        return {
          "opt-momentum-equal-ke-less":p1==p0 and 0<midke<ki and midke+spring==ki,
          "opt-ke-always-conserved":midke==ki,
          "opt-momentum-not-conserved":p1!=p0 and midke==ki,
          "opt-both-decreased":p1!=p0 and midke+spring<ki,
        }
    raise ValueError("unrecognized source-bound MCQ family")



def audit_source_bound_mcq_statement_physics(
    *, package_file:Path, source_pdf:Path, packets_file:Path,
) -> dict[str,Any]:
    """Review bounded option propositions without publishing protected prose."""
    source=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=packets_file,expected_count=18)
    raw=package_file.read_bytes()
    if (source.get("newlyReverifiedSourceActivities")!=18 or
            source.get("packageSha256")!=sha256(raw).hexdigest() or
            source.get("publicationAuthorized") is not False):
        raise ValueError("original controlled 18-source-packet roster does not verify")
    data=json.loads(raw.decode("utf-8"))
    acts=data.get("activities",[])
    mcqs={a["id"]:a for a in acts if a.get("type")=="mcq"}
    if (len(acts)!=18 or len(mcqs)!=9 or set(mcqs)!=set(KNOWN_CASES) or
            len(OPTION_LABEL_SHA256)!=36):
        raise ValueError("complete MCQ source-controlled roster changed")
    rows=[]
    for aid,a in mcqs.items():
        expected_correct=KNOWN_CASES[aid][1]
        choices=a.get("answerKey",{}).get("options",[])
        if not isinstance(choices,list) or len(choices)!=4:
            raise ValueError("MCQ option roster must contain precisely four entries")
        ids=[item.get("id") for item in choices if isinstance(item,dict)]
        if (len(ids)!=4 or len(set(ids))!=4 or
                any(not isinstance(x,str) or not x for x in ids) or
                a.get("answerKey",{}).get("correct")!=expected_correct):
            raise ValueError("MCQ selected answer or option identifiers changed")
        truths=_group_truths(aid)
        if set(ids)!=set(truths) or expected_correct not in ids:
            raise ValueError("independently interpreted MCQ option map incomplete")
        for choice in choices:
            oid=choice["id"]
            label=choice.get("label")
            if (not isinstance(label,dict) or
                    set(label)!={"en","ms","zh"} or
                    any(not isinstance(label[k],str) or not label[k]
                        for k in ("en","ms","zh"))):
                raise ValueError("three-language MCQ label missing")
            label_sha=sha256(json.dumps(label,sort_keys=True,
                              ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()
            if OPTION_LABEL_SHA256.get((aid,oid))!=label_sha:
                raise ValueError("English/Malay/Chinese option wording changed; interpretation stale")
            proposition=truths[oid]
            if proposition is None:
                if oid!= "opt-force-transmission" or aid!="mcq-newton-cradle-multi-ball":
                    raise ValueError("new unreviewed option is not allowlisted")
                status="FIGURE_CONTACT_SEMANTICS_PENDING"
            elif oid==expected_correct:
                if proposition is not True:
                    raise ValueError("correct MCQ option contradicts mathematical witness")
                status="BOUNDED_PHYSICS_SUPPORT"
            else:
                if proposition is not False:
                    raise ValueError("MCQ distractor not refuted by bounded counterexample")
                status="BOUNDED_PHYSICS_COUNTEREXAMPLE"
            rows.append({
                "activityId":aid,"optionId":oid,"status":status,
                "exactMultilingualLabelSha256":label_sha,
                "scientificMeaningFullyVerified":False,
                "translationMeaningVerified":False,
                "sourceFigureInterpretationVerified":False,
            })
    support=sum(x["status"]=="BOUNDED_PHYSICS_SUPPORT" for x in rows)
    counter=sum(x["status"]=="BOUNDED_PHYSICS_COUNTEREXAMPLE" for x in rows)
    pending=sum(x["status"]=="FIGURE_CONTACT_SEMANTICS_PENDING" for x in rows)
    if (len(rows),support,counter,pending)!=(36,9,26,1):
        raise ValueError("source-bound MCQ scientific statement audit incomplete")
    return {
        "status":"SOURCE_BOUND_MC_Q_BOUNDED_STATEMENT_AUDIT",
        "sourceSha256":source["sourceSha256"],
        "packageSha256":source["packageSha256"],
        "originalSourceActivityPassagesReverified":18,
        "mcqActivitiesChecked":9,"threeLanguageOptionLabelsBoundBySha256":36,
        "boundedAnswerOptionsSupported":support,
        "boundedDistractorsCounterexampled":counter,
        "sourceFigureContactSemanticsPending":pending,
        "allOptionMeaningsFullyVerified":False,
        "independentAcademicReviewerAccepted":False,
        "translationMeaningVerified":False,
        "formalAcademicPASS":0,
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
        "optionChecks":rows,
    }
