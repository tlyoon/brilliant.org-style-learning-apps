"""Fail-closed keyed JSONL Gemini Batch transport (source-free unit-testable).

Google's file-backed Batch API echoes the user-defined JSONL request key.
Inline SDK requests do not provide a reliable row identity. These functions
never assign response rows based on order. They do not infer model PASS,
perform review consensus or authorize publication.

The V3 journal must first bind an exact frozen package and two unsent roles.
This module cannot clear or resubmit an ambiguous historical claim.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from app_generator.gemini.v3_batch_recovery import (
    BatchJournal, _json, _row_key, inline_requests, validate_manifest,
)

_MAX_RESULT_BYTES_PER_ROW = 1_000_000


def keyed_input_jsonl(manifest: dict[str, Any],
                      prompts: dict[tuple[str, str], str], *,
                      transfer_allowed: bool = False) -> bytes:
    """Create SDK-supported file-backed Batch JSONL, with exact hash keys."""
    requests = inline_requests(
        manifest, prompts, transfer_allowed=transfer_allowed)
    if len(requests) != len(manifest["rows"]):
        raise ValueError("V3_BATCH_KEYED_INPUT_ROSTER_MISMATCH")
    output = []
    for row, entry in zip(manifest["rows"], requests):
        key = _row_key(row)
        if entry.get("metadata") != {"boslaRowSha256": key}:
            raise ValueError("V3_BATCH_KEYED_INPUT_IDENTITY_MISMATCH")
        output.append(_json({"key": key, "request": entry["request"]}))
    return ("\n".join(output) + "\n").encode("utf-8")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("V3_BATCH_DUPLICATE_JSON_PROPERTY")
        obj[key] = value
    return obj


def reconcile_keyed_jsonl(manifest: dict[str, Any],
                          raw: bytes | str) -> dict[tuple[str, str], dict[str, Any]]:
    """Bind out-of-order results to role only by provider-echoed key.

    A correct key is an identity witness, not scientific/multilingual PASS.
    Reject missing, duplicated, unknown, unkeyed, partial or contradictory
    responses, including duplicate properties and oversized text.
    """
    validate_manifest(manifest)
    if isinstance(raw, bytes):
        if len(raw) > len(manifest["rows"]) * _MAX_RESULT_BYTES_PER_ROW:
            raise ValueError("V3_BATCH_KEYED_RESULT_TOO_LARGE")
        try:
            raw = raw.decode("utf-8", "strict")
        except UnicodeDecodeError:
            raise ValueError("V3_BATCH_KEYED_RESULT_INVALID_UTF8") from None
    if (not isinstance(raw, str) or
            len(raw.encode("utf-8")) > len(manifest["rows"]) * _MAX_RESULT_BYTES_PER_ROW):
        raise ValueError("V3_BATCH_KEYED_RESULT_INVALID_OR_LARGE")
    expected = {_row_key(row): row for row in manifest["rows"]}
    lines = raw.splitlines()
    if len(lines) != len(expected) or any(not line.strip() for line in lines):
        raise ValueError("V3_BATCH_KEYED_RESPONSE_COUNT_MISMATCH")
    results: dict[str, dict[str, Any]] = {}
    for line in lines:
        try:
            record = json.loads(line, object_pairs_hook=_unique_object)
        except (TypeError, json.JSONDecodeError):
            raise ValueError("V3_BATCH_KEYED_RESPONSE_INVALID_JSON") from None
        if (not isinstance(record, dict) or "key" not in record
                or not isinstance(record["key"], str)
                or record["key"] not in expected or record["key"] in results):
            raise ValueError("V3_BATCH_KEYED_RESPONSE_IDENTITY_MISMATCH")
        payload_keys = set(record) - {"key"}
        if len(payload_keys) != 1 or not payload_keys <= {"response", "error"}:
            raise ValueError("V3_BATCH_KEYED_RESPONSE_PAYLOAD_INVALID")
        payload_key = next(iter(payload_keys))
        if not isinstance(record[payload_key], dict) or not record[payload_key]:
            raise ValueError("V3_BATCH_KEYED_RESPONSE_PAYLOAD_INVALID")
        results[record["key"]] = {payload_key: record[payload_key]}
    if set(results) != set(expected):
        raise ValueError("V3_BATCH_KEYED_RESPONSE_MISSING_ROW")
    return {
        (row["activityId"], row["role"]): results[key]
        for key, row in expected.items()
    }


def _sdk_file_name(value: Any) -> str:
    if (not isinstance(value, str) or not value.startswith("files/")
            or not value[6:] or len(value) > 256
            or not all(c.isascii() and (c.isalnum() or c in "-_/") for c in value)):
        raise ValueError("V3_BATCH_FILE_IDENTITY_INVALID")
    return value


def submit_keyed_file_once_with_sdk(
    journal: BatchJournal, manifest: dict[str, Any],
    prompts: dict[tuple[str, str], str],
    client: Any, *, operation_authorized: bool = False,
    transfer_allowed: bool = False,
) -> dict[str, Any]:
    """One authorized file upload and one batch creation; no automatic retry.

    A failure after BEGIN can mean upload/create was accepted but the client
    never received a reply. Leave the durable journal AMBIGUOUS.
    """
    if operation_authorized is not True:
        raise ValueError("V3_BATCH_OPERATION_NOT_AUTHORIZED")
    raw = keyed_input_jsonl(
        manifest, prompts, transfer_allowed=transfer_allowed)
    state = journal.status()
    if state["batchSha256"] != manifest["batchSha256"] or state["state"] != "PREPARED":
        raise ValueError("V3_BATCH_REPLAY_OR_WRONG_MANIFEST")
    if (not callable(getattr(getattr(client, "files", None), "upload", None))
            or not callable(getattr(getattr(client, "batches", None), "create", None))):
        raise ValueError("V3_BATCH_KEYED_FILE_SDK_REQUIRED")
    journal.transition("begin_submit")
    try:
        with tempfile.TemporaryDirectory(prefix="bosla-v3-batch-") as folder:
            source = Path(folder) / "requests.jsonl"
            with source.open("xb") as handle:
                handle.write(raw)
            uploaded = client.files.upload(
                file=str(source),
                config={"display_name": manifest["jobLabel"] + "-input",
                        "mime_type": "jsonl"},
            )
            file_name = _sdk_file_name(getattr(uploaded, "name", None))
            job = client.batches.create(
                model=manifest["model"], src=file_name,
                config={"display_name": manifest["jobLabel"]},
            )
    except BaseException:
        journal.transition("submission_ambiguous")
        raise ValueError("V3_BATCH_KEYED_SUBMISSION_AMBIGUOUS_NO_RETRY") from None
    try:
        journal.transition(
            "attach_verified_job",
            provider_job=getattr(job, "name", None),
            provider_display_name=getattr(job, "display_name", None))
    except ValueError:
        journal.transition("submission_ambiguous")
        raise ValueError("V3_BATCH_PROVIDER_ID_UNVERIFIED_NO_RETRY") from None
    return journal.status()


def reconcile_keyed_sdk_job(
    journal: BatchJournal, manifest: dict[str, Any], client: Any,
) -> dict[str, Any]:
    """Read-only exact-ID polling/download; never submits or approves rows.

    Caller must separately validate V3 reviewer verdicts and preserve
    immutable private role checkpoints. Re-running GET is safe, never POST.
    """
    validate_manifest(manifest)
    status = journal.status()
    if (status["batchSha256"] != manifest["batchSha256"]
            or status["state"] not in {"SUBMITTED", "RUNNING", "SUCCEEDED"}
            or not isinstance(status["providerJob"], str)):
        raise ValueError("V3_BATCH_NO_ATTRIBUTABLE_JOB_TO_RECONCILE")
    if (not callable(getattr(getattr(client, "batches", None), "get", None))
            or not callable(getattr(getattr(client, "files", None), "download", None))):
        raise ValueError("V3_BATCH_READONLY_SDK_REQUIRED")
    try:
        job = client.batches.get(name=status["providerJob"])
    except Exception:
        raise ValueError("V3_BATCH_PROVIDER_READONLY_STATUS_UNAVAILABLE") from None
    if (getattr(job, "name", None) != status["providerJob"]
            or getattr(job, "display_name", None) != manifest["jobLabel"]):
        raise ValueError("V3_BATCH_PROVIDER_IDENTITY_MISMATCH")
    raw_state = getattr(job, "state", None)
    state = getattr(raw_state, "name", raw_state)
    if state in {"JOB_STATE_PENDING", "JOB_STATE_RUNNING", "JOB_STATE_QUEUED"}:
        return {"status": "WAIT_PROVIDER_BATCH", "providerJob": status["providerJob"],
                "modelRowsAccepted": False}
    if state in {"JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}:
        return {"status": "STOP_PROVIDER_BATCH_" + state.split("_")[-1],
                "providerJob": status["providerJob"],
                "modelRowsAccepted": False}
    if state != "JOB_STATE_SUCCEEDED":
        raise ValueError("V3_BATCH_UNRECOGNIZED_PROVIDER_STATE")
    dest = getattr(job, "dest", None)
    file_name = _sdk_file_name(getattr(dest, "file_name", None))
    try:
        content = client.files.download(file=file_name)
    except Exception:
        raise ValueError("V3_BATCH_PROVIDER_READONLY_DOWNLOAD_UNAVAILABLE") from None
    mapped = reconcile_keyed_jsonl(manifest, content)
    return {"status": "KEYED_RESULTS_ATTRIBUTED_NOT_ACADEMIC_PASS",
            "providerJob": status["providerJob"],
            "modelRowsAccepted": False, "results": mapped}
