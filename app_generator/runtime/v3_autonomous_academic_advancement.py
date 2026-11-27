"""BSA276 executable non-stopping academic source-bound advancement loop.

Unlike a written reminder, this function follows all ALREADY ELIGIBLE
source-free and separately proof-admitting actions in ONE invocation. It
does not delegate autonomous source rewriting to an untrusted model, repeat
ambiguous provider requests, or keep retrying an ineligible task.

Historical signed evidence, clean exact Git HEAD and two hosted CI successes
remain mandatory. Missing new *scientific* proof families block only those
tasks; all currently verified academic work proceeds. Owner Yoga6 only.
"""
from __future__ import annotations
from pathlib import Path
import subprocess
import sys
from typing import Any

from app_generator.runtime.v3_versioned_readiness import (
    _git_info,_git_clean,_hosted_runs,_exact_ci_success,
)
from app_generator.runtime.v3_long_horizon_development import (
    read_long_horizon_development,
)
from app_generator.runtime.v3_academic_proof_registry_receipt import (
    _RECEIPT as _AUDIT_RECEIPT, sign_registry_audit,verify_registry_audit,
)
from app_generator.runtime.v3_academic_science_batch_admission import (
    _FRONTIER as _A3_FRONTIER,
    admit_new_scientific_batch,verify_academic_batch_across_git_heads,
)
from app_generator.runtime.v3_si_units_academic_batch_admission import (
    _FRONTIER as _SI_FRONTIER,
    admit_si_unit_science_batch,verify_si_unit_batch_across_git_heads,
)
from app_generator.runtime.v3_newton_force_academic_batch_admission import (
    _FRONTIER as _NEWTON_FRONTIER,
    admit_newton_source_bound_batch, verify_newton_batch_across_git_heads,
)
from app_generator.runtime.v3_paired_glider_academic_batch_admission import (
    _FRONTIER as _GLIDER_FRONTIER,
    admit_paired_glider_batch, verify_paired_glider_batch_across_git_heads,
)
from app_generator.runtime.v3_third_law_academic_batch_admission import (
    _FRONTIER as _THIRD_LAW_FRONTIER,
    admit_third_law_batch, verify_third_law_batch_across_git_heads,
)
from app_generator.runtime.v3_equal_speed_academic_batch_admission import (
    _FRONTIER as _EQUAL_SPEED_FRONTIER,
    admit_equal_speed_batch, verify_equal_speed_batch_across_git_heads,
)
from app_generator.runtime.v3_equal_energy_academic_batch_admission import (
    _FRONTIER as _EQUAL_ENERGY_FRONTIER,
    admit_equal_energy_batch, verify_equal_energy_batch_across_git_heads,
)
from app_generator.runtime.v3_isolated_pair_academic_batch_admission import (
    _FRONTIER as _ISOLATED_PAIR_FRONTIER,
    admit_isolated_pair_batch, verify_isolated_pair_batch_across_git_heads,
)
from app_generator.runtime.v3_spring_buffer_academic_batch_admission import (
    _FRONTIER as _SPRING_BUFFER_FRONTIER,
    admit_spring_buffer_batch, verify_spring_buffer_batch_across_git_heads,
)
from app_generator.runtime.v3_vector_explanation_academic_admission import (
    _FRONTIER as _VECTOR_EXPLANATION_FRONTIER,
    admit_vector_explanation, verify_vector_explanation_across_git_heads,
)
from app_generator.runtime.v3_si_explanation_academic_admission import (
    _FRONTIER as _SI_EXPLANATION_FRONTIER,
    admit_si_explanation, verify_si_explanation_across_git_heads,
)
from app_generator.runtime.v3_newton_explanation_academic_admission import (
    _FRONTIER as _NEWTON_EXPLANATION_FRONTIER,
    admit_newton_explanation, verify_newton_explanation_across_git_heads,
)
from app_generator.runtime.v3_glider_explanation_academic_admission import (
    _FRONTIER as _GLIDER_EXPLANATION_FRONTIER,
    admit_glider_explanation, verify_glider_explanation_across_git_heads,
)


def _owner_advance_worker(repo:Path)->None:
    """Existing bounded, idempotent *source-free* V1–V36 normal worker only."""
    result=subprocess.run(
        [sys.executable,"scripts/run_v3_yoga6_recovery_worker.py",
         "--source-free-advance"],
        cwd=repo,check=False,timeout=1800,
    )
    if result.returncode!=0:
        raise ValueError("BSA276_NORMAL_OWNER_V36_WORKER_NOT_SUCCESSFUL")


def advance_all_eligible_academic_actions(
    *,repo:Path,private:Path,max_steps:int=20,
)->dict[str,Any]:
    if type(max_steps) is not int or not 1<=max_steps<=20:
        raise ValueError("BSA276_INVALID_BOUNDED_AUTONOMOUS_STEP_LIMIT")
    if not isinstance(repo,Path) or not isinstance(private,Path):
        raise ValueError("BSA276_OWNER_PATHS_REQUIRED")
    head,branch=_git_info(repo)
    if not _git_clean(repo):
        raise ValueError("BSA276_DIRTY_CODE_MUST_NOT_ADMIT_SOURCE_PROOFS")
    if not _exact_ci_success(_hosted_runs(repo,branch),head):
        raise ValueError("BSA276_EXACT_HEAD_HOSTED_CI_INCOMPLETE_OR_FAILED")
    journal=[]
    for step in range(max_steps):
        # Progress is meaningful only at real source-bound phase boundaries.
        # Emit on stderr with flush; keep CLI stdout a single machine JSON.
        print("BSA283_VERIFIABLE_ACADEMIC_STEP_ENTER "+
              str(step+1)+"/"+str(max_steps)+
              " head="+head[:12],file=sys.stderr,flush=True)
        checkpoint=read_long_horizon_development(private)
        if checkpoint["gitHead"]!=head:
            print("BSA283_OWNER_SIGNED_HEAD_REBUILD_STARTED "+
                  head[:12],file=sys.stderr,flush=True)
            _owner_advance_worker(repo)
            print("BSA283_OWNER_SIGNED_HEAD_REBUILD_FINISHED "+
                  head[:12],file=sys.stderr,flush=True)
            newly=read_long_horizon_development(private)
            if newly["gitHead"]!=head:
                raise ValueError("BSA276_WORKER_DID_NOT_ESTABLISH_EXACT_HEAD")
            journal.append("CURRENT_EXACT_HEAD_NORMAL_V36_RESTORED")
            continue
        here=private/"owner-five-stage-completion"/(
            checkpoint["gitHead"])/checkpoint["proposalSha256"]
        audit_file=here/_AUDIT_RECEIPT
        if not audit_file.exists() and not audit_file.is_symlink():
            audit=sign_registry_audit(private=private)
            if (audit["independentlyAcceptedAcademicTasks"]!=2
                or audit["pendingMcqDistractorScienceTasks"]!=25):
                raise ValueError("BSA276_SOURCE_BOUND_REGISTRY_AUDIT_INVALID")
            journal.append("CURRENT_HEAD_SIGNED_BSA274_REGISTRY_AUDIT")
            continue
        audit=verify_registry_audit(private=private)
        if (audit["independentlyAcceptedAcademicTasks"]!=2
            or audit["pendingMcqDistractorScienceTasks"]!=25):
            raise ValueError("BSA276_PREVIOUS_A1_A2_SIGNATURES_UNTRUSTED")
        a3=private/"long-horizon-development"/_A3_FRONTIER
        if not a3.exists() and not a3.is_symlink():
            a=admit_new_scientific_batch(private=private)
            if a["independentlyAcceptedAcademicTasks"]!=3:
                raise ValueError("BSA276_A3_ADMISSION_WITHOUT_PROOF")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A3_SCIENCE_TASK")
            continue
        prior=verify_academic_batch_across_git_heads(private=private)
        if (prior["independentlyAcceptedAcademicTasks"]!=3
            or prior["fullAcademicTasksStillOpen"]!=426):
            raise ValueError("BSA276_A3_HISTORICAL_PROOF_NO_LONGER_VALID")
        si=private/"long-horizon-development"/_SI_FRONTIER
        if not si.exists() and not si.is_symlink():
            admitted=admit_si_unit_science_batch(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=6
                or admitted["pendingMcqDistractorScienceTasks"]!=21):
                raise ValueError("BSA276_THREE_NEW_SI_PROOFS_NOT_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A4_A6_SCIENCE_TASKS")
            continue
        latest=verify_si_unit_batch_across_git_heads(private=private)
        if (latest["independentlyAcceptedAcademicTasks"]!=6
            or latest["fullAcademicTasksStillOpen"]!=423
            or latest["completeAcademicProofGatesStillOpen"]!=90
            or latest["fullAcademicActivityPASS"]!=0
            or latest["publicationAuthorized"] is not False):
            raise ValueError("BSA276_A1_A6_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        force=private/"long-horizon-development"/_NEWTON_FRONTIER
        if not force.exists() and not force.is_symlink():
            admitted=admit_newton_source_bound_batch(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=9
                or admitted["pendingMcqDistractorScienceTasks"]!=18):
                raise ValueError("BSA277_NEWTON_BATCH_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A7_A9_NEWTON_SCIENCE_TASKS")
            continue
        force_accepted=verify_newton_batch_across_git_heads(private=private)
        if (force_accepted["independentlyAcceptedAcademicTasks"]!=9
            or force_accepted["fullAcademicTasksStillOpen"]!=420
            or force_accepted["completeAcademicProofGatesStillOpen"]!=90
            or force_accepted["fullAcademicActivityPASS"]!=0
            or force_accepted["publicationAuthorized"] is not False):
            raise ValueError("BSA277_A1_A9_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        glider=private/"long-horizon-development"/_GLIDER_FRONTIER
        if not glider.exists() and not glider.is_symlink():
            admitted=admit_paired_glider_batch(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=12
                or admitted["pendingMcqDistractorScienceTasks"]!=15):
                raise ValueError("BSA278_GLIDER_BATCH_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A10_A12_GLIDER_SCIENCE_TASKS")
            continue
        glider_verified=verify_paired_glider_batch_across_git_heads(private=private)
        if (glider_verified["independentlyAcceptedAcademicTasks"]!=12
            or glider_verified["fullAcademicTasksStillOpen"]!=417
            or glider_verified["completeAcademicProofGatesStillOpen"]!=90
            or glider_verified["fullAcademicActivityPASS"]!=0
            or glider_verified["publicationAuthorized"] is not False):
            raise ValueError("BSA278_A1_A12_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        third_law=private/"long-horizon-development"/_THIRD_LAW_FRONTIER
        if not third_law.exists() and not third_law.is_symlink():
            admitted=admit_third_law_batch(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=15
                or admitted["pendingMcqDistractorScienceTasks"]!=12
                or admitted["fullAcademicTasksStillOpen"]!=414):
                raise ValueError("BSA281_THIRD_LAW_BATCH_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A13_A15_THIRD_LAW_SCIENCE_TASKS")
            continue
        third_verified=verify_third_law_batch_across_git_heads(private=private)
        if (third_verified["independentlyAcceptedAcademicTasks"]!=15
            or third_verified["fullAcademicTasksStillOpen"]!=414
            or third_verified["pendingMcqDistractorScienceTasks"]!=12
            or third_verified["completeAcademicProofGatesStillOpen"]!=90
            or third_verified["fullAcademicActivityPASS"]!=0
            or third_verified["publicationAuthorized"] is not False):
            raise ValueError("BSA281_A1_A15_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        equal_speed=private/"long-horizon-development"/_EQUAL_SPEED_FRONTIER
        if not equal_speed.exists() and not equal_speed.is_symlink():
            admitted=admit_equal_speed_batch(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=18
                or admitted["pendingMcqDistractorScienceTasks"]!=9):
                raise ValueError("BSA287_EQUAL_SPEED_BATCH_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A16_A18_EQUAL_SPEED_SCIENCE_TASKS")
            continue
        equal_verified=verify_equal_speed_batch_across_git_heads(private=private)
        if (equal_verified["independentlyAcceptedAcademicTasks"]!=18
            or equal_verified["fullAcademicTasksStillOpen"]!=411
            or equal_verified["pendingMcqDistractorScienceTasks"]!=9
            or equal_verified["completeAcademicProofGatesStillOpen"]!=90
            or equal_verified["fullAcademicActivityPASS"]!=0
            or equal_verified["publicationAuthorized"] is not False):
            raise ValueError("BSA287_A1_A18_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        equal_energy=private/"long-horizon-development"/_EQUAL_ENERGY_FRONTIER
        if not equal_energy.exists() and not equal_energy.is_symlink():
            admitted=admit_equal_energy_batch(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=21
                or admitted["pendingMcqDistractorScienceTasks"]!=6):
                raise ValueError("BSA289_EQUAL_ENERGY_BATCH_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A19_A21_EQUAL_ENERGY_SCIENCE_TASKS")
            continue
        energy_verified=verify_equal_energy_batch_across_git_heads(private=private)
        if (energy_verified["independentlyAcceptedAcademicTasks"]!=21
            or energy_verified["fullAcademicTasksStillOpen"]!=408
            or energy_verified["pendingMcqDistractorScienceTasks"]!=6
            or energy_verified["completeAcademicProofGatesStillOpen"]!=90
            or energy_verified["fullAcademicActivityPASS"]!=0
            or energy_verified["publicationAuthorized"] is not False):
            raise ValueError("BSA289_A1_A21_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        isolated_pair=private/"long-horizon-development"/_ISOLATED_PAIR_FRONTIER
        if not isolated_pair.exists() and not isolated_pair.is_symlink():
            admitted=admit_isolated_pair_batch(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=24
                or admitted["pendingMcqDistractorScienceTasks"]!=3):
                raise ValueError("BSA290_ISOLATED_PAIR_BATCH_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A22_A24_ISOLATED_PAIR_SCIENCE_TASKS")
            continue
        pair_verified=verify_isolated_pair_batch_across_git_heads(private=private)
        if (pair_verified["independentlyAcceptedAcademicTasks"]!=24
            or pair_verified["fullAcademicTasksStillOpen"]!=405
            or pair_verified["pendingMcqDistractorScienceTasks"]!=3
            or pair_verified["completeAcademicProofGatesStillOpen"]!=90
            or pair_verified["fullAcademicActivityPASS"]!=0
            or pair_verified["publicationAuthorized"] is not False):
            raise ValueError("BSA290_A1_A24_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        spring=private/"long-horizon-development"/_SPRING_BUFFER_FRONTIER
        if not spring.exists() and not spring.is_symlink():
            admitted=admit_spring_buffer_batch(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=27
                or admitted["pendingMcqDistractorScienceTasks"]!=0):
                raise ValueError("BSA291_SPRING_BUFFER_BATCH_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A25_A27_SPRING_BUFFER_SCIENCE_TASKS")
            continue
        spring_verified=verify_spring_buffer_batch_across_git_heads(private=private)
        if (spring_verified["independentlyAcceptedAcademicTasks"]!=27
            or spring_verified["fullAcademicTasksStillOpen"]!=402
            or spring_verified["pendingMcqDistractorScienceTasks"]!=0
            or spring_verified["completeAcademicProofGatesStillOpen"]!=90
            or spring_verified["fullAcademicActivityPASS"]!=0
            or spring_verified["publicationAuthorized"] is not False):
            raise ValueError("BSA291_A1_A27_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        explanation=private/"long-horizon-development"/_VECTOR_EXPLANATION_FRONTIER
        if not explanation.exists() and not explanation.is_symlink():
            admitted=admit_vector_explanation(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=28
                or admitted["fullAcademicTasksStillOpen"]!=401):
                raise ValueError("BSA292_VECTOR_EXPLANATION_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A28_EXPLANATION_SCIENCE_TASK")
            continue
        explanation_verified=verify_vector_explanation_across_git_heads(private=private)
        if (explanation_verified["independentlyAcceptedAcademicTasks"]!=28
            or explanation_verified["fullAcademicTasksStillOpen"]!=401
            or explanation_verified["completeAcademicProofGatesStillOpen"]!=90
            or explanation_verified["fullAcademicActivityPASS"]!=0
            or explanation_verified["publicationAuthorized"] is not False):
            raise ValueError("BSA292_A1_A28_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        si_explanation=private/"long-horizon-development"/_SI_EXPLANATION_FRONTIER
        if not si_explanation.exists() and not si_explanation.is_symlink():
            admitted=admit_si_explanation(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=29
                or admitted["fullAcademicTasksStillOpen"]!=400):
                raise ValueError("BSA293_SI_EXPLANATION_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A29_SI_EXPLANATION_SCIENCE_TASK")
            continue
        si_verified=verify_si_explanation_across_git_heads(private=private)
        if (si_verified["independentlyAcceptedAcademicTasks"]!=29
            or si_verified["fullAcademicTasksStillOpen"]!=400
            or si_verified["completeAcademicProofGatesStillOpen"]!=90
            or si_verified["fullAcademicActivityPASS"]!=0
            or si_verified["publicationAuthorized"] is not False):
            raise ValueError("BSA293_A1_A29_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        newton_explanation=private/"long-horizon-development"/_NEWTON_EXPLANATION_FRONTIER
        if not newton_explanation.exists() and not newton_explanation.is_symlink():
            admitted=admit_newton_explanation(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=30
                or admitted["fullAcademicTasksStillOpen"]!=399):
                raise ValueError("BSA297_NEWTON_EXPLANATION_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A30_NEWTON_EXPLANATION_SCIENCE_TASK")
            continue
        newton_verified=verify_newton_explanation_across_git_heads(private=private)
        if (newton_verified["independentlyAcceptedAcademicTasks"]!=30
            or newton_verified["fullAcademicTasksStillOpen"]!=399
            or newton_verified["completeAcademicProofGatesStillOpen"]!=90
            or newton_verified["fullAcademicActivityPASS"]!=0
            or newton_verified["publicationAuthorized"] is not False):
            raise ValueError("BSA297_A1_A30_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        glider_explanation=private/"long-horizon-development"/_GLIDER_EXPLANATION_FRONTIER
        if not glider_explanation.exists() and not glider_explanation.is_symlink():
            admitted=admit_glider_explanation(private=private)
            if (admitted["independentlyAcceptedAcademicTasks"]!=31
                or admitted["fullAcademicTasksStillOpen"]!=398):
                raise ValueError("BSA298_GLIDER_EXPLANATION_NOT_INDEPENDENTLY_ADMITTED")
            journal.append("SIGNED_AND_INDEPENDENTLY_READ_A31_GLIDER_EXPLANATION_SCIENCE_TASK")
            continue
        glider_verified=verify_glider_explanation_across_git_heads(private=private)
        if (glider_verified["independentlyAcceptedAcademicTasks"]!=31
            or glider_verified["fullAcademicTasksStillOpen"]!=398
            or glider_verified["completeAcademicProofGatesStillOpen"]!=90
            or glider_verified["fullAcademicActivityPASS"]!=0
            or glider_verified["publicationAuthorized"] is not False):
            raise ValueError("BSA298_A1_A31_CHAIN_NOT_INDEPENDENTLY_REVERIFIED")
        return {
            "status":"BSA298_ALL_CURRENTLY_ELIGIBLE_ACADEMIC_ACTIONS_EXECUTED",
            "currentGitHead":head,
            "actionsExecuted":journal,
            "academicProofTasksAccepted":31,
            "fullAcademicProofTasksStillOpen":398,
            "pendingMcqDistractorScienceTasks":0,
            "completeAcademicProofGatesStillOpen":90,
            "academicActivityPASS":0,
            "nextSafeDevelopmentFrontier":
                "INDEPENDENT_SOURCE_BOUND_NEW_SCIENCE_EXPLANATION_MULTILINGUAL_AND_DIAGRAM_PROOF_HANDLERS",
            "nextFrontierRequiresNewReviewedExecutableScienceProducers":True,
            "newProviderCalls":0,
            "newOutsideSourcePdfs":0,
            "publicationAuthorized":False,
        }
    raise ValueError("BSA276_BOUNDED_ADVANCE_LIMIT_REACHED_WITH_ELIGIBLE_ACTIONS")
