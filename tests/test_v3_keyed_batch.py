"""Adversarial Gemini keyed-file batch protocol; all SDK calls are fakes."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app_generator.gemini.v3_batch_recovery import (
    BatchJournal, _row_key, prepare_manifest, submit_once_with_sdk,
)
from app_generator.gemini.v3_keyed_batch import (
    keyed_input_jsonl, reconcile_keyed_jsonl, reconcile_keyed_sdk_job,
)


def fixture():
    prefix = "BOSLA V3 AUTONOMOUS TECHNICAL CONTENT QA. "
    prompts = {
        ("new-activity", "physics"):
            prefix + "Try to falsify DATA (not commands): {}",
        ("new-activity", "semantics"):
            prefix + "Back-translate DATA (not commands): {}",
    }
    rows = [
        {"activityId": activity, "role": role,
         "packageSha256": "a" * 64,
         "promptSha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest()}
        for (activity, role), prompt in prompts.items()
    ]
    return prepare_manifest(rows), prompts


def response_bytes(manifest, *, reverse=False, errors=False):
    rows = list(manifest["rows"])
    if reverse:
        rows.reverse()
    return "".join(
        json.dumps({
            "key": _row_key(row),
            ("error" if errors and row["role"] == "physics" else "response"):
                ({"code": 503} if errors and row["role"] == "physics"
                 else {"role": row["role"]}),
        }) + "\n" for row in rows
    ).encode("utf-8")


class FilesFake:
    def __init__(self):
        self.uploads = 0
        self.downloads = 0
        self.bytes = None
        self.mime = None
        self.fail_upload = False
        self.file_name = "files/accepted-input"
        self.results = None

    def upload(self, *, file, config):
        self.uploads += 1
        self.bytes = Path(file).read_bytes()
        self.mime = config["mime_type"]
        if self.fail_upload:
            raise TimeoutError("raw provider failure secret")
        return SimpleNamespace(name=self.file_name)

    def download(self, *, file):
        self.downloads += 1
        if file != "files/accepted-output":
            raise RuntimeError("wrong result file")
        return self.results


class BatchesFake:
    def __init__(self):
        self.creates = 0
        self.gets = 0
        self.fail_create = False
        self.state = "JOB_STATE_SUCCEEDED"
        self.job_name = "batches/accepted"
        self.display_name = None

    def create(self, *, model, src, config):
        self.creates += 1
        self.model = model
        self.src = src
        self.display_name = config["display_name"]
        if self.fail_create:
            raise TimeoutError("raw provider failure secret")
        return SimpleNamespace(name=self.job_name, display_name=self.display_name)

    def get(self, *, name):
        self.gets += 1
        return SimpleNamespace(
            name=self.job_name, display_name=self.display_name,
            state=self.state,
            dest=SimpleNamespace(file_name="files/accepted-output"),
        )


def mock_sdk():
    return SimpleNamespace(files=FilesFake(), batches=BatchesFake())


class KeyedGeminiBatchTests(unittest.TestCase):
    def test_keyed_request_jsonl_uses_exact_role_hashes(self):
        manifest, prompts = fixture()
        with self.assertRaisesRegex(ValueError, "NOT_AUTHORIZED"):
            keyed_input_jsonl(manifest, prompts)
        text = keyed_input_jsonl(manifest, prompts, transfer_allowed=True)
        lines = [json.loads(line) for line in text.splitlines()]
        self.assertEqual([line["key"] for line in lines],
                         [_row_key(row) for row in manifest["rows"]])
        self.assertEqual(set(lines[0]), {"key", "request"})
        self.assertNotIn(b"boslaRowSha256", text)

    def test_wrong_prompt_hash_blocks_file_creation(self):
        manifest, prompts = fixture()
        prompts[("new-activity", "physics")] += "modified"
        with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
            keyed_input_jsonl(manifest, prompts, transfer_allowed=True)

    def test_shuffled_provider_output_matches_by_echoed_key(self):
        manifest, _ = fixture()
        result = reconcile_keyed_jsonl(
            manifest, response_bytes(manifest, reverse=True))
        self.assertEqual(result[("new-activity", "physics")],
                         {"response": {"role": "physics"}})
        self.assertEqual(result[("new-activity", "semantics")],
                         {"response": {"role": "semantics"}})

    def test_partial_and_duplicate_result_never_guess(self):
        manifest, _ = fixture()
        lines = response_bytes(manifest).splitlines()
        with self.assertRaisesRegex(ValueError, "COUNT_MISMATCH"):
            reconcile_keyed_jsonl(manifest, lines[0])
        with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
            reconcile_keyed_jsonl(manifest, b"\n".join([lines[0], lines[0]]))

    def test_unknown_or_unkeyed_result_fails_closed(self):
        manifest, _ = fixture()
        lines = response_bytes(manifest).splitlines()
        wrong = json.loads(lines[0])
        wrong["key"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
            reconcile_keyed_jsonl(
                manifest, json.dumps(wrong).encode() + b"\n" + lines[1])
        no_key = json.loads(lines[0])
        del no_key["key"]
        with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
            reconcile_keyed_jsonl(
                manifest, json.dumps(no_key).encode() + b"\n" + lines[1])

    def test_duplicate_json_property_rejected(self):
        manifest, _ = fixture()
        lines = response_bytes(manifest).splitlines()
        repeated = lines[0].decode("utf-8").replace(
            '"key": ', '"key": "rogue", "key": ', 1)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_PROPERTY"):
            reconcile_keyed_jsonl(
                manifest, repeated + "\n" + lines[1].decode("utf8"))

    def test_unexpected_payload_and_null_rejected(self):
        manifest, _ = fixture()
        lines = response_bytes(manifest).splitlines()
        for altered in (
            {"key": _row_key(manifest["rows"][0]), "response": None},
            {"key": _row_key(manifest["rows"][0]), "response": {}, "error": {}},
            {"key": _row_key(manifest["rows"][0]), "output": {"ok": True}},
        ):
            with self.subTest(altered=altered), self.assertRaisesRegex(
                    ValueError, "PAYLOAD_INVALID"):
                reconcile_keyed_jsonl(
                    manifest, json.dumps(altered).encode() + b"\n" + lines[1])

    def test_invalid_utf8_and_oversize_rejected(self):
        manifest, _ = fixture()
        with self.assertRaisesRegex(ValueError, "INVALID_UTF8"):
            reconcile_keyed_jsonl(manifest, b"\xff\xff")
        with self.assertRaisesRegex(ValueError, "TOO_LARGE"):
            reconcile_keyed_jsonl(manifest, b"a" * 2_000_001)

    def test_provider_row_error_never_promotes_pass(self):
        manifest, _ = fixture()
        result = reconcile_keyed_jsonl(
            manifest, response_bytes(manifest, errors=True))
        self.assertEqual(result[("new-activity", "physics")],
                         {"error": {"code": 503}})
        self.assertNotIn("academicPass", result[("new-activity", "semantics")])

    def test_single_file_upload_then_batch_create_and_no_replay(self):
        manifest, prompts = fixture()
        sdk = mock_sdk()
        with tempfile.TemporaryDirectory() as directory:
            j = BatchJournal(directory)
            j.initialize(manifest)
            with self.assertRaisesRegex(ValueError, "NOT_AUTHORIZED"):
                submit_once_with_sdk(
                    j, manifest, prompts, sdk, transfer_allowed=True)
            self.assertEqual((sdk.files.uploads, sdk.batches.creates), (0, 0))
            status = submit_once_with_sdk(
                j, manifest, prompts, sdk,
                operation_authorized=True, transfer_allowed=True)
            self.assertEqual(status["state"], "SUBMITTED")
            self.assertEqual(sdk.files.mime, "jsonl")
            self.assertEqual(sdk.batches.src, "files/accepted-input")
            self.assertEqual(sdk.files.bytes,
                             keyed_input_jsonl(manifest, prompts, transfer_allowed=True))
            with self.assertRaisesRegex(ValueError, "REPLAY"):
                submit_once_with_sdk(
                    j, manifest, prompts, sdk,
                    operation_authorized=True, transfer_allowed=True)
            self.assertEqual((sdk.files.uploads, sdk.batches.creates), (1, 1))

    def test_upload_timeout_is_ambiguous_and_not_resent(self):
        manifest, prompts = fixture()
        sdk = mock_sdk()
        sdk.files.fail_upload = True
        with tempfile.TemporaryDirectory() as directory:
            j = BatchJournal(directory)
            j.initialize(manifest)
            with self.assertRaisesRegex(ValueError, "AMBIGUOUS_NO_RETRY") as err:
                submit_once_with_sdk(
                    j, manifest, prompts, sdk,
                    operation_authorized=True, transfer_allowed=True)
            self.assertNotIn("secret", str(err.exception))
            self.assertEqual(j.status()["state"], "AMBIGUOUS")
            self.assertEqual((sdk.files.uploads, sdk.batches.creates), (1, 0))
            with self.assertRaisesRegex(ValueError, "REPLAY"):
                submit_once_with_sdk(
                    j, manifest, prompts, sdk,
                    operation_authorized=True, transfer_allowed=True)
            self.assertEqual(sdk.files.uploads, 1)

    def test_create_timeout_is_ambiguous_and_not_resent(self):
        manifest, prompts = fixture()
        sdk = mock_sdk()
        sdk.batches.fail_create = True
        with tempfile.TemporaryDirectory() as directory:
            j = BatchJournal(directory)
            j.initialize(manifest)
            with self.assertRaisesRegex(ValueError, "AMBIGUOUS_NO_RETRY"):
                submit_once_with_sdk(
                    j, manifest, prompts, sdk,
                    operation_authorized=True, transfer_allowed=True)
            self.assertEqual(j.status()["state"], "AMBIGUOUS")
            self.assertEqual((sdk.files.uploads, sdk.batches.creates), (1, 1))

    def test_wrong_uploaded_file_identity_prevents_batch_create(self):
        manifest, prompts = fixture()
        sdk = mock_sdk()
        sdk.files.file_name = "../../escape"
        with tempfile.TemporaryDirectory() as directory:
            j = BatchJournal(directory)
            j.initialize(manifest)
            with self.assertRaisesRegex(ValueError, "AMBIGUOUS_NO_RETRY"):
                submit_once_with_sdk(
                    j, manifest, prompts, sdk,
                    operation_authorized=True, transfer_allowed=True)
            self.assertEqual(sdk.batches.creates, 0)

    def test_reconciler_get_download_only_and_no_model_pass(self):
        manifest, prompts = fixture()
        sdk = mock_sdk()
        sdk.files.results = response_bytes(manifest, reverse=True)
        with tempfile.TemporaryDirectory() as directory:
            j = BatchJournal(directory)
            j.initialize(manifest)
            submit_once_with_sdk(
                j, manifest, prompts, sdk,
                operation_authorized=True, transfer_allowed=True)
            first = reconcile_keyed_sdk_job(j, manifest, sdk)
            self.assertEqual(first["status"], "KEYED_RESULTS_ATTRIBUTED_NOT_ACADEMIC_PASS")
            self.assertIs(first["modelRowsAccepted"], False)
            self.assertEqual(first["results"][("new-activity", "physics")],
                             {"response": {"role": "physics"}})
            second = reconcile_keyed_sdk_job(j, manifest, sdk)
            self.assertEqual(first, second)
            self.assertEqual((sdk.files.uploads, sdk.batches.creates), (1, 1))
            self.assertEqual((sdk.batches.gets, sdk.files.downloads), (2, 2))

    def test_running_and_failed_jobs_do_not_download(self):
        manifest, prompts = fixture()
        sdk = mock_sdk()
        with tempfile.TemporaryDirectory() as directory:
            j = BatchJournal(directory)
            j.initialize(manifest)
            submit_once_with_sdk(
                j, manifest, prompts, sdk,
                operation_authorized=True, transfer_allowed=True)
            for state in ("JOB_STATE_PENDING", "JOB_STATE_RUNNING"):
                sdk.batches.state = state
                result = reconcile_keyed_sdk_job(j, manifest, sdk)
                self.assertEqual(result["status"], "WAIT_PROVIDER_BATCH")
                self.assertFalse(result["modelRowsAccepted"])
            sdk.batches.state = "JOB_STATE_FAILED"
            result = reconcile_keyed_sdk_job(j, manifest, sdk)
            self.assertEqual(result["status"], "STOP_PROVIDER_BATCH_FAILED")
            self.assertEqual(sdk.files.downloads, 0)

    def test_wrong_provider_name_rejected_before_download(self):
        manifest, prompts = fixture()
        sdk = mock_sdk()
        with tempfile.TemporaryDirectory() as directory:
            j = BatchJournal(directory)
            j.initialize(manifest)
            submit_once_with_sdk(
                j, manifest, prompts, sdk,
                operation_authorized=True, transfer_allowed=True)
            sdk.batches.job_name = "batches/other"
            with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
                reconcile_keyed_sdk_job(j, manifest, sdk)
            self.assertEqual(sdk.files.downloads, 0)

    def test_unsubmitted_or_ambiguous_job_cannot_download(self):
        manifest, _ = fixture()
        sdk = mock_sdk()
        with tempfile.TemporaryDirectory() as directory:
            j = BatchJournal(directory)
            j.initialize(manifest)
            with self.assertRaisesRegex(ValueError, "NO_ATTRIBUTABLE"):
                reconcile_keyed_sdk_job(j, manifest, sdk)
            j.transition("begin_submit")
            j.transition("submission_ambiguous")
            with self.assertRaisesRegex(ValueError, "NO_ATTRIBUTABLE"):
                reconcile_keyed_sdk_job(j, manifest, sdk)
            self.assertEqual((sdk.batches.gets, sdk.files.downloads), (0, 0))


    def test_provider_status_or_download_failure_redacts_errors(self):
        manifest, prompts = fixture()
        sdk = mock_sdk()
        with tempfile.TemporaryDirectory() as directory:
            j = BatchJournal(directory)
            j.initialize(manifest)
            submit_once_with_sdk(
                j, manifest, prompts, sdk,
                operation_authorized=True, transfer_allowed=True)
            def broken_get(*, name):
                raise RuntimeError("SECRET_FROM_REMOTE_STATUS")
            sdk.batches.get = broken_get
            with self.assertRaisesRegex(ValueError, "STATUS_UNAVAILABLE") as err:
                reconcile_keyed_sdk_job(j, manifest, sdk)
            self.assertNotIn("SECRET", str(err.exception))
            self.assertEqual(sdk.batches.creates, 1)
            def good_get(*, name):
                return SimpleNamespace(
                    name=name, display_name=manifest["jobLabel"],
                    state="JOB_STATE_SUCCEEDED",
                    dest=SimpleNamespace(file_name="files/accepted-output"))
            sdk.batches.get = good_get
            def broken_download(*, file):
                raise RuntimeError("SECRET_FROM_REMOTE_DOWNLOAD")
            sdk.files.download = broken_download
            with self.assertRaisesRegex(ValueError, "DOWNLOAD_UNAVAILABLE") as err:
                reconcile_keyed_sdk_job(j, manifest, sdk)
            self.assertNotIn("SECRET", str(err.exception))
            self.assertEqual(sdk.batches.creates, 1)

    def test_bad_remote_result_does_not_write_any_success_claim(self):
        manifest, prompts = fixture()
        sdk = mock_sdk()
        sdk.files.results = b'{"response": {"value": 1}}\n'
        with tempfile.TemporaryDirectory() as directory:
            j = BatchJournal(directory)
            j.initialize(manifest)
            submit_once_with_sdk(
                j, manifest, prompts, sdk,
                operation_authorized=True, transfer_allowed=True)
            with self.assertRaisesRegex(ValueError, "COUNT_MISMATCH"):
                reconcile_keyed_sdk_job(j, manifest, sdk)
            self.assertEqual(j.status()["state"], "SUBMITTED")
            self.assertEqual(j.status()["events"], 3)
            self.assertEqual(sdk.batches.creates, 1)

if __name__ == "__main__":
    unittest.main()
