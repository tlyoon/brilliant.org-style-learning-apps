"""BOSLA BSA-204: actual browser QA of separately corrected Section9.6 index9.

A REAL browser exercises the new, source-bound free-floating-body version.
It does not accept/publish content, authorize revised Gemini calls or silently
replace the earlier unadmitted 108-activity proposal. Existing exact-sha QA
receipt is reusable across restarts when ALL source/renderer/git hashes agree.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from app_generator.runtime.v3_section96_scientific_failure_repair import (
    stage_known_section96_scientific_failure,
)
from app_generator.validation.autonomous_completion import package_identity
from app_generator.domains import resolve_package_domain

_SCHEMA = "BOSLA_V3_SOURCE_BOUND_SCIENCE_REVISION_REAL_CHROME_V1"
_STATUS = "ACTUAL_INDEX9_SCIENCE_REVISION_BROWSER_QA_PASS_NOT_SCIENTIFIC_QA"
_RECEIPT_DIR = "scientific-failure-browser-acceptance"


def _canonical(payload: dict) -> bytes:
    return (json.dumps(payload,sort_keys=True,
                       separators=(",",":"),ensure_ascii=True)+"\n").encode("ascii")


def _assert_result(record: dict, expected: dict) -> None:
    required=set(expected)|{"status","renderedChecks","viewports","locales",
        "all108ActivitiesVisited","allLocaleViewportPromptChecks",
        "sourceFree","publicationAuthorized",
        "versionedScopeAdmitted","learnerPilotAccepted",
        "genuineGeminiReviewsAdded","originalModelVerdictsChanged",
        "integritySha256"}
    if (not isinstance(record,dict) or set(record)!=required
            or any(record.get(k)!=value for k,value in expected.items())
            or record.get("status")!=_STATUS
            or record.get("renderedChecks")!=698
            or record.get("viewports")!=2 or record.get("locales")!=3
            or record.get("all108ActivitiesVisited") is not True
            or record.get("allLocaleViewportPromptChecks")!=648
            or record.get("sourceFree") is not True
            or record.get("publicationAuthorized") is not False
            or record.get("versionedScopeAdmitted") is not False
            or record.get("learnerPilotAccepted") is not False
            or record.get("genuineGeminiReviewsAdded")!=0
            or record.get("originalModelVerdictsChanged") is not False
            or record.get("integritySha256") != sha256(
                _canonical({k:v for k,v in record.items()
                            if k!="integritySha256"})).hexdigest()):
        raise ValueError("V3_SCIENCE_BROWSER_UNTRUSTED_PASS_RECEIPT")


def _identity(repo: Path, course: Path, private: Path):
    from scripts.check_v3_real_chapter9_browser import _source_bound_packages
    science=stage_known_section96_scientific_failure(course,repo,private)
    if science.get("status")!=(
            "NEW_SECTION96_SCIENCE_REPAIR_STAGED_REVIEW_NOT_AUTHORIZED"
            ) or science.get("paidGeminiCalls")!=0 or science.get(
                "newModelConsensusPassClaimed") is not False:
        raise ValueError("V3_SCIENCE_BROWSER_MISSING_VERIFIED_REPAIR")
    proposal_sha,source_packages=_source_bound_packages(private)
    if len(source_packages)!=6 or source_packages[5][0]!=6:
        raise ValueError("V3_SCIENCE_BROWSER_WRONG_COURSE")
    candidate_sha=science["candidatePackageSha256"]
    path=(private/"scientific-failure-rollforward"/"section-9-6"/
          candidate_sha/"package.json")
    if (path.is_symlink() or not path.is_file()
            or path.stat().st_size>2_000_000):
        raise ValueError("V3_SCIENCE_BROWSER_MISSING_NEW_VERSION")
    raw=path.read_bytes()
    digest,candidate=package_identity(raw)
    prev,old_items=source_packages[5][1:]
    if (digest!=candidate_sha or len(candidate)!=18
            or [i for i,(a,b) in enumerate(zip(old_items,candidate))
                if a!=b]!=[9]
            or candidate[9]["id"]!="int-easy-line-of-action-motion"):
        raise ValueError("V3_SCIENCE_BROWSER_VERSION_MISMATCH")
    new_packages=[*source_packages[:5],(6,raw,candidate)]
    domain=resolve_package_domain(repo,json.loads(source_packages[0][1]))
    renderer=domain.path("visuals","rendererScript")
    css=domain.path("visuals","stylesheet")
    if (renderer.is_symlink() or css.is_symlink()
            or not renderer.is_file() or not css.is_file()):
        raise ValueError("V3_SCIENCE_BROWSER_MISSING_RENDERER")
    renderer_sha=sha256(renderer.read_bytes()+css.read_bytes()).hexdigest()
    revision=subprocess.run(["git","rev-parse","HEAD"],cwd=repo,
        capture_output=True,text=True,check=True,timeout=15).stdout.strip()
    if len(revision)!=40 or set(revision)-set("0123456789abcdef"):
        raise ValueError("V3_SCIENCE_BROWSER_INVALID_REVISION")
    fields={
        "schema":_SCHEMA,
        "baseUnadmittedProposalSha256":proposal_sha,
        "correctedSection96Sha256":digest,
        "correctedIndex9ReviewInputSha256":science["isolatedReviewInputSha256"],
        "originalFrozenSection96Sha256":science["originalPackageSha256"],
        "gitRevisionSha256":revision,
        "rendererRuntimeSha256":renderer_sha,
        "activitiesInCandidate":108,
    }
    identity=sha256(_canonical(fields)).hexdigest()
    return fields,identity,new_packages


def advance_science_revision_browser_qa(
    repo: Path, course: Path, private: Path, *,
    exercise=None,
) -> dict:
    """Actual Chrome except explicitly injected fake browser in regression."""
    if (not private.is_absolute() or private.is_symlink()
            or private.resolve()==repo.resolve()
            or private.resolve().is_relative_to(repo.resolve())):
        raise ValueError("V3_SCIENCE_BROWSER_UNSAFE_PRIVATE")
    expected,identity,packages=_identity(repo,course,private)
    parent=private/_RECEIPT_DIR
    if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
        raise ValueError("V3_SCIENCE_BROWSER_INVALID_PRIVATE_ROOT")
    directory=parent/identity
    receipt=directory/"receipt.json"
    if directory.is_symlink() or receipt.is_symlink():
        raise ValueError("V3_SCIENCE_BROWSER_UNSAFE_RECEIPT")
    if directory.exists():
        if (not directory.is_dir() or not receipt.is_file()
                or receipt.stat().st_size>4096):
            raise ValueError("V3_SCIENCE_BROWSER_INVALID_PRIOR_RESULT")
        raw=receipt.read_bytes()
        value=json.loads(raw.decode("utf8"))
        _assert_result(value,expected)
        if raw!=_canonical(value):
            raise ValueError("V3_SCIENCE_BROWSER_TAMPERED_RECEIPT_BYTES")
        return value
    if exercise is None:
        # BSA-205: reuse the already registered BSA-197 verified Selenium
        # runtime instead of importing the Chrome driver in miniforge's
        # base Python (which has no Selenium). Single child, bounded 420s.
        from scripts.run_v3_yoga6_acceptance import _browser_python
        interpreter=_browser_python(repo)
        if interpreter.resolve()!=Path(sys.executable).resolve():
            runner=repo/"scripts"/"check_v3_science_candidate_browser.py"
            if runner.is_symlink() or not runner.is_file():
                raise ValueError("V3_SCIENCE_BROWSER_UNSAFE_CHILD_SCRIPT")
            child=subprocess.run(
                [str(interpreter),str(runner),"--private-root",str(private)],
                cwd=repo,capture_output=True,text=True,check=False,
                timeout=420,
                env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
            try:
                report=json.loads(child.stdout.strip().splitlines()[-1])
            except (ValueError,IndexError):
                raise ValueError("V3_SCIENCE_BROWSER_CHILD_NON_JSON") from None
            if child.returncode!=0:
                raise ValueError("V3_SCIENCE_BROWSER_CHILD_FAILED")
            _assert_result(report,expected)
            if (not receipt.is_file() or receipt.is_symlink()
                    or receipt.stat().st_size>4096):
                raise ValueError("V3_SCIENCE_BROWSER_CHILD_DID_NOT_COMMIT")
            raw=receipt.read_bytes()
            if raw!=_canonical(report):
                raise ValueError("V3_SCIENCE_BROWSER_CHILD_RECEIPT_MISMATCH")
            return report
    from scripts.check_v3_real_chapter9_browser import (
        _stage_site,_exercise,
    )
    run=_exercise if exercise is None else exercise
    with tempfile.TemporaryDirectory(prefix="bosla-v3-real-index9-version-") as temp:
        site=Path(temp)
        _stage_site(site,packages)
        observed=run(site,packages)
    if (not isinstance(observed,dict)
            or observed.get("renderedChecks")!=698
            or observed.get("allLocaleViewportPromptChecks")!=648
            or observed.get("all108ActivitiesVisited") is not True
            or observed.get("sourceFree") is not True
            or observed.get("publicationAuthorized") is not False
            or observed.get("originalModelVerdictsChanged") is not False):
        raise ValueError("V3_SCIENCE_BROWSER_GENUINE_COVERAGE_INCOMPLETE")
    payload={
        **expected,"status":_STATUS,
        "renderedChecks":observed["renderedChecks"],
        "viewports":observed["viewports"],"locales":observed["locales"],
        "all108ActivitiesVisited":observed["all108ActivitiesVisited"],
        "allLocaleViewportPromptChecks":
            observed["allLocaleViewportPromptChecks"],
        "sourceFree":True,"publicationAuthorized":False,
        "versionedScopeAdmitted":False,"learnerPilotAccepted":False,
        "genuineGeminiReviewsAdded":0,"originalModelVerdictsChanged":False,
    }
    record={**payload,"integritySha256":sha256(_canonical(payload)).hexdigest()}
    _assert_result(record,expected)
    from tempfile import mkdtemp
    parent=private/_RECEIPT_DIR
    if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
        raise ValueError("V3_SCIENCE_BROWSER_INVALID_PRIVATE_ROOT")
    parent.mkdir(parents=True,exist_ok=True)
    stage=Path(mkdtemp(prefix=".science-browser-",dir=parent))
    try:
        data=_canonical(record)
        with (stage/"receipt.json").open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            stage.rename(directory)
        except OSError:
            if not directory.exists():
                raise
            check=json.loads(receipt.read_text(encoding="utf8"))
            _assert_result(check,expected)
            if receipt.read_bytes()!=_canonical(check):
                raise ValueError("V3_SCIENCE_BROWSER_RECEIPT_COLLISION")
    finally:
        import shutil
        if stage.exists():
            shutil.rmtree(stage)
    return record
