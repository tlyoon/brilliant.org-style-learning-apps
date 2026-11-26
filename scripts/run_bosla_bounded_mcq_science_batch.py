"""BSA275: real owner one-textbook MCQ science batch pilot (read only).

Reopen the original owner Serway source, frozen candidate, signed V36 and
A1/A2 immutable academic receipts before dispatching any batch. The first
eligible opt-d directional-momentum countermodel receives a fresh source-
derived formal witness. Every unsupported task remains unadmitted.

This is NOT the separate academic receipt admission and changes no user data,
source PDF, public PR or model-provider state. Does not run a scheduler.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from app_generator.runtime.v3_academic_proof_registry import (
    audit_source_bound_academic_registry,
)
from app_generator.runtime.v3_first_academic_proof_admission import (
    _bound_inputs,
)
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,
)
from app_generator.validation.academic_science_batch_execution import (
    ScienceBatchRule, plan_next_science_batch,execute_source_bound_science_batch,
)
from app_generator.validation.section91_vector_orientation_proof import (
    verify_perpendicular_momentum_false,independently_recheck_vector_witness,
)


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cursor",type=int,default=0)
    parser.add_argument("--batch-size",type=int,default=4)
    args=parser.parse_args(argv)
    home=os.environ.get("LOCALAPPDATA")
    if not home:
        print(json.dumps({"status":"BSA275_OWNER_SOURCE_BINDING_REQUIRED"}))
        return 2
    private=Path(home)/"Microvid"/"BoslaV3ReviewYoga6"
    try:
        audit=audit_source_bound_academic_registry(private=private)
        batch=plan_next_science_batch(
            audit=audit,cursor=args.cursor,maximum=args.batch_size)
        ready=read_long_horizon_development(private)
        _,_,_,source,candidate=_bound_inputs(private,{
            "gitHead":ready["gitHead"],"proposalSha256":ready["proposalSha256"]})
        if (batch["gitHead"]!=ready["gitHead"]
            or batch["sourceSha256"]!=ready["sourceSha256"]
            or batch["candidateSha256"]!=ready["candidateSha256"]):
            raise ValueError("BSA275_BATCH_SOURCE_VERSION_CHANGED")
        # Source-specific handler registration is the only new science rule
        # in this finite pilot. All other pending tasks stay in the queue.
        def verified_direction_witness():
            result=verify_perpendicular_momentum_false(
                source_pdf=source,candidate_path=candidate)
            independently_recheck_vector_witness(result)
            return result
        # Run actual original-source witness only when opt-d is among this
        # requested batch. Never submit unmentioned or repeated operations.
        from app_generator.validation.section91_vector_orientation_proof import (
            _ACTIVITY,_PATH,
        )
        expected=[t for t in batch["tasks"]
                  if t["activityId"]==_ACTIVITY and
                  t["taskId"]==batch["taskIds"][0]]
        rules=()
        if args.cursor==0 and expected:
            # Exact task ID is independently reproduced from the ORIGINAL
            # source-pinned candidate rather than guessed from public content.
            proof=verified_direction_witness()
            if proof["taskId"]!=batch["taskIds"][0] or proof["surfacePath"]!=_PATH:
                raise ValueError("BSA275_ORIGINAL_FALSE_OPTION_NOT_BATCH_FIRST")
            rules=(ScienceBatchRule(proof["taskId"],verified_direction_witness),)
        dispatched=execute_source_bound_science_batch(batch=batch,rules=rules)
        if (dispatched["academicTasksAcceptedByBatch"]!=0
            or dispatched["completeAcademicProofGatesStillOpen"]!=90
            or dispatched["publicationAuthorized"] is not False):
            raise ValueError("BSA275_UNSUPPORTED_BATCH_ACADEMIC_PASS")
        print(json.dumps({
            "status":dispatched["status"],
            "sourceFreeGitHead":batch["gitHead"],
            "batchCursor":batch["cursor"],
            "batchTaskCount":batch["taskCount"],
            "independentlyVerifiedNewScienceWitnessesNotAdmitted":
                dispatched["verifiedWitnessCount"],
            "quarantinedTaskCount":dispatched["quarantinedCount"],
            "remainingMcqProofTasksBeforeAdmission":25,
            "academicProofTasksAcceptedBeforeBatch":2,
            "academicProofTasksAcceptedByBatch":0,
            "completeAcademicProofGatesStillOpen":90,
            "taskResults":[{"taskId":r["taskId"],"status":r["status"]}
                           for r in dispatched["results"]],
            "newGeminiCalls":0,
            "publicationAuthorized":False,
        },sort_keys=True))
        return 0
    except (OSError,ValueError,TypeError,KeyError,IndexError,
            ArithmeticError) as exc:
        print(json.dumps({
            "status":"BSA275_BATCH_SCIENCE_NOT_INDEPENDENTLY_PROVEN",
            "errorClass":type(exc).__name__,
            "errorCode":str(exc) if isinstance(exc,ValueError) else
                "OWNER_SOURCE_OR_PROOF_EVIDENCE_INVALID",
            "academicAcceptanceAdvanced":False,
            "publicationAuthorized":False,
        },sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())
