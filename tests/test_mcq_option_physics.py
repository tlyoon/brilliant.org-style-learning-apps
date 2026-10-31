"""Synthetic original-source all-MCQ-option bounded counterexample tests."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from app_generator.validation.mcq_option_physics import (
    COUNTEREXAMPLES,witness,audit_source_bound_all_mcq_options)
from app_generator.validation.physics_proofs import KNOWN_CASES


class OptionPhysicsAuditTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root=Path(tmp.name)
        self.pkg=root/"package.json";self.pdf=root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic")
        self.packets=root/"packets.json";self.packets.write_text("{}")
        items=[]
        for aid,rest in COUNTEREXAMPLES.items():
            chosen=KNOWN_CASES[aid][1]
            items.append({"id":aid,"type":"mcq","answerKey":{
                "correct":chosen,"options":[
                  {"id":oid,"label":{lang:f"{oid}.{lang}" for lang in
                    ("en","ms","zh")}} for oid in (chosen,*rest)]}})
        items.extend({"id":f"interactive-{i}","type":"interactive"} for i in range(9))
        self.activities=items
        self.write()
    def write(self):
        self.pkg.write_text(json.dumps({"activities":self.activities}),encoding="utf-8")

    def run_audit(self):
        src={"newlyReverifiedSourceActivities":18,
             "sourceSha256":sha256(self.pdf.read_bytes()).hexdigest(),
             "packageSha256":sha256(self.pkg.read_bytes()).hexdigest(),
             "publicationAuthorized":False}
        receipt={"sourceSha256":src["sourceSha256"]}
        report={"boundedPropositionsVerified":9,"failedWitnesses":0,
                "unresolvedReceipts":0,"publicationAuthorized":False,
                "proofs":[{"activityId":aid,"status":"BOUNDED_PROPOSITION_VERIFIED"}
                          for aid in KNOWN_CASES]}
        with patch("app_generator.validation.mcq_option_physics.verify_full_source_packet_roster",
                   return_value=src),patch(
             "app_generator.validation.mcq_option_physics.generate_bounded_physics_receipts",
             return_value=(receipt,report)):
            return audit_source_bound_all_mcq_options(
                package_file=self.pkg,source_pdf=self.pdf,source_packets_file=self.packets)

    def test_all_exact_scenarios_generate_finite_rational_values(self):
        scenarios={x for values in COUNTEREXAMPLES.values() for x in values.values() if x}
        self.assertEqual(11,len(scenarios))
        for name in scenarios:
            with self.subTest(name=name):
                result=witness(name)
                self.assertTrue(result)
                self.assertTrue(all(isinstance(v,str) for v in result.values()))

    def test_36_option_coverage_one_unresolved_and_zero_academic(self):
        result=self.run_audit()
        self.assertEqual(36,result["mcqOptionsChecked"])
        self.assertEqual(9,result["sourceBoundSelectedOptionWitnesses"])
        self.assertEqual(26,result["rationalCounterexamplesForDistractorIds"])
        self.assertEqual(1,result["unresolvedPhysicalDistractors"])
        self.assertEqual(0,result["formalAcademicPASS"])
        self.assertFalse(result["optionWordMeaningVerified"])
        self.assertFalse(result["publicationAuthorized"])

    def test_wrong_selected_key_rejected(self):
        self.activities[0]["answerKey"]["correct"]="opt-both-conserved"
        self.write()
        with self.assertRaisesRegex(ValueError,"correct option"):
            self.run_audit()

    def test_replaced_original_distractor_rejected(self):
        self.activities[0]["answerKey"]["options"][1]["id"]="unsourced"
        self.write()
        with self.assertRaisesRegex(ValueError,"option physics roster"):
            self.run_audit()

    def test_duplicate_option_label_is_never_approved(self):
        opts=self.activities[0]["answerKey"]["options"]
        opts[1]["label"]["en"]=opts[0]["label"]["en"]
        self.write()
        with self.assertRaisesRegex(ValueError,"structurally valid"):
            self.run_audit()

    def test_source_reverification_is_mandatory(self):
        with patch(
           "app_generator.validation.mcq_option_physics.verify_full_source_packet_roster",
           side_effect=ValueError("changed source")):
            with self.assertRaisesRegex(ValueError,"changed source"):
                audit_source_bound_all_mcq_options(
                    package_file=self.pkg,source_pdf=self.pdf,source_packets_file=self.packets)

    def test_unknown_counterexample_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"unsupported"):
            witness("not-approved")
    def test_material_contact_force_is_not_reclassified_by_rational_model(self):
        unknown=[(aid,oid) for aid,options in COUNTEREXAMPLES.items()
                 for oid,case in options.items() if case is None]
        self.assertEqual([("mcq-newton-cradle-multi-ball",
                           "opt-force-transmission")],unknown)
if __name__=="__main__":unittest.main()
