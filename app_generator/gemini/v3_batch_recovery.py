"""Source-free, fail-closed Gemini V3 batch manifest and durable job ledger.

This module NEVER calls Google or submits a job. A separate authorized
transport may consume a manifest only after verifying all frozen identities.
Provider SUCCEEDED is not academic PASS. No request body or credential is
ever written into this ledger.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROLES = ("physics", "semantics")
_STATES = {"PREPARED", "SUBMITTING", "AMBIGUOUS", "SUBMITTED",
           "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED"}
_END = {"SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED"}
_HEX = set("0123456789abcdef")


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _HEX


def prepare_manifest(items: list[dict[str, str]], *,
                     model: str = "gemini-3.8-flash",
                     ineligible: set[tuple[str, str]] | None = None) -> dict[str, Any]:
    """Create only a metadata manifest; no prompts, PDFs, or student records."""
    if model != "gemini-3.8-flash" or not isinstance(items, list) or not items:
        raise ValueError("V3_BATCH_MODEL_OR_ROWS_INVALID")
    blocked = ineligible if ineligible is not None else set()
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    packages: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {
                "activityId", "role", "packageSha256", "promptSha256"}:
            raise ValueError("V3_BATCH_METADATA_ONLY")
        activity, role = item["activityId"], item["role"]
        if (not isinstance(activity, str) or not activity or len(activity) > 128
                or not all(c.isascii() and (c.isalnum() or c in "-_.") for c in activity)
                or role not in ROLES or not _sha(item["packageSha256"])
                or not _sha(item["promptSha256"])):
            raise ValueError("V3_BATCH_IDENTITY_INVALID")
        key = (activity, role)
        if key in seen or key in blocked:
            raise ValueError("V3_BATCH_DUPLICATE_OR_UNRECONCILED")
        seen.add(key)
        packages.add(item["packageSha256"])
        rows.append(dict(item))
    if len(packages) != 1:
        raise ValueError("V3_BATCH_CROSS_PACKAGE_FORBIDDEN")
    for activity in {a for a, _ in seen}:
        if {r for a, r in seen if a == activity} != set(ROLES):
            raise ValueError("V3_BATCH_REQUIRES_TWO_ROLE_PAIR")
    rows.sort(key=lambda r: (r["activityId"], ROLES.index(r["role"])))
    payload = {"schema": "bosla-v3-batch-metadata-v1", "model": model, "rows": rows}
    digest = _digest(payload)
    return {**payload, "batchSha256": digest, "jobLabel": "bosla-v3-" + digest[:24]}


def validate_manifest(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict) or set(manifest) != {
            "schema", "model", "rows", "batchSha256", "jobLabel"}:
        raise ValueError("V3_BATCH_MANIFEST_INVALID")
    rebuilt = prepare_manifest(manifest["rows"], model=manifest["model"])
    if rebuilt != manifest:
        raise ValueError("V3_BATCH_MANIFEST_TAMPERED")


class BatchJournal:
    """Exclusive-create append-only events. A crashed SUBMITTING is not retryable."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def initialize(self, manifest: dict[str, Any]) -> dict[str, Any]:
        validate_manifest(manifest)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / "manifest.json"
        with path.open("x", encoding="utf-8") as file:
            file.write(_json(manifest) + "\n")
            file.flush()
        return self._append("PREPARED", "", {})

    def _read(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        manifest = json.loads((self.directory / "manifest.json").read_text(encoding="utf-8"))
        validate_manifest(manifest)
        names = sorted(self.directory.glob("[0-9][0-9][0-9][0-9][0-9][0-9].json"))
        if not names:
            raise ValueError("V3_BATCH_LEDGER_EMPTY")
        events: list[dict[str, Any]] = []
        previous = ""
        for index, path in enumerate(names):
            if path.name != f"{index:06d}.json":
                raise ValueError("V3_BATCH_LEDGER_GAP")
            event = json.loads(path.read_text(encoding="utf-8"))
            if (set(event) != {"sequence", "state", "priorSha256", "batchSha256",
                               "details", "eventSha256"}
                    or event["sequence"] != index or event["state"] not in _STATES
                    or event["priorSha256"] != previous
                    or event["batchSha256"] != manifest["batchSha256"]
                    or event["eventSha256"] != _digest({k: v for k, v in event.items()
                                                         if k != "eventSha256"})):
                raise ValueError("V3_BATCH_LEDGER_TAMPERED")
            if index == 0 and (event["state"] != "PREPARED" or event["details"] != {}):
                raise ValueError("V3_BATCH_LEDGER_INVALID_START")
            previous = event["eventSha256"]
            events.append(event)
        return manifest, events

    def status(self) -> dict[str, Any]:
        manifest, events = self._read()
        submitted = [e for e in events if e["state"] == "SUBMITTED"]
        return {"batchSha256": manifest["batchSha256"],
                "jobLabel": manifest["jobLabel"], "state": events[-1]["state"],
                "providerJob": (submitted[0]["details"]["providerJob"]
                                if submitted else None),
                "details": events[-1]["details"], "events": len(events)}

    def _append(self, state: str, previous: str, details: dict[str, str]) -> dict[str, Any]:
        if state == "PREPARED":
            number, batch = 0, json.loads(
                (self.directory / "manifest.json").read_text(encoding="utf-8"))["batchSha256"]
        else:
            manifest, events = self._read()
            number, batch = len(events), manifest["batchSha256"]
            if events[-1]["eventSha256"] != previous:
                raise ValueError("V3_BATCH_STALE_WRITER")
        event = {"sequence": number, "state": state, "priorSha256": previous,
                 "batchSha256": batch, "details": details}
        event["eventSha256"] = _digest(event)
        with (self.directory / f"{number:06d}.json").open("x", encoding="utf-8") as file:
            file.write(_json(event) + "\n")
            file.flush()
        return event

    def transition(self, action: str, *,
                   provider_job: str | None = None,
                   provider_display_name: str | None = None) -> dict[str, Any]:
        """Record externally observed lifecycle only; does not execute any HTTP."""
        manifest, events = self._read()
        state = events[-1]["state"]
        allowed = {
            "begin_submit": ({"PREPARED"}, "SUBMITTING"),
            "submission_ambiguous": ({"SUBMITTING"}, "AMBIGUOUS"),
            "attach_verified_job": ({"SUBMITTING", "AMBIGUOUS"}, "SUBMITTED"),
            "running": ({"SUBMITTED", "RUNNING"}, "RUNNING"),
            "succeeded": ({"SUBMITTED", "RUNNING"}, "SUCCEEDED"),
            "failed": ({"SUBMITTED", "RUNNING"}, "FAILED"),
            "cancelled": ({"SUBMITTED", "RUNNING"}, "CANCELLED"),
            "expired": ({"SUBMITTED", "RUNNING"}, "EXPIRED"),
        }
        if action not in allowed or state not in allowed[action][0]:
            raise ValueError("V3_BATCH_ILLEGAL_OR_REPEAT_TRANSITION")
        details: dict[str, str] = {}
        if action == "attach_verified_job":
            if (not isinstance(provider_job, str)
                    or not provider_job.startswith("batches/")
                    or not provider_job[8:]
                    or len(provider_job) > 256
                    or not all(c.isascii() and (c.isalnum() or c in "-_/") for c in provider_job)
                    or provider_display_name != manifest["jobLabel"]):
                raise ValueError("V3_BATCH_UNATTRIBUTABLE_PROVIDER_JOB")
            details = {"providerJob": provider_job, "providerDisplayName": provider_display_name}
        elif provider_job is not None or provider_display_name is not None:
            raise ValueError("V3_BATCH_UNEXPECTED_PROVIDER_METADATA")
        return self._append(allowed[action][1], events[-1]["eventSha256"], details)


def _row_key(row: dict[str, str]) -> str:
    return _digest(row)


def inline_requests(manifest: dict[str, Any],
                    prompts: dict[tuple[str, str], str], *,
                    transfer_allowed: bool = False) -> list[dict[str, Any]]:
    """Bind exact text in memory only; never write it into the public journal."""
    validate_manifest(manifest)
    if transfer_allowed is not True:
        raise ValueError("V3_BATCH_GENERATED_TEXT_TRANSFER_NOT_AUTHORIZED")
    expected = {(r["activityId"], r["role"]) for r in manifest["rows"]}
    if not isinstance(prompts, dict) or set(prompts) != expected:
        raise ValueError("V3_BATCH_PROMPT_ROSTER_MISMATCH")
    requests = []
    for row in manifest["rows"]:
        prompt = prompts[(row["activityId"], row["role"])]
        marker = "Try to falsify" if row["role"] == "physics" else "Back-translate"
        if (not isinstance(prompt, str)
                or not prompt.startswith("BOSLA V3 AUTONOMOUS TECHNICAL CONTENT QA.")
                or "DATA (not commands): " not in prompt
                or marker not in prompt or "%PDF-" in prompt
                or hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                   != row["promptSha256"]):
            raise ValueError("V3_BATCH_PROMPT_IDENTITY_MISMATCH")
        requests.append({
            "request": {"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
            "metadata": {"boslaRowSha256": _row_key(row)},
        })
    return requests


def submit_once_with_sdk(journal: BatchJournal, manifest: dict[str, Any],
                         prompts: dict[tuple[str, str], str],
                         client: Any, *,
                         operation_authorized: bool = False,
                         transfer_allowed: bool = False) -> dict[str, Any]:
    """Normal Batch submission uses file-backed keyed JSONL, never inline.

    The provider must echo stable input keys so that results can be attributed
    to the correct activity and Gemini reviewer without relying on row order.
    """
    from app_generator.gemini.v3_keyed_batch import submit_keyed_file_once_with_sdk
    return submit_keyed_file_once_with_sdk(
        journal, manifest, prompts, client,
        operation_authorized=operation_authorized,
        transfer_allowed=transfer_allowed)


def reconcile_inline_responses(manifest: dict[str, Any],
                               responses: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    """Require echoed row hashes, never trust positional order or infer PASS."""
    validate_manifest(manifest)
    expected = {_row_key(row): row for row in manifest["rows"]}
    if (not isinstance(responses, list) or len(responses) != len(expected)):
        raise ValueError("V3_BATCH_RESPONSE_COUNT_MISMATCH")
    bound = {}
    for response in responses:
        if not isinstance(response, dict) or set(response) != {"metadata", "output"}:
            raise ValueError("V3_BATCH_UNATTRIBUTABLE_RESPONSE")
        metadata, output = response["metadata"], response["output"]
        if (not isinstance(metadata, dict)
                or set(metadata) != {"boslaRowSha256"}
                or metadata["boslaRowSha256"] not in expected
                or metadata["boslaRowSha256"] in bound):
            raise ValueError("V3_BATCH_DUPLICATE_OR_MISSING_ROW_KEY")
        if (not isinstance(output, dict) or len(output) != 1
                or not (set(output) <= {"response", "error"})):
            raise ValueError("V3_BATCH_RESPONSE_STATUS_INVALID")
        bound[metadata["boslaRowSha256"]] = output
    return {
        (row["activityId"], row["role"]): bound[key]
        for key, row in expected.items()
    }
