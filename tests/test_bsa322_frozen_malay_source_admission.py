"""BSA322 regression: original signed V20 Malay conservation correction is frozen.

The test-only original-source case runs on Yoga6 only. A successful source
proof is not an admission or a trilingual meaning-equivalence gate.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
from unittest import TestCase, skipUnless

from app_generator.validation import section91_third_law_explanation_proof as proof
from app_generator.runtime import v3_third_law_explanation_academic_admission as admission

SAMPLE=Path("content/chapter-9/section-9-1/package.json")


class OriginalMalayV20Surface(TestCase):
    def test_old_sample_malay_frozen_hash_fails(self):
        sample=json.loads(SAMPLE.read_text(encoding="utf8"))["activities"][4]
        with self.assertRaisesRegex(ValueError,"FROZEN_THIRD_LAW_EXPLANATION_CHANGED"):
            proof._locales(sample["explanation"],proof._EXPLANATION)

    def test_exact_previous_v20_malay_repair_is_expected(self):
        sample=json.loads(SAMPLE.read_text(encoding="utf8"))["activities"][4]
        changed=dict(sample["explanation"])
        old=changed["ms"]
        self.assertEqual(old.count("keabadian momentum"),1)
        self.assertEqual(old.count("Keabadian momentum"),1)
        changed["ms"]=(old.replace("keabadian momentum","pemuliharaan momentum")
                          .replace("Keabadian momentum","Pemuliharaan momentum"))
        self.assertEqual(sha256(changed["ms"].encode("utf8")).hexdigest(),
                         "69950ede624cac633a0394309c9eed1b532d5d36fcab2acc4f115040915cae83")
        self.assertEqual(proof._locales(changed,proof._EXPLANATION),
                         proof._EXPLANATION)
        for forged in ("keabadian momentum","keabadian momentumnya",
                       "pemuliharaan tenaga"):
            altered=dict(changed)
            altered["ms"]=changed["ms"].replace("pemuliharaan momentum",forged,1)
            with self.subTest(forged=forged),self.assertRaisesRegex(
                    ValueError,"FROZEN_THIRD_LAW_EXPLANATION_CHANGED"):
                proof._locales(altered,proof._EXPLANATION)


@skipUnless(os.name=="nt" and
            os.environ.get("COMPUTERNAME","").upper()=="YOGA6" and
            os.environ.get("BOSLA_OWNER_ACADEMIC_TESTS")=="1",
            "Explicit Yoga6 private original-Serway read-only proof requested")
class OwnerOriginalMalayProof(TestCase):
    def test_real_original_serway_and_fifth_signed_v36_row_a32(self):
        from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
        private=Path(os.environ["LOCALAPPDATA"])/"Microvid"/"BoslaV3ReviewYoga6"
        latest=read_long_horizon_development(private)
        ready={"gitHead":latest["gitHead"],"proposalSha256":latest["proposalSha256"]}
        _,part,actual=admission._original_proof(
            private=private,ready=ready,historical=False)
        self.assertEqual(actual["sourceSha256"],proof._SOURCE_SHA)
        self.assertEqual(actual["candidateSha256"],proof._CANDIDATE_SHA)
        self.assertEqual(actual["explanationLocaleSha256"],proof._EXPLANATION)
        self.assertEqual(part["academicPASS"],0)
        self.assertFalse(actual["academicTaskAccepted"])
        self.assertFalse(actual["publicationAuthorized"])
