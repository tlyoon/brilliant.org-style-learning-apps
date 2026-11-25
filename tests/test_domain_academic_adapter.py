"""Cross-domain source-free regression for a reusable academic gate.

The physics subject adapter preserves existing negative evidence without
requiring hard-coded physics checks in the generic acceptance engine.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from app_generator.domains import resolve_domain
from app_generator.validation.academic_acceptance_matrix import (
    _domain_checks, audit_activity_matrix,
)
from app_generator.validation.multiball_qualification import (
    explicit_multiball_uniqueness_defects,
)
from app_generator.validation.impulse_basis_reasoning import (
    explicit_impulse_basis_rationale_defects,
)

ROOT = Path(__file__).resolve().parents[1]


def trilingual(value: str) -> dict[str, str]:
    return {"en": value, "ms": "Konsep " + value, "zh": "概念 " + value}


def activity(aid: str = "synthetic-diverse-topic") -> dict:
    return {
        "id": aid, "type": "mcq",
        "prompt": trilingual("Compare two physical systems"),
        "feedback": trilingual("Explain the qualitative behavior"),
        "answerKey": {"correct": "correct", "options": [
            {"id": "correct", "label": trilingual("Concept A")},
            {"id": "distractor", "label": trilingual("Concept B")},
        ]},
    }


class DomainAcademicAdapterTests(unittest.TestCase):
    def test_installed_physics_profile_supplies_negative_only_hooks(self):
        rationale, science = _domain_checks(ROOT, {"activities": [activity()]})
        self.assertEqual([], rationale(activity()))
        self.assertEqual([], science(activity()))
        self.assertFalse(hasattr(resolve_domain(ROOT).load_module(
            "validation", "academicValidatorModule"), "grant_academic_pass"))

    def test_physics_specific_defect_behavior_preserved(self):
        rationale, science = _domain_checks(ROOT, {"activities": [activity()]})
        cradle = activity("mcq-newton-cradle-multi-ball")
        cradle["explanation"] = trilingual(
            "the only configuration that satisfies both conservation laws")
        self.assertEqual(
            explicit_multiball_uniqueness_defects(cradle),
            science(cradle))
        impulse = activity("mcq-impulse-approximation-basis")
        impulse["answerKey"] = {
            "correct": "opt-internal-forces-dominate",
            "options": [
                {"id": "opt-equal-masses-required",
                 "label": {
                     "en": "Equal mass and opposite velocity",
                     "ms": "Jisim sama dan halaju bertentangan",
                     "zh": "质量相等，速度相反"}},
                {"id": "opt-internal-forces-dominate",
                 "label": trilingual("Internal forces dominate")},
            ],
        }
        impulse["answerLogic"] = {
            "en": "Option D fails because the normal forces vanish.",
            "ms": "Pilihan D tidak sah kerana daya normal hilang.",
            "zh": "选项 D 由于法向力消失而不成立。",
        }
        self.assertEqual(explicit_impulse_basis_rationale_defects(impulse),
                         rationale(impulse))
        self.assertTrue(rationale(impulse))

    def test_generic_engine_source_has_no_direct_pdf_specific_import(self):
        source = (ROOT / "app_generator" / "validation" /
                  "academic_acceptance_matrix.py").read_text(encoding="utf-8")
        for item in ("multiball_qualification", "ballistic_impulse_scope",
                     "inelastic_separation_claim",
                     "relative_velocity_derivation", "impulse_basis_reasoning"):
            self.assertNotIn("from app_generator.validation." + item, source)
        self.assertIn("resolve_package_domain", source)

    def test_unrelated_domain_without_adapter_remains_unknown(self):
        other = SimpleNamespace(manifest={"validation": {}})
        with patch("app_generator.validation.academic_acceptance_matrix.resolve_package_domain",
                   return_value=other):
            rationale, science = _domain_checks(ROOT, {"activities": [activity()]})
        self.assertEqual([], rationale(activity()))
        self.assertEqual([], science(activity()))

    def test_invalid_domain_adapter_cannot_manufacture_success(self):
        bogus = SimpleNamespace(
            manifest={"validation": {"academicValidatorModule": "anything.py"}},
            load_module=lambda *_: SimpleNamespace(
                answer_rationale_defects=lambda a: ["known"],
                scientific_consistency_defects=lambda a: "PASS"),
        )
        with patch("app_generator.validation.academic_acceptance_matrix.resolve_package_domain",
                   return_value=bogus):
            rationale, science = _domain_checks(ROOT, {"activities": [activity()]})
        self.assertEqual(["known"], rationale(activity()))
        with self.assertRaisesRegex(ValueError, "malformed defect"):
            science(activity())
        self.assertFalse(hasattr(bogus, "academicallyApproved"))

    def test_missing_mandatory_adapter_hook_fails_closed(self):
        fake = SimpleNamespace(
            manifest={"validation": {"academicValidatorModule": "anything.py"}},
            load_module=lambda *_: SimpleNamespace(
                scientific_consistency_defects=lambda a: []),
        )
        with patch("app_generator.validation.academic_acceptance_matrix.resolve_package_domain",
                   return_value=fake):
            with self.assertRaisesRegex(ValueError, "two negative-evidence hooks"):
                _domain_checks(ROOT, {"activities": [activity()]})

    def test_two_diverse_synthetic_activities_still_require_science_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-1.4 synthetic unit-test placeholder")
            pkg = root / "candidate.json"
            pkg.write_text(json.dumps({"activities": [
                activity("synthetic-thermodynamics"),
                activity("synthetic-optics"),
            ]}), encoding="utf-8")
            result = audit_activity_matrix(
                repo_root=ROOT, package_path=pkg, source_pdf=pdf,
                source_sha256=sha256(pdf.read_bytes()).hexdigest(),
                expected_count=2)
        self.assertEqual(0, result["counts"]["PASS"])
        self.assertEqual(2, result["counts"]["REVIEW_REQUIRED"])
        self.assertFalse(result["publicationAuthorized"])


if __name__ == "__main__":
    unittest.main()
