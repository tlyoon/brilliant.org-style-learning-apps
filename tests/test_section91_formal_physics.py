"""BSA252 Section9.1 independent exact-arithmetic answer science regressions."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation import section91_formal_physics as m

ROOT=Path(__file__).resolve().parents[1]


class Section91FormalPhysicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=json.loads(
            (ROOT/"content/chapter-9/section-9-1/package.json").read_text(
                encoding="utf8"))

    def test_independent_proof_models_cover_all_18_and_68_answer_items(self):
        results=m._prove_exact_roster(deepcopy(self.original["activities"]))
        self.assertEqual(len(results),18)
        self.assertEqual(sum(x["exactRationalAndDimensionalWitnesses"]
                             for x in results),68)
        self.assertEqual(len({(x["activityId"],x["independentFormalSolutionSha256"])
                              for x in results}),18)
        self.assertTrue(all(x["answerPhysicsBoundedVerified"]
                            and not x["fullScientificAcademicPASS"]
                            and not x["allEnglishStatementAndTranslatedSemanticsVerified"]
                            and not x["publicationAuthorized"]
                            for x in results))

    def test_mutated_each_of_nine_mcq_keys_independently_detected(self):
        for index in range(9):
            activities=deepcopy(self.original["activities"])
            mcq=activities[index]
            correct=mcq["answerKey"]["correct"]
            mcq["answerKey"]["correct"]=next(
                opt["id"] for opt in mcq["answerKey"]["options"]
                if opt["id"]!=correct)
            with self.subTest(mcq=mcq["id"]):
                with self.assertRaisesRegex(ValueError,
                                             "BSA252_ACTUAL_MCQ_ANSWER_KEY_DEFECT"):
                    m._prove_exact_roster(activities)

    def test_mutated_each_of_nine_interactive_solutions_detected(self):
        for index in range(9,18):
            activities=deepcopy(self.original["activities"])
            a=activities[index]
            interaction=a["interaction"]
            mode=a["interactionMode"]
            if mode=="ordering":
                interaction["correctOrder"] = list(
                    reversed(interaction["correctOrder"]))
            elif mode=="selection":
                interaction["correctSelections"].pop()
            else:
                targets=interaction["targets"]
                placement=interaction["placements"][0]
                placement["targetId"]=next(
                    t["id"] for t in targets
                    if t["id"]!=placement["targetId"])
            with self.subTest(interactive=a["id"],mode=mode):
                with self.assertRaisesRegex(ValueError,
                                             "BSA252_ACTUAL_"):
                    m._prove_exact_roster(activities)

    def test_duplicate_or_new_mcq_distractor_identity_rejected(self):
        for what in ("duplicate","new"):
            activities=deepcopy(self.original["activities"])
            a=activities[2]
            options=a["answerKey"]["options"]
            options[1]["id"]=(
                options[0]["id"] if what=="duplicate" else "injected-distractor")
            with self.subTest(mutant=what):
                with self.assertRaisesRegex(ValueError,"BSA252_MCQ_OPTION_IDENTITY"):
                    m._prove_exact_roster(activities)

    def test_interactive_mode_and_unknown_item_never_borrow_proof(self):
        for where in ("mode","item","target"):
            activities=deepcopy(self.original["activities"])
            a=activities[10]
            if where=="mode":
                a["interactionMode"]="selection"
            elif where=="item":
                a["interaction"]["items"][0]["id"]="tampered-physics"
            else:
                a["interaction"]["targets"][0]["id"]="tampered-unit"
            with self.subTest(where=where):
                with self.assertRaisesRegex(ValueError,"BSA252_"):
                    m._prove_exact_roster(activities)

    def test_source_axioms_reject_wrong_pdf_bytes_without_upload(self):
        with tempfile.TemporaryDirectory() as path:
            fake=Path(path)/"source.pdf"
            fake.write_bytes(b"%PDF-tampered")
            with self.assertRaisesRegex(ValueError,
                                         "BSA252_ORIGINAL_SINGLE_TEXTBOOK_SHA_CHANGED"):
                m._source_axioms(fake,m._SOURCE_SHA)

    def test_source_axioms_reject_wrong_authority_sha(self):
        with tempfile.TemporaryDirectory() as path:
            fake=Path(path)/"source.pdf"
            fake.write_bytes(b"%PDF-tampered")
            with self.assertRaisesRegex(ValueError,
                                         "BSA252_ORIGINAL_SINGLE_TEXTBOOK_SHA_CHANGED"):
                m._source_axioms(fake,sha256(fake.read_bytes()).hexdigest())

    def test_source_missing_independent_textbook_premises_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            fake=Path(folder)/"source.pdf"
            fake.write_bytes(b"%PDF-synthetic")
            with (patch.object(m,"_SOURCE_SHA",
                               sha256(fake.read_bytes()).hexdigest()),
                  patch.object(m,"extract_pages",
                      return_value=("linear momentum is a vector",)*3)):
                with self.assertRaisesRegex(ValueError,
                                             "BSA252_SOURCE_PHYSICS_AXIOM_MISSING"):
                    m._source_axioms(fake,sha256(fake.read_bytes()).hexdigest())

    def test_edited_activity_or_locale_byte_content_is_not_approved(self):
        with tempfile.TemporaryDirectory() as folder:
            candidate=Path(folder)/"package.json"
            data=deepcopy(self.original)
            data["activities"][4]["prompt"]["ms"]+=" changed"
            candidate.write_text(json.dumps(data),encoding="utf8")
            with self.assertRaisesRegex(ValueError,
                                         "BSA252_EXACT_PACKAGE_VERSION_DRIFT"):
                m.bounded_section91_science_audit(
                    source_pdf=Path(folder)/"source.pdf",
                    source_sha=m._SOURCE_SHA,
                    package_file=candidate)

    def test_unapproved_new_parent_sha_cannot_skip_exact_version_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            candidate=Path(folder)/"package.json"
            candidate.write_text(json.dumps(self.original),encoding="utf8")
            with self.assertRaisesRegex(ValueError,
                                         "BSA252_APPROVED_EXACT_REVISION_REQUIRED"):
                m.bounded_section91_science_audit(
                    source_pdf=Path(folder)/"source.pdf",
                    source_sha=m._SOURCE_SHA,
                    package_file=candidate,
                    expected_sha=sha256(candidate.read_bytes()).hexdigest())

    def test_nonunique_model_truth_does_not_accept_any_mcq(self):
        activities=deepcopy(self.original["activities"])
        cases=m._mcq_cases()
        cases[activities[0]["id"]]={key:True for key in cases[activities[0]["id"]]}
        with patch.object(m,"_mcq_cases",return_value=cases):
            with self.assertRaisesRegex(ValueError,
                                         "BSA252_SOURCE_MODEL_NOT_UNIQUE"):
                m._prove_exact_roster(activities)

    def test_science_result_cannot_claim_full_academic_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            candidate=Path(folder)/"package.json"
            raw=json.dumps(self.original,ensure_ascii=False).encode("utf8")
            candidate.write_bytes(raw)
            digest=sha256(raw).hexdigest()
            with (patch.object(m,"_CANDIDATE_SHA",digest),
                  patch.object(m,"_source_axioms",
                      return_value={x:y for x,y in m._AXIOMS})):
                result=m.bounded_section91_science_audit(
                    source_pdf=Path(folder)/"source.pdf",
                    source_sha=m._SOURCE_SHA,
                    package_file=candidate,
                    expected_sha=digest)
            self.assertEqual(result["boundedFormalAnswerItemWitnesses"],68)
            self.assertEqual(result["completeIndependentAcademicProofGatePASS"],0)
            self.assertEqual(result["formalAcademicActivityPASS"],0)
            self.assertFalse(result["publicationAuthorized"])
            self.assertFalse(result["newExternalPdfsRequired"])

    def test_real_worker_must_dispatch_v25_and_validate_evidence(self):
        worker=(ROOT/"scripts/run_v3_yoga6_recovery_worker.py").read_text(
            encoding="utf8")
        self.assertIn("run_post_v24_formal_science(",worker)
        self.assertIn('result["formalSection91Physics"]',worker)
        self.assertIn('"boundedFormalAnswerItemWitnesses")==68',worker)

    def test_v25_integration_does_not_bypass_genuine_v24_signature(self):
        from app_generator.runtime import v3_section91_formal_academic_dispatch as v
        with (patch.object(v,"_preflight",return_value=(
                    Path("."),None,None,None,None)),
              patch.object(v,"_signed",
                    side_effect=[{"status":"FORGED"},{},]),
              patch.object(v,"bounded_section91_science_audit",
                    side_effect=AssertionError("SHOULD_NOT_PROVE"))):
            with self.assertRaisesRegex(ValueError,"BSA252_GENUINE_V24"):
                v.run_post_v24_formal_science(
                    ROOT,Path("."),{"gitHead":"a"*40,"proposalSha256":"b"*64},
                    {},{},{},{})


if __name__=="__main__":
    unittest.main()
