"""Source-free negative fixtures for exact academic evidence-coverage gates."""
from __future__ import annotations

from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.academic_coverage_gate import audit_academic_coverage
from scripts.audit_academic_coverage import main as academic_cli

SOURCE = "a" * 64


def packet(status="REVIEW_REQUIRED", *, verified_source=False, ids=("mcq-a", "interactive-b")):
    package = {"activities": [{"id": aid, "type": "mcq" if aid.startswith("mcq") else "interactive",
                                "prompt": {"en": "Synthetic", "ms": "Sintetik", "zh": "合成"}}
                               for aid in ids]}
    raw = json.dumps(package, ensure_ascii=False).encode("utf-8")
    rows = []
    for activity in package["activities"]:
        digest = sha256(json.dumps(activity, sort_keys=True,
            ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        states = {gate: status for gate in REQUIRED}
        if status == "PASS" and not verified_source:
            states["source_fidelity"] = "REVIEW_REQUIRED"
        actual = ("FAIL" if "FAIL" in states.values() else
                  "PASS" if all(state == "PASS" for state in states.values()) else
                  "REVIEW_REQUIRED")
        rows.append({
            "activityId": activity["id"], "activitySha256": digest,
            "gates": states, "academicQA": actual,
            "sourceLocationVerified": verified_source,
            "publicationAuthorized": False,
        })
    counts = {key: sum(row["academicQA"] == key for row in rows)
              for key in ("PASS", "FAIL", "REVIEW_REQUIRED")}
    overall = ("FAIL" if counts["FAIL"] else
               "PASS" if counts["PASS"] == len(rows) else "REVIEW_REQUIRED")
    matrix = {
        "packageSha256": sha256(raw).hexdigest(),
        "sourceSha256": SOURCE, "activityCount": len(rows),
        "activities": rows, "counts": counts, "academicQA": overall,
        "publicationAuthorized": False,
    }
    return raw, matrix


class AcademicCoverageGateTests(unittest.TestCase):
    def test_unknown_meaning_requires_five_independent_proofs(self):
        raw,matrix = packet()
        result = audit_academic_coverage(
            package_bytes=raw, matrix=matrix, source_sha256=SOURCE)
        self.assertEqual("INDEPENDENT_ACADEMIC_PROOF_REQUIRED", result["status"])
        self.assertEqual(2, result["activityCount"])
        self.assertEqual({gate: 2 for gate in REQUIRED}, result["perGateOutstanding"])
        self.assertEqual("REVIEW_REQUIRED", result["academicQA"])
        self.assertEqual(0, result["formalAcademicPassCount"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertFalse(result["humanInterventionRequiredByThisTool"])

    def test_all_pass_claimed_without_proof_does_not_become_acceptance(self):
        raw,matrix = packet("PASS", verified_source=True)
        result = audit_academic_coverage(
            package_bytes=raw, matrix=matrix, source_sha256=SOURCE)
        self.assertEqual(2, result["matrixClaimedStatuses"]["PASS"])
        self.assertEqual("REVIEW_REQUIRED", result["academicQA"])
        self.assertFalse(result["academicEvidenceIndependentlyVerifiedHere"])
        self.assertEqual(0, result["formalAcademicPassCount"])

    def test_concrete_defect_is_reported_without_publish(self):
        raw,matrix = packet("FAIL")
        result = audit_academic_coverage(
            package_bytes=raw, matrix=matrix, source_sha256=SOURCE)
        self.assertEqual("DETERMINISTIC_FAILURES_REQUIRE_CORRECTION", result["status"])
        self.assertEqual("FAIL", result["academicQA"])
        self.assertEqual(2, result["perGateFailures"]["physics_consistency"])
        self.assertFalse(result["publicationAuthorized"])

    def test_mutated_package_or_source_sha_is_rejected(self):
        raw,matrix = packet()
        with self.assertRaises(ValueError):
            audit_academic_coverage(package_bytes=raw+b" ",
                                    matrix=matrix,source_sha256=SOURCE)
        with self.assertRaises(ValueError):
            audit_academic_coverage(package_bytes=raw,matrix=matrix,
                                    source_sha256="b"*64)
        with self.assertRaises(ValueError):
            audit_academic_coverage(package_bytes=raw,matrix=matrix,
                                    source_sha256="not-a-sha")

    def test_absent_gate_or_duplicate_and_stale_roster_is_rejected(self):
        raw,matrix = packet()
        matrix["activities"][0]["gates"].pop("visual_semantics")
        with self.assertRaisesRegex(ValueError, "gate"):
            audit_academic_coverage(package_bytes=raw,matrix=matrix,
                                    source_sha256=SOURCE)
        raw,matrix = packet()
        matrix["activities"][1]["activityId"] = matrix["activities"][0]["activityId"]
        with self.assertRaises(ValueError):
            audit_academic_coverage(package_bytes=raw,matrix=matrix,
                                    source_sha256=SOURCE)

    def test_source_fidelity_pass_claim_without_verified_original_page_rejected(self):
        raw,matrix = packet()
        row = matrix["activities"][0]
        row["gates"]["source_fidelity"] = "PASS"
        with self.assertRaisesRegex(ValueError, "original passage"):
            audit_academic_coverage(package_bytes=raw,matrix=matrix,
                                    source_sha256=SOURCE)

    def test_counter_disagreement_and_publication_true_are_rejected(self):
        raw,matrix = packet()
        matrix["counts"]["PASS"] = 1
        with self.assertRaisesRegex(ValueError, "aggregate"):
            audit_academic_coverage(package_bytes=raw,matrix=matrix,
                                    source_sha256=SOURCE)
        raw,matrix = packet()
        matrix["publicationAuthorized"] = True
        with self.assertRaises(ValueError):
            audit_academic_coverage(package_bytes=raw,matrix=matrix,
                                    source_sha256=SOURCE)

    def test_offline_cli_yields_gap_inventory_not_academic_pass(self):
        raw,matrix = packet()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/"candidate.json").write_bytes(raw)
            (root/"matrix.json").write_text(json.dumps(matrix),encoding="utf-8")
            output=io.StringIO()
            with redirect_stdout(output):
                status=academic_cli([
                    "--package",str(root/"candidate.json"),
                    "--matrix",str(root/"matrix.json"),
                    "--source-sha256",SOURCE,
                ])
        self.assertEqual(0,status)
        body=json.loads(output.getvalue())
        self.assertEqual("REVIEW_REQUIRED",body["academicQA"])
        self.assertFalse(body["publicationAuthorized"])
        self.assertNotIn("Synthetic", output.getvalue())

    def test_offline_cli_rejects_bogus_provenance_without_dumping_files(self):
        raw,matrix=packet()
        matrix["sourceSha256"] = "x" * 64
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"candidate.json").write_bytes(raw)
            (root/"matrix.json").write_text(json.dumps(matrix),encoding="utf-8")
            output=io.StringIO()
            with redirect_stdout(output):
                status=academic_cli([
                    "--package",str(root/"candidate.json"),
                    "--matrix",str(root/"matrix.json"),
                    "--source-sha256",SOURCE,
                ])
        self.assertEqual(2,status)
        self.assertEqual("INVALID_OR_UNVERIFIED_ACADEMIC_EVIDENCE",
                         json.loads(output.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
