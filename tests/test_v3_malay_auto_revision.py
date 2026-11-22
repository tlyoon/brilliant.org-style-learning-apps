"""BSA247 reused old Malay science repair, private version and no false PASS."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.runtime import v3_malay_auto_revision as m
from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.language_qa import check_multilingual_surface

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "content/chapter-9/section-9-1/package.json"
FAIL_IDS = {
    "act-mcq-05-third-law-connection",
    "act-mcq-08-isolated-subsystem-fallacy",
    "act-int-05-newton-second-law-steps-order",
    "act-int-08-conservation-validity-select",
}


class SourceBoundMalayAutomaticRevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.private = Path(self.tmp.name)
        self.pdf = self.private / "source.pdf"
        self.pdf.write_bytes(b"%PDF-FAKE_TEST_SOURCE")
        self.source_sha = sha256(self.pdf.read_bytes()).hexdigest()
        self.raw = PACKAGE.read_bytes()
        self.package = json.loads(self.raw.decode("utf8"))
        self.package_sha = sha256(self.raw).hexdigest()
        self.identity = {"gitHead": "a"*40, "proposalSha256": "b"*64}
        self.original = [
            {"activityId": a["id"],
             "academicQA": "FAIL" if a["id"] in FAIL_IDS
                           else "REVIEW_REQUIRED",
             "gates": {
                 g: ("FAIL" if g == "multilingual_meaning"
                     and a["id"] in FAIL_IDS else "REVIEW_REQUIRED")
                 for g in REQUIRED},
            }
            for a in self.package["activities"]
        ]
        self.audit = {"activities": self.original}
        self.validate_real_9_1_statuses()

    def validate_real_9_1_statuses(self):
        actual = {a["id"] for a in self.package["activities"]
                  if check_multilingual_surface(a).result == "FAIL"}
        self.assertEqual(actual, FAIL_IDS)

    def recheck(self, **kw):
        bytes_ = kw["package_path"].read_bytes()
        p = json.loads(bytes_.decode("utf8"))
        self.assertEqual(len(p["activities"]), 18)
        self.assertEqual(kw["source_sha256"], self.source_sha)
        self.assertIsNone(kw["source_packets"])
        failed = sum(check_multilingual_surface(a).result == "FAIL"
                     for a in p["activities"])
        return {
            "counts": {
                "PASS": 0, "FAIL": failed, "REVIEW_REQUIRED": 18-failed,
            },
            "packageSha256": sha256(bytes_).hexdigest(),
            "sourceSha256": self.source_sha,
            "publicationAuthorized": False,
            "activities": [
                {"sourceLocationVerified": False}
                for _ in range(18)
            ],
        }

    def execute(self, audit=None):
        with patch.object(m, "audit_activity_matrix", side_effect=self.recheck):
            return m.auto_repair_known_malay_science_defects(
                repo=ROOT, folder=self.private,
                original_package=self.package,
                original_package_sha=self.package_sha,
                source_pdf=self.pdf, source_sha=self.source_sha,
                original_audit=self.audit if audit is None else audit,
                identity=self.identity,
            )

    def test_actual_four_detected_negative_fails_repaired_by_historical_engine(self):
        before = PACKAGE.read_bytes()
        first = self.execute()
        again = self.execute()
        self.assertEqual(first, again)
        self.assertEqual(first["status"], m._REPAIR_STATUS)
        self.assertEqual(first["repairedActivityCount"], 4)
        self.assertEqual(first["correctedTerms"], 10)
        self.assertEqual(before, PACKAGE.read_bytes())
        proof = json.loads((self.private/m._RECEIPT).read_text(encoding="utf8"))
        self.assertEqual(proof["changedMalayFieldCount"], 8)
        self.assertEqual(proof["newCandidateFiveGateNegativeFindings"], 0)
        self.assertEqual(proof["newCandidateAll18AcademicQA"], "REVIEW_REQUIRED")
        self.assertFalse(proof["newCandidateSourceLocationFreshlyVerified"])
        self.assertFalse(proof["oldGeminiReviewerClaimsTransferred"])
        self.assertFalse(proof["publicationAuthorized"])
        self.assertEqual(proof["originalPackageSha256"], self.package_sha)
        candidate = json.loads((self.private/m._CANDIDATE).read_text(encoding="utf8"))
        self.assertEqual(
            {a["id"] for a,b in zip(self.package["activities"],candidate["activities"])
             if a != b}, FAIL_IDS,
        )
        for old, new in zip(self.package["activities"], candidate["activities"]):
            if old["id"] in FAIL_IDS:
                self.assertEqual(old["prompt"]["en"], new["prompt"]["en"])
                self.assertEqual(old["prompt"]["zh"], new["prompt"]["zh"])
                self.assertNotEqual(
                    sha256(json.dumps(old,sort_keys=True).encode("utf8")).hexdigest(),
                    sha256(json.dumps(new,sort_keys=True).encode("utf8")).hexdigest(),
                )
        self.assertNotIn("keabadian",json.dumps(candidate,ensure_ascii=False))
        self.assertNotIn("keabadian",str(proof))  # metadata receipt only

    def test_non_malay_fail_is_queued_not_overwritten(self):
        rows = json.loads(json.dumps(self.original))
        rows[0]["academicQA"] = "FAIL"
        rows[0]["gates"]["physics_consistency"] = "FAIL"
        result = self.execute({"activities":rows})
        self.assertEqual(result["status"],
                         "UNRELATED_DETERMINISTIC_FAILS_REQUIRE_SEPARATE_REPAIR")
        self.assertFalse((self.private/m._CANDIDATE).exists())

    def test_candidate_tamper_refuses_resume(self):
        self.execute()
        path = self.private/m._CANDIDATE
        path.write_bytes(path.read_bytes()+b"\n")
        with self.assertRaisesRegex(ValueError, "V20_REPAIR_PRIVATE_CANDIDATE_TAMPERED"):
            self.execute()

    def test_forged_recheck_positive_academic_pass_rejected(self):
        with patch.object(m, "audit_activity_matrix", return_value={
            "counts":{"PASS":18,"FAIL":0,"REVIEW_REQUIRED":0},
            "packageSha256":"a"*64,"sourceSha256":self.source_sha,
            "publicationAuthorized":False,"activities":[]},
        ):
            with self.assertRaisesRegex(ValueError,"V20_REPAIR_NEW_VERSION_GATES"):
                m.auto_repair_known_malay_science_defects(
                    repo=ROOT,folder=self.private,
                    original_package=self.package,
                    original_package_sha=self.package_sha,
                    source_pdf=self.pdf,source_sha=self.source_sha,
                    original_audit=self.audit,identity=self.identity,
                )

    def test_original_without_fails_does_not_generate_new_candidate(self):
        rows = json.loads(json.dumps(self.original))
        for item in rows:
            item["academicQA"]="REVIEW_REQUIRED"
            item["gates"]["multilingual_meaning"]="REVIEW_REQUIRED"
        outcome = self.execute({"activities":rows})
        self.assertEqual(outcome["status"],"NO_DETERMINISTIC_FAILS_TO_REPAIR")
        self.assertFalse((self.private/m._CANDIDATE).exists())

    def test_normal_recovery_integrated_malay_repair_invocation(self):
        stage = (ROOT/"app_generator/runtime/v3_historical_academic_audit.py"
                 ).read_text(encoding="utf8")
        self.assertIn("auto_repair_known_malay_science_defects(",stage)
        self.assertIn("automaticKnownMalayRepairStatus",stage)


if __name__=="__main__":
    unittest.main()
