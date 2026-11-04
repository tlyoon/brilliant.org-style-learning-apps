"""Independent three-ball finite-stiffness contact-force counterexample.

Steel spheres deform during impact. A simultaneously compressed pair of
adjacent contacts can both exert positive forces; zero propagation range is
not a physical law. Static exact-rational force balance is rigorous for the
assumed linear compliant contact model. A finite discrete dynamic sequence
only illustrates overlapping compression, not an exact continuum solution.
This does not prove a rendered textbook figure or all natural-language QA.
"""
from __future__ import annotations
from fractions import Fraction as F
from typing import Any


def _forces(x: tuple[F,F,F], stiffness:F) -> tuple[F,F]:
    return (stiffness*max(F(0),x[0]-x[1]),
            stiffness*max(F(0),x[1]-x[2]))


def contact_chain_counterexample(
    *, stiffness:F=F(5), compression:F=F(1,100),
    step:F=F(1,20),
) -> dict[str,Any]:
    if (type(stiffness) is not F or type(compression) is not F or
        type(step) is not F or
        not F(0)<stiffness<=F(100) or
        not F(0)<compression<=F(1,10) or
        not F(0)<step<=F(1,10)):
        raise ValueError("positive bounded exact-rational contact parameters required")
    # Three equal balls held in static series contact by balanced applied
    # end loads. Both internal forces F12=F23=k*delta are positive at once.
    x_static=(compression*2,compression,F(0))
    f12,f23=_forces(x_static,stiffness)
    if f12!=f23 or f12<=0:
        raise ValueError("static middle-ball force balance invalid")
    # A separate *illustrative* impact with initially touching contacts:
    # ball 1 starts moving while balls 2 and 3 are stationary.
    # Symplectic Euler uses exact fractions but approximates continuum
    # contact dynamics, so it is not an exact trajectory proof.
    x=[F(0),F(0),F(0)]
    v=[F(1),F(0),F(0)]
    overlapping=False
    first_step_contact=False
    max_steps=8
    for i in range(max_steps):
        x=[p+step*vel for p,vel in zip(x,v)]
        f12,f23=_forces(tuple(x),stiffness)
        if i==0:
            first_step_contact=f12>0 and f23==0
        if f12>0 and f23>0:
            overlapping=True
        accelerations=(-f12,f12-f23,f23)
        v=[vel+step*a for vel,a in zip(v,accelerations)]
    if not first_step_contact or not overlapping:
        raise ValueError("multi-contact impact illustration failed")
    return {
       "model":"BOUNDED_THREE_BALL_COMPLIANT_CONTACT",
       "staticTwoSimultaneousContactForces":True,
       "staticEqualMiddleBallContactLoads":True,
       "exactStaticForceMagnitude":str(stiffness*compression),
       "finiteStepOverlapObserved":True,
       "finiteStepIsExactContinuumTrajectory":False,
       "sourceFigureMeaningAutomaticallyVerified":False,
       "textbookAcademicPASS":False,
    }
