"""Source-free multi-package V3 readiness tests with entirely synthetic data."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app_generator.validation.v3_course_readiness import course_readiness
from tests.test_autonomous_completion_v3 import FakeModel, sessions
from app_generator.validation.autonomous_completion import assess_with_models


def write_course(root: Path, count=6):
    chapter=root/"content"/"chapter-demo"
    for i in range(1,count+1):
        section=chapter/f"section-{i}"
        section.mkdir(parents=True)
        data={"packageId":f"synthetic-{i}","activities":[{
            "id":f"synthetic-{i}-a","type":"mcq",
            "prompt":{"en":"Question","ms":"Soalan","zh":"问题"},
            "answerKey":{"correct":"a"}
        }]}
        (section/"package.json").write_text(json.dumps(data),encoding="utf-8")
    return chapter


class V3CourseReadinessTests(unittest.TestCase):
    def test_six_sourcefree_structural_packages_have_zero_model_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            chapter=write_course(root)
            result=course_readiness(chapter,root)
            self.assertEqual((6,6,0),(
                result["sectionsTotal"],result["activitiesTotal"],
                result["activitiesFullyModelReviewed"]))
            self.assertEqual(0,result["modelConsensusPassActivities"])
            self.assertEqual("PENDING_AUTOMATED_ASSESSMENT",
                             result["currentTechnicalDisposition"])
            self.assertFalse(result["publicationAuthorized"])
            self.assertEqual(6,len(result["sectionProgress"]))
            self.assertEqual([],list(root.rglob("v3-assessment-*.json")))

    def test_private_durable_evidence_is_read_without_mutation_or_model_call(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"repo"
            chapter=write_course(root)
            private=Path(d)/"private"
            pack=(chapter/"section-1"/"package.json").read_bytes()
            result=assess_with_models(
                pack,sessions(FakeModel(),FakeModel()),
                generated_content_transfer_allowed=True)
            digest=result["packageSha256"]
            state=private/f"v3-generated-{digest}"/"batches"
            state.mkdir(parents=True)
            stage=state/f"v3-assessment-{digest}.json"
            stage.write_text(json.dumps(result),encoding="utf-8")
            before=stage.read_bytes()
            report=course_readiness(chapter,root,private_root=private)
            self.assertEqual(1,report["activitiesFullyModelReviewed"])
            self.assertEqual(1,report["modelConsensusPassActivities"])
            self.assertEqual(6,report["activitiesTotal"])
            self.assertFalse(report["publicationAuthorized"])
            self.assertEqual(before,stage.read_bytes())

    def test_corrupted_private_evidence_must_not_be_silently_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"repo"
            chapter=write_course(root)
            private=Path(d)/"private"
            from app_generator.validation.autonomous_completion import package_identity
            digest,_=package_identity(
                (chapter/"section-1"/"package.json").read_bytes())
            stage=private/f"v3-generated-{digest}"/"batches"
            stage.mkdir(parents=True)
            (stage/f"v3-assessment-{digest}.json").write_text(
                '{"wrong":true}',encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"V3_"):
                course_readiness(chapter,root,private_root=private)

    def test_missing_duplicate_or_unsafe_six_section_roster_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"repo"
            chapter=write_course(root,count=5)
            with self.assertRaisesRegex(ValueError,"V3_"):
                course_readiness(chapter,root)
            extra=chapter/"section-6"
            extra.mkdir()
            (extra/"package.json").write_bytes(
                (chapter/"section-1"/"package.json").read_bytes())
            with self.assertRaisesRegex(ValueError,"V3_"):
                course_readiness(chapter,root)
            with self.assertRaisesRegex(ValueError,"V3_"):
                course_readiness(chapter,root,
                    private_root=root/"content"/"private-state")

    def test_normal_cli_recovers_frozen_scope_and_rejects_replacement_sections(self):
        repo=Path(__file__).resolve().parents[1]
        def run(*args):
            return subprocess.run(
                [sys.executable,
                 str(repo/"scripts"/"check_final_acceptance_closure.py"),
                 "--course-dir","content/chapter-9",*args],
                cwd=repo,capture_output=True,text=True,timeout=20)
        recovered=run()
        self.assertEqual(0,recovered.returncode,recovered.stderr)
        automatic=json.loads(recovered.stdout)
        self.assertEqual((6,108,0),(
            automatic["sectionsTotal"],automatic["activitiesTotal"],
            automatic["activitiesFullyModelReviewed"]))
        self.assertEqual("FROZEN_CANDIDATE_MANIFEST",automatic["scopeSource"])
        self.assertFalse(automatic["publicationAuthorized"])
        alternate=run("--sections","4,5,6,7,8,9")
        self.assertEqual(2,alternate.returncode)
        self.assertFalse(json.loads(alternate.stdout)["publicationAuthorized"])
        valid=run("--sections","1,2,3,4,5,6")
        self.assertEqual(0,valid.returncode,valid.stderr)
        status=json.loads(valid.stdout)
        self.assertEqual((6,108,0),(
            status["sectionsTotal"],status["activitiesTotal"],
            status["activitiesFullyModelReviewed"]))
        self.assertFalse(status["publicationAuthorized"])
        invalid=run("--sections","1,2,3,4,5,5")
        self.assertEqual(2,invalid.returncode)
        self.assertFalse(json.loads(invalid.stdout)["publicationAuthorized"])

    def test_other_chapter_automatically_resolves_frozen_manifest_and_rejects_drift(self):
        # Synthetic chapter 7 has nine tracked packages but six approved
        # candidates: proof that the resolver is not special-cased to 9.1.
        from hashlib import sha256
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source=write_course(root,count=9)
            chapter=source.rename(source.parent/"chapter-7")
            candidates=[]
            for number in range(1,10):
                folder=chapter/f"section-{number}"
                renamed=folder.rename(chapter/f"section-7-{number}")
                if number <= 6:
                    raw=(renamed/"package.json").read_bytes()
                    candidates.append({"section":f"7.{number}",
                                       "packageSha256":sha256(raw).hexdigest(),
                                       "activityCount":1})
            docs=root/"docs"
            docs.mkdir()
            archive=docs/"acceptance_closure_chapter7.json"
            archive.write_text(json.dumps({
                "project":"BOSLA",
                "contract":"FINAL_ACCEPTANCE_NO_REPEAT_V2",
                "policy":{"frozen":True},
                "frozenCandidates":candidates,
            }),encoding="utf-8")
            result=course_readiness(chapter,root)
            self.assertEqual((6,6),(
                result["sectionsTotal"],result["activitiesTotal"]))
            self.assertEqual("FROZEN_CANDIDATE_MANIFEST",result["scopeSource"])
            self.assertEqual(
                [f"section-7-{i}" for i in range(1,7)],
                [row["section"] for row in result["sectionProgress"]])
            with self.assertRaisesRegex(
                ValueError,"V3_SECTION_OVERRIDE_CONFLICTS_WITH_FROZEN_SCOPE"):
                course_readiness(chapter,root,
                                 section_numbers=(4,5,6,7,8,9))
            with self.assertRaisesRegex(
                ValueError,"V3_INVALID_EXPLICIT_COURSE_SCOPE"):
                course_readiness(chapter,root,
                                 section_numbers=(True,2,3,4,5,6))
            # A renamed folder from a different chapter cannot inherit
            # the same trusted ordinal and digest by accident.
            correct=chapter/"section-7-1"
            wrong=chapter/"section-8-1"
            correct.rename(wrong)
            with self.assertRaisesRegex(
                ValueError,"V3_FROZEN_SECTION_NAME_MISMATCH"):
                course_readiness(chapter,root)
            wrong.rename(correct)
            package=chapter/"section-7-2"/"package.json"
            package.write_bytes(package.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"V3_FROZEN_PACKAGE_IDENTITY_DRIFT"):
                course_readiness(chapter,root)
            # A broken scope manifest must not fall back to scanning all
            # present directory entries and pretending this is a new campaign.
            data=json.loads(archive.read_text(encoding="utf-8"))
            data["frozenCandidates"][0]["packageSha256"]="0"*64
            archive.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"V3_FROZEN_PACKAGE_IDENTITY_DRIFT"):
                course_readiness(chapter,root)

    def test_cross_platform_crlf_frozen_bytes_match_only_exact_lf_git_blob(self):
        # Historical BSA-20261107-127: Yoga 6 CRLF package SHA versus
        # hosted Linux checkout LF of the SAME tracked Git blob.
        from hashlib import sha1, sha256
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            chapter=write_course(root,count=6).rename(
                root/"content"/"chapter-7")
            frozen=[]
            for i in range(1,7):
                folder=(chapter/f"section-{i}").rename(
                    chapter/f"section-7-{i}")
                pkg=folder/"package.json"
                data=json.loads(pkg.read_text(encoding="utf-8"))
                lf=(json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode()
                crlf=lf.replace(b"\n",b"\r\n")
                pkg.write_bytes(lf)  # Simulate GitHub LF checkout.
                frozen.append({
                    "section":f"7.{i}","activityCount":1,
                    "packageSha256":sha256(crlf).hexdigest(),
                    "packageGitBlobSha1":sha1(
                        b"blob "+str(len(lf)).encode()+b"\0"+lf).hexdigest(),
                })
            docs=root/"docs"
            docs.mkdir()
            manifest=docs/"acceptance_closure_chapter7.json"
            archive={"project":"BOSLA",
                     "contract":"FINAL_ACCEPTANCE_NO_REPEAT_V2",
                     "policy":{"frozen":True},
                     "frozenCandidates":frozen}
            manifest.write_text(json.dumps(archive),encoding="utf-8")
            summary=course_readiness(chapter,root)
            self.assertEqual((6,6),(
                summary["sectionsTotal"],summary["activitiesTotal"]))
            self.assertTrue(all(
                row["frozenIdentityBasis"]=="EOL_NORMALIZED_GIT_BLOB"
                for row in summary["sectionProgress"]))
            # Genuine content mutation (not newline normalization) fails.
            p=chapter/"section-7-2"/"package.json"
            original=p.read_bytes()
            p.write_bytes(original.replace(b"Question",b"Altered"))
            with self.assertRaisesRegex(
                ValueError,"V3_FROZEN_PACKAGE_IDENTITY_DRIFT"):
                course_readiness(chapter,root)
            # Restore original and now tamper with frozen Git identity:
            # the matching CRLF SHA cannot rehabilitate a changed blob ID.
            p.write_bytes(original)
            archive["frozenCandidates"][1]["packageGitBlobSha1"]="0"*40
            manifest.write_text(json.dumps(archive),encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError,"V3_FROZEN_PACKAGE_IDENTITY_DRIFT"):
                course_readiness(chapter,root)

    def test_frozen_scope_missing_or_corrupt_fails_closed_not_autocleared(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source=write_course(root,count=9)
            chapter=source.rename(source.parent/"chapter-4")
            docs=root/"docs"
            docs.mkdir()
            scope=docs/"acceptance_closure_chapter4.json"
            # No scope means a nine-section directory is not implicitly six.
            with self.assertRaisesRegex(ValueError,"V3_INCOMPLETE_COURSE_ROSTER"):
                course_readiness(chapter,root)
            scope.write_text('{"project":"BOSLA","frozenCandidates":[]}',
                             encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"V3_INVALID_FROZEN_SCOPE_MANIFEST"):
                course_readiness(chapter,root)

    def test_real_repo_six_packages_are_structure_only_without_side_effects(self):
        repo=Path(__file__).resolve().parents[1]
        chapter=repo/"content"/"chapter-9"
        # Nine tracked sections exist, but the approved frozen roster
        # must be recovered automatically and checked against exact hashes.
        report=course_readiness(chapter,repo)
        self.assertEqual("FROZEN_CANDIDATE_MANIFEST",report["scopeSource"])
        with self.assertRaisesRegex(ValueError,"V3_"):
            course_readiness(chapter,repo,
                section_numbers=(4,5,6,7,8,9))
        self.assertEqual((6,108,0),(
            report["sectionsTotal"],report["activitiesTotal"],
            report["activitiesFullyModelReviewed"]))
        self.assertFalse(report["publicationAuthorized"])


if __name__=="__main__":
    unittest.main()
