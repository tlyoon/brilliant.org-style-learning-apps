"""Adversarial, synthetic-only narrow numerical-notation audit tests."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.narrow_numeric_notation import (
    _normalize_only_warranted_zh, audit_private_narrow_numeric_notation,
)
from app_generator.validation.multilingual_numeric_triage import numeric_tokens


class NarrowNotationTests(unittest.TestCase):
    def test_one_dimension_literal_numeric_only(self):
        triplet = {"en": "A 1D collision", "ms": "Perlanggaran 1D",
                   "zh": "\u4e00\u7ef4\u78b0\u649e"}
        reason, out = _normalize_only_warranted_zh(triplet)
        self.assertEqual("EXACT_DIMENSION_1_NUMERIC_NORMALIZATION", reason)
        self.assertEqual(Counter(numeric_tokens(triplet["en"])),
                         Counter(numeric_tokens(out)))

    def test_repeated_one_dimension_but_only_exact_multiplicities(self):
        triplet={"en":"1D versus 1D", "ms":"1D lawan 1D",
                 "zh":"\u4e00\u7ef4\u4e0e\u4e00\u7ef4"}
        reason, out = _normalize_only_warranted_zh(triplet)
        self.assertEqual("EXACT_DIMENSION_1_NUMERIC_NORMALIZATION",reason)
        self.assertEqual(2, Counter(numeric_tokens(out))["1"])
        triplet["zh"] = "\u4e00\u7ef4\u4e0e\u4e00\u7ef4\uff0c\u4ee5\u53ca\u4e00\u7ef4"
        reason, _ = _normalize_only_warranted_zh(triplet)
        self.assertEqual("NOTATION_NOT_STRICTLY_RESOLVED",reason)

    def test_two_dimension_missing_one_numeric(self):
        triplet={"en":"2D collision", "ms":"2D perlanggaran",
                 "zh":"\u4e8c\u7ef4\u78b0\u649e"}
        reason, out = _normalize_only_warranted_zh(triplet)
        self.assertEqual("EXACT_DIMENSION_2_NUMERIC_NORMALIZATION", reason)
        self.assertEqual(["2"], numeric_tokens(out))

    def test_momentum_zero_context_only(self):
        triplet={"en":"Total momentum is 0", "ms":"Momentum sifar 0",
                 "zh":"\u603b\u52a8\u91cf\u4e3a\u96f6"}
        reason, out = _normalize_only_warranted_zh(triplet)
        self.assertEqual("EXACT_MOMENTUM_ZERO_NUMERIC_NORMALIZATION", reason)
        self.assertEqual(["0"],numeric_tokens(out))
        triplet["zh"]="\u67d0\u4e9b\u78b0\u649e\u4e3a\u96f6"
        self.assertEqual("NOTATION_NOT_STRICTLY_RESOLVED",
                         _normalize_only_warranted_zh(triplet)[0])

    def test_mixed_numeral_and_written_one_dimension_across_en_ms_zh(self):
        triplet = {
            "en": "The 1D rule concerns one-dimensional elastic collisions.",
            "ms": "Hukum 1D untuk perlanggaran kenyal satu dimensi.",
            "zh": "\u4e00\u7ef4\u5173\u7cfb\u4ec5\u7528\u4e8e\u4e00\u7ef4\u5f39\u6027\u78b0\u649e\u3002",
        }
        reason, zh_normalized = _normalize_only_warranted_zh(triplet)
        self.assertEqual("EXACT_MIXED_WRITTEN_ONE_DIMENSION_NOTATION", reason)
        self.assertEqual(2, Counter(numeric_tokens(zh_normalized))["1"])
        self.assertEqual(2, triplet["zh"].count("\u4e00\u7ef4"))
        self.assertEqual(["1"], numeric_tokens(triplet["en"]))
        self.assertEqual(["1"], numeric_tokens(triplet["ms"]))

    def test_mixed_dimension_requires_exact_writing_in_both_en_and_ms(self):
        triplet = {
            "en": "The 1D rule applies to one-dimensional collisions.",
            "ms": "Hukum 1D untuk perlanggaran kenyal.",
            "zh": "\u4e00\u7ef4\u5173\u7cfb\u4ec5\u7528\u4e8e\u4e00\u7ef4\u5f39\u6027\u78b0\u649e\u3002",
        }
        self.assertEqual("NOTATION_NOT_STRICTLY_RESOLVED",
                         _normalize_only_warranted_zh(triplet)[0])
        triplet["ms"] = "Hukum 1D untuk perlanggaran satu dimensi."
        triplet["zh"] += "\u4e00\u7ef4"
        self.assertEqual("NOTATION_NOT_STRICTLY_RESOLVED",
                         _normalize_only_warranted_zh(triplet)[0])

    def test_extra_numeric_value_does_not_get_hidden_by_mixed_alias(self):
        triplet = {
            "en": "1D one-dimensional collision with 3 objects",
            "ms": "1D perlanggaran satu dimensi dengan 3 objek",
            "zh": "\u4e00\u7ef4\u4e00\u7ef4\u78b0\u649e\u4e0e4\u4e2a\u7269\u4f53",
        }
        self.assertEqual("NOTATION_NOT_STRICTLY_RESOLVED",
                         _normalize_only_warranted_zh(triplet)[0])

    def test_mixed_written_dimensionality_not_2d_or_attached_words(self):
        triplet = {
            "en": "1D pseudoone-dimensional effect",
            "ms": "1D kesan satu dimensi",
            "zh": "\u4e00\u7ef4\u4e00\u7ef4\u6548\u5e94",
        }
        self.assertEqual("NOTATION_NOT_STRICTLY_RESOLVED",
                         _normalize_only_warranted_zh(triplet)[0])
        triplet["en"] = "1D and two-dimensional effects"
        self.assertEqual("NOTATION_NOT_STRICTLY_RESOLVED",
                         _normalize_only_warranted_zh(triplet)[0])

    def test_unrelated_number_mismatch_not_hidden(self):
        triplet={"en":"2D and 3 objects", "ms":"2D dan 3 objek",
                 "zh":"\u4e8c\u7ef4\u548c4\u4e2a\u7269\u4f53"}
        self.assertEqual("NOTATION_NOT_STRICTLY_RESOLVED",
                         _normalize_only_warranted_zh(triplet)[0])

    def test_source_verified_whole_roster_and_no_semantic_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            pkg=root/"package.json"; pdf=root/"source.pdf"; packet=root/"packets.json"
            activities=[{"id":f"x{i}", "prompt":{
                "en":"1D collision","ms":"1D perlanggaran",
                "zh":"\u4e00\u7ef4\u78b0\u649e"}} for i in range(18)]
            pkg.write_text(json.dumps({"activities":activities}),encoding="utf-8")
            pdf.write_bytes(b"%PDF-1.4 synthetic")
            packet.write_text("{}",encoding="utf-8")
            flags=[{"field":"prompt","candidateReason":"POSSIBLE_ONE_DIMENSION_NOTATION"}]
            triage={
                "status":"SOURCE_BOUND_NUMERIC_TOKEN_TRIAGE",
                "sourceSha256":sha256(pdf.read_bytes()).hexdigest(),
                "packageSha256":sha256(pkg.read_bytes()).hexdigest(),
                "sourceVerifiedActivities":18,
                "localizedFieldsChecked":18,
                "numericDriftFlagCount":18,
                "academicPASS":0,"publicationAuthorized":False,
                "activities":[{"activityId":a["id"],
                               "localizedFieldsChecked":1,
                               "numericTokenDriftFlags":flags} for a in activities],
            }
            with patch(
                "app_generator.validation.narrow_numeric_notation.audit_source_bound_multilingual_numeric_triage",
                return_value=triage,
            ) as verifier:
                report=audit_private_narrow_numeric_notation(
                    package_file=pkg,source_pdf=pdf,source_packets_file=packet)
                verifier.assert_called_once()
            self.assertEqual(18,report["narrowNumericNotationMatches"])
            self.assertEqual(0,report["remainingUnresolvedNumericFlags"])
            self.assertFalse(report["wholeTranslationMeaningVerified"])
            self.assertFalse(report["physicsMeaningVerified"])
            self.assertEqual(0,report["academicPASS"])
            self.assertFalse(report["publicationAuthorized"])
            self.assertNotIn("\u4e00\u7ef4",json.dumps(report,ensure_ascii=False))

    def test_source_perturbation_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            p=root/"package.json";p.write_text('{"activities":[]}')
            pdf=root/"source.pdf";pdf.write_bytes(b"%PDF-1.4 synthetic")
            packet=root/"source-packets.json";packet.write_text("{}")
            with patch(
                "app_generator.validation.narrow_numeric_notation.audit_source_bound_multilingual_numeric_triage",
                side_effect=ValueError("source passage not exact"),
            ):
                with self.assertRaisesRegex(ValueError,"not exact"):
                    audit_private_narrow_numeric_notation(
                        package_file=p,source_pdf=pdf,source_packets_file=packet)


if __name__ == "__main__":
    unittest.main()
