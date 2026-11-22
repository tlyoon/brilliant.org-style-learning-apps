"""BSA250: fresh exact revision-only source-bound model QA never replays."""
from __future__ import annotations
from contextlib import nullcontext
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_revised91_fresh_model_reviews as m
from app_generator.runtime import v3_exact_revised_review_reconciliation as v22
from app_generator.runtime.v3_malay_auto_revision import _CANDIDATE
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.validation.malay_conservation_lexicon import _replace_in_malay,ROOTS

ROOT=Path(__file__).resolve().parents[1]


class PrivateNew91ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.private=Path(self.tmp.name)/"private"
        self.private.mkdir()
        self.head="a"*40
        self.proposal="b"*64
        self.folder=self.private/"owner-five-stage-completion"/self.head/self.proposal
        self.folder.mkdir(parents=True)
        self.source_root=self.private/"Serway"
        self.pdf=self.source_root/"9"/"9.1"/"source.pdf"
        self.pdf.parent.mkdir(parents=True)
        self.pdf.write_bytes(b"%PDF-actual-source-content-test-fixture")
        self.source_sha=sha256(self.pdf.read_bytes()).hexdigest()
        self.original=json.loads((ROOT/"content/chapter-9/section-9-1/package.json"
                                  ).read_text(encoding="utf8"))
        paths=[];counts={s:0 for s,_,_ in ROOTS}
        self.revised=_replace_in_malay(self.original,"",paths,counts)
        raw=(json.dumps(self.revised,ensure_ascii=False,indent=2)+"\n").encode("utf8")
        (self.folder/_CANDIDATE).write_bytes(raw)
        self.candidate_sha=sha256(raw).hexdigest()
        self.identity={"gitHead":self.head,"proposalSha256":self.proposal,
                       "publicationAuthorized":False}
        _v6_checkpoint(self.private/m._SOURCE_BINDING,{
            "contract":"BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1",
            "sourceRoot":str(self.source_root),"sourcePdf":str(self.pdf),
            "sourceSha256":self.source_sha,"section":"9.1",
            "externalFallbackAllowed":False,"sourcePdfUploaded":False,
        })
        by_id={a["id"]:i for i,a in enumerate(self.revised["activities"])}
        fresh=[{
            "activityId":aid,
            "originalIndex":by_id[aid],
            "activityCanonicalSha256":sha256(json.dumps(
                self.revised["activities"][by_id[aid]],
                sort_keys=True,ensure_ascii=False,
                separators=(",",":")).encode("utf8")).hexdigest(),
        } for aid in sorted(v22._REVISED)]
        rows=v22._stage_changed_private(
            folder=self.folder,candidate=self.revised,
            candidate_sha=self.candidate_sha,source_sha=self.source_sha,
            fresh=fresh)
        r21=_v6_checkpoint(self.folder/m._RESULT21,{
            **self.identity,"sourceSha256":self.source_sha,
            "revisedCandidateSha256":self.candidate_sha,
        })
        v21=_v6_checkpoint(self.folder/m._V21,{
            **self.identity,"resultSha256":r21["integritySha256"],
        })
        r22=_v6_checkpoint(self.folder/m._RESULT22,{
            **self.identity,"sourceSha256":self.source_sha,
            "revisedCandidateSha256":self.candidate_sha,
            "existingVerifiedOriginalReviewerPairs":17,
            "advisoryHistoricallyVerifiedIdenticalRolePairs":13,
            "changedActivityOldPairsNotTransferred":4,
            "originalIndex0UncertainQuarantined":True,
            "independentFullAcademicProofSlotsOpen":90,
            "newPrivateVersionedReviewInputsStaged":rows,
        })
        self.v22=_v6_checkpoint(self.folder/m._V22,{
            **self.identity,
            "status":m._STATUS22,
            "resultSha256":r22["integritySha256"],
            "sourceV21ReceiptSha256":v21["integritySha256"],
            "oldUncertainRoleReplayed":False,
            "newGeminiCalls":0,"formalAcademicPASS":0,
        })

    def plan(self):
        return m.fresh_revised91_inputs(
            repo=ROOT,private=self.private,
            source_head=self.head,proposal_sha=self.proposal)

    def test_real_four_immutable_revised_version_inputs_preflight(self):
        result=self.plan()
        self.assertEqual(result["status"],
                         "FOUR_NEW_EXACT_REVISED_91_REVIEW_INPUTS_VERIFIED")
        self.assertEqual(len(result["stagedReviewInputs"]),4)
        self.assertEqual(len({x["sha"] for x in result["stagedReviewInputs"]}),4)
        self.assertTrue(result["oldOriginalUncertainStillQuarantined"])
        self.assertEqual(result["fullAcademicProofSlotsStillOpen"],90)
        self.assertFalse(result["publicationAuthorized"])
        for entry in result["stagedReviewInputs"]:
            decoded=json.loads(entry["raw"].decode("utf8"))
            self.assertFalse(decoded["sourcePdfUploaded"])
            self.assertFalse(decoded["originalReviewerClaimsTransferred"])
            self.assertEqual(decoded["sourcePackageSha256"],self.candidate_sha)
            self.assertEqual(len(decoded["activities"]),1)

    def test_source_pdf_modification_blocks_all_new_roles(self):
        self.pdf.write_bytes(b"%PDF-altered-private-source")
        with self.assertRaisesRegex(ValueError,"V23_ORIGINAL_SELECTED_PRIVATE_PDF_CHANGED"):
            self.plan()

    def test_modified_candidate_bytes_block_all_new_roles(self):
        p=self.folder/_CANDIDATE
        p.write_bytes(p.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"V23_REVISED_91_GENERATED_CONTENT"):
            self.plan()

    def test_tampered_signed_v22_result_denied(self):
        p=self.folder/m._V22
        data=json.loads(p.read_text(encoding="utf8"))
        data["newGeminiCalls"]=8
        p.write_text(json.dumps(data),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"EXACT_SIGNED_PREVIOUS_STAGE"):
            self.plan()

    def test_tampered_private_role_input_denied(self):
        row=json.loads((self.folder/m._RESULT22).read_text(encoding="utf8")
                       )["newPrivateVersionedReviewInputsStaged"][0]
        target=self.folder/m._QUEUE/row["reviewInputSha256"]/"activity.json"
        target.write_bytes(b"forged-activity")
        with self.assertRaisesRegex(ValueError,"V23_NEW_VERSIONED_PRIVATE_ROLE_INPUT_CHANGED"):
            self.plan()

    def test_original_frozen_index0_not_new_scope(self):
        plan=self.plan()
        expected=set(v22._REVISED)
        self.assertEqual({x["activityId"] for x in plan["stagedReviewInputs"]},expected)
        self.assertNotIn(self.original["activities"][0]["id"],expected)

    def test_unsafe_version_identifier_refused(self):
        with self.assertRaisesRegex(ValueError,"V23_PRECISE_SIGNED"):
            m.fresh_revised91_inputs(repo=ROOT,private=self.private,
                source_head="../x",proposal_sha=self.proposal)

    def test_old_unknown_run_is_never_resubmitted(self):
        plan=self.plan()
        count=[]
        def forbidden(*args):
            count.append("PAID");raise AssertionError("must not send")
        def deny_prior(*args):
            raise ValueError("V3_REVISED96_OLD_REQUEST_UNRESOLVED_NO_REPLAY")
        with (patch.object(m,"authorize_standing",return_value={
                "maxPaidGeminiCalls":8,"standingConsent":True}),
              patch.object(m,"fresh_revised91_inputs",return_value=plan),
              patch("app_generator.runtime.v3_yoga6_recovery.coordinator_lock",
                    return_value=nullcontext()),
              patch.object(m,"section91_evidence",return_value={
                    "oldUncertainIndex":0,"originalAssessedUnchanged":1}),
              patch.object(m,"unsent_revised_input",return_value=False),
              patch.object(m,"read_prior_two_role_science",side_effect=deny_prior)):
            with self.assertRaisesRegex(ValueError,"OLD_REQUEST_UNRESOLVED_NO_REPLAY"):
                m.advance_bounded_revised91(
                    repo=ROOT,private=self.private,
                    source_head=self.head,proposal_sha=self.proposal,
                    execute=True,transfer=True,review_one=forbidden)
        self.assertEqual(count,[])

    def test_both_explicit_execution_and_text_transfer_required(self):
        with self.assertRaises(ValueError):
            m.advance_bounded_revised91(
                repo=ROOT,private=self.private,
                source_head=self.head,proposal_sha=self.proposal,
                execute=False,transfer=False,review_one=lambda *_:None)

    def test_new_review_failure_does_not_fabricate_evidence(self):
        plan=self.plan()
        def failed(*args):
            return {"activitiesAssessed":1}
        with (patch.object(m,"authorize_standing",return_value={
                "maxPaidGeminiCalls":8,"standingConsent":True}),
              patch.object(m,"fresh_revised91_inputs",return_value=plan),
              patch("app_generator.runtime.v3_yoga6_recovery.coordinator_lock",
                    return_value=nullcontext()),
              patch.object(m,"section91_evidence",return_value={
                    "oldUncertainIndex":0,"originalAssessedUnchanged":1}),
              patch.object(m,"unsent_revised_input",return_value=True),
              patch.object(m,"verify_persisted_two_role_science",
                          side_effect=ValueError("REAL_RECEIPTS_MISSING"))):
            with self.assertRaisesRegex(ValueError,"REAL_RECEIPTS_MISSING"):
                m.advance_bounded_revised91(
                    repo=ROOT,private=self.private,
                    source_head=self.head,proposal_sha=self.proposal,
                    execute=True,transfer=True,review_one=failed)

    def test_normal_authorized_entrypoint_is_separate_from_frozen_campaign(self):
        p=ROOT/"scripts/run_v3_revised91_fresh_model_reviews.py"
        source=p.read_text(encoding="utf8")
        self.assertIn("advance_bounded_revised91(",source)
        self.assertIn("delegate_to_supported_sdk(",source)
        self.assertIn("--allow-generated-text-transfer",source)
        sdk=(ROOT/"app_generator/runtime/native_sdk_environment.py"
             ).read_text(encoding="utf8")
        self.assertIn('run_v3_revised91_fresh_model_reviews.py',sdk)


if __name__=="__main__":
    unittest.main()
