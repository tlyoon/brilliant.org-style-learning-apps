"""Independent numerical check of a supplied isolated one-dimensional collision witness.

This checks the stated numeric model, not whether the textbook actually supports
the witness or whether an activity's verbal answer is correct.
"""
from __future__ import annotations
import math
from collections.abc import Mapping
from app_generator.validation.academic_qa import Finding

def check_collision_witness(witness: Mapping | None, evidence_ref: str) -> Finding:
    gate = "physics_consistency"
    if not isinstance(witness, Mapping):
        return Finding(gate, "REVIEW_REQUIRED", "not_available", evidence_ref, "no independent numerical witness")
    try:
        mode = witness["collisionType"]
        if mode not in ("elastic", "inelastic", "perfectly_inelastic"):
            raise ValueError("unknown collision type")
        m1, m2, u1, u2, v1, v2 = (witness[k] for k in ("m1","m2","u1","u2","v1","v2"))
        numbers=(m1,m2,u1,u2,v1,v2)
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in numbers):
            raise ValueError("nonfinite or nonnumeric quantities")
        if m1 <= 0 or m2 <= 0:
            raise ValueError("masses must be strictly positive")
    except (KeyError, TypeError, ValueError) as exc:
        return Finding(gate, "REVIEW_REQUIRED", "invalid_witness", evidence_ref, f"cannot verify witness: {exc}")
    initial_momentum=m1*u1+m2*u2
    final_momentum=m1*v1+m2*v2
    initial_ke=(m1*u1*u1+m2*u2*u2)/2
    final_ke=(m1*v1*v1+m2*v2*v2)/2
    def close(a,b):
        return abs(a-b) <= 1e-9*max(1,abs(a),abs(b))
    mismatches=[]
    if not close(initial_momentum, final_momentum): mismatches.append("momentum")
    if mode == "elastic" and not close(initial_ke,final_ke): mismatches.append("kinetic_energy")
    if mode == "perfectly_inelastic" and not close(v1,v2): mismatches.append("shared_final_velocity")
    if mode != "elastic" and final_ke > initial_ke + 1e-9*max(1,abs(initial_ke)):
        mismatches.append("spontaneous_kinetic_energy_gain")
    if mismatches:
        return Finding(gate, "FAIL", "deterministic", evidence_ref,
                       "numerical collision model contradicts "+", ".join(mismatches), True)
    return Finding(gate,"PASS","deterministic",evidence_ref,
                   "supplied collision witness obeys the tested isolated-system conservation laws; source applicability unverified",True)
