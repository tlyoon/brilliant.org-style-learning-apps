"""BSA248/V21: source-reverified candidate, adversarial scope, normal dispatch."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_revised_source_proof_rebinding as m
from app_generator.runtime.v3_five_stage_completion import _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_selected_textbook_scientific_provenance import (
    _source_candidates,
)
from app_generator.validation.malay_conservation_lexicon import (
    _replace_in_malay, ROOTS,
)
from app_generator.validation.source_passages import _normalized
from app_generator.validation.academic_qa import REQUIRED

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / m._PACKAGE
CHANGED = {
    "act-mcq-05-third-law-connection",
    "act-mcq-08-isolated-subsystem-fallacy",
    "act-int-05-newton-second-law-steps-order",
    "act-int-08-conservation-validity-select",
}


class ExactRevisionRebindTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source_root = self.root/"source-root"
        self.pdf = self.source_root/"9"/"9.1"/"source.pdf"
        self.pdf.parent.mkdir(parents=True)
        self.pdf.write_bytes(b"%PDF-test-only-not-an-actual-source")
        self.source_sha = sha256(self.pdf.read_bytes()).hexdigest()
        self.original_raw = PACKAGE.read_bytes()
        self.original = json.loads(self.original_raw)
        self.original_sha = sha256(self.original_raw).hexdigest()
        paths=[]
        counts={src:0 for src,_,_ in ROOTS}
        self.candidate = _replace_in_malay(self.original,"",paths,counts)
        self.assertEqual(set(a["id"] for a,b in zip(
            self.original["activities"], self.candidate["activities"]) if a!=b),
            CHANGED)
        self.candidate_raw=(json.dumps(
            self.candidate, ensure_ascii=False,indent=2)+"\n").encode("utf8")
        self.candidate_sha=sha256(self.candidate_raw).hexdigest()
        self.quote=("The linear momentum of a particle depends on its mass and "
                    "velocity. Newton's second law connects the net external "
                    "force to the rate of change of system momentum. A closed "
                    "system can have internal interactions that cancel in the "
                    "total system momentum balance. This sentence is a synthetic "
                    "PDF fixture, not a scientific source verification.")
        self.candidates=_source_candidates((self.quote,))
        self.assertTrue(self.candidates)
        page,quote,_=self.candidates[0]
        self.assertEqual(page,1)
        digest=sha256(_normalized(quote).encode("utf8")).hexdigest()
        self.anchors=[{
            "activityId":a["id"],
            "activitySha256":_hash(a),
            "physicalPage":1,
            "passageSha256":digest,
            "uniquePagePassageLocated":True,
            "scientificMeaningVerified":False,
        } for a in self.original["activities"]]

    def bind(self, *, candidate=None, anchors=None, source_sha=None,
             expected=None):
        with (patch(
            "app_generator.runtime.v3_historical_academic_audit.extract_pages",
            return_value=(self.quote,)),
              patch.object(m,"extract_pages",return_value=(self.quote,))):
            return m.independently_rebind_revision(
                pdf=self.pdf,source_sha=self.source_sha if source_sha is None else source_sha,
                original=self.original,
                candidate=self.candidate if candidate is None else candidate,
                original_sha=self.original_sha,candidate_sha=self.candidate_sha,
                original_anchors=self.anchors if anchors is None else anchors,
                expected_changed_ids=CHANGED if expected is None else expected,
            )

    def test_reverify_real_pdf_locator_not_old_model_claim(self):
        packets, changed=self.bind()
        self.assertEqual(set(changed),CHANGED)
        self.assertEqual(len(packets["packets"]),18)
        self.assertEqual(packets["packageSha256"],self.candidate_sha)
        for aid,packet in packets["packets"].items():
            self.assertEqual(packet["sourceSha256"],self.source_sha)
            self.assertEqual(packet["activityChangedSinceOriginal"],aid in CHANGED)
            self.assertFalse(packet["priorModelReviewTransferred"])
            self.assertFalse(packet["sourceInterpretationVerified"])
            self.assertTrue(packet["sourceLocationOnly"])
            self.assertEqual(packet["verifiedPages"],[1])

    def test_original_pdf_changed_rejected_before_any_source_promotion(self):
        self.pdf.write_bytes(b"%PDF-different-actual-input")
        with self.assertRaisesRegex(ValueError,"V21_SELECTED_ORIGINAL_PDF"):
            self.bind()

    def test_new_answer_key_change_cannot_borrow_source_alignment(self):
        rev=json.loads(json.dumps(self.candidate))
        rev["activities"][4]["answerKey"]["correct"]="injected-wrong-key"
        with self.assertRaisesRegex(ValueError,"V21_REVISED_NON_MALAY"):
            self.bind(candidate=rev)

    def test_extra_malay_edit_on_fifth_activity_disallowed(self):
        rev=json.loads(json.dumps(self.candidate))
        rev["activities"][0]["prompt"]["ms"] += " extra"
        with self.assertRaisesRegex(ValueError,"V21_UNREVIEWED_CANDIDATE"):
            self.bind(candidate=rev)

    def test_revised_activity_identity_or_duplicate_rejected(self):
        rev=json.loads(json.dumps(self.candidate))
        rev["activities"][1]["id"]=rev["activities"][0]["id"]
        with self.assertRaisesRegex(ValueError,"V21_REVISED_ROSTER"):
            self.bind(candidate=rev)

    def test_previous_passage_digest_tamper_cannot_be_reused(self):
        anchors=json.loads(json.dumps(self.anchors))
        anchors[0]["passageSha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"V20_SOURCE_ANCHOR_NOT_REFOUND"):
            self.bind(anchors=anchors)

    def test_old_reviewer_or_changed_english_never_becomes_pass(self):
        rev=json.loads(json.dumps(self.candidate))
        rev["activities"][4]["prompt"]["en"] += " incorrect external edit"
        with self.assertRaisesRegex(ValueError,"V21_REVISED_NON_MALAY"):
            self.bind(candidate=rev)


class NormalStageV21Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.private=Path(self.tmp.name)/"private"
        self.private.mkdir()
        self.folder=self.private/"signed"
        self.folder.mkdir()
        self.source_root=self.private/"external-selected"
        self.pdf=self.source_root/"9"/"9.1"/"source.pdf"
        self.pdf.parent.mkdir(parents=True)
        self.pdf.write_bytes(b"%PDF-test-private")
        self.source_sha=sha256(self.pdf.read_bytes()).hexdigest()
        self.ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        self.original_raw=PACKAGE.read_bytes()
        self.original_sha=sha256(self.original_raw).hexdigest()
        orig=json.loads(self.original_raw)
        paths=[]; counts={src:0 for src,_,_ in ROOTS}
        candidate=_replace_in_malay(orig,"",paths,counts)
        candraw=(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n").encode("utf8")
        self.candidate_sha=sha256(candraw).hexdigest()
        (self.folder/m._CANDIDATE).write_bytes(candraw)
        self.bind=_v6_checkpoint(self.private/m._SOURCE_BINDING,{
            "contract":"BOSLA_SELECTED_SERWAY_TEXTBOOK_LOCAL_BINDING_V1",
            "section":"9.1", "sourceRoot":str(self.source_root),
            "sourcePdf":str(self.pdf),"sourceSha256":self.source_sha,
            "externalFallbackAllowed":False,"sourcePdfUploaded":False,
        })
        identity={**self.ready,"publicationAuthorized":False}
        self.v18=_v6_checkpoint(self.folder/m._V18,{
            **identity,"status":m._STATUS18,
        })
        self.v19=_v6_checkpoint(self.folder/m._V19,{
            **identity,"status":m._STATUS19,
            "sourceV18ReceiptSha256":self.v18["integritySha256"],
        })
        self.source18=_v6_checkpoint(self.folder/
            "V18_SELECTED_TEXTBOOK_SCIENCE_RESULT.json",{
            **identity,
            "audit":{"sourceSha256":self.source_sha,
                     "packageSha256":self.original_sha,
                     "sourceAnchors":[]},
        })
        self.repair=_v6_checkpoint(self.folder/m._MALAY_RECEIPT,{
            **identity,"status":m._REPAIR_STATUS,
            "originalPackageSha256":self.original_sha,
            "newPrivateCandidateSha256":self.candidate_sha,
            "affectedOriginalActivityIds":sorted(CHANGED),
            "repairedActivityCount":4,
            "newCandidateFiveGateNegativeFindings":0,
            "newCandidateAll18AcademicQA":"REVIEW_REQUIRED",
            "oldGeminiReviewerClaimsTransferred":False,
            "otherLocalesOrAnswerKeysModified":False,
            "originalPackageModified":False,
        })
        self.result20=_v6_checkpoint(self.folder/m._RESULT20,{
            **identity,
            "automaticHistoricalMalayRepair":{
                "receiptSha256":self.repair["integritySha256"]
            },
        })
        self.v20=_v6_checkpoint(self.folder/m._V20,{
            **identity,"status":m._STATUS20,
            "sourceV19ReceiptSha256":self.v19["integritySha256"],
            "sourceV18ResultSha256":self.source18["integritySha256"],
            "resultSha256":self.result20["integritySha256"],
            "automaticKnownMalayRepairStatus":m._REPAIR_STATUS,
            "formalAcademicPASS":0, "newModelCalls":0,
            "independentAcademicProofSlotsStillOpen":90,
        })

    def fake_report(self):
        candidate=json.loads((self.folder/m._CANDIDATE).read_text(encoding="utf8"))
        return {
            "packageSha256":self.candidate_sha,
            "sourceSha256":self.source_sha,
            "activityCount":18,
            "counts":{"PASS":0,"FAIL":0,"REVIEW_REQUIRED":18},
            "publicationAuthorized":False,
            "activities":[{
                "activityId":a["id"],
                "activitySha256":sha256(json.dumps(
                    a,sort_keys=True,ensure_ascii=False,
                    separators=(",",":")).encode("utf8")).hexdigest(),
                "sourceLocationVerified":True,
                "sourcePages":[1],
                "gates":{g:"REVIEW_REQUIRED" for g in REQUIRED},
                "academicQA":"REVIEW_REQUIRED",
            } for a in candidate["activities"]],
        }

    def execute(self, *, report=None):
        with (
            patch.object(m,"_preflight",return_value=(
                self.folder,None,None,None,None)),
            patch.object(m,"independently_rebind_revision",
                         return_value=(
                {"packageSha256":self.candidate_sha,
                 "sourceSha256":self.source_sha,
                 "packets":{a["id"]:{} for a in json.loads(self.original_raw)["activities"]}},
                sorted(CHANGED))),
            patch.object(m,"audit_activity_matrix",
                         return_value=self.fake_report() if report is None else report),
        ):
            return m.run_post_v20_revised_source_rebind(
                ROOT,self.private,self.ready,{},{},{},
                self.v18,self.v19,self.v20,
            )

    def test_normal_signed_v21_private_version_chain_idempotent(self):
        first=self.execute()
        self.assertEqual(first,self.execute())
        self.assertEqual(first["status"],m._STATUS21)
        self.assertEqual(first["candidateSourceLocationsActuallyReverified"],18)
        self.assertEqual(first["changedActivitiesReverified"],4)
        self.assertEqual(first["verifiedBoundedMathIdentities"],6)
        self.assertEqual(first["verifiedBoundedMCQCorrectKeyPatterns"],5)
        self.assertEqual(first["candidateFormalAcademicPASS"],0)
        self.assertEqual(first["priorModelReviewerClaimsTransferred"],0)
        self.assertFalse(first["publicationAuthorized"])
        result=json.loads((self.folder/m._RESULT21).read_text(encoding="utf8"))
        self.assertEqual(len(result["candidateRows"]),18)
        self.assertNotIn("sourceEvidence",str(result))
        self.assertEqual(result["gateEvidenceStillReviewRequired"],90)

    def test_tampered_signatures_from_v20_stopped_before_pre_call(self):
        self.v20={**self.v20,"newModelCalls":1}
        with self.assertRaisesRegex(ValueError,"V21_REVISED_SOURCE_INVALID"):
            self.execute()
        self.assertFalse((self.folder/m._PRE21).exists())

    def test_changed_candidate_bytes_refused_before_source_check(self):
        p=self.folder/m._CANDIDATE
        p.write_bytes(p.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"V21_STALE_OR_CHANGED"):
            self.execute()
        self.assertFalse((self.folder/m._PRE21).exists())

    def test_forged_full_academic_pass_cannot_be_accepted(self):
        report=self.fake_report()
        report["counts"]={"PASS":18,"FAIL":0,"REVIEW_REQUIRED":0}
        with self.assertRaisesRegex(ValueError,"V21_REVISED_FIVE_GATE"):
            self.execute(report=report)

    def test_stage_normal_worker_integration_required(self):
        worker=(ROOT/"scripts/run_v3_yoga6_recovery_worker.py"
                ).read_text(encoding="utf8")
        self.assertIn("run_post_v20_revised_source_rebind(",worker)
        self.assertIn('result["revisedSourceProofRebinding"]',worker)
        self.assertIn('"candidateSourceLocationsActuallyReverified")==18',worker)


if __name__=="__main__":
    unittest.main()
