"""Finite, private PDF acquisition with fail-closed checkpoints.

This module is source preparation only: never calls a model or the generator,
modifies user project files, reruns source-bearing requests or publishes.
All manifest fields and prior-file hashes are checked BEFORE network access.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Callable
from urllib.parse import urljoin, urlsplit

MAX_PDF_BYTES = 12_000_000
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
IDENT_RE = re.compile(r"[a-z][a-z0-9-]{2,80}\Z")
FILE_RE = re.compile(r"[a-z][a-z0-9-]{2,80}\.pdf\Z")
TOPICS = frozenset(("mechanics", "electromagnetism", "thermodynamics"))
REQUIRED = frozenset(("schemaVersion", "campaignId", "selectionWitnessCommit",
    "selectionWitnessFile", "generatorBaselineGitSha", "priorStopReceiptSha256",
    "previousSourceSha256s", "allowedSourceHosts", "maxNewDownloads", "modelCallsAllowed",
    "publicationAllowed", "cases"))
CASE_REQUIRED = frozenset(("caseId", "topicFamily", "filename", "sourceURL"))
CASE_REUSE = frozenset(("reuseLocalPath", "reuseSha256"))


class AcquisitionStop(ValueError):
    """Stable, sanitized and non-retriable stop category."""


@dataclass(frozen=True)
class SourceSelection:
    case_id: str
    topic_family: str
    filename: str
    source_url: str
    reuse_path: Path | None = None
    reuse_sha: str | None = None


def _stop_if(condition: bool, category: str) -> None:
    if condition:
        raise AcquisitionStop(category)


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def validate_acquisition_plan(plan: dict[str, Any]) -> tuple[SourceSelection, ...]:
    """Validate *every* row shape and reuse identity before any source transfer."""
    _stop_if(not isinstance(plan, dict) or set(plan) != REQUIRED,
             "INVALID_PLAN_FIELDS")
    _stop_if(type(plan["schemaVersion"]) is not int or plan["schemaVersion"] != 1,
             "INVALID_PLAN_VERSION")
    _stop_if(not isinstance(plan["campaignId"], str) or
             not IDENT_RE.fullmatch(plan["campaignId"]), "INVALID_CAMPAIGN_ID")
    for key in ("selectionWitnessCommit", "generatorBaselineGitSha"):
        _stop_if(not isinstance(plan[key], str) or not COMMIT_RE.fullmatch(plan[key]),
                 "INVALID_CODE_IDENTITY")
    _stop_if(not isinstance(plan["selectionWitnessFile"], str) or
             not plan["selectionWitnessFile"].startswith("docs/") or
             ".." in plan["selectionWitnessFile"] or
             "\\" in plan["selectionWitnessFile"] or
             ":" in plan["selectionWitnessFile"],
             "INVALID_SELECTION_WITNESS_PATH")
    _stop_if(not isinstance(plan["priorStopReceiptSha256"], str) or
             not SHA_RE.fullmatch(plan["priorStopReceiptSha256"]),
             "INVALID_PRIOR_STOP_IDENTITY")
    hosts = plan["allowedSourceHosts"]
    _stop_if(not isinstance(hosts, list) or not 1 <= len(hosts) <= 5 or
             len(hosts) != len(set(map(str, hosts))) or
             any(not isinstance(host, str) or
                 not re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+", host)
                 for host in hosts), "INVALID_TRUSTED_HOST_ALLOWLIST")
    prior = plan["previousSourceSha256s"]
    _stop_if(not isinstance(prior, list) or len(prior) < 1 or
             len(prior) != len(set(map(str, prior))) or
             any(not isinstance(v, str) or not SHA_RE.fullmatch(v) for v in prior),
             "INVALID_PRIOR_SOURCE_IDS")
    _stop_if(plan["modelCallsAllowed"] is not False or
             plan["publicationAllowed"] is not False, "UNSAFE_PUBLICATION_OR_MODEL_FLAGS")
    cases = plan["cases"]
    _stop_if(not isinstance(cases, list) or len(cases) != 3,
             "INVALID_THREE_SOURCE_SCOPE")
    result: list[SourceSelection] = []
    for case in cases:
        _stop_if(not isinstance(case, dict) or
                 set(case) not in (CASE_REQUIRED, CASE_REQUIRED | CASE_REUSE),
                 "INVALID_SOURCE_ROW_FIELDS")
        case_id, family, filename, url = (
            case["caseId"], case["topicFamily"], case["filename"], case["sourceURL"]
        )
        _stop_if(not isinstance(case_id, str) or not IDENT_RE.fullmatch(case_id) or
                 not isinstance(family, str) or family not in TOPICS or
                 not isinstance(filename, str) or
                 not FILE_RE.fullmatch(filename) or not isinstance(url, str),
                 "INVALID_SOURCE_ROW_IDENTITY")
        parsed = urlsplit(url)
        _stop_if(parsed.scheme != "https" or parsed.hostname not in hosts or
                 bool(parsed.username or parsed.password or parsed.fragment) or
                 not parsed.path.lower().endswith(".pdf"),
                 "NONTRUSTED_SOURCE_URL")
        reuse_path, reuse_sha = None, None
        if "reuseLocalPath" in case:
            raw_path = case["reuseLocalPath"]
            reuse_sha = case["reuseSha256"]
            _stop_if(not isinstance(raw_path, str) or not raw_path or
                     not isinstance(reuse_sha, str) or not SHA_RE.fullmatch(reuse_sha) or
                     reuse_sha in prior, "INVALID_REUSE_IDENTITY")
            reuse_path = Path(raw_path)
            _stop_if(not reuse_path.is_absolute() or reuse_path.is_symlink() or
                     not reuse_path.is_file() or
                     reuse_path.stat().st_size > MAX_PDF_BYTES or
                     _sha(reuse_path.read_bytes()) != reuse_sha,
                     "REUSED_PDF_MISMATCH")
        result.append(SourceSelection(
            case_id, family, filename, url, reuse_path, reuse_sha))
    _stop_if({r.topic_family for r in result} != TOPICS or
             len({r.case_id for r in result}) != 3 or
             len({r.filename.casefold() for r in result}) != 3 or
             len({r.source_url for r in result}) != 3,
             "NONDISTINCT_SOURCE_SELECTION")
    _stop_if(type(plan["maxNewDownloads"]) is not int or
             plan["maxNewDownloads"] != sum(r.reuse_path is None for r in result),
             "DOWNLOAD_BUDGET_MISMATCH")
    return tuple(result)


def verify_selection_witness(plan: dict[str, Any], repo: Path) -> str:
    """Read the immutable committed selection, not a mutable local document."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "show",
             f"{plan['selectionWitnessCommit']}:{plan['selectionWitnessFile']}"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=8,
        )
    except (subprocess.SubprocessError, OSError, KeyError) as exc:
        raise AcquisitionStop("PRECOMMITTED_WITNESS_UNAVAILABLE") from exc
    body = result.stdout.decode("utf-8")
    for case in plan["cases"]:
        _stop_if(case["sourceURL"] not in body or case["caseId"] not in body,
                 "SOURCE_NOT_IN_PRECOMMITTED_WITNESS")
    try:
        subprocess.run(["git", "-C", str(repo), "cat-file", "-t",
                        plan["generatorBaselineGitSha"]],
                       check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=8)
    except (subprocess.SubprocessError, OSError) as exc:
        raise AcquisitionStop("BASELINE_GIT_REVISION_UNAVAILABLE") from exc
    return _sha(result.stdout)


def fetch_trusted_pdf_once(url: str, trusted_hosts: tuple[str, ...]) -> bytes:
    """One logical fetch; follow only bounded, same-allowlist HTTPS redirects.

    Redirect hops are not retries of a failed or ambiguous source transfer.
    An HTTP error or interrupted transfer is terminal and is never retried.
    """
    import requests
    session = requests.Session()
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=0))
    visited: set[str] = set()
    current = url
    try:
        for _hop in range(4):
            target = urlsplit(current)
            _stop_if(current in visited or target.scheme != "https" or
                     target.hostname not in trusted_hosts or
                     bool(target.username or target.password),
                     "SOURCE_REDIRECT_OUT_OF_SCOPE")
            visited.add(current)
            with session.get(current, stream=True, timeout=(15, 90),
                             allow_redirects=False) as response:
                if response.is_redirect:
                    location = response.headers.get("Location")
                    _stop_if(not isinstance(location, str) or not location,
                             "INVALID_SOURCE_REDIRECT")
                    dest = urljoin(current, location)
                    parsed = urlsplit(dest)
                    _stop_if(parsed.scheme != "https" or
                             parsed.hostname not in trusted_hosts or
                             bool(parsed.username or parsed.password),
                             "SOURCE_REDIRECT_OUT_OF_SCOPE")
                    current = dest
                    continue
                response.raise_for_status()
                _stop_if("text/html" in
                         response.headers.get("Content-Type", "").lower(),
                         "SOURCE_RESPONSE_NOT_PDF")
                data = bytearray()
                for chunk in response.iter_content(65536):
                    data.extend(chunk)
                    _stop_if(len(data) > MAX_PDF_BYTES, "PDF_OVERSIZE")
                return bytes(data)
        raise AcquisitionStop("SOURCE_REDIRECT_LIMIT_EXCEEDED")
    finally:
        session.close()


def classify_source_suitability(*, pages: int, words: int,
                                rights_indicators: list[str]) -> str:
    """Explanatory triage, not a waiver of the frozen 300-word PASS gate.

    Sparse slide decks are retained as BORDERLINE_REVIEW_REQUIRED, never
    automatically promoted to academic suitability.
    """
    if rights_indicators:
        return "RIGHTS_REVIEW_REQUIRED"
    if pages < 5 or words < 240:
        return "INSUFFICIENT_SOURCE_CONTENT"
    if words < 300:
        return "BORDERLINE_REVIEW_REQUIRED"
    return "PASS"


def inspect_pdf_metadata(path: Path, pdfinfo: Path, pdftotext: Path) -> dict[str, Any]:
    """Inspect local bytes only; return numerical properties, never source text."""
    _stop_if(not pdfinfo.is_file() or not pdftotext.is_file(),
             "LOCAL_PDF_TOOLS_UNAVAILABLE")
    try:
        info = subprocess.run([str(pdfinfo), str(path)], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=35).stdout
        found = re.search(rb"^Pages:\s*(\d+)", info, re.M)
        _stop_if(not found, "PDF_PAGE_COUNT_MISSING")
        body = subprocess.run([str(pdftotext), "-layout", str(path), "-"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=50).stdout
    except subprocess.SubprocessError as exc:
        raise AcquisitionStop("PDF_LOCAL_INSPECTION_FAILED") from exc
    text = body.decode("utf-8", "replace")
    words = len(re.findall(r"\b[\w'-]{3,}\b", text))
    indicators = [
        s for s in ("all rights reserved", "reproduced with permission",
                    "courtesy of", "used with permission") if s in text.casefold()
    ]
    category = classify_source_suitability(
        pages=int(found.group(1)), words=words, rights_indicators=indicators)
    return {"pages": int(found.group(1)), "approxWords": words,
            "rightsIndicatorsDetected": indicators,
            "sourceSuitabilityCategory": category,
            "textSuitabilityPass": category == "PASS"}


def _write_once(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def acquire_frozen_sources(
    plan: dict[str, Any], *, repo: Path, output_root: Path,
    fetch: Callable[[str, tuple[str, ...]], bytes] = fetch_trusted_pdf_once,
    inspector: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    """One manifest, one run, at most one fetch per new case; no hidden retries."""
    rows = validate_acquisition_plan(plan)
    witness_sha = verify_selection_witness(plan, repo)
    _stop_if(output_root.is_symlink() or not output_root.is_dir() or
             output_root.resolve().is_relative_to(repo.resolve()) or
             list(output_root.iterdir()), "UNSAFE_OR_REUSED_PRIVATE_OUTPUT")
    pdf_dir = output_root / "pdfs"
    attempts = output_root / "attempts"
    pdf_dir.mkdir()
    attempts.mkdir()
    _write_once(output_root / "started.json", {
        "campaignId": plan["campaignId"], "baselineGitSha": plan["generatorBaselineGitSha"],
        "priorStopReceiptSha256": plan["priorStopReceiptSha256"],
        "selectionWitnessSha256": witness_sha, "maxNewDownloads": plan["maxNewDownloads"],
        "sourceBearingModelCalls": 0, "publicationAuthorized": False,
        "noNetworkReplay": True,
    })
    results: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    pending_category = "UNDETERMINED"
    done_shas: set[str] = set(plan["previousSourceSha256s"])
    try:
        for row in rows:
            _write_once(attempts / (row.case_id + ".json"), {
                "caseId": row.case_id, "sourceURL": row.source_url,
                "mode": "VERIFIED_PRIVATE_REUSE" if row.reuse_path else "ONE_PUBLIC_FETCH",
                "noAutomaticRetry": True, "publicationAuthorized": False,
            })
            data = (row.reuse_path.read_bytes() if row.reuse_path else
                    fetch(row.source_url, tuple(plan["allowedSourceHosts"])))
            _stop_if(not isinstance(data, bytes) or len(data) > MAX_PDF_BYTES or
                     not data.startswith(b"%PDF-") or
                     b"%%EOF" not in data[-1024:], "INVALID_PDF_BYTES")
            digest = _sha(data)
            _stop_if(digest in done_shas or
                     (row.reuse_sha is not None and row.reuse_sha != digest),
                     "DUPLICATE_OR_MISMATCHED_PDF_IDENTITY")
            done_shas.add(digest)
            dest = pdf_dir / row.filename
            with dest.open("xb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            retained_row = {
                "caseId": row.case_id, "sourceSha256": digest,
                "fileBytes": len(data), "persisted": True,
                "modelCalls": 0, "publicationAuthorized": False,
            }
            retained.append(retained_row)
            # This receipt is deliberately durable BEFORE source suitability:
            # a failed borderline gate must not erase a sound downloaded PDF.
            _write_once(attempts / (row.case_id + "-acquired.json"), retained_row)
            meta = inspector(dest)
            claimed_category = (meta.get("sourceSuitabilityCategory")
                                if isinstance(meta, dict) else None)
            pending_category = (
                claimed_category if claimed_category in {
                    "PASS", "BORDERLINE_REVIEW_REQUIRED",
                    "INSUFFICIENT_SOURCE_CONTENT", "RIGHTS_REVIEW_REQUIRED"}
                else "INVALID_METADATA"
            )
            _stop_if(not isinstance(meta, dict) or
                     set(meta) != {"pages", "approxWords",
                                   "rightsIndicatorsDetected", "textSuitabilityPass",
                                   "sourceSuitabilityCategory"} or
                     meta.get("sourceSuitabilityCategory") != "PASS" or
                     meta.get("textSuitabilityPass") is not True or
                     type(meta.get("pages")) is not int or meta["pages"] < 5 or
                     type(meta.get("approxWords")) is not int or
                     meta["approxWords"] < 300 or
                     meta.get("rightsIndicatorsDetected") != [],
                     "SOURCE_STRUCTURE_OR_RIGHTS_REVIEW_STOP")
            record = {
                "caseId": row.case_id, "topicFamily": row.topic_family,
                "filename": row.filename, "sourceURL": row.source_url,
                "sourceSha256": digest, "fileBytes": len(data),
                "reuseVerifiedNoRedownload": row.reuse_path is not None,
                "rightsStatus": "NONCOMMERCIAL_PRIVATE_ONLY_THIRD_PARTY_UNVERIFIED",
                "sourceBearingModelCalls": 0, "publicationAuthorized": False,
                **meta,
            }
            results.append(record)
            _write_once(attempts / (row.case_id + "-finished.json"), record)
        report = {
            "status": "ALL_THREE_PRIVATE_SOURCES_ACQUIRED",
            "campaignId": plan["campaignId"],
            "preselectionCommit": plan["selectionWitnessCommit"],
            "generatorBaselineGitSha": plan["generatorBaselineGitSha"],
            "sources": results, "sourceBearingModelCalls": 0,
            "thirdPartyFigureRightsIndependentlyVerified": False,
            "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False,
        }
        _write_once(output_root / "source_integrity.json", report)
        return report
    except BaseException as exc:
        category = str(exc) if isinstance(exc, AcquisitionStop) else "UNEXPECTED_ACQUISITION_STOP"
        _write_once(output_root / "terminal_stop.json", {
            "status": "STOPPED_NO_AUTO_RETRY", "failureCategory": category,
            "completedCases": [r["caseId"] for r in results],
            "retainedVerifiedPdfCases": [r["caseId"] for r in retained],
            "unacceptedSourceSuitabilityCategory": pending_category,
            "sourceBearingModelCalls": 0, "publicationAuthorized": False,
        })
        raise AcquisitionStop(category) from exc
