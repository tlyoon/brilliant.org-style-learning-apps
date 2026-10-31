"""Synthetic adversarial admission checks: no source or browser required."""
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from app_generator.validation.fresh_academic_review_admission import (
    admit_fresh_academic_review,
)


class FreshAdmissionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root=Path(tmp.name)
        self.repo=root/"repo";self.repo.mkdir()
        self.private=root/"private";self.private.mkdir()
        self.pdf=self.private/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 mock only")
        self.pkg=self.private/"package.json"
        self.acts=[{"id":f"example-{i}"} for i in range(18)]
        self.pkg.write_text(json.dumps({"activities":self.acts}),encoding="utf-8")
        self.psha=sha256(self.pkg.read_bytes()).hexdigest()
        self.ssha=sha256(self.pdf.read_bytes()).hexdigest()
        self.anchor={"activityId":"example-0","quotedText":"synthetic source only","pageIndex":2}
        self.packet={"sourceAnchors":[self.anchor],
                     "sourceEvidence":"synthetic source evidence - not a textbook",
                     "passageSha256":["a"*64],"verifiedPages":[2]}
        self.packets=self.private/"packets.json"
        self.manifest={
            "packageSha256":self.psha,"sourceSha256":self.ssha,
            "packets":{a["id"]:self.packet for a in self.acts}}
        self.queue=self.private/"queue.json"
        self.queue_data={
            "status":"SOURCE_BOUND_AUTONOMOUS_ACADEMIC_REVIEW_QUEUE",
            "packageSha256":self.psha,"sourceSha256":self.ssha,
            "activityCount":18,"publicationAuthorized":False,
            "activities":[{"activityId":a["id"],
                           "priority":"INDEPENDENT_MULTILINGUAL_SEMANTIC_REVIEW",
                           "missingOrUnsentReviewSlots":10,
                           "unreconciledSubmittedOrSkippedClaims":0,
                           "publicationAuthorized":False} for a in self.acts]}
        self.neutral=self.private/"neutral.json"
        self.neutral_data={
            "status":"NEUTRAL_TWO_CONTEXTS_CONFIRMED",
            "reviewerMode":"same_authorized_login_separate_new_chats",
            "sourcePdfUploaded":False,"promptContainsSource":False,
            "providerAccountsIndependent":False,
            "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
            "roles":{name:{"state":"COMPLETE_CAPTURED","responseCaptured":True,
                           "validRoleAndShape":True,
                           "promptSha256":"a"*64,"responseSha256":"b"*64}
                     for name in ("physics","semantics")}}
        self.write()
        self.args=dict(
            package_file=self.pkg,source_pdf=self.pdf,packets_file=self.packets,
            priority_queue_file=self.queue,neutral_receipt_file=self.neutral,
            private_evidence_root=self.private,run_id="new-run-a",
            activity_id="example-0",claim_prefix="new-review-a",
            repository_root=self.repo)

    def write(self):
        self.packets.write_text(json.dumps(self.manifest),encoding="utf-8")
        self.queue.write_text(json.dumps(self.queue_data),encoding="utf-8")
        self.neutral.write_text(json.dumps(self.neutral_data),encoding="utf-8")

    def verify(self):
        with patch(
            "app_generator.validation.fresh_academic_review_admission.verified_source_packet",
            return_value={**self.packet,"activityId":"example-0","sourceSha256":self.ssha}
        ) as verifier:
            result=admit_fresh_academic_review(**self.args)
            verifier.assert_called_once()
        return result

    def test_fresh_source_bound_admission_does_not_open_browser(self):
        result=self.verify()
        self.assertEqual("example-0",result["activityId"])
        self.assertEqual(self.psha,result["packageSha256"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertFalse(result["privateRunDirectory"].exists())

    def test_previous_run_path_cannot_be_overwritten(self):
        (self.private/"academic-new-review-runs"/"new-run-a").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,"never replay"):
            self.verify()

    def test_previous_submitted_claim_detected_even_when_queue_is_stale(self):
        batch=self.private/"another-review"/"batches"
        batch.mkdir(parents=True)
        (batch/"previous-source-fidelity-0.json").write_text(json.dumps({
            "activityId":"example-0","sourceHash":self.ssha,"packageHash":self.psha,
            "state":"AMBIGUOUS"}),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"existing private activity review"):
            self.verify()

    def test_previous_claim_priority_is_blocked(self):
        self.queue_data["activities"][0]["priority"]="RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS"
        self.write()
        with self.assertRaisesRegex(ValueError,"cannot be replayed"):
            self.verify()

    def test_neutral_ambiguous_response_is_not_replayed(self):
        self.neutral_data["roles"]["semantics"]["state"]="POSSIBLY_SENT"
        self.write()
        with self.assertRaisesRegex(ValueError,"not completely captured"):
            self.verify()

    def test_changed_source_and_packet_fail_closed(self):
        self.pdf.write_bytes(b"%PDF-1.4 changed")
        with self.assertRaisesRegex(ValueError,"identity mismatch"):
            self.verify()
        self.pdf.write_bytes(b"%PDF-1.4 mock only")
        self.manifest["packets"]["example-0"]={**self.packet,"verifiedPages":[3]}
        self.write()
        with self.assertRaisesRegex(ValueError,"passage/page"):
            self.verify()

    def test_expired_success_receipt_does_not_authorize_new_model_request(self):
        old=time.time()-1801
        os.utime(self.neutral,(old,old))
        with self.assertRaisesRegex(ValueError,"expired"):
            self.verify()

    def test_future_clock_and_uncaptured_response_digests_rejected(self):
        future=time.time()+90
        os.utime(self.neutral,(future,future))
        with self.assertRaisesRegex(ValueError,"clock"):
            self.verify()
        self.write()
        self.neutral_data["roles"]["semantics"]["responseSha256"]=None
        self.write()
        with self.assertRaisesRegex(ValueError,"not completely captured"):
            self.verify()

    def test_newer_failed_neutral_probe_invalidates_recent_success(self):
        earlier=self.private/"section94-neutral-gemini-probe-earlier"
        earlier.mkdir()
        newer=self.private/"section94-neutral-gemini-probe-newer"
        newer.mkdir()
        old_receipt=earlier/"state.json"
        old_receipt.write_text(json.dumps(self.neutral_data),encoding="utf-8")
        now=time.time()
        os.utime(old_receipt,(now-20,now-20))
        blocked=newer/"state.json"
        blocked.write_text(json.dumps({
            "status":"BLOCKED_BEFORE_OR_DURING_PROBE",
            "failurePhase":"FRESH_NEUTRAL_TAB_NAVIGATION",
            "remoteRequestPossiblySubmitted":False,
        }),encoding="utf-8")
        os.utime(blocked,(now-10,now-10))
        with self.assertRaisesRegex(ValueError,"newer neutral Gemini probe"):
            with patch(
                "app_generator.validation.fresh_academic_review_admission.verified_source_packet",
            ):
                admit_fresh_academic_review(**{
                    **self.args,"neutral_receipt_file":old_receipt})
        os.utime(blocked,(now-30,now-30))
        with patch(
            "app_generator.validation.fresh_academic_review_admission.verified_source_packet",
            return_value={**self.packet,"activityId":"example-0",
                          "sourceSha256":self.ssha},
        ):
            result=admit_fresh_academic_review(**{
                **self.args,"neutral_receipt_file":old_receipt})
        self.assertEqual("example-0",result["activityId"])

    def test_source_bearing_or_approved_neutral_cannot_pass_admission(self):
        for key,value in (
            ("sourcePdfUploaded",True),("promptContainsSource",True),
            ("publicationAuthorized",True),("providerAccountsIndependent",True),
        ):
            with self.subTest(field=key):
                original=self.neutral_data[key]
                self.neutral_data[key]=value
                self.write()
                with self.assertRaisesRegex(ValueError,"source-free neutral readiness"):
                    self.verify()
                self.neutral_data[key]=original
        self.write()

    def test_neutral_wrong_role_or_duplicate_context_rejected(self):
        self.neutral_data["roles"]["extra"]={
            "state":"COMPLETE_CAPTURED","responseCaptured":True,
            "validRoleAndShape":True,"promptSha256":"a"*64,
            "responseSha256":"b"*64}
        self.write()
        with self.assertRaisesRegex(ValueError,"both independent"):
            self.verify()

    def test_private_paths_and_unsafe_run_names_rejected(self):
        with self.assertRaisesRegex(ValueError,"authorized private"):
            admit_fresh_academic_review(**{**self.args,"private_evidence_root":self.repo})
        with self.assertRaisesRegex(ValueError,"unique safe"):
            admit_fresh_academic_review(**{**self.args,"run_id":"../unsafe"})

    def test_unrecognized_broken_claim_receipt_fails_closed(self):
        batch=self.private/"old"/"batches"
        batch.mkdir(parents=True)
        (batch/"bad.json").write_text("[]",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"unrecognized private"):
            self.verify()


if __name__=="__main__":
    unittest.main()
