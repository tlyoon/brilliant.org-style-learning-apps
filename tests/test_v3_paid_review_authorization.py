"""Source-free V3 owner's separately authorized paid API campaign.

Tests never generate model content or create billing activity.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_paid_review_authorization import (
    CONTRACT, authorize_paid_v3_action, load_paid_review_contract,
)
from app_generator.validation.final_acceptance_closure import (
    load_frozen_charter,
)

_CORRECTED = "49a7f18c7cc2b7c00e0b6b23838cca1ed7fe52262384e0c26bbc8360fa3e9174"


class V3PaidOwnerCampaignTests(unittest.TestCase):
    def test_explicit_paid_and_transfer_authorization_new_version(self):
        c=load_paid_review_contract()
        self.assertTrue(c["paidGeminiApiGenerationAuthorized"])
        self.assertTrue(c["generatedLearningTextTransferAuthorized"])
        self.assertEqual(c["maxActivitiesPerInvocation"], 4)
        self.assertEqual(c["maxElapsedSecondsPerInvocation"], 900)
        self.assertEqual(c["maxIndependentGeminiCallsPerActivity"], 2)
        self.assertFalse(c["allowBatchJobCreation"])
        self.assertFalse(c["publicationAuthorized"])

    def test_historical_frozen_charter_is_unchanged(self):
        old=load_frozen_charter()
        self.assertTrue(old["policy"]["frozen"])
        self.assertFalse(old["policy"]["sourceBearingModelCallsAllowed"])
        self.assertFalse(old["policy"]["publicReleaseAuthorized"])
        self.assertEqual(old["policy"]["newCampaignsAuthorized"],[])

    def test_review_one_new_original_activity_and_four_max(self):
        for n in (1,4):
            approved=authorize_paid_v3_action(
                "FROZEN_ORIGINAL_ELIGIBLE_NEW_ACTIVITY",
                execute=True,transfer=True,next_section="section-9-5",
                max_activities=n,max_elapsed_seconds=900)
            self.assertEqual(approved["maxActivities"],n)
            self.assertFalse(approved["publicationAuthorized"])

    def test_corrected_one_activity_only_and_no_original_ambiguous(self):
        allowed=authorize_paid_v3_action(
            "ISOLATED_CORRECTED_SECTION_9_2_ACTIVITY",
            execute=True,transfer=True,
            corrected_candidate_sha256=_CORRECTED)
        self.assertEqual(allowed["maxActivities"],1)
        for section in ("section-9-1","section-9-2",None):
            with self.subTest(section=section):
                with self.assertRaisesRegex(ValueError,"NOT_AUTHORIZED"):
                    authorize_paid_v3_action(
                        "FROZEN_ORIGINAL_ELIGIBLE_NEW_ACTIVITY",
                        execute=True,transfer=True,next_section=section)
        with self.assertRaisesRegex(ValueError,"REVISED_SCOPE"):
            authorize_paid_v3_action(
                "ISOLATED_CORRECTED_SECTION_9_2_ACTIVITY",
                execute=True,transfer=True,
                corrected_candidate_sha256="0"*64)

    def test_missing_one_permission_fails_closed(self):
        for execute,transfer in ((False,True),(True,False),(False,False)):
            with self.subTest(execute=execute,transfer=transfer):
                with self.assertRaisesRegex(ValueError,"BOTH_EXECUTE_AND_TRANSFER"):
                    authorize_paid_v3_action(
                        "FROZEN_ORIGINAL_ELIGIBLE_NEW_ACTIVITY",
                        execute=execute,transfer=transfer,
                        next_section="section-9-5")

    def test_budgets_exceed_caps_fail_before_provider(self):
        for activities,seconds in ((0,900),(5,900),(1,901),(1,5)):
            with self.subTest(activities=activities,seconds=seconds):
                with self.assertRaisesRegex(ValueError,"BUDGET_EXCEEDED"):
                    authorize_paid_v3_action(
                        "FROZEN_ORIGINAL_ELIGIBLE_NEW_ACTIVITY",
                        execute=True,transfer=True,
                        next_section="section-9-5",
                        max_activities=activities,
                        max_elapsed_seconds=seconds)

    def test_authorization_tamper_never_enables_batch_or_release(self):
        original=json.loads(CONTRACT.read_text(encoding="utf8"))
        for field,value in (("allowBatchJobCreation",True),
                            ("publicationAuthorized",True),
                            ("maxActivitiesPerInvocation",1000),
                            ("authorizedHost","Dell-115"),
                            ("noRetryOfAmbiguousProviderRequest",False),
                            ("allowAutomatedScheduler",True),
                            ("generatedLearningTextTransferAuthorized",False)):
            with self.subTest(field=field):
                changed=dict(original)
                changed[field]=value
                with tempfile.TemporaryDirectory() as folder:
                    path=Path(folder)/"campaign.json"
                    path.write_text(json.dumps(changed),encoding="utf8")
                    with self.assertRaisesRegex(ValueError,"SCOPE_OR_BUDGET|SAFETY_BOUNDARY"):
                        load_paid_review_contract(path)

    def test_no_unknown_workflow_and_exact_one_review_scope(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_WORKFLOW"):
            authorize_paid_v3_action(
                "UNBOUNDED_PAYMENTS",execute=True,transfer=True)
        with self.assertRaisesRegex(ValueError,"REVISED_SCOPE"):
            authorize_paid_v3_action(
                "ISOLATED_CORRECTED_SECTION_9_2_ACTIVITY",
                execute=True,transfer=True,
                corrected_candidate_sha256=_CORRECTED,
                max_activities=2)

if __name__ == "__main__":
    unittest.main()
