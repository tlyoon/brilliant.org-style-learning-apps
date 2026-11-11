"""Source-free adversarial tests for six-section pilot candidate preflight."""
from __future__ import annotations

from hashlib import sha256
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from scripts.audit_course_pilot_readiness import main as pilot_cli

from app_generator.validation.course_pilot_readiness import (
    assess_pilot_candidates, validate_pilot_scope,
)

REVISION = "a" * 40


def package(section: int) -> dict:
    activities = []
    for kind in ("mcq", "interactive"):
        for difficulty in ("easy", "moderate", "challenging"):
            for n in range(3):
                activities.append({
                    "id": f"{kind}-{difficulty}-{n}",
                    "type": kind,
                    "difficulty": difficulty,
                })
    return {
        "packageId": f"chapter-9-section-9-{section}",
        "chapter": "Chapter 9",
        "subchapter": f"9.{section} Synthetic source-free activity",
        "sourceManifest": f"content/source-manifests/chapter-9-section-9-{section}.json",
        "status": "draft",
        "locales": ["en", "ms", "zh"],
        "activities": activities,
    }


def fixture():
    data = {}
    cases = []
    for section in range(1, 7):
        path = f"content/chapter-9/section-9-{section}/package.json"
        raw = json.dumps(package(section), sort_keys=True).encode("utf-8")
        data[path] = raw
        cases.append({
            "sectionNumber": section,
            "packagePath": path,
            "packageSha256": sha256(raw).hexdigest(),
        })
    return ({
        "scopeId": "sourcefree-pilot-class-synthetic",
        "baselineGitSha": REVISION,
        "chapterNumber": 9,
        "mode": "OFFLINE_EXISTING_PACKAGES_ONLY",
        "cases": cases,
        "modelCallsAllowed": False,
        "pdfReadsAllowed": False,
        "publicationAllowed": False,
    }, data)


class SixSectionPilotTests(unittest.TestCase):
    def test_six_valid_packages_are_candidates_not_approved(self):
        manifest, data = fixture()
        seen = []
        def loader(path):
            seen.append(path)
            return data[path]
        report = assess_pilot_candidates(
            manifest, loader, observed_git_sha=REVISION,
        )
        self.assertEqual(6, report["structuralCandidateCount"])
        self.assertEqual(6, len(seen))
        self.assertEqual(
            "SIX_STRUCTURAL_CANDIDATES_REQUIRE_INDEPENDENT_EVIDENCE",
            report["status"],
        )
        self.assertFalse(report["classroomPilotReady"])
        self.assertFalse(report["publicationAuthorized"])
        self.assertFalse(report["independentAcademicAcceptanceVerified"])
        self.assertFalse(report["instructorSelectionVerified"])
        self.assertFalse(report["courseDiagnosticOrPrerequisiteRoutingEnabled"])
        self.assertEqual(
            [0] * 6,
            [case["declaredVisualPlans"] for case in report["cases"]],
        )
        self.assertTrue(all(
            case["academicQA"] == "REVIEW_REQUIRED"
            and case["visualValueReviewPending"]
            for case in report["cases"]
        ))

    def test_v2_pilot_evidence_does_not_reintroduce_removed_rights_gate(self):
        """Both direct and normal audit CLI paths must honor Decision 0033."""
        manifest, data = fixture()
        report = assess_pilot_candidates(
            manifest, data.__getitem__, observed_git_sha=REVISION,
        )
        for row in report["cases"]:
            self.assertNotIn("independentSourceAndRightsVerified", row)
            self.assertNotIn("sourceAndFigureRights", row)
            self.assertIs(row["independentSourceVerified"], False)
            self.assertIs(row["independentPhysicsAndTrilingualMeaningVerified"], False)
            self.assertIs(row["independentVisualSemanticsVerified"], False)
        self.assertFalse(report["classroomPilotReady"])
        self.assertFalse(report["publicationAuthorized"])

    def test_strict_scope_rejects_bad_counts_paths_and_flags_before_reads(self):
        modifications = [
            lambda m: m["cases"].pop(),
            lambda m: m["cases"].append(m["cases"][0].copy()),
            lambda m: m["cases"][1].update(sectionNumber=1),
            lambda m: m["cases"][1].update(packagePath="content/chapter-9/section-9-1/package.json"),
            lambda m: m["cases"][0].update(packagePath="../../private/package.json"),
            lambda m: m["cases"][0].update(packagePath="C:/tmp/package.json"),
            lambda m: m["cases"][0].update(packagePath="content/chapter-8/section-8-1/package.json"),
            lambda m: m["cases"][0].update(packagePath="content/chapter-9/section-9-01/package.json"),
            lambda m: m["cases"][0].update(packageSha256=m["cases"][1]["packageSha256"]),
            lambda m: m.update(modelCallsAllowed=True),
            lambda m: m.update(pdfReadsAllowed=True),
            lambda m: m.update(publicationAllowed=True),
            lambda m: m.update(mode="RUN_PDF_AND_MODEL"),
            lambda m: m.update(chapterNumber=True),
            lambda m: m.update(scopeId="fake"),
            lambda m: m.update(unrecognized=123),
        ]
        for change in modifications:
            manifest, _ = fixture()
            change(manifest)
            with self.subTest(change=change.__code__.co_firstlineno):
                with self.assertRaises(ValueError):
                    assess_pilot_candidates(
                        manifest,
                        lambda path: self.fail("must reject before package read"),
                        observed_git_sha=REVISION,
                    )

    def test_revision_mismatch_never_loads_candidate(self):
        manifest, _ = fixture()
        with self.assertRaisesRegex(ValueError, "FROZEN_GIT_REVISION_MISMATCH"):
            assess_pilot_candidates(
                manifest,
                lambda path: self.fail("no reads on mismatched revision"),
                observed_git_sha="b" * 40,
            )

    def test_package_hash_swap_does_not_pass(self):
        manifest, data = fixture()
        a, b = manifest["cases"][:2]
        data[a["packagePath"]] = data[b["packagePath"]]
        report = assess_pilot_candidates(
            manifest, data.__getitem__, observed_git_sha=REVISION,
        )
        self.assertEqual("STOP_INVALID_OR_INCOMPLETE_CANDIDATES", report["status"])
        self.assertEqual(5, report["structuralCandidateCount"])
        self.assertEqual("INVALID_PACKAGE_EVIDENCE", report["cases"][0]["status"])

    def test_roster_mismatch_fails_even_with_valid_sha(self):
        manifest, data = fixture()
        path = manifest["cases"][2]["packagePath"]
        bad = package(3)
        bad["activities"][0]["type"] = "interactive"
        raw = json.dumps(bad, sort_keys=True).encode("utf-8")
        data[path] = raw
        manifest["cases"][2]["packageSha256"] = sha256(raw).hexdigest()
        report = assess_pilot_candidates(
            manifest, data.__getitem__, observed_git_sha=REVISION,
        )
        self.assertEqual("INVALID_STAGE0_ROSTER", report["cases"][2]["status"])
        self.assertFalse(report["classroomPilotReady"])

    def test_declared_locales_not_trilingual_meaning(self):
        manifest, data = fixture()
        path = manifest["cases"][0]["packagePath"]
        bad = package(1)
        bad["locales"] = ["en", "ms"]
        raw = json.dumps(bad).encode("utf-8")
        data[path] = raw
        manifest["cases"][0]["packageSha256"] = sha256(raw).hexdigest()
        report = assess_pilot_candidates(
            manifest, data.__getitem__, observed_git_sha=REVISION,
        )
        self.assertEqual("INVALID_PACKAGE_EVIDENCE", report["cases"][0]["status"])
        self.assertFalse(report["independentAcademicAcceptanceVerified"])

    def test_package_identity_and_source_reference_must_match_section(self):
        for field, value in (
            ("packageId", "chapter-9-section-9-4"),
            ("subchapter", "9.10 wrong topic"),
            ("sourceManifest", "content/source-manifests/chapter-9-section-9-2.json"),
            ("status", "released"),
        ):
            manifest, data = fixture()
            path = manifest["cases"][0]["packagePath"]
            bad = package(1)
            bad[field] = value
            raw = json.dumps(bad).encode("utf-8")
            data[path] = raw
            manifest["cases"][0]["packageSha256"] = sha256(raw).hexdigest()
            with self.subTest(field=field):
                result = assess_pilot_candidates(
                    manifest, data.__getitem__, observed_git_sha=REVISION,
                )
                self.assertEqual("INVALID_PACKAGE_EVIDENCE", result["cases"][0]["status"])

    def test_declared_visual_plans_are_not_independent_visual_proof(self):
        manifest, data = fixture()
        for case in manifest["cases"]:
            path = case["packagePath"]
            section = case["sectionNumber"]
            item = package(section)
            for activity in item["activities"]:
                activity["visualPlan"] = {"selectedMode": "none"}
            raw = json.dumps(item).encode("utf-8")
            data[path] = raw
            case["packageSha256"] = sha256(raw).hexdigest()
        report = assess_pilot_candidates(
            manifest, data.__getitem__, observed_git_sha=REVISION,
        )
        self.assertTrue(all(
            row["declaredVisualPlans"] == 18
            and row["allVisualPlansDeclared"]
            and row["visualValueReviewPending"]
            and not row["independentVisualSemanticsVerified"]
            for row in report["cases"]
        ))
        self.assertFalse(report["classroomPilotReady"])
        self.assertFalse(report["publicationAuthorized"])

    def test_non_dict_and_invalid_input_rejected(self):
        manifest, _ = fixture()
        for bad in (None, [], 2, {}, {"cases": []}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    validate_pilot_scope(bad)


    def test_cli_reads_six_existing_files_with_exact_revision(self):
        manifest, data = fixture()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for relative, raw in data.items():
                target = root.joinpath(*relative.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            manifest_path = root / "scope.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = pilot_cli([
                    "--manifest", str(manifest_path),
                    "--repo-root", str(root),
                    "--observed-git-sha", REVISION,
                ])
            self.assertEqual(0, exit_code)
            result = json.loads(stdout.getvalue())
            self.assertEqual(6, result["structuralCandidateCount"])
            self.assertFalse(result["classroomPilotReady"])
            for row in result["cases"]:
                self.assertNotIn("independentSourceAndRightsVerified", row)
                self.assertIs(row["independentSourceVerified"], False)

    def test_cli_rejects_absent_package_and_wrong_revision(self):
        manifest, data = fixture()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for relative, raw in data.items():
                target = root.joinpath(*relative.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            manifest_path = root / "scope.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with redirect_stdout(StringIO()) as stdout:
                result = pilot_cli([
                    "--manifest", str(manifest_path),
                    "--repo-root", str(root),
                    "--observed-git-sha", "b" * 40,
                ])
            self.assertEqual(2, result)
            self.assertNotIn("Traceback", stdout.getvalue())
            first = manifest["cases"][0]["packagePath"]
            root.joinpath(*first.split("/")).unlink()
            with redirect_stdout(StringIO()) as stdout:
                result = pilot_cli([
                    "--manifest", str(manifest_path),
                    "--repo-root", str(root),
                    "--observed-git-sha", REVISION,
                ])
            self.assertEqual(1, result)
            self.assertIn("STOP_INVALID_OR_INCOMPLETE_CANDIDATES", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
