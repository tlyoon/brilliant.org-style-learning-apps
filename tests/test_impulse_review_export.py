"""Private candidate export and provenance safety regressions."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.make_impulse_review_candidate import make_candidate

ROOT=Path(__file__).resolve().parents[1]


class ReviewOnlyExportTests(unittest.TestCase):
    def test_cli_uses_owned_checkout_under_python_isolated_mode(self):
        command=[sys.executable,"-I",str(ROOT/"scripts/make_impulse_review_candidate.py"),"--help"]
        run=subprocess.run(command,capture_output=True,text=True,timeout=20,cwd=ROOT)
        self.assertEqual(0,run.returncode,run.stderr)
        self.assertIn("--installed-package",run.stdout)

    def test_byte_exact_sha_refuse_overwrite_and_original_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            installed=root/"installed.json"
            source=root/"source.pdf"
            out=root/"review-copy"
            original={"activities":[{"id":"target","type":"interactive","prompt":{"en":"old"}},
                                     {"id":"other","type":"mcq"}]}
            installed.write_bytes((json.dumps(original,ensure_ascii=False)+"\n").encode("utf-8"))
            source.write_bytes(b"%PDF-1.4 synthetic")
            unchanged=hashlib.sha256(installed.read_bytes()).hexdigest()
            candidate=copy.deepcopy(original)
            candidate["activities"][0]["prompt"]={"en":"new revised text","zh":"\u8fd1\u4f3c\u5b88\u6052"}
            review={"activityId":"target","changedFields":["prompt"],
                    "reviewOnly":True,"answerKeyUnchanged":True}
            with patch("scripts.make_impulse_review_candidate.build_review_candidate",
                       return_value=(candidate,review)):
                result=make_candidate(installed,source,out)
            disk=hashlib.sha256((out/"package.json").read_bytes()).hexdigest()
            meta=json.loads((out/"review.json").read_text(encoding="utf-8"))
            self.assertEqual(disk,meta["candidatePackageFileSha256"])
            self.assertEqual(disk,result["candidateSha256"])
            self.assertEqual(unchanged,hashlib.sha256(installed.read_bytes()).hexdigest())
            self.assertEqual("REVIEW_REQUIRED",meta["academicQA"])
            self.assertFalse(meta["publicationAuthorized"])
            self.assertNotIn(b"\r\n",(out/"package.json").read_bytes())
            with self.assertRaisesRegex(ValueError,"already exists"):
                make_candidate(installed,source,out)

    def test_candidate_must_remain_outside_git_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            installed=root/"package.json"
            pdf=root/"source.pdf"
            installed.write_text("{}",encoding="utf-8")
            pdf.write_bytes(b"%PDF-1.4 synthetic")
            with self.assertRaisesRegex(ValueError,"inside code repository"):
                make_candidate(installed,pdf,ROOT/"review-should-not-be-created")


if __name__=="__main__":
    unittest.main()
