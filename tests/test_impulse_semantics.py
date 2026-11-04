import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.validation.impulse_qualifier_repair import ACTIVITY_ID, REVISION
from app_generator.validation.impulse_semantics import (
    IDS, SELECTED, option_signature, ordered_condition, narrative_semantic_surface,
    physics_counterexamples, audit_impulse_candidate,
)


class TrilingualDistractorTests(unittest.TestCase):
    def test_bounded_conditional_meaning_across_languages(self):
        examples={
            "en":"Momentum is approximately conserved when net external impulse is negligible, and exactly conserved when net external impulse is zero.",
            "ms":"Momentum diabadikan secara anggaran apabila impuls luar bersih boleh diabaikan, dan diabadikan dengan tepat apabila impuls luar bersih sifar.",
            "zh":"\u51c0\u5916\u529b\u51b2\u91cf\u53ef\u5ffd\u7565\u5219\u52a8\u91cf\u8fd1\u4f3c\u5b88\u6052\uff1b\u51c0\u5916\u529b\u51b2\u91cf\u4e3a\u96f6\u5219\u52a8\u91cf\u7cbe\u786e\u5b88\u6052\u3002",
        }
        for lang,text in examples.items():
            with self.subTest(lang=lang):
                self.assertTrue(ordered_condition(text,lang)[0])
        self.assertFalse(ordered_condition(
            "Momentum is exactly conserved when external impulse is negligible, and approximately conserved when impulse is zero.",
            "en")[0])
        self.assertFalse(ordered_condition(
            "Momentum tidak diabadikan secara anggaran apabila impuls luar bersih boleh diabaikan, dan diabadikan dengan tepat apabila impuls luar bersih sifar.",
            "ms")[0])
        self.assertFalse(ordered_condition(
            "\u51c0\u5916\u529b\u51b2\u91cf\u53ef\u5ffd\u7565\u5219\u52a8\u91cf\u4e0d\u8fd1\u4f3c\u5b88\u6052\uff1b\u51c0\u5916\u529b\u51b2\u91cf\u4e3a\u96f6\u5219\u52a8\u91cf\u7cbe\u786e\u5b88\u6052\u3002",
            "zh")[0])

    def test_malay_collision_word_does_not_match_approximation(self):
        good="Momentum diabadikan secara anggaran apabila impuls luar bersih boleh diabaikan dan diabadikan dengan tepat apabila impuls luar bersih sifar."
        self.assertTrue(ordered_condition(good,"ms")[0])
        bad=good.replace("secara anggaran","semasa perlanggaran")
        self.assertFalse(ordered_condition(bad,"ms")[0])

    def test_narrative_concept_coverage_is_not_translation_pass(self):
        activity={
            "prompt":REVISION["prompt"],"feedback":REVISION["feedback"],
            "answerLogic":REVISION["answerLogic"],"explanation":REVISION["explanation"],
            "hints":[{"en":"unneeded"},{"en":"base","ms":"base","zh":"base"},],
            "prerequisiteRecovery":{"prompt":REVISION["prerequisite"]},
            "interaction":{"items":[{"id":"item-momentum-conserved-regardless-type",
                                      "label":REVISION["selectedItem"]}]},
        }
        activity["hints"][1]=REVISION["secondHint"]
        result=narrative_semantic_surface(activity)
        self.assertEqual(21,result["localizedFieldChecks"])
        self.assertEqual(21,result["boundedConceptsPresent"])
        self.assertFalse(result["translationMeaningCertified"])
        wrong=copy.deepcopy(activity)
        wrong["feedback"]["ms"]="Momentum berkurang apabila impuls luar sifar."
        check=narrative_semantic_surface(wrong)
        self.assertLess(check["boundedConceptsPresent"],21)
        self.assertFalse(check["translationMeaningCertified"])

    def test_exact_rational_counterexamples(self):
        x=physics_counterexamples()
        self.assertEqual(x["stickingInitialMomentum"],x["stickingFinalMomentum"])
        self.assertGreater(int(x["stickingKEInitial"]),int(x["stickingKEFinal"]))
        self.assertEqual(x["nonzeroExternalImpulse"],"1/100000")
        self.assertEqual(x["balancedExternalForceA"],"1000")
        self.assertEqual(x["balancedExternalForceB"],"-1000")
        self.assertEqual(x["netExternalImpactImpulse"],"0")

    def _fictional_candidate(self):
        markers={
            IDS[0]:{
                "en":"The impact force is vastly greater than any external forces.",
                "ms":"Daya sentuhan jauh lebih besar daripada sebarang daya luar.",
                "zh":"\u529b\u8fdc\u5927\u4e8e\u4efb\u4f55\u5916\u90e8\u529b\u3002",
            },
            IDS[1]:{
                "en":"Newton's third law gives an internal action-reaction pair.",
                "ms":"Daya hukum ketiga Newton membentuk pasangan dalaman.",
                "zh":"\u725b\u987f\u7b2c\u4e09\u5b9a\u5f8b\u8868\u660e\u8fd9\u662f\u7cfb\u7edf\u5185\u90e8\u529b\u5bf9\u3002",
            },
            IDS[2]:REVISION["selectedItem"],
            IDS[3]:{
                "en":"Kinetic energy dissipation always means total momentum decreases.",
                "ms":"Kehilangan tenaga kinetik bermakna momentum linear sistem berkurang.",
                "zh":"\u52a8\u80fd\u635f\u5931\u5c31\u610f\u5473\u7740\u603b\u52a8\u91cf\u51cf\u5c11\u3002",
            },
            IDS[4]:{
                "en":"Conservation only if external force is zero before and after.",
                "ms":"Momentum hanya jika daya luar sifar sebelum dan selepas hentaman.",
                "zh":"\u4ec5\u5f53\u5916\u529b\u5728\u78b0\u649e\u524d\u540e\u90fd\u4e3a\u96f6\u65f6\u624d\u5b88\u6052\u3002",
            },
        }
        return {
            "activities":[{
                "id":ACTIVITY_ID,"interactionMode":"selection",
                "prompt":REVISION["prompt"],"feedback":REVISION["feedback"],
                "answerLogic":REVISION["answerLogic"],
                "explanation":REVISION["explanation"],
                "hints":[{"en":"unused"},REVISION["secondHint"]],
                "prerequisiteRecovery":{"prompt":REVISION["prerequisite"]},
                "interaction":{"correctSelections":list(SELECTED),
                    "items":[{"id":id_,"label":markers[id_]} for id_ in IDS]},
            }]
        }

    def test_independent_answer_distractor_screening_never_unlocks_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            pkg=p/"package.json"
            source=p/"source.pdf"
            review=p/"review.json"
            source.write_bytes(b"%PDF-1.4 synthetic test")
            data=self._fictional_candidate()
            pkg.write_bytes(json.dumps(data,ensure_ascii=False).encode("utf-8"))
            digest=hashlib.sha256(pkg.read_bytes()).hexdigest()
            source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
            review.write_text(json.dumps({
                "candidatePackageFileSha256":digest,
                "controlledSourceSha256":source_sha,
                "reviewOnly":True,
                "publicationAuthorized":False,
            }),encoding="utf-8")
            with patch("app_generator.validation.impulse_semantics.EXPECTED_V2_SHA256",digest):
              with patch("app_generator.validation.impulse_semantics.SOURCE_SHA256",source_sha):
                report=audit_impulse_candidate(pkg,review,source)
                self.assertEqual(4,report["boundedOptionModelsVerified"])
                self.assertEqual(1,report["optionQualifiersReviewRequired"])
                self.assertEqual(21,report["multilingualNarrative"]["boundedConceptsPresent"])
                self.assertFalse(report["completeMultilingualSemanticAgreement"])
                self.assertFalse(report["publicationAuthorized"])
                with self.assertRaisesRegex(ValueError,"selection key"):
                    bad=copy.deepcopy(data)
                    bad["activities"][0]["interaction"]["correctSelections"].pop()
                    pkg.write_bytes(json.dumps(bad,ensure_ascii=False).encode("utf-8"))
                    changed=hashlib.sha256(pkg.read_bytes()).hexdigest()
                    with patch("app_generator.validation.impulse_semantics.EXPECTED_V2_SHA256",changed):
                        # Receipt must still match altered content even when
                        # an attacker re-signs private local review.json.
                        review.write_text(json.dumps({
                            "candidatePackageFileSha256":changed,
                            "controlledSourceSha256":source_sha,
                            "reviewOnly":True,"publicationAuthorized":False,
                        }),encoding="utf-8")
                        audit_impulse_candidate(pkg,review,source)

    def test_missing_or_negated_localized_knowledge_is_not_a_pass(self):
        good={"label":REVISION["selectedItem"]}
        check=option_signature(good,"conditional_momentum")
        self.assertTrue(all(x["status"]=="BOUNDED_SIGNATURE_FOUND" for x in check.values()))
        broken=copy.deepcopy(good)
        broken["label"]["ms"]=broken["label"]["ms"].replace(
            "diabadikan secara anggaran","tidak diabadikan secara anggaran")
        check=option_signature(broken,"conditional_momentum")
        self.assertEqual("REVIEW_REQUIRED",check["ms"]["status"])

    def test_direct_cli_rejects_in_repo_evidence_destination(self):
        script=Path(__file__).resolve().parents[1]/"scripts/audit_impulse_semantics.py"
        result=subprocess.run(
            [sys.executable,"-I",str(script),"--help"],
            capture_output=True,text=True,timeout=20,
        )
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertIn("--source-pdf",result.stdout)
        with tempfile.TemporaryDirectory() as tmp:
            t=Path(tmp)
            source=t/"source.pdf";source.write_bytes(b"%PDF-1.4 fixture")
            candidate=t/"package.json";candidate.write_text("{}",encoding="utf-8")
            review=t/"review.json";review.write_text("{}",encoding="utf-8")
            in_repo=Path(__file__).resolve().parents[1]/"unapproved-evidence.json"
            trial=subprocess.run(
                [sys.executable,"-I",str(script),"--package",str(candidate),
                 "--review",str(review),"--source-pdf",str(source),
                 "--out",str(in_repo)],capture_output=True,text=True,timeout=20,
            )
            self.assertEqual(2,trial.returncode)
            self.assertIn("outside public repository",trial.stdout)
            self.assertFalse(in_repo.exists())

    def test_file_alone_does_not_claim_a_credential_or_deployment(self):
        self.assertFalse(narrative_semantic_surface({
            "prompt":REVISION["prompt"],"interaction":{"items":[]},
        })["translationMeaningCertified"])

if __name__=="__main__":
    unittest.main()
