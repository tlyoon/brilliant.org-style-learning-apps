"""Private preview needs all original-source evidence but cannot claim approval."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.runtime.private_release_candidate import stage_private_candidate
from tests import test_academic_batch_gap_plan as batch_fixture


class PrivateReleaseStagingTests(unittest.TestCase):
    def setUp(self):
        self.fixture=batch_fixture.BatchPlanTests("test_all_activities_reconciled_with_pilot_first")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        private=tempfile.TemporaryDirectory()
        self.addCleanup(private.cleanup)
        self.out=Path(private.name)/"preview"
        self.repo=Path(__file__).resolve().parents[1]

    def stage(self):
        f=self.fixture
        return stage_private_candidate(
            repo_root=self.repo,package_file=f.pkg,source_pdf=f.pdf,
            matrix_file=f.m,physics_file=f.p,out_dir=self.out,
            expected_package_sha256=sha256(f.pkg.read_bytes()).hexdigest(),
            expected_source_sha256=sha256(f.pdf.read_bytes()).hexdigest(),
            expected_count=2,
        )

    def test_private_preview_is_reproducible_and_unapproved(self):
        result=self.stage()
        self.assertEqual("PRIVATE_PREVIEW_STAGED",result["status"])
        self.assertFalse(result["publicationAuthorized"])
        self.assertEqual(0,result["fullAcademicPassCount"])
        manifest=json.loads((self.out/"private-manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["originalPdfIncluded"])
        self.assertFalse(manifest["publicationAuthorized"])
        self.assertEqual(2,manifest["independentSemanticAndVisualReviewPending"])
        self.assertIn('data-package-url="package.json"',
                      (self.out/"index.html").read_text(encoding="utf-8"))
        self.assertEqual(self.fixture.pkg.read_bytes(),(self.out/"package.json").read_bytes())
        self.assertFalse((self.out/"source.pdf").exists())
        for name,digest in manifest["filesSha256"].items():
            self.assertEqual(digest,sha256((self.out/name).read_bytes()).hexdigest())
        self.assertIn("NOT A PUBLISHABLE",
            (self.out/"PRIVATE-NOT-APPROVED.txt").read_text(encoding="utf-8"))

    def test_no_overwrite_on_repeated_attempt(self):
        self.stage()
        with self.assertRaisesRegex(ValueError,"new"):
            self.stage()

    def test_tampered_package_or_source_hash_blocks_before_staging(self):
        f=self.fixture
        f.pkg.write_bytes(f.pkg.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"stale or mismatched"):
            self.stage()
        self.assertFalse(self.out.exists())

    def test_false_academic_status_blocks_preview(self):
        f=self.fixture
        f.matrix["activities"][0]["academicQA"]="PASS"
        f.matrix["counts"]={"PASS":1,"FAIL":0,"REVIEW_REQUIRED":1}
        f.flush()
        with self.assertRaises(ValueError):
            self.stage()
        self.assertFalse(self.out.exists())

    def test_git_checkout_destination_never_allowed(self):
        self.out=self.repo/"test-private-preview-never-create"
        self.assertFalse(self.out.exists())
        with self.assertRaisesRegex(ValueError,"outside Git"):
            self.stage()
        self.assertFalse(self.out.exists())


if __name__=="__main__":
    unittest.main()