"""Synthetic exact collision parameter-sweep tests."""
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.collision_property_grid import collision, verify_grid, audit
from app_generator.validation.physics_proofs import KNOWN_CASES
from app_generator.validation.interactive_physics import SUPPORTED, assignments


class GridTests(unittest.TestCase):
    def test_com_exact(self):
        self.assertEqual((F(0),F(4)),collision(F(2),F(2),F(4),F(0),F(1)))
        self.assertEqual((F(2),F(2)),collision(F(2),F(2),F(4),F(0),F(0)))
        self.assertEqual((F(3,2),F(5,2)),collision(F(2),F(2),F(3),F(1),F(1,2)))

    def test_bad_masses_velocities_coefficients(self):
        for args in ((F(0),F(1),F(3),F(0),F(1)),
                     (F(1),F(1),F(0),F(1),F(1)),
                     (F(1),F(1),F(2),F(0),F(5,4)),
                     (F(1),F(1),F(2),F(0),F(-1,4)),
                     (1,F(1),F(2),F(0),F(1))):
            with self.assertRaises(ValueError):collision(*args)

    def test_320_exact_cases(self):
        r=verify_grid()
        self.assertEqual((320,64,64,192),
            (r["exactCollisionCases"],r["elastic"],r["sticky"],r["partial"]))
        self.assertEqual("1/1001",r["heavyTargetKineticRetention"])
        self.assertTrue(r["oblique2dFullVectorReversalCounterexample"])
        self.assertFalse(r["fullScientificSemanticsVerified"])

    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        d=Path(t.name)
        self.pdf=d/"original.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic")
        self.pack=d/"packets.json"
        self.pack.write_text("{}")
        self.pkg=d/"package.json"
        self.activities=[]
        for aid,(_,correct) in KNOWN_CASES.items():
            self.activities.append({"id":aid,"type":"mcq","answerKey":{
                "correct":correct,"options":[{"id":i} for i in
                (correct,"decoy-1","decoy-2","decoy-3")]}})
        for aid,name in SUPPORTED.items():
            mode,key,_,_=assignments(name)
            if mode in ("classification","matching"):
                ix={"items":[{"id":i} for i in key],
                    "targets":[{"id":v} for v in set(key.values())],
                    "placements":[{"itemId":i,"targetId":v} for i,v in key.items()]}
            elif mode=="ordering":
                ix={"items":[{"id":i} for i in key],"correctOrder":list(key)}
            else:
                ix={"items":[{"id":i} for i in key],"correctSelections":list(key)}
            self.activities.append({"id":aid,"type":"interactive",
                "interactionMode":mode,"interaction":ix})
        self.save()

    def save(self):
        self.pkg.write_text(json.dumps({"activities":self.activities}),encoding="utf-8")

    def run_audit(self):
        receipt={"newlyReverifiedSourceActivities":18,
            "packageSha256":sha256(self.pkg.read_bytes()).hexdigest(),
            "sourceSha256":sha256(self.pdf.read_bytes()).hexdigest(),
            "publicationAuthorized":False}
        with patch("app_generator.validation.collision_property_grid.verify_full_source_packet_roster",
                   return_value=receipt) as verified:
            answer=audit(package_file=self.pkg,source_pdf=self.pdf,packets_file=self.pack)
            verified.assert_called_once()
        return answer

    def test_all_mcq_and_interaction_answer_mappings(self):
        result=self.run_audit()
        self.assertEqual(18,result["originalSourceActivitiesReverified"])
        self.assertEqual(9,result["mcqAnswerIdRostersChecked"])
        self.assertEqual(36,result["mcqOptionIdentifiersChecked"])
        self.assertEqual(9,result["interactionAnswerModelsCompared"])
        self.assertEqual(0,result["formalAcademicPASS"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertFalse(result["mcqDistractorProseVerified"])

    def test_wrong_mcq_key_and_duplicate_distractor(self):
        entry=self.activities[0]
        correct=entry["answerKey"]["correct"]
        entry["answerKey"]["correct"]="decoy-1"
        self.save()
        with self.assertRaisesRegex(ValueError,"MCQ correct"):self.run_audit()
        entry["answerKey"]["correct"]=correct
        entry["answerKey"]["options"][1]["id"]=correct
        self.save()
        with self.assertRaisesRegex(ValueError,"MCQ correct"):self.run_audit()

    def test_wrong_interaction_order(self):
        entry=next(a for a in self.activities if a["id"]=="int-order-post-collision-speeds")
        entry["interaction"]["correctOrder"].reverse()
        self.save()
        with self.assertRaisesRegex(ValueError,"interactive answer"):self.run_audit()

    def test_source_perturbation_blocks(self):
        with patch("app_generator.validation.collision_property_grid.verify_full_source_packet_roster",
                   side_effect=ValueError("source mismatch")):
            with self.assertRaisesRegex(ValueError,"source mismatch"):
                audit(package_file=self.pkg,source_pdf=self.pdf,packets_file=self.pack)


if __name__=="__main__":
    unittest.main()
