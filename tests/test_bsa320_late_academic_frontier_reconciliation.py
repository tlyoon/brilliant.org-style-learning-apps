"""BSA320: latest signed A32-A35 proofs remain visible after owner failure.

Source-free mocks exercise dispatch only; they cannot mint academic evidence.
Real dispatch always invokes the genuine original-Serway independent verifiers.
"""
from contextlib import ExitStack
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime import v3_incremental_signed_science_progress as progress


class LateAcademicFrontierReconciliation(TestCase):
    HEAD = "a" * 40
    WHEN = "2026-11-28T16:00:00+00:00"

    @staticmethod
    def _fake_verified(count):
        return {
            "status": "BSA320_TEST_SIGNED_SOURCE_REVERIFIED",
            "currentGitHead": LateAcademicFrontierReconciliation.HEAD,
            "batchProofOriginGitHead": "b" * 40,
            "acceptedAcademicTaskIds": [f"{i:064x}" for i in range(count)],
            "independentlyAcceptedAcademicTasks": count,
            "fullAcademicTasksStillOpen": 429 - count,
            "completeAcademicProofGatesStillOpen": 90,
            "fullAcademicActivityPASS": 0,
            "newProviderCalls": 0,
            "publicationAuthorized": False,
        }

    def test_bsa320_new_signed_proof_stages_are_ordered_and_readonly(self):
        counts = [s[0] for s in progress.STAGES]
        self.assertEqual(counts[:7], [35, 34, 33, 32, 31, 30, 29])
        self.assertEqual(counts, sorted(counts, reverse=True))
        self.assertEqual(len(counts), len(set(counts)))
        for count, name, frontier, verify in progress.STAGES[:4]:
            module = import_module(name)
            self.assertTrue(hasattr(module, frontier))
            self.assertTrue(callable(getattr(module, verify)))
            self.assertTrue(verify.startswith("verify_"))
            self.assertIn(count, (32, 33, 34, 35))

    def _run(self, signed_counts, *, broken=None, previous=31, seen_head=None):
        broken = broken or {}
        with TemporaryDirectory() as td:
            private = Path(td)
            with ExitStack() as stack:
                for n, name, frontier, verify in progress.STAGES:
                    if n not in signed_counts:
                        continue
                    module = import_module(name)
                    location = private / "long-horizon-development" / getattr(module, frontier)
                    location.parent.mkdir(parents=True, exist_ok=True)
                    location.write_text("synthetic-only", encoding="utf8")
                    result = {**self._fake_verified(n), **broken.get(n, {})}
                    stack.enter_context(patch.object(module, verify, return_value=result))
                stack.enter_context(patch.object(
                    progress, "read_long_horizon_development",
                    return_value={"gitHead": seen_head or self.HEAD},
                ))
                state = {"scienceAcceptance": {
                    "acceptedCount": previous,
                    "lastVerifiedHead": "b" * 40,
                    "lastIncreaseAt": "2026-11-28T12:00:00+00:00",
                    "noGainOwnerHeads": 1,
                }}
                outcome = progress.reconcile_independent_science(
                    private=private, state=state, head=self.HEAD,
                    now=self.WHEN, cycle=110,
                )
                return outcome, state

    def test_bsa320_signed_a35_survives_failed_later_owner_stage(self):
        result, state = self._run([32, 33, 34, 35])
        self.assertEqual(result["acceptedCount"], 35)
        self.assertEqual(result["pendingCount"], 394)
        self.assertTrue(result["independentVerifierExecuted"])
        self.assertEqual(state["scienceAcceptance"]["acceptedCount"], 35)
        self.assertTrue(state["scienceAcceptance"]["advancedThisObservation"])
        self.assertFalse(state["scientificProgress"]["publicationAuthorized"])
        self.assertEqual(state["scienceAcceptance"]["noGainOwnerHeads"], 0)

    def test_bsa320_failed_top_proof_falls_back_to_authentic_previous_receipt(self):
        outcome, state = self._run(
            [33, 34, 35], broken={35: {"newProviderCalls": 1}})
        self.assertEqual(outcome["acceptedCount"], 34)
        self.assertEqual(outcome["pendingCount"], 395)
        self.assertEqual(outcome["higherFrontiersQuarantined"], [
            {"count": 35, "class": "ValueError"}])
        self.assertEqual(state["scienceAcceptance"]["acceptedCount"], 34)

    def test_bsa320_tamper_cannot_roll_back_a_previously_verified_35(self):
        with self.assertRaisesRegex(ValueError, "ROLLBACK"):
            self._run([34, 35], broken={35: {"publicationAuthorized": True}},
                      previous=35)

    def test_bsa320_no_new_receipt_no_academic_credit(self):
        outcome, state = self._run([], previous=29)
        self.assertFalse(outcome["independentVerifierExecuted"])
        self.assertEqual(outcome["priorAcceptedCount"], 29)
        self.assertEqual(state["scienceAcceptance"]["acceptedCount"], 29)

    def test_bsa320_current_signed_head_must_match_exact_code_head(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_HEAD_NOT_CURRENT"):
            self._run([35], previous=29, seen_head="c" * 40)
