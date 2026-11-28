"""Owner-only original Serway MCQ09 task and signed ninth partition check."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless

from app_generator.runtime.v3_long_horizon_development import read_long_horizon_development
from app_generator.runtime.v3_malay_auto_revision import _CANDIDATE
from app_generator.runtime.v3_selected_textbook_scientific_provenance import _SOURCE_BINDING
from app_generator.runtime.v3_public_bundle_handoff import _trusted_json
from app_generator.runtime.v3_revised_source_proof_rebinding import _signed
from app_generator.validation.full_semantic_proof_queue import plan_full_semantic_proofs
from app_generator.validation import section91_spring_buffer_false_options_proof as science


@skipUnless(os.name == "nt" and os.environ.get("COMPUTERNAME", "").upper() == "YOGA6",
            "Original selected Serway source exists only on owner Yoga6")
class OwnerMcq09CanonicalIds(TestCase):
    def _inputs(self):
        private = Path(os.environ["LOCALAPPDATA"]) / "Microvid" / "BoslaV3ReviewYoga6"
        head = read_long_horizon_development(private)
        ready = {"gitHead": head["gitHead"], "proposalSha256": head["proposalSha256"]}
        folder = private / "owner-five-stage-completion" / ready["gitHead"] / ready["proposalSha256"]
        candidate = folder / _CANDIDATE
        source = Path(_trusted_json(private / _SOURCE_BINDING)["sourcePdf"])
        return candidate, source, folder, ready

    def test_real_source_and_signed_ninth_partition_rederive_all_three(self):
        candidate, source, folder, ready = self._inputs()
        self.assertFalse(candidate.is_symlink())
        raw = candidate.read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), science._CANDIDATE_SHA)
        queue = plan_full_semantic_proofs(package=json.loads(raw), source_sha256=science._SOURCE_SHA)
        self.assertEqual(queue["taskCount"], 429)
        part = _signed(folder, "V36_PARTITION_09.json", ready)
        self.assertEqual(part["activity"]["activityId"], science._ACTIVITY)
        self.assertEqual(part["candidateSha256"], science._CANDIDATE_SHA)
        self.assertEqual(part["sourceSha256"], science._SOURCE_SHA)
        rows = part["activity"]["evidenceRows"]
        ids = []
        for position, option in enumerate(science._OPTIONS_ORDER, 1):
            matches = [task for task in queue["tasks"] if task["activityId"] == science._ACTIVITY
                       and task["kind"] == "MCQ_DISTRACTOR_SCIENCE"
                       and task["surfacePath"] == f"answerKey/options/{position}/label"]
            self.assertEqual(len(matches), 1)
            task = matches[0]
            signed = [row for row in rows if row.get("taskId") == task["taskId"]]
            self.assertEqual(len(signed), 1)
            self.assertEqual(signed[0]["surfaceSha256"], task["surfaceSha256"])
            proof = science.independently_prove_spring_buffer_false_option(
                source_pdf=source, candidate_path=candidate, option_id=option)
            self.assertEqual(proof["taskId"], task["taskId"])
            self.assertFalse(proof["academicTaskAccepted"])
            ids.append(proof["taskId"])
        self.assertEqual(len(set(ids)), 3)
        sample = json.loads(Path("content/chapter-9/section-9-1/package.json").read_text("utf8"))
        sample_queue = plan_full_semantic_proofs(package=sample, source_sha256=science._SOURCE_SHA)
        sample_ids = [task["taskId"] for task in sample_queue["tasks"] if
                      task["activityId"] == science._ACTIVITY and task["kind"] == "MCQ_DISTRACTOR_SCIENCE"]
        self.assertNotEqual(ids, sample_ids)

    def test_mutated_candidate_cannot_produce_owner_science(self):
        candidate, source, _, _ = self._inputs()
        with TemporaryDirectory() as tmp:
            altered = Path(tmp) / "candidate.json"
            altered.write_bytes(candidate.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "AUTHENTIC_ONE_SERWAY"):
                science.independently_prove_spring_buffer_false_option(
                    source_pdf=source, candidate_path=altered,
                    option_id=science._OPTIONS_ORDER[0])
