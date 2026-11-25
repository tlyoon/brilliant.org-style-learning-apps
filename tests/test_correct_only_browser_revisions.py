"""Controlled version-specific scientific explanation UI admission tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.audit_private_correct_explanations_browser import (
    audit,V10_SHA,V11_SHA,PDF_SHA,
)

class CorrectOnlyRevisionTests(unittest.TestCase):
    def test_unknown_candidate_revision_fails_before_browser(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            for version in ("v9","v12","",None):
                with self.subTest(version=version):
                    with self.assertRaisesRegex(ValueError,"only controlled"):
                        audit(package_file=p/"unused.json",source_pdf=p/"unused.pdf",
                              packets_file=p/"unused-packets.json",repository=p,
                              candidate_revision=version)

    def test_wrong_source_sha_or_candidate_package_fails_before_browser(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            data=p/"package.json"
            data.write_text(json.dumps({"activities":[]}),encoding="utf-8")
            for package_sha,source_sha,revision in (
               (V10_SHA,PDF_SHA,"v11"),
               (V11_SHA,"0"*64,"v11"),
               (V11_SHA,PDF_SHA,"v10"),
            ):
                with self.subTest(package_sha=package_sha,revision=revision):
                    receipt={"packageSha256":package_sha,"sourceSha256":source_sha,
                             "newlyReverifiedSourceActivities":18,
                             "publicationAuthorized":False}
                    with patch(
                        "scripts.audit_private_correct_explanations_browser.verify_full_source_packet_roster",
                        return_value=receipt,
                    ):
                        with self.assertRaisesRegex(ValueError,"SHA drift"):
                            audit(package_file=data,source_pdf=p/"source.pdf",
                                  packets_file=p/"packets.json",repository=p,
                                  candidate_revision=revision)

if __name__=="__main__":unittest.main()
