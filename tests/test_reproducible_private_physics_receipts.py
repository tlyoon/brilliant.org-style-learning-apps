"""Source-free tests for reproducible, private Section 9.4 proof receipts."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.physics_proofs import KNOWN_CASES
from app_generator.validation.physics_receipt_generation import (
    WITNESSES, generate_bounded_physics_receipts,
)


class PrivatePhysicsReceiptTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.pdf=self.root/"source.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 private unit fixture")
        self.package=self.root/"package.json"
        acts=[{"id":aid,"answerKey":{"correct":answer}}
              for aid,(_,answer) in KNOWN_CASES.items()]
        acts.extend({"id":"other-"+str(i),"type":"selection"} for i in range(9))
        self.package.write_text(json.dumps({"activities":acts}),encoding="utf-8")
        self.packets=self.root/"packets.json"
        evidence="verified content snippet used for deterministic testing"
        hash_text=sha256(evidence.encode()).hexdigest()
        packet={a["id"]:{
            "sourceAnchors":[{"activityId":a["id"],"pageIndex":1,"quotedText":evidence}],
            "sourceEvidence":evidence,"passageSha256":hash_text,"verifiedPages":[1]}
            for a in acts}
        self.data={"packageSha256":sha256(self.package.read_bytes()).hexdigest(),
            "sourceSha256":sha256(self.pdf.read_bytes()).hexdigest(),
            "packets":packet}
        self.packets.write_text(json.dumps(self.data),encoding="utf-8")

    def _verified(self, source, digest, aid, anchors):
        return self.data["packets"][aid]

    def _audit(self, package, pdf, digest, receipts):
        return {"boundedPropositionsVerified":len(receipts["proofs"]),
                "failedWitnesses":0,"unresolvedReceipts":0,
                "academicActivitiesPassed":0,"publicationAuthorized":False}

    def _run(self):
        with patch("app_generator.validation.physics_receipt_generation.verified_source_packet",
                   side_effect=self._verified), \
             patch("app_generator.validation.physics_receipt_generation.audit_proofs",
                   side_effect=self._audit):
            return generate_bounded_physics_receipts(self.package,self.pdf,self.packets)

    def test_builds_all_nine_exact_stable_source_bound_proof_inputs(self):
        receipt,report=self._run()
        self.assertEqual(9,report["boundedPropositionsVerified"])
        self.assertEqual(set(WITNESSES),set(x["activityId"] for x in receipt["proofs"]))
        self.assertEqual(self.data["sourceSha256"],receipt["sourceSha256"])
        self.assertEqual(0,report["academicActivitiesPassed"])
        self.assertFalse(report["publicationAuthorized"])

    def test_modified_pdf_fails_closed_before_source_or_model_review(self):
        self.pdf.write_bytes(b"%PDF-1.4 tampered fixture")
        with self.assertRaisesRegex(ValueError,"identity"):
            self._run()

    def test_modified_package_fails_closed(self):
        self.package.write_text(self.package.read_text()+" ",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"identity"):
            self._run()

    def test_wrong_key_in_package_is_not_accepted_even_if_packet_hash_updated(self):
        doc=json.loads(self.package.read_text())
        doc["activities"][0]["answerKey"]["correct"]="false-key"
        self.package.write_text(json.dumps(doc),encoding="utf-8")
        self.data["packageSha256"]=sha256(self.package.read_bytes()).hexdigest()
        self.packets.write_text(json.dumps(self.data),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"answer key"):
            self._run()

    def test_source_passage_mismatch_cannot_be_a_verified_proof(self):
        def bogus(*args):
            return {"sourceEvidence":"unrelated",
                    "passageSha256":"0"*64,"verifiedPages":[1]}
        with patch("app_generator.validation.physics_receipt_generation.verified_source_packet",
                   side_effect=bogus):
            with self.assertRaisesRegex(ValueError,"reverify"):
                generate_bounded_physics_receipts(self.package,self.pdf,self.packets)

    def test_reviewer_contract_cannot_be_claimed_from_bounded_proof(self):
        with patch("app_generator.validation.physics_receipt_generation.verified_source_packet",
                   side_effect=self._verified), \
             patch("app_generator.validation.physics_receipt_generation.audit_proofs",
                   return_value={"boundedPropositionsVerified":9,"failedWitnesses":0,
                                 "unresolvedReceipts":0,"academicActivitiesPassed":1,
                                 "publicationAuthorized":True}):
            with self.assertRaisesRegex(ValueError,"bounded"):
                generate_bounded_physics_receipts(self.package,self.pdf,self.packets)


if __name__=="__main__":
    unittest.main()
