import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.validation.physics_proofs import audit_proofs, prove_case, KNOWN_CASES


class AcademicPhysicsProofTests(unittest.TestCase):
    def test_all_supported_exact_arithmetic_models(self):
        examples = {
            "equal_mass_sticking": {"m":"2","u":"4"},
            "equal_mass_exchange": {"m":"2","u":"4"},
            "newton_two_out": {"m":"1","u":"6"},
            "heavy_target_sticking": {"m":"1","M":"100","u":"5"},
            "ballistic_two_phase": {"m1":"1","m2":"9","u":"10","g":"10"},
            "spring_energy_storage": {"m":"2","u":"3","k":"2","x":"2"},
            "elastic_relative_velocity": {"m1":"2","m2":"3","u1":"4","u2":"0"},
        }
        self.assertEqual(set(examples),set(name for name,_ in KNOWN_CASES.values()))
        for name, values in examples.items():
            with self.subTest(name=name):
                report=prove_case(name,values)
                self.assertEqual(name,report["model"])
                self.assertTrue(all(isinstance(value,str) for value in report.values()))

    def test_cli_isolated_current_checkout_import_and_receipt_boundary(self):
        import subprocess
        import sys
        repo=Path(__file__).resolve().parents[1]
        result=subprocess.run(
            [sys.executable,"-I",str(repo/"scripts/audit_physics_proofs.py"),"--help"],
            capture_output=True,text=True,cwd=repo,timeout=20
        )
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertIn("--receipts",result.stdout)

    def test_adversarial_values_do_not_create_false_proofs(self):
        for model, params in (
            ("equal_mass_sticking",{"m":"0","u":"4"}),
            ("equal_mass_exchange",{"m":"2","u":"0"}),
            ("newton_two_out",{"m":"-1","u":"3"}),
            ("heavy_target_sticking",{"m":"1","M":"90","u":"5"}),
            ("ballistic_two_phase",{"m1":"1","m2":"9","u":"10","g":"0"}),
            ("spring_energy_storage",{"m":"2","u":"3","k":"50","x":"2"}),
            ("elastic_relative_velocity",{"m1":"2","m2":"3","u1":"4","u2":"4"}),
            ("equal_mass_sticking",{"m":"nan","u":"4"}),
        ):
            with self.subTest(model=model,params=params):
                with self.assertRaises(ValueError):
                    prove_case(model,params)

    def _fixture(self):
        activity={"id":"mcq-perfectly-inelastic-outcome","type":"mcq",
                  "answerKey":{"correct":"opt-perfectly-inelastic-forward"}}
        package={"activities":[activity]}
        package_sha=hashlib.sha256(
            json.dumps(package,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
        ).hexdigest()
        quote="When the objects stick together after they collide, it is a perfectly inelastic collision."
        receipt={"sourceSha256":"","packageCanonicalSha256":package_sha,
                 "proofs":[{
                     "activityId":activity["id"],"model":"equal_mass_sticking",
                     "parameters":{"m":"2","u":"4"},
                     "anchor":{"activityId":activity["id"],"pageIndex":1,"quotedText":quote}
                 }]}
        return package,receipt,quote

    def test_source_and_package_binding_plus_anti_fabrication(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf=Path(temp)/"source.pdf"
            pdf.write_bytes(b"%PDF-1.4 source fixture")
            digest=hashlib.sha256(pdf.read_bytes()).hexdigest()
            package,receipt,quote=self._fixture()
            receipt["sourceSha256"]=digest
            with patch("app_generator.validation.physics_proofs.extract_pages",return_value=(quote,)):
                report=audit_proofs(package,pdf,digest,receipt)
                self.assertEqual(1,report["boundedPropositionsVerified"])
                self.assertEqual(0,report["academicActivitiesPassed"])
                self.assertEqual("REVIEW_REQUIRED",report["academicQA"])
                self.assertFalse(report["publicationAuthorized"])
                altered=json.loads(json.dumps(package))
                altered["activities"][0]["answerKey"]["correct"]="wrong"
                with self.assertRaisesRegex(ValueError,"identity"):
                    audit_proofs(altered,pdf,digest,receipt)
                receipt["proofs"][0]["anchor"]["pageIndex"]=2
                pending=audit_proofs(package,pdf,digest,receipt)
                self.assertEqual(0,pending["boundedPropositionsVerified"])
                self.assertEqual(1,pending["unresolvedReceipts"])
                receipt["proofs"][0]["anchor"]["pageIndex"]=1
                receipt["proofs"][0]["parameters"]["m"]="0"
                failed=audit_proofs(package,pdf,digest,receipt)
                self.assertEqual(1,failed["failedWitnesses"])
                receipt["proofs"].append(receipt["proofs"][0].copy())
                with self.assertRaisesRegex(ValueError,"duplicate"):
                    audit_proofs(package,pdf,digest,receipt)
                with self.assertRaisesRegex(ValueError,"source"):
                    audit_proofs(package,pdf,"0"*64,receipt)


if __name__=="__main__":
    unittest.main()
