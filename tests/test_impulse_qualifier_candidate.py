"""Fail-closed review-only correction of the exact installed impulse activity."""
import copy
import hashlib
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from app_generator.validation.impulse_qualifier_repair import (
    ACTIVITY_ID, EXPECTED_ANSWERS, REVISION, SELECTED_ITEM, SOURCE_SHA256,
    build_review_candidate, canonical_hash, check_physics_rule,
)
from app_generator.validation.interactive_physics import (
    EXPECTED_TEXT_SHA256, semantic_digest,
)

ROOT=Path(__file__).resolve().parents[1]
# The checked-in repository sample is not the generated pilot. Unit tests
# use independent source-free inputs; actual candidate verification uses
# the protected Yoga6 installed package outside version control.


def fixture():
    activity={
        "id":ACTIVITY_ID,"type":"interactive","interactionMode":"selection",
        "objective":"old objective",
        "prompt":{"en":"Old language","ms":"Lama","zh":"???"},
        "hints":[{"en":"old","ms":"lama","zh":"?"},{"en":"old two","ms":"lama dua","zh":"???"}],
        "feedback":{"en":"old","ms":"lama","zh":"?"},
        "answerLogic":{"en":"old","ms":"lama","zh":"?"},
        "explanation":{"en":"old","ms":"lama","zh":"?"},
        "prerequisiteRecovery":{"prerequisiteId":"basic",
            "prompt":{"en":"old","ms":"lama","zh":"?"}},
        "interaction":{
            "items":[
                {"id":i,"label":{"en":"old","ms":"lama","zh":"?"}}
                for i in [*EXPECTED_ANSWERS,"item-deformation-decreases-momentum",
                          "item-requires-zero-external-forces-ever"]
            ],
            "correctSelections":list(EXPECTED_ANSWERS),
        },
    }
    return {"activities":[activity,{"id":"unrelated","type":"mcq","prompt":{"en":"Keep unchanged"}}]}


class ImpulseReviewCandidateTests(unittest.TestCase):
    def source(self,tmp):
        path=Path(tmp)/"source.pdf"
        path.write_bytes(b"%PDF-1.4 fixture")
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def build(self,doc,pdf,digest):
        old=next(a for a in doc["activities"] if a["id"]==ACTIVITY_ID)
        return build_review_candidate(
            doc,pdf,source_sha256=digest,
            original_package_hash=canonical_hash(doc),
            original_semantic_sha=semantic_digest(old),
        )

    def test_exact_external_impulse_is_not_strict_conservation(self):
        check_physics_rule()
        pi=Fraction(2); j=Fraction(1,100000)
        self.assertNotEqual(pi+j,pi)
        self.assertEqual(pi+Fraction(0),pi)

    def test_generated_candidate_changes_only_one_activity_and_keeps_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            pdf,digest=self.source(folder)
            old=fixture()
            original=copy.deepcopy(old)
            with patch("app_generator.validation.impulse_qualifier_repair.SOURCE_SHA256",digest):
                new,meta=self.build(old,pdf,digest)
            self.assertEqual(old,original)
            self.assertEqual(old["activities"][1],new["activities"][1])
            self.assertEqual(old["activities"][0]["interaction"]["correctSelections"],
                             new["activities"][0]["interaction"]["correctSelections"])
            self.assertEqual(old["activities"][0]["interaction"]["items"][0],
                             new["activities"][0]["interaction"]["items"][0])
            self.assertTrue(meta["answerKeyUnchanged"])
            self.assertTrue(meta["reviewOnly"])
            self.assertFalse(meta["publicationAuthorized"])
            self.assertEqual("REVIEW_REQUIRED",meta["academicQA"])
            self.assertEqual(["en","ms","zh"],meta["locales"])

    def test_rejects_wrong_source_wrong_package_changed_answers_or_text(self):
        with tempfile.TemporaryDirectory() as folder:
            pdf,digest=self.source(folder)
            old=fixture()
            with self.assertRaisesRegex(ValueError,"controlled"):
                build_review_candidate(old,pdf)
            with patch("app_generator.validation.impulse_qualifier_repair.SOURCE_SHA256",digest):
                with self.assertRaisesRegex(ValueError,"protected baseline"):
                    build_review_candidate(old,pdf,source_sha256=digest,
                                           original_package_hash="0"*64)
                with self.assertRaisesRegex(ValueError,"localized question"):
                    build_review_candidate(old,pdf,source_sha256=digest,
                                           original_package_hash=canonical_hash(old),
                                           original_semantic_sha="0"*64)
                corrupt=copy.deepcopy(old)
                corrupt["activities"][0]["interaction"]["correctSelections"].pop()
                with self.assertRaisesRegex(ValueError,"selection answer"):
                    self.build(corrupt,pdf,digest)
                duplicate=copy.deepcopy(old)
                duplicate["activities"].append(copy.deepcopy(duplicate["activities"][0]))
                with self.assertRaisesRegex(ValueError,"unique"):
                    self.build(duplicate,pdf,digest)
                missing=copy.deepcopy(old)
                missing["activities"][0]["interaction"]["items"]=[
                    x for x in missing["activities"][0]["interaction"]["items"]
                    if x["id"]!=SELECTED_ITEM
                ]
                with self.assertRaisesRegex(ValueError,"targeted item"):
                    self.build(missing,pdf,digest)

    def test_translations_explicitly_preserve_exact_vs_approximate(self):
        # Terminology predicates are deterministic *minimum requirements*,
        # not an independent semantic translation-quality certificate.
        checks={
            "en":("approximate","exact","external impulse"),
            "ms":("anggaran","tepat","impuls luar"),

            "zh":("\u8fd1\u4f3c","\u7cbe\u786e","\u5916\u529b\u51b2\u91cf"),
        }
        for field in ("prompt","feedback","answerLogic","explanation",
                      "selectedItem","secondHint","prerequisite"):
            for locale,terms in checks.items():
                with self.subTest(field=field,locale=locale):
                    text=REVISION[field][locale].casefold()
                    for token in terms:
                        self.assertIn(token.casefold(),text)
        self.assertIn("\u0394p",REVISION["feedback"]["en"])
        self.assertIn("J_ext",REVISION["explanation"]["ms"])
        self.assertIn("J_ext",REVISION["explanation"]["zh"])
        for field in ("prompt","feedback","answerLogic","explanation","selectedItem","secondHint","prerequisite"):
            value=REVISION[field]["zh"]
            self.assertNotIn("?",value)
            self.assertNotIn("\uFFFD",value)
            self.assertTrue(any("\u4e00"<=c<="\u9fff" for c in value))

    def test_new_candidate_fails_prior_frozen_text_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            pdf,digest=self.source(folder)
            old=fixture()
            with patch("app_generator.validation.impulse_qualifier_repair.SOURCE_SHA256",digest):
                new,_=self.build(old,pdf,digest)
            a=new["activities"][0]
            self.assertNotEqual(semantic_digest(a),semantic_digest(old["activities"][0]))
            self.assertNotEqual(semantic_digest(a),
                                EXPECTED_TEXT_SHA256.get(ACTIVITY_ID))
            self.assertEqual(new["activities"][0]["interaction"]["correctSelections"],
                             list(EXPECTED_ANSWERS))


if __name__=="__main__":
    unittest.main()
