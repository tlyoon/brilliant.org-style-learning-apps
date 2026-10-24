import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch
from app_generator.validation.page_candidates import words, propose_pages, audit_page_candidates

class PageCandidateTests(unittest.TestCase):
    def test_topic_pages_have_deterministic_rank_but_never_qapass(self):
        pages=(
            "The ballistic pendulum embeds a projectile in a block, and the combined body rises to a greater height.",
            "An elastic transfer between equal masses on a glider track conserves total kinetic energy and momentum.",
            "The contact impulse may be short compared with forces due to friction and gravity."
        )
        prompt={"id":"glider-qa","prompt":{"en":"Why do equal masses on the glider track conserve kinetic energy during an elastic transfer?"}}
        report=propose_pages(pages,prompt)
        self.assertEqual("REVIEW_REQUIRED",report["status"])
        self.assertFalse(report["sourceInterpretationVerified"])
        self.assertEqual(2,report["pageCandidates"][0]["pageIndex"])
        self.assertNotIn("elastic transfer between equal",str(report))
        self.assertEqual(report["pageCandidates"],propose_pages(pages,prompt)["pageCandidates"])

    def test_low_signal_never_invents_source_match(self):
        pages=("The isolated system conserves momentum during the impact.",)
        self.assertEqual([],propose_pages(pages,{"id":"x","prompt":{"en":"Which?"}})["pageCandidates"])
        self.assertTrue(words("elastic pendulum glider track"))

    def test_direct_cli_entrypoints_import_current_checkout_without_editable_install(self):
        import subprocess
        import sys
        repo=Path(__file__).resolve().parents[1]
        for script in ("scripts/audit_source_passages.py","scripts/suggest_source_pages.py"):
            proc=subprocess.run(
                [sys.executable,"-I",str(repo/script),"--help"],
                capture_output=True,text=True,timeout=20,cwd=repo,
            )
            self.assertEqual(0,proc.returncode,(script,proc.stderr))
            self.assertIn("--pdf",proc.stdout)

    def test_hash_and_no_academic_pass(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"fake.pdf"
            path.write_bytes(b"%PDF-1.4 fake fixture")
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            package={"activities":[{"id":"x","prompt":{"en":"Why do gliders have elastic kinetic energy after transfer?"}}]}
            with patch("app_generator.validation.page_candidates.extract_pages",return_value=(
                "Elastic gliders transfer kinetic energy between particles and the total momentum remains unchanged.",
            )):
                report=audit_page_candidates(package,path,digest)
                self.assertEqual(1,report["activitiesExamined"])
                self.assertEqual(0,report["academicallyVerified"])
                self.assertFalse(report["publicationAuthorized"])
                with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                    audit_page_candidates(package,path,"f"*64)

if __name__=="__main__": unittest.main()
