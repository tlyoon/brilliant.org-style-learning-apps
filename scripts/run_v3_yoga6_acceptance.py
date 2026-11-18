"""BOSLA Yoga6 normal source-free real-course browser QA stage.

On-demand, idempotent and bounded. Reuses the project-local pinned Selenium
environment, never modifies global Python, and never generates model output.
QA is a private *unadmitted* candidate verification, not academic/release.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

_HEX=set("0123456789abcdef")
_CHECK_FILES=(
    "scripts/check_v3_real_chapter9_browser.py",
    "scripts/run_v3_yoga6_acceptance.py",
    "app/app.js",
    "app/course-preview.js",
    "app/rc1-chapter9-bridge.js",
    "app/rc1-course-routing.js",
    "app/visual-renderers.js",
)
_QA="v3-real-chapter9-browser-qa.json"


def _digest(obj: dict) -> str:
    return sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),
                             ensure_ascii=True).encode("utf8")).hexdigest()


def _runtime_sha(root: Path) -> str:
    full=sha256()
    for rel in _CHECK_FILES:
        file=root.joinpath(*rel.split("/"))
        if file.is_symlink() or not file.is_file():
            raise ValueError("V3_BROWSER_QA_MISSING_RENDERER")
        data=file.read_bytes()
        full.update(rel.encode("ascii")+b"\0"+len(data).to_bytes(8,"big")+data)
    return full.hexdigest()


def _supported_python(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    try:
        result=subprocess.run([str(path),"-c",
                               "import selenium; assert selenium.__version__ == '4.47.0'"],
                              check=False,capture_output=True,timeout=10)
    except (OSError,subprocess.TimeoutExpired):
        return False
    return result.returncode==0


def _browser_python(root: Path) -> Path:
    current=Path(sys.executable)
    if _supported_python(current):
        return current
    env=root/".venv"
    executable=env/("Scripts/python.exe" if os.name=="nt" else "bin/python")
    if env.is_symlink() or executable.is_symlink():
        raise ValueError("V3_BROWSER_QA_UNSAFE_LOCAL_RUNTIME")
    if not executable.is_file():
        subprocess.run([str(current),"-m","venv",str(env)],cwd=root,
                       capture_output=True,timeout=90,check=True)
    if not _supported_python(executable):
        requirements=(root/"requirements-generator.txt").read_text(encoding="utf8")
        if not re.search(r"(?m)^selenium==4\.47\.0$",requirements):
            raise ValueError("V3_BROWSER_QA_UNPINNED_SELENIUM")
        subprocess.run([
            str(executable),"-m","pip","install",
            "--disable-pip-version-check","--retries","0",
            "--timeout","15","selenium==4.47.0"
        ],cwd=root,capture_output=True,check=True,timeout=240)
        if not _supported_python(executable):
            raise ValueError("V3_BROWSER_QA_BOOTSTRAP_FAILED")
    return executable


def _read_saved(path: Path) -> dict | None:
    if path.is_symlink():
        raise ValueError("V3_BROWSER_QA_SYMLINK_RECEIPT")
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size>20_000:
        raise ValueError("V3_BROWSER_QA_RECEIPT_UNSAFE")
    doc=json.loads(path.read_text(encoding="utf8"))
    check={k:v for k,v in doc.items() if k!="integritySha256"}
    if (doc.get("integritySha256")!=_digest(check)
            or doc.get("publicationAuthorized") is not False
            or doc.get("genuineGeminiReviewsAdded") != 0
            or doc.get("versionedScopeAdmitted") is not False
            or doc.get("activitiesInCandidate") != 108
            or doc.get("sections") != 6
            or doc.get("viewports") != 2
            or doc.get("locales") != 3):
        raise ValueError("V3_BROWSER_QA_RECEIPT_INTEGRITY_ERROR")
    if (doc.get("all108ActivitiesVisited") is True
            and doc.get("allLocaleViewportPromptChecks") == 648
            and doc.get("renderedChecks") == 698):
        return doc
    # BSA-197: a genuine SHA-valid 50-check receipt from the previous
    # real Yoga6 browser release must be automatically refreshed, not
    # promoted to 108-activity PASS or mistaken for corrupted evidence.
    # The actual prior authenticated receipt is kept intact until a new
    # full run succeeds; malicious or malformed receipts still fail STOP.
    if (doc.get("status") == "ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
            and doc.get("renderedChecks") == 50
            and doc.get("all108ActivitiesVisited") in (None, False)
            and doc.get("allLocaleViewportPromptChecks") in (None, 0)):
        return {**doc,"status":"STALE_50_SPOT_CHECK_FULL_QA_REQUIRED"}
    raise ValueError("V3_BROWSER_QA_RECEIPT_INTEGRITY_ERROR")


def _write_saved(path: Path, report: dict) -> dict:
    doc={**report,"integritySha256":_digest(report)}
    data=(json.dumps(doc,sort_keys=True,indent=2)+"\n").encode("utf8")
    if path.is_symlink():
        raise ValueError("V3_BROWSER_QA_RECEIPT_SYMLINK")
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=".v3-browser-stage-",suffix=".tmp",
                             dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        try: Path(name).unlink()
        except FileNotFoundError: pass
    return doc


def advance_real_candidate_browser_qa(
    root: Path, private: Path, source_free: dict,
) -> dict:
    """Called by normal Yoga6 worker only after source-free stage succeeds.

    Any exception is a truthful QA STOP, never a license for publication.
    Paid/review work remains governed by its independent authorization.
    """
    historical=source_free.get("historicalUnrecoverableRoleRecovery",{})
    if (not isinstance(historical,dict)
            or historical.get("status") !=
              "NEW_VERSIONED_SECTION96_REPAIR_STAGED_QA_NOT_AUTHORIZED"
            or not isinstance(source_free.get("proposalSha256"),str)):
        return {"status":"NO_NEW_REAL_CANDIDATE_FOR_BROWSER_QA",
                "publicationAuthorized":False}
    if os.name!="nt":
        return {"status":"NOT_NATIVE_YOGA6_BROWSER_WORKSTATION",
                "publicationAuthorized":False}
    if (private.is_symlink() or not private.is_absolute()
            or not private.resolve().is_relative_to(
                (Path(os.environ["LOCALAPPDATA"])/"Microvid").resolve())):
        raise ValueError("V3_BROWSER_QA_UNSAFE_PRIVATE_ROOT")
    proposed=source_free["proposalSha256"]
    if len(proposed)!=64 or set(proposed)-_HEX:
        raise ValueError("V3_BROWSER_QA_BAD_PROPOSAL_DIGEST")
    revision=subprocess.run(["git","rev-parse","HEAD"],cwd=root,
                            capture_output=True,text=True,check=True,
                            timeout=15).stdout.strip()
    runtime=_runtime_sha(root)
    target=private/_QA
    prior=_read_saved(target)
    if (prior and prior.get("status")=="ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
            and prior.get("proposalSha256")==proposed
            and prior.get("revisionSha")==revision
            and prior.get("rendererRuntimeSha256")==runtime):
        return {**prior,"reusedVerifiedBrowserReceipt":True}
    interpreter=_browser_python(root)
    command=[str(interpreter),
             str(root/"scripts"/"check_v3_real_chapter9_browser.py"),
             "--private-root",str(private)]
    child=subprocess.run(command,cwd=root,capture_output=True,text=True,
                         check=False,timeout=420,
                         env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    try:
        result=json.loads(child.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):
        raise ValueError("V3_BROWSER_QA_CHILD_NON_JSON_OUTPUT") from None
    if (child.returncode!=0
            or result.get("status")!="ACTUAL_UNADMITTED_CHAPTER9_BROWSER_QA_PASS"
            or result.get("proposalSha256")!=proposed
            or result.get("activitiesInCandidate")!=108
            or result.get("sections")!=6
            or result.get("renderedChecks")!=698
            or result.get("all108ActivitiesVisited") is not True
            or result.get("allLocaleViewportPromptChecks")!=648
            or result.get("genuineGeminiReviewsAdded")!=0
            or result.get("publicationAuthorized") is not False):
        return {"status":"STOP_REAL_CANDIDATE_BROWSER_QA_FAILED",
                "proposalSha256":proposed,"publicationAuthorized":False}
    report={**result,"revisionSha":revision,"rendererRuntimeSha256":runtime,
            "versionedScopeAdmitted":False,"publicationAuthorized":False}
    return _write_saved(target,report)
