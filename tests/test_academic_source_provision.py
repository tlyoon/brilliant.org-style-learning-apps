"""Fail-closed automatic source evidence provisioning tests, no paid AI."""
import hashlib
import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from app_generator.runtime.academic_source_provision import (
    REGISTRY_DIR,provision_run_source_packets,
)
from app_generator.runtime.academic_generation_stage import run_academic_stage
from app_generator.runtime.run_context import RunContext

@dataclass
class Config:
    state_dir:Path
    repo_root:Path
    chrome_profile_dir:Path
    llm_backend:str="gemini_browser"
    browser_mode:str="controlled"

class AutomaticSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/"source.pdf"
        self.source.write_bytes(b"%PDF-1.4 synthetic textbook private fixture")
        self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.pkg=self.root/"package.json"
        self.pkg.write_bytes(json.dumps({"activities":[
            {"id":"first","type":"mcq"},{"id":"second","type":"interactive"}
        ]}).encode("utf-8"))
        self.pkgsha=hashlib.sha256(self.pkg.read_bytes()).hexdigest()
        self.repo=self.root/"repo"
        self.repo.mkdir()
        self.config=Config(self.root/"state",self.repo,self.root/"chrome")
        self.config.state_dir.mkdir()
        self.context=RunContext.create(self.root/"private-run")
        self.prior=self.root/"prior.json"
        self.prior.write_text(self.pkg.read_text(encoding="utf-8"),encoding="utf-8")
        self.receipts=[self.root/"r1.json",self.root/"r2.json"]
        for p in self.receipts:p.write_text("{}",encoding="utf-8")
        self.registry=self.config.state_dir/REGISTRY_DIR/f"{self.sha}.json"
        self.registry.parent.mkdir()
        self.registry.write_text(json.dumps({
            "version":1,"sourceSha256":self.sha,
            "priorPackage":str(self.prior.resolve()),
            "proofReceipts":[str(p.resolve()) for p in self.receipts],
        }),encoding="utf-8")
        self.anchor={
            "activityId":"first","sourceSha256":self.sha,
            "sourceEvidence":"Private source passage with enough detailed original textbook words to review.",
            "sourceAnchors":[{"activityId":"first","pageIndex":1,"quotedText":
                "A physically meaningful textbook passage with sufficient original words."}],
            "verifiedPages":[1],"passageSha256":["a"*64],
        }
    def fake_migration(self):
        return {
            "packageSha256":self.pkgsha,"sourceSha256":self.sha,
            "packets":{"first":self.anchor,"second":{**self.anchor,
                "activityId":"second","sourceAnchors":[{
                "activityId":"second","pageIndex":1,"quotedText":
                    "A physically meaningful textbook passage with sufficient original words."
            }]}},
            "activityCount":2,"verifiedSourceLocations":2,
            "changedActivityIds":[],"sourceInterpretationVerified":False,
            "academicQA":"REVIEW_REQUIRED","publicationAuthorized":False,
        }
    def test_missing_private_registry_is_nonblocking(self):
        self.registry.unlink()
        report=provision_run_source_packets(
            self.config,self.context,self.pkg,self.source)
        self.assertEqual("NO_PRIVATE_PROVENANCE_REGISTRY",report["status"])
        self.assertFalse((self.context.validation/"academic-review-source-packets.json").exists())
    def test_registry_migration_and_existing_packet_immutability(self):
        with patch("app_generator.runtime.academic_source_provision.migrate_anchor_packets",
                   return_value=self.fake_migration()) as migration:
            result=provision_run_source_packets(self.config,self.context,self.pkg,self.source)
            self.assertEqual(2,result["verifiedSourceLocations"])
            self.assertEqual(1,migration.call_count)
            path=self.context.validation/"academic-review-source-packets.json"
            original=path.read_bytes()
            again=provision_run_source_packets(self.config,self.context,self.pkg,self.source)
            self.assertEqual("RUN_PACKET_EXISTS_RECHECK_IN_STAGE",again["status"])
            self.assertEqual(original,path.read_bytes())
            self.assertFalse(result["publicationAuthorized"])
    def test_source_or_registry_tampering_blocks_without_model(self):
        self.source.write_bytes(b"%PDF-1.4 altered original")
        report=provision_run_source_packets(self.config,self.context,self.pkg,self.source)
        self.assertEqual("NO_PRIVATE_PROVENANCE_REGISTRY",report["status"])
        with self.assertRaisesRegex(ValueError,"differs"):
            provision_run_source_packets(self.config,self.context,self.pkg,self.source,
                                         registry_file=self.registry)
        self.source.write_bytes(b"%PDF-1.4 synthetic textbook private fixture")
        x=json.loads(self.registry.read_text())
        x["proofReceipts"]=[str(self.receipts[0])]*2
        self.registry.write_text(json.dumps(x))
        with self.assertRaisesRegex(ValueError,"distinct"):
            provision_run_source_packets(self.config,self.context,self.pkg,self.source)
    def test_external_proofs_cannot_be_read_from_public_checkout(self):
        x=json.loads(self.registry.read_text())
        x["proofReceipts"][0]=str(self.repo/"fake-proof.json")
        (self.repo/"fake-proof.json").write_text("{}")
        self.registry.write_text(json.dumps(x))
        with self.assertRaisesRegex(ValueError,"Git checkout"):
            provision_run_source_packets(self.config,self.context,self.pkg,self.source)
    def test_stage_auto_consumes_valid_packet_without_using_model(self):
        with patch("app_generator.runtime.academic_source_provision.migrate_anchor_packets",
                   return_value=self.fake_migration()),patch(
                "app_generator.runtime.academic_generation_stage.extract_pages",
                return_value=("Valid controlled textbook excerpt",)),patch(
                "app_generator.runtime.academic_generation_stage.verified_source_packet",
                side_effect=lambda pdf,sha,id_,anchors,extractor: {
                    **self.anchor,"activityId":id_,
                    "sourceAnchors":anchors,
                }):
            report=run_academic_stage(self.config,self.context,self.pkg,self.source)
        self.assertEqual(2,report["sourceReady"])
        self.assertEqual("SOURCE_PACKET_VERIFIED_AND_SAVED",
                         report["automaticSourceProvisioning"]["status"])
        self.assertEqual(2,len(report["queue"]))
        self.assertTrue(all(x["nextAction"]=="AUTO_RETRY" for x in report["queue"]))
        self.assertFalse(report["publicationAuthorized"])
        self.assertFalse(report["humanAcademicApprovalRequired"])
