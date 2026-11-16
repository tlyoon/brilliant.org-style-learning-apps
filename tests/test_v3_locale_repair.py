"""Regression guards for multilingual script corruption and private V3 repair.

The original frozen package and old AI verdict must remain untouched.
No test communicates with a model or calls a paid provider.
"""
from __future__ import annotations

from hashlib import sha1, sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.v3_locale_script_integrity import script_findings
from app_generator.validation.v3_versioned_text_repair import (
    make_locale_repair, store_private_repair,
)
from app_generator.runtime.v3_course_review import plan_v3_course_review
from tests.test_v3_course_review_dispatch import synthetic_course


def fixture():
    return {"activities": [
        {"id": "synthetic-one", "type": "mcq",
         "prompt": {"en": "Choose ΔF / Σp.", "ms": "Pilih sebuahเลgelongsor.",
                    "zh": "请选择力。"},
         "hints": [{"en": "Momentum.", "ms": "Rover-legelongsor.",
                    "zh": "动量守恒。"}],
         "answerKey": {"correct": "a", "options": [{"id": "a"}, {"id": "b"}]}},
        {"id": "synthetic-two", "type": "mcq",
         "prompt": {"en": "Unaffected", "ms": "Tidak diubah", "zh": "未修改。"},
         "answerKey": {"correct": "a", "options": [{"id": "a"}]}}
    ]}


def raw_package(package):
    return (json.dumps(package, ensure_ascii=False, indent=2) + "\n").encode("utf8")


class LocaleRepairTests(unittest.TestCase):
    def test_real_frozen_section92_corruption_matches_two_reviewers(self):
        root = Path(__file__).resolve().parents[1]
        frozen = root / "content/chapter-9/section-9-2/package.json"
        package = json.loads(frozen.read_text(encoding="utf8"))
        issues = script_findings(package)
        self.assertEqual(
            [(r["activityId"], r["codepoint"]) for r in issues],
            [("act-int-iso-05", "U+0E40"), ("act-int-iso-05", "U+0E25")])
        self.assertTrue(all(r["path"].endswith(".prompt.ms") for r in issues))

    def test_english_malay_chinese_legitimate_math_symbols_pass(self):
        package = fixture()
        package["activities"][0]["prompt"]["ms"] = "Pilih konsep daya Δ, Σ."
        package["activities"][0]["hints"][0]["ms"] = "Rover dan kereta luncur."
        self.assertEqual(script_findings(package), [])

    def test_mixed_script_replacement_arabic_cjk_and_thai_rejected(self):
        package = fixture()
        package["activities"][0]["prompt"]["en"] = "Bad x漢字"
        package["activities"][1]["prompt"]["zh"] = "字\ufffd"
        kinds = {finding["scriptName"] for finding in script_findings(package)}
        self.assertIn("THAI", kinds)
        self.assertIn("CJK UNIFIED IDEOGRAPH", kinds)
        self.assertIn("REPLACEMENT_CHARACTER", kinds)
        package["activities"][0]["prompt"]["en"] = "hello ภาษา"
        self.assertTrue(any(x["scriptName"] == "THAI" for x in script_findings(package)))

    def test_exact_locale_repair_preserves_other_activities_and_en_zh(self):
        old = raw_package(fixture())
        new, receipt = make_locale_repair(
            old, "synthetic-one", "ms",
            (("sebuahเลgelongsor", "sebuah kereta luncur"),
             ("legelongsor", "kereta luncur")))
        original = json.loads(old)
        revised = json.loads(new)
        self.assertEqual(revised["activities"][1], original["activities"][1])
        self.assertEqual(revised["activities"][0]["prompt"]["en"],
                         original["activities"][0]["prompt"]["en"])
        self.assertEqual(revised["activities"][0]["prompt"]["zh"],
                         original["activities"][0]["prompt"]["zh"])
        self.assertEqual(revised["activities"][0]["prompt"]["ms"],
                         "Pilih sebuah kereta luncur.")
        self.assertEqual(revised["activities"][0]["hints"][0]["ms"],
                         "Rover-kereta luncur.")
        self.assertEqual(script_findings(revised), [])
        self.assertNotEqual(receipt["candidatePackageSha256"],
                            receipt["parentPackageSha256"])
        self.assertEqual(receipt["status"], "PENDING_FRESH_GEMINI_TWO_REVIEWER_QA")
        self.assertIs(receipt["publicationAuthorized"], False)
        self.assertIs(receipt["parentModelVerdictModified"], False)

    def test_private_store_restart_safe_no_overwrite(self):
        old = raw_package(fixture())
        new, receipt = make_locale_repair(
            old, "synthetic-one", "ms",
            (("sebuahเลgelongsor", "sebuah kereta luncur"),
             ("legelongsor", "kereta luncur")))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/"Microvid"/"Bosla"/"repairs"
            first = store_private_repair(root, new, receipt)
            second = store_private_repair(root, new, receipt)
            self.assertEqual(first, second)
            self.assertEqual((first/"package.json").read_bytes(), new)
            (first/"review-required.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "IDENTITY_CONFLICT"):
                store_private_repair(root, new, receipt)

    def test_bad_review_target_expected_string_and_foreign_script_refused(self):
        old = raw_package(fixture())
        with self.assertRaisesRegex(ValueError, "ACTIVITY_NOT_UNIQUE"):
            make_locale_repair(old, "not-in-package", "ms",
                               (("legelongsor", "kereta luncur"),))
        with self.assertRaisesRegex(ValueError, "NOT_PRESENT"):
            make_locale_repair(old, "synthetic-one", "ms",
                               (("unmatched-thing", "normal"),))
        with self.assertRaisesRegex(ValueError, "UNRESOLVED_SCRIPT"):
            make_locale_repair(old, "synthetic-one", "ms",
                               (("legelongsor", "kereta luncur"),))

    def test_malformed_edit_and_publish_promotion_refused(self):
        old = raw_package(fixture())
        for changes in ((), (("", "x"),), (("x", "x"),),
                        (("dup", "one"), ("dup", "two"))):
            with self.subTest(changes=changes), self.assertRaisesRegex(
                    ValueError, "INVALID_REQUEST"):
                make_locale_repair(old, "synthetic-one", "ms", changes)
        new, receipt = make_locale_repair(
            old, "synthetic-one", "ms",
            (("sebuahเลgelongsor", "sebuah kereta luncur"),
             ("legelongsor", "kereta luncur")))
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "NOT_PUBLICATION_AUTHORITY"):
                store_private_repair(Path(folder), new, receipt,
                                     authorization_to_publish=True)

    def test_normal_course_dispatch_quarantines_script_before_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/"repo"
            chapter = synthetic_course(root)
            path = chapter/"section-7-1"/"package.json"
            package = json.loads(path.read_text(encoding="utf8"))
            package["activities"][0]["prompt"]["ms"] += "เล"
            replacement = raw_package(package)
            path.write_bytes(replacement)
            manifest = root/"docs/acceptance_closure_chapter7.json"
            frozen = json.loads(manifest.read_text(encoding="utf8"))
            first = frozen["frozenCandidates"][0]
            first["packageSha256"] = sha256(replacement).hexdigest()
            first["packageGitBlobSha1"] = sha1(
                b"blob "+str(len(replacement)).encode()+b"\0"+replacement).hexdigest()
            manifest.write_text(json.dumps(frozen), encoding="utf8")
            result = plan_v3_course_review(
                chapter, root, private_root=Path(folder)/"private",
                continue_independent=True)
            self.assertEqual(result["nextSection"], "section-7-2")
            self.assertIn("section-7-1", result["quarantinedSections"])
            self.assertEqual(result["scriptQuarantinedSections"],
                             {"section-7-1": 2})
            self.assertEqual(result["dispatchStatus"],
                             "READY_FOR_AUTHORIZED_REVIEW_SESSIONS")
            self.assertIs(result["publicationAuthorized"], False)

    def test_private_candidate_cannot_be_stored_in_git_checkout(self):
        old = raw_package(fixture())
        new, receipt = make_locale_repair(
            old, "synthetic-one", "ms",
            (("sebuahเลgelongsor", "sebuah kereta luncur"),
             ("legelongsor", "kereta luncur")))
        checkout = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(ValueError, "CANNOT_STORE_PRIVATE_TEXT_IN_GIT"):
            store_private_repair(checkout / "PRIVATE-UNSAFE", new, receipt)
        self.assertFalse((checkout / "PRIVATE-UNSAFE").exists())

    def test_unrelated_thai_script_in_source_provenance_ignored(self):
        package = fixture()
        package["sourceManifest"] = "ข้อมูล"
        package["activities"][0]["provenance"] = {
            "sourceLocation": "Unicode Thai file names may be valid"}
        # The source location/provenance should not be read as learner copy.
        self.assertEqual(len(script_findings(package)), 2)


    def test_atomic_private_candidate_promotion_survives_interrupted_write(self):
        old = raw_package(fixture())
        new, receipt = make_locale_repair(
            old, "synthetic-one", "ms",
            (("sebuahเลgelongsor", "sebuah kereta luncur"),
             ("legelongsor", "kereta luncur")))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "private" / "repairs"
            final = root / receipt["candidatePackageSha256"]
            with patch(
                    "app_generator.validation.v3_versioned_text_repair.Path.rename",
                    side_effect=OSError("simulated interrupted atomic promotion")):
                with self.assertRaisesRegex(
                        OSError, "interrupted atomic promotion"):
                    store_private_repair(root, new, receipt)
            self.assertFalse(final.exists())
            candidate = store_private_repair(root, new, receipt)
            self.assertEqual(candidate, final)
            self.assertEqual((candidate / "package.json").read_bytes(), new)
            self.assertTrue((candidate / "review-required.json").is_file())
            self.assertFalse(json.loads(
                (candidate / "review-required.json").read_text())[
                    "publicationAuthorized"])

    def test_orphaned_precommit_stage_does_not_block_restart(self):
        old = raw_package(fixture())
        new, receipt = make_locale_repair(
            old, "synthetic-one", "ms",
            (("sebuahเลgelongsor", "sebuah kereta luncur"),
             ("legelongsor", "kereta luncur")))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "private" / "repairs"
            orphan = root / ".v3-repair-stage-hard-crash"
            orphan.mkdir(parents=True)
            (orphan / "package.json").write_bytes(new[:20])
            final = store_private_repair(root, new, receipt)
            self.assertEqual(
                final.name, receipt["candidatePackageSha256"])
            self.assertEqual((final / "package.json").read_bytes(), new)
            self.assertTrue(orphan.exists())
            self.assertEqual(final, store_private_repair(root, new, receipt))

if __name__ == "__main__":
    unittest.main()
