"""Source-free adversarial tests of 36 option-specific physics models."""
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import json
import tempfile
import unittest

from app_generator.validation.mcq_statement_physics import (
    _group_truths,audit_source_bound_mcq_statement_physics,
)
from app_generator.validation.physics_proofs import KNOWN_CASES


def digest(labels):
    return sha256(json.dumps(labels,sort_keys=True,ensure_ascii=False,
                             separators=(",",":")).encode("utf-8")).hexdigest()


class StatementPhysicsTests(unittest.TestCase):
    def test_independent_option_propositions_cover_9_by_4(self):
        supported=refuted=pending=0
        for aid,(_,correct) in KNOWN_CASES.items():
            results=_group_truths(aid)
            self.assertEqual(4,len(results))
            self.assertIs(results[correct],True)
            supported+=sum(x is True for x in results.values())
            refuted+=sum(x is False for x in results.values())
            pending+=sum(x is None for x in results.values())
        self.assertEqual((9,26,1),(supported,refuted,pending))

    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root=Path(tmp.name)
        self.pkg=root/"candidate.json"
        self.pdf=root/"original.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 controlled test only")
        self.packets=root/"packets.json"
        self.packets.write_text("{}",encoding="utf-8")
        self.acts=[]
        self.digests={}
        for aid,(_,correct) in KNOWN_CASES.items():
            options=[]
            for oid in _group_truths(aid):
                labels={"en":"EN "+oid,"ms":"MS "+oid,"zh":"ZH "+oid}
                self.digests[aid,oid]=digest(labels)
                options.append({"id":oid,"label":labels})
            self.acts.append({"id":aid,"type":"mcq",
                "answerKey":{"correct":correct,"options":options}})
        self.acts.extend({"id":f"nonmcq-{n}","type":"interactive"}
                         for n in range(9))
        self.save()

    def save(self):
        self.pkg.write_text(json.dumps({"activities":self.acts}),encoding="utf-8")

    def audit(self):
        check={
            "newlyReverifiedSourceActivities":18,
            "packageSha256":sha256(self.pkg.read_bytes()).hexdigest(),
            "sourceSha256":sha256(self.pdf.read_bytes()).hexdigest(),
            "publicationAuthorized":False,
        }
        with patch(
            "app_generator.validation.mcq_statement_physics.verify_full_source_packet_roster",
            return_value=check,
        ),patch(
            "app_generator.validation.mcq_statement_physics.OPTION_LABEL_SHA256",
            self.digests,
        ):
            return audit_source_bound_mcq_statement_physics(
                package_file=self.pkg,source_pdf=self.pdf,packets_file=self.packets)

    def test_all_36_options_and_hold_academic_gate(self):
        out=self.audit()
        self.assertEqual(36,out["threeLanguageOptionLabelsBoundBySha256"])
        self.assertEqual(18,out["originalSourceActivityPassagesReverified"])
        self.assertEqual((9,26,1),
            (out["boundedAnswerOptionsSupported"],
             out["boundedDistractorsCounterexampled"],
             out["sourceFigureContactSemanticsPending"]))
        self.assertFalse(out["allOptionMeaningsFullyVerified"])
        self.assertEqual(0,out["formalAcademicPASS"])
        self.assertFalse(out["publicationAuthorized"])
        self.assertNotIn("EN ",json.dumps(out))

    def test_wrong_correct_answer_cannot_be_accepted(self):
        self.acts[0]["answerKey"]["correct"]=_group_truths(self.acts[0]["id"])
        self.save()
        with self.assertRaisesRegex(ValueError,"selected answer"):
            self.audit()

    def test_same_option_id_reworded_en_ms_zh_cannot_pass(self):
        option=self.acts[0]["answerKey"]["options"][0]
        for lang in ("en","ms","zh"):
            original=option["label"][lang]
            option["label"][lang]=original+" changed"
            self.save()
            with self.assertRaisesRegex(ValueError,"wording changed"):
                self.audit()
            option["label"][lang]=original

    def test_wrong_option_id_and_duplicate_cannot_pass(self):
        option=self.acts[0]["answerKey"]["options"]
        option[0]["id"]=option[1]["id"]
        self.save()
        with self.assertRaises(ValueError):self.audit()

    def test_source_passage_validation_failure_cannot_pass(self):
        with patch(
            "app_generator.validation.mcq_statement_physics.verify_full_source_packet_roster",
            side_effect=ValueError("original source passage tampered"),
        ):
            with self.assertRaisesRegex(ValueError,"tampered"):
                audit_source_bound_mcq_statement_physics(
                    package_file=self.pkg,source_pdf=self.pdf,packets_file=self.packets)

    def test_bad_mathematical_interpretation_rejected(self):
        aid=self.acts[0]["id"]
        fake={**_group_truths(aid)}
        fake[KNOWN_CASES[aid][1]]=False
        real=_group_truths
        def modified(k):
            return fake if k==aid else real(k)
        with patch(
            "app_generator.validation.mcq_statement_physics._group_truths",
            side_effect=modified,
        ):
            with self.assertRaisesRegex(ValueError,"correct MCQ option contradicts"):
                self.audit()


if __name__=="__main__":
    unittest.main()
