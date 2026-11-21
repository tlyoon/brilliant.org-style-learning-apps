"""BSA241 V17 real source-bound science and frozen C3 historical gates."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_science_c3_independent_dispatch as m
from app_generator.runtime.v3_five_stage_completion import _hash


def signed_v16():
    body={
        "status":m._V16_STATUS,
        "gitHead":"a"*40,
        "publicPrDraft":True,
        "publicationAuthorized":False,
        "publicMergeExecuted":False,
        "publicDeployExecuted":False,
        "technicalEvidence":{
            "realChromeAccessibilityTree":{
                "pagesAudited":3,
                "localeAccessibilityTreeChecks":9,
                "unnamedControls":0,
                "documentLanguageMatches":9,
                "minimumNamedControls":8,
            },
        },
    }
    return {**body,"integritySha256":_hash(body)}


class V17ScienceC3IndependentTests(unittest.TestCase):
    def test_true_signed_v16_required(self):
        obj=signed_v16()
        m.check_signed_v16(obj,{"gitHead":"a"*40})
        obj["gitHead"]="b"*40
        with self.assertRaisesRegex(ValueError,"SIGNED_V16_REQUIRED"):
            m.check_signed_v16(obj,{"gitHead":"a"*40})

    def test_false_ax_pass_and_injected_publication_refused(self):
        for key,invalid in (
            ("localeAccessibilityTreeChecks",8),
            ("unnamedControls",1),
            ("documentLanguageMatches",8),
            ("minimumNamedControls",0),
        ):
            v16=signed_v16()
            v16["technicalEvidence"]["realChromeAccessibilityTree"][key]=invalid
            # A true signed receipt could legitimately encode a failed AX gate
            # after an adverse upstream mutation. Its admission must stop.
            v16["integritySha256"]=_hash({
                k:v for k,v in v16.items() if k!="integritySha256"})
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,"CHROME_AX"):
                m.check_signed_v16(v16,{"gitHead":"a"*40})
        v16=signed_v16()
        v16["publicationAuthorized"]=True
        v16["integritySha256"]=_hash({
            k:v for k,v in v16.items() if k!="integritySha256"})
        with self.assertRaisesRegex(ValueError,"SIGNED_V16_REQUIRED"):
            m.check_signed_v16(v16,{"gitHead":"a"*40})

    def test_forged_v16_blocks_all_actual_tasks(self):
        with TemporaryDirectory() as td:
            folder=Path(td)
            broken=signed_v16()
            broken["integritySha256"]="0"*64
            with (patch.object(m,"_v13_preflight",return_value=(
                       folder,{},{}, "branch", [])),
                  patch.object(m,"_trusted_json",return_value=broken),
                  patch.object(m,"_task_c3") as a,
                  patch.object(m,"_task_academic") as b):
                with self.assertRaisesRegex(ValueError,"SIGNED_V16_REQUIRED"):
                    m.run_post_v16_science_c3(
                        folder,folder,{"gitHead":"a"*40,
                            "proposalSha256":"c"*64},{},{},{},broken)
                a.assert_not_called()
                b.assert_not_called()

    def test_normal_dispatch_writes_real_signed_pre_and_result_receipts(self):
        with TemporaryDirectory() as td:
            folder=Path(td)
            valid=signed_v16()
            ready={"gitHead":"a"*40,"proposalSha256":"c"*64}
            result1={
                "taskStatus":"FROZEN_C3_FAILURE_PRESERVED_NEW_DRAFT_BROWSER_QA_VERIFIED",
                "historicalC3TechnicalResult":"FAILED_LIMITED_CAMPAIGN",
            }
            result2={"taskStatus":
                "36_GENUINE_C3_DRAFT_ACTIVITIES_180_INDEPENDENT_PROOFS_MISSING",
                "unverifiedGateInstances":180}
            with (patch.object(m,"_v13_preflight",return_value=(
                       folder,{},{}, "branch", [])),
                  patch.object(m,"_trusted_json",return_value=valid),
                  patch.dict(m._TASK_HANDLERS,{
                      m._TASKS[0]:lambda base,repo:result1,
                      m._TASKS[1]:lambda base,repo:result2,
                  })):
                out=m.run_post_v16_science_c3(
                    folder,folder,ready,{},{},{},valid)
            self.assertEqual(out["status"],m._STATUS)
            self.assertTrue(out["taskDispatchActuallyExecuted"])
            self.assertEqual(out["quarantinedTaskIds"],[])
            self.assertEqual(out["historicalC3"],"FAILED_LIMITED_CAMPAIGN")
            self.assertEqual(out["newPaidModelCalls"],0)
            self.assertFalse(out["publicationAuthorized"])
            self.assertTrue((folder/m._V17).is_file())
            for task in m._TASKS:
                self.assertTrue((folder/f"V17_TASK_{task}_PRE_CALL.json").is_file())
                self.assertTrue((folder/f"V17_TASK_{task}_RESULT.json").is_file())
            # Repeat a genuine read-only task. Immutable source result receipt
            # must agree exactly; never quietly overwrite changed metadata.
            self.assertEqual(out["integritySha256"],
                             m._hash({k:v for k,v in out.items()
                                      if k!="integritySha256"}))

    def test_one_task_error_quarantines_but_dispatches_other(self):
        with TemporaryDirectory() as td:
            folder=Path(td)
            valid=signed_v16()
            ready={"gitHead":"a"*40,"proposalSha256":"c"*64}
            count=[]
            def first(_base,_repo):
                raise RuntimeError("synthetic non-secret")
            def second(_base,_repo):
                count.append("actual")
                return {"taskStatus":"SECOND_INDEPENDENT_TASK_EXECUTED"}
            with (patch.object(m,"_v13_preflight",return_value=(
                       folder,{},{}, "branch", [])),
                  patch.object(m,"_trusted_json",return_value=valid),
                  patch.dict(m._TASK_HANDLERS,{
                      m._TASKS[0]:first,m._TASKS[1]:second,
                  })):
                result=m.run_post_v16_science_c3(
                    folder,folder,ready,{},{},{},valid)
            self.assertEqual(count,["actual"])
            self.assertEqual(result["quarantinedTaskIds"],[m._TASKS[0]])
            self.assertEqual(result["status"],
                             "V17_SCIENCE_C3_READONLY_TASKS_QUARANTINED_NO_RELEASE")
            self.assertFalse(result["publicationAuthorized"])
            self.assertEqual(result["newOriginalPdfReads"],0)


if __name__=="__main__":
    unittest.main()
