"""Source-free fail-closed Malay conservation-vocabulary repair tests."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from app_generator.validation.malay_conservation_lexicon import (
    conservation_lexicon_flags,repair_private_malay_v9,
)
from app_generator.validation.mcq_statement_physics import (
    _approved_v9_malay_lexicon_reconciliation,
    APPROVED_MALAY_LEXICON_V9_SHA,
)


def fixture():
    activities=[{"id":"synthetic-"+str(i)} for i in range(18)]
    activities[0]["feedback"]={
        "en":"Conservation of momentum",
        "ms":"Keabadian momentum dan diabadikan serta mengabadikan tenaga",
        "zh":"\\u52a8\\u91cf\\u5b88\\u6052",
    }
    return {"activities":activities}


class MalayConservationVocabularyTests(unittest.TestCase):
    def test_exact_lexemes_case_and_copy_on_write(self):
        before=fixture()
        old=copy.deepcopy(before)
        with patch("app_generator.validation.malay_conservation_lexicon.ROOTS",
                   (("keabadian","pemuliharaan",1),
                    ("mengabadikan","mengekalkan",1),
                    ("diabadikan","dikekalkan",1))),patch(
            "app_generator.validation.malay_conservation_lexicon.EXPECTED_TOTAL",3
        ),patch("app_generator.validation.malay_conservation_lexicon.EXPECTED_FIELDS",1):
            repaired,receipt=repair_private_malay_v9(before)
        self.assertEqual(before,old)
        self.assertEqual(3,receipt["localizedScientificTermReplacements"])
        self.assertEqual(1,receipt["changedMalayFields"])
        self.assertEqual("Conservation of momentum",repaired["activities"][0]["feedback"]["en"])
        self.assertEqual(old["activities"][0]["feedback"]["zh"],repaired["activities"][0]["feedback"]["zh"])
        self.assertEqual("Pemuliharaan momentum dan dikekalkan serta mengekalkan tenaga",
                         repaired["activities"][0]["feedback"]["ms"])
        self.assertEqual([],conservation_lexicon_flags(repaired))
        self.assertFalse(receipt["publicationAuthorized"])

    def test_new_or_missing_legacy_terms_reject(self):
        with self.assertRaisesRegex(ValueError,"outside original roster"):
            repair_private_malay_v9(fixture())
        x=fixture()
        x["activities"][0]["feedback"]["ms"] += " keabadian"
        with self.assertRaisesRegex(ValueError,"outside original roster"):
            repair_private_malay_v9(x)

    def test_does_not_rewrite_non_malay_or_unrelated_immortality(self):
        x=fixture()
        x["activities"][0]["feedback"]["en"]="keabadian"
        x["activities"][0]["notes"]={"ms":"kehidupan abadi"}
        with patch("app_generator.validation.malay_conservation_lexicon.ROOTS",
                   (("keabadian","pemuliharaan",1),
                    ("mengabadikan","mengekalkan",1),
                    ("diabadikan","dikekalkan",1))),patch(
            "app_generator.validation.malay_conservation_lexicon.EXPECTED_TOTAL",3
        ),patch("app_generator.validation.malay_conservation_lexicon.EXPECTED_FIELDS",1):
            new,_=repair_private_malay_v9(x)
        self.assertEqual("keabadian",new["activities"][0]["feedback"]["en"])
        self.assertEqual("kehidupan abadi",new["activities"][0]["notes"]["ms"])

    def test_original_mcq_option_sha_reconciled_only_from_exact_lexicon(self):
        original={"en":"Momentum conserved","ms":"Keabadian momentum dan diabadikan",
                  "zh":"momentum"}
        correct={"en":original["en"],"ms":"Pemuliharaan momentum dan dikekalkan",
                 "zh":original["zh"]}
        def digest(label):
            return hashlib.sha256(json.dumps(label,sort_keys=True,
                  ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
        baseline=digest(original)
        self.assertTrue(_approved_v9_malay_lexicon_reconciliation(
            correct,baseline,APPROVED_MALAY_LEXICON_V9_SHA))
        self.assertFalse(_approved_v9_malay_lexicon_reconciliation(
            correct,baseline,"0"*64))
        self.assertFalse(_approved_v9_malay_lexicon_reconciliation(
            dict(correct,en="Changed option"),baseline,APPROVED_MALAY_LEXICON_V9_SHA))
        self.assertFalse(_approved_v9_malay_lexicon_reconciliation(
            dict(correct,ms=correct["ms"]+" extra"),baseline,APPROVED_MALAY_LEXICON_V9_SHA))
        self.assertFalse(_approved_v9_malay_lexicon_reconciliation(
            original,baseline,APPROVED_MALAY_LEXICON_V9_SHA))

    def test_roster_drift_fails(self):
        x=fixture()
        x["activities"].pop()
        with self.assertRaisesRegex(ValueError,"roster"):
            repair_private_malay_v9(x)

if __name__=="__main__":unittest.main()
