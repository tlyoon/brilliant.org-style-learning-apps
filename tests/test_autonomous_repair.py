"""Exact academic repair candidate security and no-human-review regressions."""
import json
import tempfile
import unittest
from pathlib import Path

from app_generator.runtime.run_context import RunContext
from app_generator.validation.autonomous_repair import (
    MAX_ATTEMPTS, canonical_hash, accept_repair_response, propose_private_repair,
)

ACT={
    "id":"example-impulse",
    "prompt":{"en":"Momentum in a collision","ms":"Momentum dalam perlanggaran",
              "zh":"????????"},
    "answerLogic":{"en":"Contact forces dominate the situation",
                   "ms":"Daya sentuhan menguasai keadaan",
                   "zh":"?????????"},
    "interaction":{"items":[
        {"id":"force","label":{"en":"Every external force must be tiny",
                                "ms":"Setiap daya luar mesti kecil",
                                "zh":"?????????"}},
        {"id":"other","label":{"en":"Newton third law always holds",
                                "ms":"Hukum ketiga Newton sentiasa sah",
                                "zh":"??????????"}},
        ],
        "correctSelections":["force"],
    },
    "visualPlan":{"kind":"balance"},
}
FIX={
 "en":"The net external impulse must be negligible compared with collision impulse.",
 "ms":"Impuls luar bersih mesti boleh diabaikan berbanding impuls perlanggaran.",
 "zh":"???????????????????",
}
SOURCE={"sourceSha256":"b"*64,"sourceEvidence":"Private original PDF source passage with enough physical material to evaluate impulse balance."}

def response(patches, activity=ACT):
    return "BEGIN_JSON\n"+json.dumps({
        "activityId":activity["id"],
        "baseActivitySha256":canonical_hash(activity),
        "patches":patches,
    },ensure_ascii=False)+"\nEND_JSON"

def label_patches():
    return [{"path":["interaction","items",0,"label",lang],"text":text}
            for lang,text in FIX.items()]

class Model:
    def __init__(self, reply, fail=False):
        self.reply=reply
        self.fail=fail
        self.calls=0
    def ask(self,prompt,*,stage=None):
        self.calls+=1
        if self.fail:
            raise TimeoutError("uncertain post-send response")
        self.stage=stage
        return self.reply

class RepairTests(unittest.TestCase):
    def test_trilingual_repair_keeps_grading_and_visual_contract(self):
        changed=accept_repair_response(response(label_patches()),ACT)
        self.assertEqual(FIX,changed["interaction"]["items"][0]["label"])
        self.assertEqual(ACT["interaction"]["correctSelections"],
                         changed["interaction"]["correctSelections"])
        self.assertEqual(ACT["visualPlan"],changed["visualPlan"])
        self.assertEqual(ACT["interaction"]["items"][1],changed["interaction"]["items"][1])
        self.assertEqual("Every external force must be tiny",
                         ACT["interaction"]["items"][0]["label"]["en"])

    def test_reject_partial_translation_or_grading_key_override(self):
        with self.assertRaisesRegex(ValueError,"three locales"):
            accept_repair_response(response(label_patches()[:2]),ACT)
        with self.assertRaisesRegex(ValueError,"structural"):
            accept_repair_response(response([
                {"path":["interaction","correctSelections"],"text":"wrong"}]),ACT)
        with self.assertRaisesRegex(ValueError,"duplicate"):
            accept_repair_response(response(label_patches()+label_patches()),ACT)

    def test_wrong_activity_hash_and_corrupted_character_rejected(self):
        bad=response(label_patches()).replace(canonical_hash(ACT),"0"*64)
        with self.assertRaisesRegex(ValueError,"wrong activity/version"):
            accept_repair_response(bad,ACT)
        patches=label_patches()
        patches[2]["text"]="Replacement \ufffd invalid"
        with self.assertRaisesRegex(ValueError,"Unicode"):
            accept_repair_response(response(patches),ACT)

    def test_real_private_receipt_and_safe_recovery(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            ctx=RunContext.create(root/"context")
            model=Model(response(label_patches()))
            private=root/"private-candidate"
            result=propose_private_repair(run=ctx,activity=ACT,source=SOURCE,
                objections=["External forces can cancel in the whole isolated system."],
                package_sha256="a"*64,model=model,attempt=1,private_dir=private)
            self.assertEqual("RECHECK_WITH_FRESH_REVIEWERS",result["status"])
            self.assertEqual(1,model.calls)
            receipt=json.loads((private/"receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(result["candidateSha256"],receipt["candidateSha256"])
            self.assertTrue(receipt["independentReverificationRequired"])
            self.assertFalse(receipt["publicationAuthorized"])
            new=propose_private_repair(run=ctx,activity=ACT,source=SOURCE,
                objections=["External forces can cancel in the whole isolated system."],
                package_sha256="a"*64,model=model,attempt=1,
                private_dir=root/"next-should-not-be-written")
            self.assertEqual("RECONCILE_PREVIOUS_ATTEMPT",new["status"])
            self.assertEqual(1,model.calls)

    def test_ambiguous_model_submission_not_repeated(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            ctx=RunContext.create(root/"context")
            model=Model("",fail=True)
            details=dict(run=ctx,activity=ACT,source=SOURCE,
                objections=["External forces can cancel in the whole isolated system."],
                package_sha256="a"*64,model=model,attempt=1)
            r=propose_private_repair(**details,private_dir=root/"first")
            self.assertEqual("AUTO_RETRY_AFTER_RECONCILIATION",r["status"])
            r=propose_private_repair(**details,private_dir=root/"second")
            self.assertEqual("RECONCILE_PREVIOUS_ATTEMPT",r["status"])
            self.assertEqual(1,model.calls)

    def test_bounded_attempt_count_and_private_output_only(self):
        with tempfile.TemporaryDirectory() as t:
            ctx=RunContext.create(Path(t)/"context")
            for n in (0,MAX_ATTEMPTS+1):
                with self.assertRaisesRegex(ValueError,"bounded"):
                    propose_private_repair(
                        run=ctx,activity=ACT,source=SOURCE,
                        objections=["External forces can cancel in the collision system."],
                        package_sha256="a"*64,model=Model(response(label_patches())),
                        attempt=n,private_dir=Path(t)/f"bad-{n}")
