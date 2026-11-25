"""BSA249 real source-shape, fake historical claims, no-replay regressions."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from app_generator.runtime import v3_exact_revised_review_reconciliation as m
from app_generator.runtime.v3_malay_auto_revision import _CANDIDATE
from app_generator.validation.malay_conservation_lexicon import _replace_in_malay, ROOTS
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint

ROOT = Path(__file__).resolve().parents[1]


class V22EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        raw=(ROOT/m._PACKAGE).read_bytes()
        self.original=json.loads(raw.decode("utf8"))
        self.oldsha=sha256(raw).hexdigest()
        paths=[];counter={s:0 for s,_,_ in ROOTS}
        self.candidate=_replace_in_malay(self.original,"",paths,counter)
        self.candidate_bytes=(json.dumps(
            self.candidate,indent=2,ensure_ascii=False)+"\n").encode("utf8")
        self.newsha=sha256(self.candidate_bytes).hexdigest()
        self.repair={
            "affectedOriginalActivityIds": sorted(m._REVISED),
            "repairedActivityCount":4,
            "originalPackageSha256":self.oldsha,
            "newPrivateCandidateSha256":self.newsha,
        }
        self.original_state={
            "oldUncertainIndex":0,
            "originalAssessedUnchanged":1,
            "parentSha256":self.oldsha,
            "items":[{"index":i} for i in range(1,18)],
        }
        self.roles=[]
        for i,a in enumerate(self.original["activities"][1:],1):
            self.roles.append({
                "originalActivityIndex":i,
                "activityId":a["id"],
                "activitySha256":m._activity_digest(a),
                "sourcePackageSha256":self.oldsha,
                "status":"POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED",
                "sourceReviewSha256":sha256(("review"+str(i)).encode()).hexdigest(),
                "supplementalReviewSliceSha256":sha256(("slice"+str(i)).encode()).hexdigest(),
            })

    def plan(self, *, candidate=None, roles=None, state=None,repair=None):
        return m.plan_exact_revised_history(
            original=self.original,
            candidate=self.candidate if candidate is None else candidate,
            existing_pairs=self.roles if roles is None else roles,
            original_state=self.original_state if state is None else state,
            signed_repair=self.repair if repair is None else repair,
            source_sha="c"*64,
        )

    def test_genuine_shape_13_unchanged_4_changed_one_uncertain(self):
        out=self.plan()
        self.assertEqual(out["alreadyVerifiedHistoricRolePairs"],17)
        self.assertEqual(out["exactUnchangedHistoricPairsSafeForAdvisoryReuse"],13)
        self.assertEqual(out["changedPreviouslyReviewedPairsDisallowed"],4)
        self.assertEqual(out["newRolePairsStillNeeded"],4)
        self.assertTrue(out["originalIndex0Quarantined"])
        self.assertEqual(len(out["unchangedEvidence"]),13)
        self.assertEqual({x["activityId"] for x in out["changedRoleInputs"]},m._REVISED)
        self.assertEqual(out["fullAcademicAccepted"],0)

    def test_different_old_model_activity_sha_not_admitted(self):
        roles=json.loads(json.dumps(self.roles))
        roles[0]["activitySha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"V22_STALE_OR_FABRICATED"):
            self.plan(roles=roles)

    def test_forged_original_review_status_not_admitted(self):
        roles=json.loads(json.dumps(self.roles))
        roles[0]["status"]="ACADEMIC_PASS"
        with self.assertRaisesRegex(ValueError,"V22_STALE_OR_FABRICATED"):
            self.plan(roles=roles)

    def test_old_uncertain_index_not_replayable_as_new(self):
        state={**self.original_state,"oldUncertainIndex":3}
        with self.assertRaisesRegex(ValueError,"V22_ORIGINAL_17"):
            self.plan(state=state)

    def test_unrelated_fifth_activity_change_fails(self):
        altered=json.loads(json.dumps(self.candidate))
        altered["activities"][0]["prompt"]["ms"]+=" extra"
        with self.assertRaisesRegex(ValueError,"V22_ONLY_FOUR"):
            self.plan(candidate=altered)

    def test_answer_key_mutation_even_in_one_changed_item_fails(self):
        altered=json.loads(json.dumps(self.candidate))
        a=next(a for a in altered["activities"] if a["id"] in m._REVISED and a["type"]=="mcq")
        a["answerKey"]["correct"]="fake-changed-key"
        with self.assertRaisesRegex(ValueError,"V22_OUTSIDE_PRIOR"):
            self.plan(candidate=altered)

    def test_chinese_or_visual_modification_rejected(self):
        altered=json.loads(json.dumps(self.candidate))
        a=next(a for a in altered["activities"] if a["id"] in m._REVISED)
        a["explanation"]["zh"]="injected"
        with self.assertRaisesRegex(ValueError,"V22_OUTSIDE_PRIOR"):
            self.plan(candidate=altered)

    def test_duplicate_activity_id_rejected(self):
        altered=json.loads(json.dumps(self.candidate))
        altered["activities"][1]["id"]=altered["activities"][0]["id"]
        with self.assertRaisesRegex(ValueError,"V22_ORIGINAL_AND_REVISED"):
            self.plan(candidate=altered)

    def test_new_review_inputs_exactly_four_private_and_idempotent(self):
        original=(self.dir/m._CANDIDATE)
        original.write_bytes(self.candidate_bytes)
        out=self.plan()
        first=m._stage_changed_private(
            folder=self.dir,candidate=self.candidate,
            candidate_sha=self.newsha,source_sha="c"*64,
            fresh=out["changedRoleInputs"])
        self.assertEqual(first,m._stage_changed_private(
            folder=self.dir,candidate=self.candidate,
            candidate_sha=self.newsha,source_sha="c"*64,
            fresh=out["changedRoleInputs"]))
        self.assertEqual(len(first),4)
        self.assertEqual(len(list((self.dir/m._QUEUE).iterdir())),4)
        for item in first:
            target=self.dir/m._QUEUE/item["reviewInputSha256"]
            identity=json.loads((target/"review-identity.json").read_text(encoding="utf8"))
            self.assertFalse(identity["providerSubmissionOccurred"])
            self.assertFalse(identity["sourcePdfUploadAllowed"])
            self.assertFalse(identity["originalModelClaimsReusable"])
            a=json.loads((target/"activity.json").read_text(encoding="utf8"))
            self.assertEqual(m._activity_digest(a),identity["activityCanonicalSha256"])

    def test_tampered_staged_private_input_not_silently_reused(self):
        out=self.plan()
        first=m._stage_changed_private(
            folder=self.dir,candidate=self.candidate,
            candidate_sha=self.newsha,source_sha="c"*64,
            fresh=out["changedRoleInputs"])
        target=self.dir/m._QUEUE/first[0]["reviewInputSha256"]/"activity.json"
        target.write_bytes(b"forged")
        with self.assertRaisesRegex(ValueError,"V22_RESTART_CHANGED"):
            m._stage_changed_private(folder=self.dir,candidate=self.candidate,
                candidate_sha=self.newsha,source_sha="c"*64,
                fresh=out["changedRoleInputs"])

    def test_source_reviewed_unchanged_but_not_formally_accepted(self):
        out=self.plan()
        self.assertTrue(all(not x["independentAcademicPASS"] for x in out["unchangedEvidence"]))
        self.assertEqual(out["publicationAuthorized"],False)

    def test_worker_normal_v22_dispatch_must_exist(self):
        source=(ROOT/"scripts/run_v3_yoga6_recovery_worker.py").read_text(encoding="utf8")
        self.assertIn("run_post_v21_exact_revised_history_reconciliation(",source)
        self.assertIn('result["exactRevisedReviewReconciliation"]',source)
        self.assertIn('"unchangedReviewerPairsReusedAsAdvisoryEvidence")==13',source)


if __name__=="__main__":
    unittest.main()
