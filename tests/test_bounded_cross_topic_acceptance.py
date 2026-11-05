"""Source-free cross-topic integration: finite three-case acceptance workflow."""
from __future__ import annotations

from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.academic_qa import REQUIRED
from app_generator.validation.bounded_cross_topic_acceptance import (
    assess_cross_topic_evidence, canonical_digest, validate_cross_topic_manifest,
)
from scripts.run_bounded_cross_topic_acceptance import main as acceptance_cli, _git_head

TOPICS = ("mechanics", "electromagnetism", "thermodynamics")
GIT_HEAD = "1" * 40


def _raw(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")


def make_fixture(learner_complete=True, *, fail_academic=False):
    artifacts = {}
    cases = []
    for index, topic in enumerate(TOPICS, 1):
        case_id = f"fixture-{topic}"
        candidate = {
            "activities": [
                {"id":f"mcq-{index}","type":"mcq","prompt":{
                    "en":"Synthetic question","ms":"Soalan sintetik","zh":"合成题目"}},
                {"id":f"interactive-{index}","type":"interactive","prompt":{
                    "en":"Synthetic interaction","ms":"Interaksi sintetik","zh":"合成交互"}},
            ],
        }
        package_bytes = _raw(candidate)
        package_sha = sha256(package_bytes).hexdigest()
        source_sha = f"{index}" * 64
        learner = {
            "packageSha256":package_sha,
            "publicationAuthorized":False,
            "checks":[]
        }
        if learner_complete or index != 2:
            learner["checks"]=[
                {"activityId":a["id"],"locale":lang,"viewportWidth":width,
                 "rendered":True,"responsive":True,
                 "keyboardOperable":True,"answerInteractionExercised":True}
                for a in candidate["activities"]
                for lang in ("en","ms","zh") for width in (390,1280)
            ]
        rows=[]
        for activity in candidate["activities"]:
            row_hash=sha256(json.dumps(
                activity, sort_keys=True, ensure_ascii=False,
                separators=(",",":")).encode("utf-8")).hexdigest()
            gates={gate:"REVIEW_REQUIRED" for gate in REQUIRED}
            if fail_academic and index == 3:
                gates["physics_consistency"]="FAIL"
            row_status="FAIL" if "FAIL" in gates.values() else "REVIEW_REQUIRED"
            rows.append({
                "activityId":activity["id"],"activitySha256":row_hash,
                "gates":gates,"academicQA":row_status,
                "sourceLocationVerified":False,
                "publicationAuthorized":False,
            })
        counts={state:sum(row["academicQA"]==state for row in rows)
                for state in ("PASS","FAIL","REVIEW_REQUIRED")}
        matrix={
            "packageSha256":package_sha,"sourceSha256":source_sha,
            "activityCount":2, "activities":rows,"counts":counts,
            "academicQA":"FAIL" if counts["FAIL"] else "REVIEW_REQUIRED",
            "publicationAuthorized":False,
        }
        files={
            "package":f"case-{index}/candidate.json",
            "learnerReceipt":f"case-{index}/learner.json",
            "academicMatrix":f"case-{index}/academic.json",
        }
        artifacts[files["package"]]=package_bytes
        artifacts[files["learnerReceipt"]]=_raw(learner)
        artifacts[files["academicMatrix"]]=_raw(matrix)
        cases.append({
            "caseId":case_id, "topicFamily":topic,
            "sourceSha256":source_sha,"packageSha256":package_sha, **files
        })
    manifest={
        "campaignId":"sourcefree-cross-topic-fixtures-20261105",
        "baselineGitSha":GIT_HEAD,
        "mode":"OFFLINE_EXISTING_EVIDENCE_ONLY",
        "maxCases":3,"maxChecksPerCase":1,
        "modelCallsAllowed":False,
        "pdfReadsAllowed":False,
        "publicationAllowed":False,
        "cases":cases,
    }
    return manifest,artifacts


def evaluate(manifest, files):
    calls=[]
    def load(path):
        calls.append(path)
        return files[path]
    report=assess_cross_topic_evidence(manifest,load,observed_git_sha=manifest["baselineGitSha"])
    return report,calls


class BoundedCrossTopicAcceptanceTests(unittest.TestCase):
    def test_three_complete_rosters_still_stop_for_real_independent_proof(self):
        manifest,files=make_fixture()
        report,calls=evaluate(manifest,files)
        self.assertEqual(3,report["caseCount"])
        self.assertEqual(9,len(calls)) # Exactly package + learner + academic per case.
        self.assertEqual(3,report["casesChecked"])
        self.assertTrue(report["stoppingConditionMet"])
        self.assertFalse(report["repeatEvaluationAllowed"])
        self.assertFalse(report["newProviderOrPdfCallsAllowed"])
        self.assertEqual("STOP_INDEPENDENT_VERIFICATION_REQUIRED",report["terminalDisposition"])
        self.assertEqual(3,report["counts"]["METADATA_COMPLETE_PROOF_UNVERIFIED"])
        self.assertFalse(report["interactiveLearnerAcceptanceGranted"])
        self.assertFalse(report["academicAcceptanceGranted"])
        self.assertFalse(report["publicationAuthorized"])
        self.assertEqual(sorted(TOPICS),report["topicFamilies"])

    def test_missing_learner_evidence_does_not_silently_pass(self):
        manifest,files=make_fixture(learner_complete=False)
        report,calls=evaluate(manifest,files)
        self.assertEqual(9,len(calls))
        self.assertEqual(1,report["counts"]["MISSING_LEARNER_OBSERVATIONS"])
        self.assertEqual("STOP_INCOMPLETE_OR_INVALID_EVIDENCE",report["terminalDisposition"])
        self.assertEqual("MISSING_LEARNER_OBSERVATIONS",report["caseResults"][1]["status"])

    def test_deterministic_defect_stops_without_retry(self):
        manifest,files=make_fixture(fail_academic=True)
        report,calls=evaluate(manifest,files)
        self.assertEqual(9,len(calls))
        self.assertEqual("STOP_REPORTED_DEFECTS",report["terminalDisposition"])
        self.assertEqual("REPORTED_DETERMINISTIC_DEFECTS",report["caseResults"][2]["status"])
        self.assertTrue(report["stoppingConditionMet"])

    def test_tampered_academic_matrix_fails_only_one_case_and_never_leaks_text(self):
        manifest,files=make_fixture()
        name=manifest["cases"][1]["academicMatrix"]
        matrix=json.loads(files[name])
        matrix["activities"][0]["activitySha256"]="f"*64
        matrix["secretPrompts"]="dont-print-this-secret"
        files[name]=_raw(matrix)
        report,calls=evaluate(manifest,files)
        self.assertEqual(9,len(calls))
        self.assertEqual(1,report["counts"]["INVALID_EVIDENCE"])
        self.assertEqual("INVALID_EVIDENCE",report["caseResults"][1]["status"])
        self.assertEqual("STOP_INCOMPLETE_OR_INVALID_EVIDENCE",report["terminalDisposition"])
        self.assertNotIn("dont-print-this-secret",json.dumps(report))

    def test_transient_missing_artifact_is_terminal_case_error_not_a_retry(self):
        manifest,files=make_fixture()
        reads=[]
        missing=manifest["cases"][0]["learnerReceipt"]
        def load(name):
            reads.append(name)
            if name == missing:
                raise OSError("source-containing-private-exception")
            return files[name]
        report=assess_cross_topic_evidence(
            manifest,load,observed_git_sha=manifest["baselineGitSha"])
        self.assertEqual("INVALID_EVIDENCE",report["caseResults"][0]["status"])
        self.assertEqual(1,reads.count(missing))
        self.assertEqual(3,report["casesChecked"])
        self.assertEqual("STOP_INCOMPLETE_OR_INVALID_EVIDENCE",report["terminalDisposition"])
        self.assertNotIn("source-containing-private-exception",json.dumps(report))

    def test_hash_mismatch_is_not_a_reported_acceptance(self):
        manifest,files=make_fixture()
        name=manifest["cases"][0]["package"]
        files[name]+=b" "
        report,calls=evaluate(manifest,files)
        self.assertEqual("INVALID_EVIDENCE",report["caseResults"][0]["status"])
        self.assertEqual(7,len(calls)) # Bad package: no learner/matrix load.

    def test_manifest_rejects_duplicate_topics_or_old_campaign(self):
        manifest,files=make_fixture()
        manifest["cases"][2]["topicFamily"]="mechanics"
        with self.assertRaises(ValueError):
            validate_cross_topic_manifest(manifest)
        manifest,_=make_fixture()
        manifest["campaignId"]="sourcefree-c3-round2-20261104"
        with self.assertRaises(ValueError):
            validate_cross_topic_manifest(manifest)

    def test_requires_exact_three_cases_one_check_each_and_no_provider(self):
        for mutation in (
            lambda m: m["cases"].pop(),
            lambda m: m.update(maxCases=4),
            lambda m: m.update(maxChecksPerCase=2),
            lambda m: m.update(modelCallsAllowed=True),
            lambda m: m.update(pdfReadsAllowed=True),
            lambda m: m.update(publicationAllowed=True),
            lambda m: m.update(mode="GENERATE_NEW_PDFS"),
        ):
            manifest,_=make_fixture()
            mutation(manifest)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                validate_cross_topic_manifest(manifest)

    def test_rejects_traversal_windows_paths_and_unbound_revision(self):
        for value in ("../source.pdf", "C:/private.json", "/etc/data.json",
                      "case-1/../source.json", "case-1\\other.json"):
            manifest,files=make_fixture()
            manifest["cases"][0]["package"]=value
            with self.subTest(value=value),self.assertRaises(ValueError):
                validate_cross_topic_manifest(manifest)
        manifest,files=make_fixture()
        with self.assertRaisesRegex(ValueError,"frozen"):
            assess_cross_topic_evidence(manifest,files.__getitem__,
                                         observed_git_sha="e"*40)

    def test_mutated_manifest_changes_deterministic_hash(self):
        manifest,_=make_fixture()
        digest=canonical_digest(manifest)
        manifest["cases"][0]["topicFamily"]="modern-physics"
        self.assertNotEqual(digest,canonical_digest(manifest))

    def test_one_shot_cli_refuses_to_overwrite_completed_report(self):
        manifest,files=make_fixture()
        manifest["baselineGitSha"]=_git_head()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            inputs=root/"inputs"
            outputs=root/"outputs"
            inputs.mkdir()
            outputs.mkdir()
            for name,data in files.items():
                target=inputs/name
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(data)
            manifest_path=inputs/"manifest.json"
            manifest_path.write_bytes(_raw(manifest))
            stdout=io.StringIO()
            args=["--manifest",str(manifest_path),
                  "--input-root",str(inputs),
                  "--output-root",str(outputs)]
            with redirect_stdout(stdout):
                first=acceptance_cli(args)
            self.assertEqual(0,first)
            result=json.loads(stdout.getvalue())
            self.assertEqual("STOP_INDEPENDENT_VERIFICATION_REQUIRED",
                             result["terminalDisposition"])
            folders=list(outputs.iterdir())
            self.assertEqual(1,len(folders))
            report=json.loads((folders[0]/"disposition.json").read_text(encoding="utf-8"))
            self.assertEqual(3,report["casesChecked"])
            stdout=io.StringIO()
            with redirect_stdout(stdout):
                second=acceptance_cli(args)
            self.assertEqual(2,second)
            self.assertEqual("REJECTED_SOURCE_FREE_ACCEPTANCE_RUN",
                             json.loads(stdout.getvalue())["status"])

    def test_cli_denies_mismatched_git_sha_without_new_run_folder(self):
        manifest,files=make_fixture()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            inputs=root/"inputs"; outputs=root/"outputs"
            inputs.mkdir();outputs.mkdir()
            manifest_path=inputs/"manifest.json"
            manifest_path.write_bytes(_raw(manifest))
            stdout=io.StringIO()
            with redirect_stdout(stdout):
                status=acceptance_cli([
                    "--manifest",str(manifest_path),
                    "--input-root",str(inputs),
                    "--output-root",str(outputs)])
            self.assertEqual(2,status)
            self.assertEqual([],list(outputs.iterdir()))
            self.assertFalse(json.loads(stdout.getvalue())["publicationAuthorized"])

    def test_cli_rejects_symlinked_artifact_when_supported(self):
        manifest,files=make_fixture()
        manifest["baselineGitSha"]=_git_head()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            inputs=root/"inputs";outputs=root/"outputs"
            inputs.mkdir();outputs.mkdir()
            for name,data in files.items():
                target=inputs/name
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(data)
            bad=inputs/manifest["cases"][0]["package"]
            manifest_path=inputs/"manifest.json"
            manifest_path.write_bytes(_raw(manifest))
            original=Path.is_symlink
            def pretend_link(path):
                return str(path) == str(bad) or original(path)
            output=io.StringIO()
            # Cross-platform: simulate a link without requiring Windows
            # developer-mode symlink privilege or modifying live files.
            with patch.object(Path,"is_symlink",pretend_link):
                with redirect_stdout(output):
                    status=acceptance_cli([
                        "--manifest",str(manifest_path),
                        "--input-root",str(inputs),
                        "--output-root",str(outputs)])
            self.assertEqual(2,status)
            folders=list(outputs.iterdir())
            self.assertEqual(1,len(folders))
            report=json.loads((folders[0]/"disposition.json").read_text())
            self.assertEqual("INVALID_EVIDENCE",report["caseResults"][0]["status"])


if __name__ == "__main__":
    unittest.main()
