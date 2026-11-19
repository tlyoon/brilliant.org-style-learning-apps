"""BSA225: dispatch genuine six-section public-bundle builds after private V6.

This is the original public release *builder* and V3 HMAC gate, exercised in
private temporary storage. Never call a publisher, Git merge, model, or PDF API.
A successful local bundle is not authority to deploy the public app.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import tempfile

from app_generator.runtime.academic_release import enforce_academic_release_gate
from app_generator.runtime.v3_five_stage_completion import _BASE, _candidate_dir, _hash
from app_generator.runtime.v3_native_release_adapter import _v6_checkpoint
from app_generator.runtime.v3_versioned_readiness import (
    _git_info, _git_clean, _read_previous, _hosted_runs, _exact_ci_success,
)
from scripts.build_public_release import build

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_V6 = "V6_GENUINE_NATIVE_V3_RELEASE_ATTESTATION.json"
_V7 = "V7_ACTUAL_PUBLIC_BUNDLE_BUILDER_HANDOFF.json"
_STATUS = "SIX_REAL_PUBLIC_BUNDLE_BUILDS_VERIFIED_PRIVATE_NO_DEPLOY"


def _trusted_json(path: Path, maxbytes: int = 16000) -> dict:
    if (path.is_symlink() or not path.is_file()
            or path.stat().st_size > maxbytes):
        raise ValueError("V3_PUBLIC_BUILD_UNSAFE_CHECKPOINT")
    data = json.loads(path.read_text(encoding="utf8"))
    if not isinstance(data, dict):
        raise ValueError("V3_PUBLIC_BUILD_INVALID_CHECKPOINT")
    return data


def dispatch_private_public_bundle_build(
    repo: Path, private: Path, readiness: dict, completed_v6: dict,
) -> dict:
    """Run *six* real release builds within the normal source-free supervisor.

    Reads genuine exact-package V3 HMAC receipts, not synthetic PASS fields.
    Preserves the production builder, immutable original reviewer evidence,
    finite C3 failure, and publication-disabled operational boundary.
    """
    if (readiness.get("status") !=
            "VERSIONED_SCIENCE_BROWSER_AND_CI_VERIFIED_UNADMITTED"
            or readiness.get("exactHeadHostedCiSuccess") is not True
            or readiness.get("codeWorkingTreeClean") is not True
            or readiness.get("proposedContentScientificCoverage") != 108
            or readiness.get("publicationAuthorized") is not False
            or completed_v6.get("status") !=
            "FIVE_STAGE_PRIVATE_TECHNICAL_PATH_COMPLETE_NO_PUBLICATION"
            or completed_v6.get("technicalV3ReleaseAttestationsVerified") is not True
            or completed_v6.get("privateNativeV3Attestations") != 6
            or completed_v6.get("publicationAuthorized") is not False):
        raise ValueError("V3_PUBLIC_BUILD_GENUINE_V6_PREREQUISITE_MISSING")
    head = readiness.get("gitHead")
    proposal = readiness.get("proposalSha256")
    if (not isinstance(head, str) or not _HEX40.fullmatch(head)
            or not isinstance(proposal, str) or not _HEX64.fullmatch(proposal)
            or completed_v6.get("gitHead") != head
            or completed_v6.get("proposalSha256") != proposal):
        raise ValueError("V3_PUBLIC_BUILD_SOURCE_VERSION_MISMATCH")
    if _read_previous(private / "v3-current-versioned-evidence-readiness.json") != readiness:
        raise ValueError("V3_PUBLIC_BUILD_READINESS_NOT_SAVED")
    live_head, branch = _git_info(repo)
    if (live_head != head or not _git_clean(repo)
            or not _exact_ci_success(_hosted_runs(repo, branch), head)):
        raise ValueError("V3_PUBLIC_BUILD_EXACT_HEAD_CI_OR_CLEAN_MISSING")
    folder = private / _BASE / head / proposal
    v6 = _trusted_json(folder / _V6)
    unsigned = {k: v for k, v in v6.items() if k != "integritySha256"}
    if (v6.get("integritySha256") != _hash(unsigned)
            or v6.get("status") !=
            "SIX_PRIVATE_NATIVE_V3_RELEASE_ATTESTATIONS_VERIFIED_NO_PUBLIC_DEPLOY"
            or v6.get("gitHead") != head
            or v6.get("proposalSha256") != proposal
            or v6.get("nativeV3TechnicalReleaseChecksPassed") != 6
            or v6.get("sourceGenuineTwoReviewerPositions") != 108
            or v6.get("publicationAuthorized") is not False
            or v6.get("publicDeployExecuted") is not False
            or completed_v6.get("nativeV3TechnicalReleaseEvidence", {}).get(
                "integritySha256") != v6["integritySha256"]):
        raise ValueError("V3_PUBLIC_BUILD_V6_INTEGRITY_OR_STATUS_CHANGED")
    rows = v6.get("packages")
    if (not isinstance(rows, list) or len(rows) != 6
            or [x.get("section") for x in rows if isinstance(x, dict)] !=
               [f"section-9-{i}" for i in range(1, 7)]):
        raise ValueError("V3_PUBLIC_BUILD_INCORRECT_SECTION_ROSTER")

    # Only copy ordinary app/domain source assets; actual generated packages
    # remain in the LOCALAPPDATA private root, never committed to Git.
    records = []
    with tempfile.TemporaryDirectory(prefix="bosla-v7-release-", dir=private) as temp:
        scratch = Path(temp)
        overlay = scratch / "source-root"
        for name in ("app", "domains"):
            source = repo / name
            if source.is_symlink() or not source.is_dir():
                raise ValueError("V3_PUBLIC_BUILD_UNSAFE_SOURCE_TREE")
            shutil.copytree(source, overlay / name)
        for index, record in enumerate(rows, 1):
            section = f"section-9-{index}"
            raw_path = (_candidate_dir(private, head, proposal) / "content" /
                        "chapter-9" / section / "package.json")
            attestation = (folder / "native-v3-exact-attestations" / section /
                           "autonomous-v3-release-receipt.json")
            if (raw_path.is_symlink() or not raw_path.is_file()
                    or attestation.is_symlink() or not attestation.is_file()):
                raise ValueError("V3_PUBLIC_BUILD_MISSING_AUTHENTIC_PACKAGE")
            raw = raw_path.read_bytes()
            digest = sha256(raw).hexdigest()
            if (len(raw) > 2_000_000 or digest != record.get("packageSha256")
                    or record.get("privateAttestationSha256") !=
                       sha256(attestation.read_bytes()).hexdigest()
                    or record.get("nativeV3TechnicalGatePassed") is not True):
                raise ValueError("V3_PUBLIC_BUILD_PACKAGE_OR_ATTESTATION_CHANGED")
            receipt_dir = attestation.parent
            accepted = enforce_academic_release_gate(repo, raw_path, receipt_dir)
            if (accepted.get("artifactSha256") != digest or
                    accepted.get("automatedTechnicalEligible") is not True):
                raise ValueError("V3_PUBLIC_BUILD_PRODUCTION_RELEASE_GATE_FAILED")
            staged = overlay / "content" / "chapter-9" / section / "package.json"
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(raw)
            output = scratch / f"bundle-{index}"
            build(output, staged, source_root=overlay, validation_dir=receipt_dir)
            packaged = output / "content" / "package.json"
            if (packaged.is_symlink() or not packaged.is_file()
                    or packaged.read_bytes() != raw):
                raise ValueError("V3_PUBLIC_BUILD_PRODUCTION_BUNDLE_BYTES_CHANGED")
            index_html = output / "index.html"
            if (not index_html.is_file()
                    or "LOCAL DRAFT PREVIEW" in index_html.read_text(encoding="utf8")):
                raise ValueError("V3_PUBLIC_BUILD_NOT_REAL_RELEASE_MODE")
            files = sorted(x for x in output.rglob("*") if x.is_file())
            if len(files) < 7 or any(x.is_symlink() for x in files):
                raise ValueError("V3_PUBLIC_BUILD_INCOMPLETE_BUNDLE")
            witnesses = [{
                "path": x.relative_to(output).as_posix(),
                "sha256": sha256(x.read_bytes()).hexdigest(),
            } for x in files]
            records.append({
                "section": section, "packageSha256": digest,
                "bundleFileCount": len(files), "bundleManifestSha256":
                    _hash({"files": witnesses}),
            })
    payload = {
        "contract": "BOSLA_V7_REAL_PUBLIC_BUNDLE_BUILD_HANDOFF_V1",
        "status": _STATUS, "gitHead": head, "proposalSha256": proposal,
        "previousNativeV6Sha256": v6["integritySha256"],
        "realOriginalPublicBuilderInvocations": len(records),
        "technicalReleaseBuildVerified": True, "releases": records,
        "nextEligibleMilestone": "PUBLIC_DEPLOYMENT_SCOPE_AND_PERMISSION_CHECK",
        "heldoutC3CampaignReopened": False,
        "newModelCalls": 0, "publicMergeExecuted": False,
        "publicDeployExecuted": False, "publicationAuthorized": False,
    }
    return _v6_checkpoint(folder / _V7, payload)
