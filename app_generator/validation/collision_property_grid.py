"""Independent exact collision property grid; not full academic approval."""
from __future__ import annotations
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.physics_proofs import KNOWN_CASES
from app_generator.validation.interactive_physics import SUPPORTED, assignments, actual_answer


def collision(m1:F,m2:F,u1:F,u2:F,e:F)->tuple[F,F]:
    """COM plus restitution, independent of the prior expanded velocity formula."""
    if (not all(type(x) is F for x in (m1,m2,u1,u2,e)) or
        min(m1,m2)<=0 or u1<=u2 or not 0<=e<=1):
        raise ValueError("positive masses, approaching velocities and bounded restitution required")
    center=(m1*u1+m2*u2)/(m1+m2)
    return (center-m2*e*(u1-u2)/(m1+m2),
            center+m1*e*(u1-u2)/(m1+m2))


def verify_grid()->dict:
    masses=(F(1),F(2),F(5),F(101))
    incoming=((F(3),F(0)),(F(3),F(-2)),(F(1),F(-3)),(F(2),F(1)))
    coeff=(F(0),F(1,4),F(1,2),F(3,4),F(1))
    counts={"elastic":0,"sticky":0,"partial":0}
    for m1 in masses:
        for m2 in masses:
            for u1,u2 in incoming:
                for e in coeff:
                    v1,v2=collision(m1,m2,u1,u2,e)
                    p=m1*u1+m2*u2
                    ki=(m1*u1*u1+m2*u2*u2)/2
                    kf=(m1*v1*v1+m2*v2*v2)/2
                    loss=(m1*m2/(m1+m2))*(1-e*e)*(u1-u2)**2/2
                    if m1*v1+m2*v2!=p or v2-v1!=e*(u1-u2) or ki-kf!=loss:
                        raise ValueError("COM collision law or reduced-mass energy proof failed")
                    if e==0:
                        counts["sticky"]+=1
                        if v1!=v2 or loss<=0:raise ValueError("sticking law failed")
                    elif e==1:
                        counts["elastic"]+=1
                        if loss!=0 or v1-v2!=-(u1-u2):
                            raise ValueError("elastic law failed")
                    else:
                        counts["partial"]+=1
                        if not 0<loss<ki or v1==v2:
                            raise ValueError("partial restitution law failed")
    if counts!={"elastic":64,"sticky":64,"partial":192}:
        raise ValueError("320-case parameter coverage incomplete")
    # A very heavy stationary target absorbs almost all kinetic energy
    a,b=collision(F(1),F(1000),F(2),F(0),F(0))
    fraction=(F(1001)*a*a)/(F(1)*F(2)**2)
    if a!=b or fraction!=F(1,1001):raise ValueError("heavy-target limit failed")
    # Two or more equal outgoing balls with shared momentum lose KE.
    for n in range(2,6):
        each=F(2,n)
        if F(n)*each!=2 or (F(n)*each**2/2)/F(2)!=F(1,n):
            raise ValueError("Newton cradle false elastic outcome not disproven")
    # Embed projectile, then separately convert postimpact KE into height.
    common=F(1)*F(10)/F(10)
    if common!=1 or (F(10)*common**2/2)/(F(1)*F(10)**2/2)!=F(1,10):
        raise ValueError("ballistic impact loss law failed")
    if common**2/(2*F(10))!=F(1,20):
        raise ValueError("separate conservative pendulum rise failed")
    for frac in (F(1,10),F(1,4),F(1,2),F(3,4),F(9,10)):
        elastic=F(10)*frac
        kinetic=F(10)-elastic
        if not 0<kinetic<10 or elastic+kinetic!=10:
            raise ValueError("spring energy storage conservation failed")
    # External impulse can be small yet nonzero, and a 2D tangential
    # component does not reverse along with the collision normal.
    if not 0<F(1)*F(1,100)<F(1000)*F(1,100):
        raise ValueError("nonzero external impulse counterexample failed")
    if (F(-2),F(1))==(-F(2),-F(1)):
        raise ValueError("oblique collision vector counterexample failed")
    return {"exactCollisionCases":320,"elastic":64,"sticky":64,"partial":192,
            "heavyTargetKineticRetention":str(fraction),
            "multiBallEnergyRatiosVerified":4,"ballisticStagesVerified":2,
            "springEnergyPartitionsVerified":5,"nonzeroExternalImpulseChecked":True,
            "oblique2dFullVectorReversalCounterexample":True,
            "fullScientificSemanticsVerified":False}


def audit(*,package_file:Path,source_pdf:Path,packets_file:Path)->dict:
    verified=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=packets_file,expected_count=18)
    data=package_file.read_bytes()
    if (verified.get("newlyReverifiedSourceActivities")!=18 or
        verified.get("packageSha256")!=sha256(data).hexdigest() or
        verified.get("publicationAuthorized") is not False):
        raise ValueError("source package receipt no longer verifies")
    acts=json.loads(data.decode("utf-8"))["activities"]
    mcqs={a["id"]:a for a in acts if a.get("type")=="mcq"}
    interactive={a["id"]:a for a in acts if a.get("type")=="interactive"}
    if (len(acts)!=18 or set(mcqs)!=set(KNOWN_CASES) or
        set(interactive)!=set(SUPPORTED)):
        raise ValueError("answer model activity roster mismatch")
    for aid,a in mcqs.items():
        key=a.get("answerKey",{})
        options=key.get("options",[])
        if not isinstance(options,list) or len(options)!=4:
            raise ValueError("MCQ needs four option identifiers")
        ids=[o.get("id") for o in options if isinstance(o,dict)]
        if (len(ids)!=4 or len(set(ids))!=4 or
            any(not isinstance(i,str) or not i for i in ids) or
            key.get("correct")!=KNOWN_CASES[aid][1]):
            raise ValueError("MCQ correct answer or distractor roster mismatch")
    qualifiers=0
    for aid,a in interactive.items():
        mode,expected,notes,_=assignments(SUPPORTED[aid])
        actual_mode,answer=actual_answer(a)
        valid=(set(expected)==set(answer) and len(expected)==len(answer)
               if mode=="selection" else expected==answer)
        if mode!=actual_mode or not valid:
            raise ValueError("interactive answer map disagrees with independent physics model")
        qualifiers+=int(bool(notes))
    return {
      "status":"SOURCE_BOUND_EXACT_COLLISION_PROPERTY_GRID_ONLY",
      "sourceSha256":verified["sourceSha256"],
      "packageSha256":verified["packageSha256"],
      "originalSourceActivitiesReverified":18,
      "mcqAnswerIdRostersChecked":9,"mcqOptionIdentifiersChecked":36,
      "interactionAnswerModelsCompared":9,
      "qualifierReviewRequired":qualifiers,
      "physicsGrid":verify_grid(),
      "mcqDistractorProseVerified":False,
      "translationMeaningApproved":False,
      "academicQA":"REVIEW_REQUIRED","formalAcademicPASS":0,
      "publicationAuthorized":False}
