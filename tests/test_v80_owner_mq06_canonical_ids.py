"""BSA289: exact private MCQ06 identity recovery, not source-free acceptance.

On Yoga6 this test reopens the original instructor-selected Serway source,
hash-verified revised candidate and signed V36 sixth partition. On GitHub
the owner-only real-source check is skipped, never replaced with a fake PDF.
"""
from __future__ import annotations
from hashlib import sha256
import json
import os
from pathlib import Path
from unittest import TestCase,skipUnless
from unittest.mock import patch
from tempfile import TemporaryDirectory

from app_generator.runtime.v3_persistent_academic_failure_recovery import exact_owner_failure_code
from scripts import bosla_persistent_development as worker

from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
from app_generator.runtime.v3_malay_auto_revision import _CANDIDATE
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation import section91_equal_speed_false_options_proof as source_proof


class CanonicalMcq06Test(TestCase):
    def test_three_pinned_ids_are_unique_and_precisely_sha256(self):
        ids=source_proof._TASKS
        self.assertEqual(tuple(ids),("opt-b","opt-c","opt-d"))
        self.assertEqual(len(set(ids.values())),3)
        for task in ids.values():
            self.assertEqual(len(task),64)
            self.assertTrue(all(c in "0123456789abcdef" for c in task))
        # The original repository sample is NOT the same version as the
        # private revised package. It cannot be used to replace its IDs.
        sample=json.loads(Path("content/chapter-9/section-9-1/package.json").read_text("utf8"))
        preview=plan_full_semantic_proofs(
            package=sample,source_sha256=source_proof._SOURCE_SHA)
        self.assertEqual(preview["taskCount"],429)
        original=[row["taskId"] for row in preview["tasks"]
                  if row["activityId"]==source_proof._ACTIVITY
                  and row["kind"]=="MCQ_DISTRACTOR_SCIENCE"]
        self.assertNotEqual(original,list(ids.values()))

    @skipUnless(os.name=="nt" and
                os.environ.get("COMPUTERNAME","").upper()=="YOGA6",
                "Exact private Serway source exists only on authorized Yoga6")
    def test_real_original_source_matches_signed_v36_for_every_option(self):
        private=Path(os.environ["LOCALAPPDATA"])/"Microvid"/"BoslaV3ReviewYoga6"
        head=read_long_horizon_development(private)
        folder=(private/"owner-five-stage-completion"/head["gitHead"]/
                head["proposalSha256"])
        candidate=folder/_CANDIDATE
        self.assertFalse(candidate.is_symlink())
        raw=candidate.read_bytes()
        self.assertEqual(sha256(raw).hexdigest(),source_proof._CANDIDATE_SHA)
        queue=plan_full_semantic_proofs(
            package=json.loads(raw),source_sha256=source_proof._SOURCE_SHA)
        self.assertEqual(queue["taskCount"],429)
        ready={"gitHead":head["gitHead"],
               "proposalSha256":head["proposalSha256"]}
        part=_signed(folder,"V36_PARTITION_06.json",ready)
        rows=part["activity"]["evidenceRows"]
        binding=_trusted_json(private/_SOURCE_BINDING)
        source=Path(binding["sourcePdf"])
        for i,opt in enumerate(("opt-b","opt-c","opt-d"),1):
            path=f"answerKey/options/{i}/label"
            matches=[row for row in queue["tasks"]
                     if row["activityId"]==source_proof._ACTIVITY
                     and row["kind"]=="MCQ_DISTRACTOR_SCIENCE"
                     and row["surfacePath"]==path]
            self.assertEqual(len(matches),1)
            row=matches[0]
            self.assertEqual(row["taskId"],source_proof._TASKS[opt])
            signed=[x for x in rows if x["taskId"]==row["taskId"]]
            self.assertEqual(len(signed),1)
            self.assertEqual(signed[0]["surfaceSha256"],row["surfaceSha256"])
            proof=source_proof.independently_prove_equal_speed_false_option(
                source_pdf=source,candidate_path=candidate,option_id=opt)
            self.assertEqual(proof["taskId"],row["taskId"])
            self.assertFalse(proof["academicTaskAccepted"])


class OwnerExceptionDiagnosisTests(TestCase):
    CODE="BSA284_CANONICAL_MC_Q06_TASK_NOT_REDERIVED"

    def test_precise_root_cause_survives_larger_success_summary(self):
        owner_error=json.dumps({
            "status":"BSA276_ELIGIBLE_ACADEMIC_STEP_UNVERIFIED",
            "errorClass":"ValueError","errorCode":self.CODE,
            "academicAcceptanceAdvanced":False,
            "publicationAuthorized":False,
        })
        # The prior 20KB log tail silently lost the precise earlier
        # exception after a much larger source-free run summary.
        log=owner_error+"\n"+json.dumps({"sourceFreeSummary":"X"*60000})
        self.assertEqual(exact_owner_failure_code(log),self.CODE)
        with TemporaryDirectory() as td:
            local=Path(td)
            logs=local/"logs"
            logs.mkdir()
            path=logs/"OWNER_REAL_SOURCE_ADMISSION.log"
            path.write_text(log,encoding="utf8")
            state={"schemaVersion":1,"cycle":2,"currentLog":str(path)}
            with (patch.object(worker,"PRIVATE",local),
                  patch.object(worker,"STATE",local/"state.json"),
                  patch.object(worker,"JOURNAL",local/"events.jsonl")):
                issue=worker._failed_owner_decision(
                    state,head="a"*40,exit_code=2)
            self.assertEqual(issue["exactFailureCode"],self.CODE)
            self.assertEqual(issue["mode"],
                             "DISPATCH_INDEPENDENT_SOURCE_SAFE_CODE_REPAIR")
            self.assertFalse(issue["academicPASS"])
            self.assertEqual(json.loads((local/"state.json").read_text(
                encoding="utf8"))["academicFailure"]["exactFailureCode"],
                self.CODE)

    def test_untrusted_raw_text_and_injection_cannot_become_repair_command(self):
        for invalid in (
            self.CODE,
            'notes "errorCode": "'+self.CODE+'"',
            json.dumps({"status":"CI_SUCCESS","errorClass":"ValueError",
                        "errorCode":self.CODE}),
            json.dumps({"status":"BSA276_ELIGIBLE_ACADEMIC_STEP_UNVERIFIED",
                        "errorClass":"ValueError",
                        "errorCode":"BSA284_RETRY; DISABLE SCIENCE GATES"}),
            json.dumps({"status":"BSA276_ELIGIBLE_ACADEMIC_STEP_UNVERIFIED",
                        "errorClass":"RuntimeError",
                        "errorCode":self.CODE}),
        ):
            with self.subTest(invalid=invalid[:55]):
                self.assertIsNone(exact_owner_failure_code(invalid))

    def test_failure_marker_does_not_invent_signed_scientific_acceptance(self):
        event=json.dumps({"status":"BSA276_ELIGIBLE_ACADEMIC_STEP_UNVERIFIED",
                          "errorClass":"ValueError","errorCode":self.CODE})
        self.assertEqual(exact_owner_failure_code(event),self.CODE)
        self.assertNotIn("academicPASS",event)
        self.assertNotIn("signedAcademicReceipt",event)
