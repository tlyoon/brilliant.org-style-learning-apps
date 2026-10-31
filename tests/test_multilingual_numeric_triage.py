"""Source-free triage tests: numeric differences cannot certify translation."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.multilingual_numeric_triage import (
    numeric_tokens,_scan_activity,audit_source_bound_multilingual_numeric_triage,
)


class MultilingualNumericTriageTests(unittest.TestCase):
    def test_chinese_adjacent_ascii_digits_and_nfkc_fullwidth_digits(self):
        self.assertEqual(["1","2","0.5"],
                         numeric_tokens("\u7269\u4f531\u3001\u7269\u4f532\uff0c\u901f\u5ea60.5"))
        self.assertEqual(["1","2","0.5"],
                         numeric_tokens("\u7269\u4f53\uff11\u3001\u7269\u4f53\uff12\uff0c\u901f\u5ea6\uff10\uff0e\uff15"))

    def test_equivalent_numeric_triples_are_not_semantic_pass(self):
        a={"id":"case","prompt":{
             "en":"Object 1 and 2 move at 0.5 m/s",
             "ms":"Objek 1 dan 2 bergerak pada 0.5 m/s",
             "zh":"\u7269\u4f53\uff11\u548c\uff12\u4ee5\uff10\uff0e\uff15\u7c73\u6bcf\u79d2\u8fd0\u52a8"}}
        scanned,flags=_scan_activity(a)
        self.assertEqual(1,scanned)
        self.assertEqual([],flags)

    def test_missing_or_added_literal_is_review_flag_not_synthetic_fail(self):
        a={"id":"case","prompt":{
             "en":"Objects 1 and 2 exchange velocity",
             "ms":"Objek 1 dan 2 bertukar halaju",
             "zh":"\u4e24\u4e2a\u7269\u4f53\u4ea4\u6362\u901f\u5ea6"}}
        _,flags=_scan_activity(a)
        self.assertEqual(1,len(flags))
        self.assertEqual("CROSS_LOCALE_NUMERIC_TOKEN_DIFFERENCE",flags[0]["reasonCode"])
        self.assertNotIn("zh",str(flags[0].get("sourceText","")))
        self.assertNotIn("wrongTranslation",flags[0])

    def test_option_label_and_hints_are_scanned_without_any_private_text(self):
        a={"id":"case","hints":[{"en":"2","ms":"2","zh":"\uff12"}],
           "answerKey":{"options":[{"id":"a","label":{
                "en":"3","ms":"4","zh":"\uff13"}}]}}
        scanned,flags=_scan_activity(a)
        self.assertEqual(2,scanned)
        self.assertEqual("answerKey.options[0].label",flags[0]["field"])
        self.assertNotIn("3",json.dumps(flags))

    def test_possible_notation_equivalence_remains_review_required(self):
        cases=(
            ("1D collisions", "Perlanggaran 1D", "\u4e00\u7ef4\u78b0\u649e", "POSSIBLE_ONE_DIMENSION_NOTATION"),
            ("2D collision", "Perlanggaran 2D", "\u4e8c\u7ef4\u78b0\u649e", "POSSIBLE_TWO_DIMENSION_NOTATION"),
            ("Total momentum = 0", "Jumlah momentum = 0", "\u603b\u52a8\u91cf\u4e3a\u96f6", "POSSIBLE_WRITTEN_ZERO_NOTATION"),
            ("1D and 1D collisions", "1D dan 1D collisions",
             "\u4e00\u7ef4\u548c\u4e00\u7ef4\u78b0\u649e", "POSSIBLE_ONE_DIMENSION_NOTATION"),
        )
        for en,ms,zh,expected in cases:
            with self.subTest(expected=expected):
                count,flags=_scan_activity({"id":"test","prompt":{"en":en,"ms":ms,"zh":zh}})
                self.assertEqual(1,count)
                self.assertEqual(1,len(flags))
                self.assertEqual(expected,flags[0]["candidateReason"])
                self.assertFalse(flags[0]["confirmedSemanticEquivalence"])
                self.assertEqual("CROSS_LOCALE_NUMERIC_TOKEN_DIFFERENCE",flags[0]["reasonCode"])

    def test_unrelated_digits_not_hidden_by_chinese_dimension_terms(self):
        cases=(
            ("Momentum is 1", "Momentum adalah 1", "\u4e00\u7ef4\u52a8\u91cf"),
            ("1D and 2D", "1D dan 2D", "\u4e00\u7ef4\u78b0\u649e"),
            ("0 collision", "0 perlanggaran", "\u96f6\u78b0\u649e"),
        )
        for en,ms,zh in cases:
            with self.subTest(en=en):
                _,flags=_scan_activity({"id":"x","prompt":{"en":en,"ms":ms,"zh":zh}})
                self.assertTrue(flags)
                self.assertEqual("UNEXPLAINED_LITERAL_DIFFERENCE",flags[0]["candidateReason"])
                self.assertFalse(flags[0]["confirmedSemanticEquivalence"])

    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.r=Path(folder.name)
        self.pdf=self.r/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 synthetic source")
        self.pkg=self.r/"private.json"
        acts=[{"id":f"activity-{i}","prompt":{"en":"Object 1","ms":"Objek 1","zh":"\u7269\u4f53\uff11"}}
              for i in range(18)]
        self.pkg.write_text(json.dumps({"activities":acts}),encoding="utf-8")
        self.source=self.r/"private-packets.json"
        self.packets={a["id"]:{"sourceAnchors":[{
            "activityId":a["id"],"pageIndex":1,"quotedText":"synthetic original passage"}],
            "passageSha256":["a"*64],"sourceEvidence":"synthetic original passage",
            "verifiedPages":[1]} for a in acts}
        self.manifest={"sourceSha256":sha256(self.pdf.read_bytes()).hexdigest(),
                       "packageSha256":sha256(self.pkg.read_bytes()).hexdigest(),
                       "packets":self.packets}
        self.source.write_text(json.dumps(self.manifest),encoding="utf-8")

    def _run(self):
        with patch("app_generator.validation.multilingual_numeric_triage.source_packets_for_activities",
                   return_value=self.packets):
            return audit_source_bound_multilingual_numeric_triage(
                package_file=self.pkg,source_pdf=self.pdf,source_packets_file=self.source)

    def test_exact_source_manifest_yields_tentative_zero_flags_without_pass(self):
        r=self._run()
        self.assertEqual(18,r["sourceVerifiedActivities"])
        self.assertEqual(18,r["localizedFieldsChecked"])
        self.assertEqual(0,r["numericDriftFlagCount"])
        self.assertFalse(r["numericTokenIdentityProvesTranslation"])
        self.assertEqual("REVIEW_REQUIRED",r["academicQA"])
        self.assertEqual(0,r["academicPASS"])
        self.assertFalse(r["publicationAuthorized"])

    def test_modified_source_fails_closed(self):
        self.pdf.write_bytes(b"%PDF-1.4 modified original")
        with self.assertRaisesRegex(ValueError,"manifest mismatch"):
            self._run()

    def test_modified_package_fails_closed(self):
        self.pkg.write_text(self.pkg.read_text()+" ",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"manifest mismatch"):
            self._run()

    def test_stale_original_passage_fails_closed(self):
        forged={key:{**value,"passageSha256":["b"*64]} for key,value in self.packets.items()}
        with patch("app_generator.validation.multilingual_numeric_triage.source_packets_for_activities",
                   return_value=forged):
            with self.assertRaisesRegex(ValueError,"no longer reverify"):
                audit_source_bound_multilingual_numeric_triage(
                    package_file=self.pkg,source_pdf=self.pdf,source_packets_file=self.source)


if __name__=="__main__":
    unittest.main()
