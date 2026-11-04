"""Source-free tests for immutable review receipt reconciliation."""
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.validation.academic_claim_inventory import audit_immutable_claims
from app_generator.validation.academic_qa import REQUIRED

A="a"*64
B="b"*64
C="c"*64
D="d"*64
E="e"*64


class ImmutableClaimsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)

    def args(self):
        return dict(claims_dir=self.folder, claim_prefix="new-v5",
                    activity_id="example",activity_sha256=A,
                    package_sha256=B,source_sha256=C,source_context_sha256=D)

    def put(self,gate,role,state,**kwargs):
        base=dict(activityId="example",activityHash=A,packageHash=B,
                  sourceHash=C,sourceContextHash=D,roleIndex=role,
                  gate=gate,promptHash=E,state=state)
        base.update(kwargs)
        (self.folder/f"new-v5-{gate.replace('_','-')}-{role}.json").write_text(
            json.dumps(base),encoding="utf-8")

    def test_missing_claims_are_gaps_not_pass(self):
        r=audit_immutable_claims(**self.args())
        self.assertEqual(10,r["claimCount"])
        self.assertEqual({"MISSING":10},r["stateCounts"])
        self.assertEqual(0,r["modelRequestsMadeByAudit"])
        self.assertEqual("REVIEW_REQUIRED",r["academicQA"])
        self.assertFalse(r["publicationAuthorized"])

    def test_realistic_lifecycle_is_classified_without_trusting_content(self):
        for gate in REQUIRED:
            for role in (0,1):
                if gate=="source_fidelity" and role==0:
                    self.put(gate,role,"AMBIGUOUS",responseCaptured=True,
                             reasonCode="SOURCE_PAGE_NOT_AUTHORIZED",
                             responseSha256=E,
                             injectedModelText="sensitive untrusted response")
                elif gate=="source_fidelity" and role==1:
                    self.put(gate,role,"AMBIGUOUS",responseCaptured=False,
                             reasonCode="MODEL_RESPONSE_NOT_CAPTURED",
                             responseSha256=None)
                elif gate=="visual_semantics" and role==1:
                    self.put(gate,role,"SKIPPED_UNSENT",responseCaptured=False,
                             requestSubmitted=False,responseSha256=None,
                             reasonCode="UNCAPTURED_ROLE_CIRCUIT_OPEN")
                else:
                    self.put(gate,role,"COMPLETE",responseCaptured=True,
                             responseSha256=E,decision={"verdict":"SUPPORTED"})
        result=audit_immutable_claims(**self.args())
        self.assertEqual({"COMPLETE":7,"AMBIGUOUS":2,"SKIPPED_UNSENT":1},
                         result["stateCounts"])
        self.assertFalse(result["allAcademicGatesProven"])
        self.assertNotIn("sensitive untrusted response",json.dumps(result))
        self.assertFalse(result["publicationAuthorized"])

    def test_exact_identity_rejects_changed_activity_or_source(self):
        self.put("source_fidelity",0,"IN_FLIGHT")
        with self.assertRaisesRegex(ValueError,"mismatched immutable claim"):
            audit_immutable_claims(**{**self.args(),"source_sha256":E})
        with self.assertRaisesRegex(ValueError,"mismatched immutable claim"):
            audit_immutable_claims(**{**self.args(),"activity_sha256":E})

    def test_false_unsent_and_bogus_captured_digests_rejected(self):
        self.put("source_fidelity",0,"SKIPPED_UNSENT",
                 requestSubmitted=True,responseCaptured=False,responseSha256=None,
                 reasonCode="UNCAPTURED_ROLE_CIRCUIT_OPEN")
        with self.assertRaisesRegex(ValueError,"unsent claim"):
            audit_immutable_claims(**self.args())
        self.put("source_fidelity",0,"AMBIGUOUS",responseCaptured=True,
                 reasonCode="SOURCE_PAGE_NOT_AUTHORIZED",responseSha256=None)
        with self.assertRaisesRegex(ValueError,"response SHA"):
            audit_immutable_claims(**self.args())

    def test_inflight_submission_is_not_misclassified_as_unsent(self):
        self.put("source_fidelity",0,"IN_FLIGHT")
        result=audit_immutable_claims(**self.args())
        self.assertEqual(1,result["stateCounts"]["IN_FLIGHT"])
        self.assertFalse(result["allClaimRolesComplete"])
        self.assertEqual(0,result["modelRequestsMadeByAudit"])

    def test_invalid_gate_name_and_prefix_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"prefix"):
            audit_immutable_claims(**{**self.args(),"claim_prefix":"../oops"})
        with self.assertRaisesRegex(ValueError,"gate set"):
            audit_immutable_claims(**{**self.args(),"gates":("invented",)})


if __name__=="__main__":
    unittest.main()
