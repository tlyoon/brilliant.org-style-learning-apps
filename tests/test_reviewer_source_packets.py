import hashlib
import tempfile
import unittest
from pathlib import Path

from app_generator.validation.reviewer_source_packets import (
    verified_source_packet,source_packets_for_activities,
)

QUOTE="Two objects collide; if the net external impulse is negligible during impact, total momentum is approximately conserved."
class PacketTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pdf=Path(self.tmp.name)/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 tiny private fixture")
        self.sha=hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.pages=(QUOTE+" Additional source content.", "Other unique source physics text.")
        self.anchor={"activityId":"one","pageIndex":1,"quotedText":QUOTE}

    def packet(self,anchors=None,source=None):
        return verified_source_packet(self.pdf,source or self.sha,"one",
              [self.anchor] if anchors is None else anchors,
              extractor=lambda _:self.pages)

    def test_source_verified_private_packet(self):
        report=self.packet()
        self.assertEqual([1],report["verifiedPages"])
        self.assertIn("momentum",report["sourceEvidence"])
        self.assertEqual(1,report["passageCount"])
        self.assertFalse(report["sourceInterpretationVerified"])
        self.assertFalse(report["humanReviewRequired"])

    def test_source_wrong_page_or_version_rejected(self):
        with self.assertRaisesRegex(ValueError,"hash"):
            self.packet(source="0"*64)
        bad=dict(self.anchor,pageIndex=2)
        with self.assertRaisesRegex(ValueError,"page"):
            self.packet([bad])

    def test_unrelated_short_or_duplicate_anchors_rejected(self):
        for altered in (
            [dict(self.anchor,activityId="two")],
            [dict(self.anchor,quotedText="short")],
            [self.anchor,self.anchor],
        ):
            with self.subTest(altered=altered):
                with self.assertRaises(ValueError):
                    self.packet(altered)

    def test_ambiguous_page_quote_no_auto_approval(self):
        with self.assertRaisesRegex(ValueError,"multiple"):
            verified_source_packet(
                self.pdf,self.sha,"one",[self.anchor],
                extractor=lambda _: (QUOTE,QUOTE)
            )

    def test_batch_requires_source_for_every_activity(self):
        package={"activities":[{"id":"one"},{"id":"two"}]}
        with self.assertRaisesRegex(ValueError,"bounded"):
            source_packets_for_activities(
                self.pdf,self.sha,package,[self.anchor],
                extractor=lambda _:self.pages,
            )
        with self.assertRaisesRegex(ValueError,"unknown"):
            source_packets_for_activities(
                self.pdf,self.sha,package,[dict(self.anchor,activityId="wrong")],
                extractor=lambda _:self.pages,
            )
