"""BSA294 MCQ07: real private candidate must agree with signed V36.

The source-bound test runs only on the owner Yoga6. CI does not substitute
the tracked sample package for the private revised candidate.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from unittest import TestCase, skipUnless

from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
from app_generator.runtime.v3_malay_auto_revision import _CANDIDATE
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation import section91_equal_energy_false_options_proof as science


@skipUnless(os.name == "nt" and os.environ.get("COMPUTERNAME", "").upper() == "YOGA6",
            "Private selected Serway source exists only on owner Yoga6")
class OwnerMcq07CanonicalIds(TestCase):
    def test_real_source_and_signed_seventh_partition_rederive_all_three(self):
        private = Path(os.environ["LOCALAPPDATA"]) / "Microvid" / "BoslaV3ReviewYoga6"
        head = read_long_horizon_development(private)
        ready = {"gitHead": head["gitHead"], "proposalSha256": head["proposalSha256"]}
        folder = private / "owner-five-stage-completion" / ready["gitHead"] / ready["proposalSha256"]
        candidate = folder / _CANDIDATE
        self.assertFalse(candidate.is_symlink())
        raw = candidate.read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), science._CANDIDATE_SHA)
        package = json.loads(raw)
        queue = plan_full_semantic_proofs(package=package, source_sha256=science._SOURCE_SHA)
        self.assertEqual(queue["taskCount"], 429)
        part = _signed(folder, "V36_PARTITION_07.json", ready)
        rows = part["activity"]["evidenceRows"]
        self.assertEqual(part["activity"]["activityId"], science._ACTIVITY)
        self.assertEqual(part["candidateSha256"], science._CANDIDATE_SHA)
        self.assertEqual(part["sourceSha256"], science._SOURCE_SHA)
        source = Path(_trusted_json(private / _SOURCE_BINDING)["sourcePdf"])
        ids = []
        for position, option in enumerate(science._OPTIONS_ORDER, 1):
            tasks = [t for t in queue["tasks"] if t["activityId"] == science._ACTIVITY
                     and t["kind"] == "MCQ_DISTRACTOR_SCIENCE"
                     and t["surfacePath"] == f"answerKey/options/{position}/label"]
            self.assertEqual(len(tasks), 1)
            task = tasks[0]
            signed = [row for row in rows if row.get("taskId") == task["taskId"]]
            self.assertEqual(len(signed), 1)
            self.assertEqual(signed[0]["surfaceSha256"], task["surfaceSha256"])
            proof = science.independently_prove_equal_energy_false_option(
                source_pdf=source, candidate_path=candidate, option_id=option)
            self.assertEqual(proof["taskId"], task["taskId"])
            self.assertFalse(proof["academicTaskAccepted"])
            ids.append(task["taskId"])
        self.assertEqual(len(set(ids)), 3)
        sample = json.loads(Path("content/chapter-9/section-9-1/package.json").read_text("utf8"))
        sample_queue = plan_full_semantic_proofs(
            package=sample, source_sha256=science._SOURCE_SHA)
        sample_ids = [t["taskId"] for t in sample_queue["tasks"] if
                      t["activityId"] == science._ACTIVITY and
                      t["kind"] == "MCQ_DISTRACTOR_SCIENCE"]
        self.assertNotEqual(ids, sample_ids)

    def test_mutated_candidate_cannot_produce_owner_science(self):
        from tempfile import TemporaryDirectory

        private = Path(os.environ["LOCALAPPDATA"]) / "Microvid" / "BoslaV3ReviewYoga6"
        head = read_long_horizon_development(private)
        folder = private / "owner-five-stage-completion" / head["gitHead"] / head["proposalSha256"]
        original = (folder / _CANDIDATE).read_bytes()
        source = Path(_trusted_json(private / _SOURCE_BINDING)["sourcePdf"])
        with TemporaryDirectory() as tmp:
            altered = Path(tmp) / "candidate.json"
            altered.write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                science.independently_prove_equal_energy_false_option(
                    source_pdf=source, candidate_path=altered,
                    option_id=science._OPTIONS_ORDER[0])
