"""BSA316 new explanation producer and owner receipt chain negative controls."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app_generator.validation import section91_third_law_explanation_proof as p
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.runtime import v3_third_law_explanation_academic_admission as a

_PACKAGE = Path("content/chapter-9/section-9-1/package.json")
_REAL_SOURCE_SHA = p._SOURCE_SHA


def _approved_malay_v20_style_fixture():
    """Model only the exact previously authorized Malay conservation repair.

    The actual original-source candidate is owner-private, never copied into
    Git. This fixture tests the same frozen MCQ05 explanation surface.
    """
    package = json.loads(_PACKAGE.read_text(encoding="utf8"))
    text = package["activities"][4]["explanation"]["ms"]
    assert text.count("keabadian momentum") == 1
    assert text.count("Keabadian momentum") == 1
    revised = (text.replace("keabadian momentum", "pemuliharaan momentum")
                   .replace("Keabadian momentum", "Pemuliharaan momentum"))
    package["activities"][4]["explanation"]["ms"] = revised
    return package


class ThirdLawExplanation(TestCase):
    def test_exact_models_and_mutation(self):
        for row in p._pair_models():
            p._reparse_physics(row)
            self.assertEqual(row["totalMomentumBefore"], row["totalMomentumAfter"])
            self.assertNotEqual(row["particle1MomentumBefore"], row["particle1MomentumAfter"])
        bad = deepcopy(p._pair_models()[0])
        bad["forceOn1"] = "0"
        with self.assertRaises(ValueError):
            p._reparse_physics(bad)

    def test_source_bound_restart_falsification(self):
        with TemporaryDirectory() as folder:
            source = Path(folder)/"source.pdf"
            candidate = Path(folder)/"candidate.json"
            source.write_bytes(b"%PDF-synthetic")
            candidate.write_text(json.dumps(_approved_malay_v20_style_fixture(), ensure_ascii=False), encoding="utf8")
            with patch.object(p, "extract_pages", side_effect=AssertionError("unpinned extraction")):
                with self.assertRaisesRegex(ValueError, "AUTHENTIC_SERWAY"):
                    p.independently_prove_third_law_explanation(source_pdf=source, candidate_path=candidate)
            anchors = [{} for _ in range(5)]
            anchors[4] = {"activityId":p._ACTIVITY,"uniquePagePassageLocated":True,
                          "physicalPage":1,"passageSha256":"a"*64}
            with (patch.object(p,"_SOURCE_SHA",sha256(source.read_bytes()).hexdigest()),
                  patch.object(p,"_CANDIDATE_SHA",sha256(candidate.read_bytes()).hexdigest()),
                  patch.object(p,"_source_axioms",return_value={"third law":3,
                      "time rate of change of the linear momentum":1,
                      "defined to be the product of the mass and velocity":1}),
                  patch.object(p,"extract_pages",return_value=["equal in magnitude opposite in direction"]),
                  patch.object(p,"_source_activity_anchors",return_value=anchors),
                  patch.object(p,"plan_full_semantic_proofs",side_effect=lambda **kw:
                      plan_full_semantic_proofs(package=kw["package"],source_sha256=_REAL_SOURCE_SHA))):
                proof=p.independently_prove_third_law_explanation(source_pdf=source,candidate_path=candidate)
                self.assertEqual(proof,p.independently_prove_third_law_explanation(source_pdf=source,candidate_path=candidate))
                forged=deepcopy(proof)
                forged["models"][0]["forceOn1"]="0"
                forged["witnessSha256"]=p._digest({k:v for k,v in forged.items() if k!="witnessSha256"})
                with self.assertRaises(ValueError):
                    p.independently_check_third_law_explanation_witness(forged)
                candidate.write_bytes(candidate.read_bytes()+b" ")
                with self.assertRaisesRegex(ValueError,"AUTHENTIC_SERWAY"):
                    p.independently_prove_third_law_explanation(source_pdf=source,candidate_path=candidate)

    def test_frozen_trilingual_surface(self):
        activity=_approved_malay_v20_style_fixture()["activities"][4]
        self.assertEqual(p._locales(activity["prompt"],p._PROMPT),p._PROMPT)
        self.assertEqual(p._locales(activity["explanation"],p._EXPLANATION),p._EXPLANATION)
        changed=dict(activity["explanation"])
        changed["zh"]+="。"
        with self.assertRaises(ValueError):
            p._locales(changed,p._EXPLANATION)

    def test_prior_chain_and_cross_head_restart(self):
        prior={"independentlyAcceptedAcademicTasks":31,"fullAcademicTasksStillOpen":398,
               "acceptedAcademicTaskIds":[str(i) for i in range(31)],
               "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
               "publicationAuthorized":False,"gliderExplanationReceiptSha256":"prior"}
        with patch.object(a,"verify_glider_explanation_across_git_heads",return_value=prior):
            self.assertEqual(a._prior(Path(".")),prior)
        with patch.object(a,"verify_glider_explanation_across_git_heads",return_value={**prior,"fullAcademicTasksStillOpen":399}):
            with self.assertRaisesRegex(ValueError,"A1_A31_CHAIN"):
                a._prior(Path("."))
        proof={"taskId":"t"*64,"models":p._pair_models()}
        frontier={"gitHead":"a"*40,"proposalSha256":"b"*64,"status":a._FRONTIER_STATUS,
                  "sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA,
                  "cumulativeAcademicTasksAccepted":32,"fullAcademicTasksStillOpen":397,
                  "completeAcademicProofGatesStillOpen":90,"fullAcademicActivityPASS":0,
                  "publicationAuthorized":False,"newScientificReceiptSha256":"signed",
                  "previousAcademicTaskIds":prior["acceptedAcademicTaskIds"],"newAcceptedTaskId":"t"*64}
        now={"gitHead":"c"*40,"proposalSha256":"d"*64,"sourceSha256":a._SOURCE_SHA,"candidateSha256":a._CANDIDATE_SHA}
        receipt={"integritySha256":"signed","previousGliderExplanationReceiptSha256":"prior"}
        def check(fresh):
            with (patch.object(a,"_read_signed",return_value=frontier),
                  patch.object(a,"read_long_horizon_development",return_value=now),
                  patch.object(a,"_verify_receipt",return_value=(receipt,proof)),
                  patch.object(a,"_original_proof",return_value=({}, {}, fresh)),
                  patch.object(a,"_prior",return_value=prior)):
                return a.verify_third_law_explanation_across_git_heads(private=Path("."))
        self.assertTrue(check(proof)["carriedAcrossGitHead"])
        with self.assertRaisesRegex(ValueError,"SCIENCE_CHANGED_ACROSS_CODE_HEADS"):
            check({**proof,"models":[]})

    def test_signed_fifth_partition_requires_exact_canonical_row(self):
        ready={"gitHead":"a"*40,"proposalSha256":"b"*64}
        proof={"taskId":"t"*64,"surfaceSha256":"s"*64,"newProviderCalls":0,
               "publicationAuthorized":False}
        partition={"integritySha256":"signed","sourceSha256":a._SOURCE_SHA,
                   "candidateSha256":a._CANDIDATE_SHA,"academicPASS":0,
                   "publicationAuthorized":False,"activity":{"activityId":p._ACTIVITY,
                   "evidenceRows":[{"taskId":proof["taskId"],"kind":"COMPLETE_SCIENTIFIC_MEANING",
                                    "status":"BOUNDED_SUPPORT_ONLY_REVIEW_REQUIRED",
                                    "surfaceSha256":proof["surfaceSha256"]}]}}
        v36={"signedPartitionHashes":[{} for _ in range(18)],
             "semanticTasksAutomaticallyDispatched":429,"fullAcademicProofTasksAccepted":0,
             "completeAcademicProofGatesStillOpen":90,"sourceSha256":a._SOURCE_SHA,
             "publicationAuthorized":False}
        v36["signedPartitionHashes"][4]={"activityId":p._ACTIVITY,"signedEvidenceSha256":"signed"}
        def run(part):
            with (patch.object(a,"_bound_inputs",return_value=(None,v36,None,Path("source.pdf"),Path("candidate.json"))),
                  patch.object(a,"_signed",return_value=part),
                  patch.object(a,"independently_prove_third_law_explanation",return_value=proof),
                  patch.object(a,"independently_check_third_law_explanation_witness")):
                return a._original_proof(private=Path("."),ready=ready,historical=False)
        self.assertEqual(run(partition)[2],proof)
        for field in ("taskId","kind","status","surfaceSha256"):
            changed=deepcopy(partition)
            changed["activity"]["evidenceRows"][0][field]="forged"
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"SCIENCE_NOT_REPROVEN"):
                run(changed)
        duplicate=deepcopy(partition)
        duplicate["activity"]["evidenceRows"].append(deepcopy(duplicate["activity"]["evidenceRows"][0]))
        with self.assertRaisesRegex(ValueError,"SCIENCE_NOT_REPROVEN"):
            run(duplicate)
