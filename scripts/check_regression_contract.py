"""Fail-closed incident-to-regression guard for the development contract.

No network, credentials, source PDFs, student data or real browser required.
The historical ledger has duplicate legacy IDs; new IDs after the cutover
must be unique and represented in the machine-readable registry.
"""
from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^BSA-(\d{8})-(\d{3})$")
LEDGER_RE = re.compile(r"\|\s*(BSA-\d{8}-\d{3})\s*\|")
CUTOVER = "BSA-20261102-096"
# New incidents must reuse an established mechanism before duplicating a fix.
# Legacy records remain unchanged; the audit does not rewrite their history.
FAMILY_LINK_CUTOVER = "BSA-20261106-119"
# Following the owner v5.0 directive, a new RESOLVED incident must also
# demonstrate a remedy in a normally dispatched runtime, not only a test.
# Keep historic incidents unchanged; start with the already-integrated
# Stage-0 learner fixes, and apply this to all later resolved incidents.
AUTO_REMEDY_CUTOVER = "BSA-20261110-135"
NORMAL_RUNTIME_PREFIXES = ("app/", "app_generator/", "scripts/", "domains/")
NORMAL_DISPATCH_PREFIXES = (*NORMAL_RUNTIME_PREFIXES, ".github/workflows/")
FAMILY_ANCHORS: dict[str, tuple[str, ...]] = {
    "recurrence-governance": ("BSA-20261102-096",),
    "source-acquisition": ("BSA-20261105-117",),
    "pdf-repair-loop": ("BSA-20261103-102",),
    "academic-evidence": ("BSA-20261105-114",),
    "learner-browser": ("BSA-20261105-116",),
    "provider-no-replay": ("BSA-20261104-108",),
    "external-denial": ("BSA-20261103-099", "BSA-20261104-111"),
    "integration-readiness": ("BSA-20261104-109",),
    "runtime-preflight": ("BSA-20261102-097",),
}
FAMILY_NEW = "genuinely-new-root-cause"
REQUIRED_BASELINE = frozenset({
    "BSA-20261023-003",
    "BSA-20261024-001",
    "BSA-20261024-004",
    "BSA-20261030-048",
    "BSA-20261030-049",
    "BSA-20261030-051",
    "BSA-20261030-052",
    "BSA-20261031-055",
    "BSA-20261031-057",
    "BSA-20261031-058",
    "BSA-20261031-059",
    "BSA-20261031-060",
    "BSA-20261031-061",
    "BSA-20261031-062",
    "BSA-20261031-063",
    "BSA-20261031-066",
    "BSA-20261031-067",
    "BSA-20261031-070",
    "BSA-20261101-074",
    "BSA-20261101-077",
    "BSA-20261102-090",
    "BSA-20261102-091",
    "BSA-20261102-094",
    "BSA-20261102-096",
    "BSA-20261102-097",
    "BSA-20261102-098",
    "BSA-20261103-099",
    "BSA-20261103-100",
    "BSA-20261103-101",
    "BSA-20261103-102",
    "BSA-20261103-103",
    "BSA-20261104-104",
    "BSA-20261104-105",
    "BSA-20261104-106",
    "BSA-20261104-107",
    "BSA-20261104-108",
    "BSA-20261104-109",
    "BSA-20261104-110",
    "BSA-20261104-111",
    "BSA-20261105-112",
    "BSA-20261105-113",
    "BSA-20261105-114",
    "BSA-20261105-115",
    "BSA-20261105-116",
    "BSA-20261105-117",
    "BSA-20261106-119",
    "BSA-20261106-120",
    "BSA-20261106-121",
    "BSA-20261106-122",
    "BSA-20261106-123",
})
STANDARD_PYTHON_CI = "python -m unittest discover -s tests -v"
GUARD_CI = "python scripts/check_regression_contract.py"
# Immutable owner-approved Decision 0037: runtime recovery, not manual patches.
NORMAL_RECOVERY_DECISION = "docs/decisions/0037-automatic-recovery-normal-pipeline.md"
NORMAL_RECOVERY_PRINCIPLE = (
    "automatic recovery must be part of normal pipeline execution, "
    "not depend on you repeatedly asking me to fix the next blocker."
)
NORMAL_RECOVERY_REQUIREMENTS = (
    "reuseEarlierRemedyBeforeNewCode",
    "automaticDetectionInNormalPipeline",
    "boundedOwnedStateRecoveryOrStop",
    "normalDispatchProofForEveryResolvedIncident",
    "adversarialNegativeControlRequired",
    "normalPathRegressionRequired",
    "exactHeadCIRequired",
    "advanceIndependentAuthorizedWorkWithoutUserPrompt",
    "truthfulUnresolvedExternalBlockers",
    "noAmbiguousRequestReplay",
    "noExternalDenialBypass",
)
NORMAL_RECOVERY_TERMINAL = (
    "BLOCKED_EXTERNAL", "BLOCKED_EXTERNAL_REVIEW_TRANSPORT",
    "RECONCILE_AMBIGUOUS_REVIEW",
)


def _repo_file(root: Path, name: object) -> Path | None:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        return None
    if (name.startswith("/") or any(part in ("", ".", "..") for part in name.split("/"))
            or ":" in name):
        return None
    target = (root / name).resolve()
    return target if target.is_relative_to(root.resolve()) and target.is_file() else None


def _python_has_test(source: str, marker: str) -> bool:
    """Accept only an active unittest.TestCase method in normal discovery.

    A bare test-named function, an inert nested helper or an explicitly
    skipped method must not satisfy a supposedly permanent regression.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    if not marker.startswith("test_") or not marker.isidentifier():
        return False
    for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        is_test_case = any(
            (isinstance(base, ast.Name) and base.id == "TestCase")
            or (isinstance(base, ast.Attribute) and base.attr == "TestCase")
            for base in cls.bases
        )
        if not is_test_case:
            continue
        if any(
            isinstance(decorator, (ast.Name, ast.Attribute))
            and (
                (isinstance(decorator, ast.Name) and decorator.id == "skip")
                or (isinstance(decorator, ast.Attribute) and decorator.attr == "skip")
            )
            for decorator in cls.decorator_list
        ):
            continue
        for method in cls.body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) or method.name != marker:
                continue
            decorators = [
                dec.func if isinstance(dec, ast.Call) else dec
                for dec in method.decorator_list
            ]
            if any(
                (isinstance(dec, ast.Name) and dec.id == "skip")
                or (isinstance(dec, ast.Attribute) and dec.attr == "skip")
                for dec in decorators
            ):
                continue
            return True
    return False


def _js_has_assertion(source: str, marker: str) -> bool:
    # Require the marker on a line that is actually an assertion, rather
    # than an inert comment or an explanatory contract paragraph.
    if not marker or len(marker) < 12 or "\n" in marker:
        return False
    return any(marker in line and re.search(r"\bassert(?:\.|\()", line)
               and not line.lstrip().startswith(("//", "*", "/*"))
               for line in source.splitlines())


def _family_history_errors(
    entry: dict, incident_id: str, earlier: dict[str, dict],
) -> list[str]:
    """Prevent new IDs from concealing a previously solved failure family.

    The classification is intentionally explicit; AI similarity scores or
    shared words in a log cannot grant permission to replay an operation.
    """
    if incident_id < FAMILY_LINK_CUTOVER:
        return []
    errors: list[str] = []
    family = entry.get("rootCauseFamily")
    if family not in (*FAMILY_ANCHORS, FAMILY_NEW):
        return [incident_id + " missing recognized rootCauseFamily"]
    links = entry.get("relatedIncidentIds")
    if (not isinstance(links, list) or len(links) != len(set(map(str, links))) or
            any(not isinstance(link, str) or not ID_RE.fullmatch(link)
                or link not in earlier for link in links)):
        return [incident_id + " requires distinct, existing earlier incident links"]
    if family == FAMILY_NEW:
        explanation = entry.get("noveltyExplanation")
        if not isinstance(explanation, str) or len(explanation.strip()) < 35:
            errors.append(incident_id + " new-root-cause requires a detailed novelty explanation")
    else:
        anchors = set(FAMILY_ANCHORS[family])
        anchors.update(old_id for old_id, old in earlier.items()
                       if old.get("rootCauseFamily") == family)
        if not anchors.intersection(links):
            errors.append(incident_id + " repeated root cause must link an earlier same-family incident")
        delta = entry.get("differenceFromLinkedIncident")
        if not isinstance(delta, str) or len(delta.strip()) < 35:
            errors.append(incident_id + " must explain why earlier regression did not catch recurrence")
    return errors


def _active_marker(source: str, marker: object) -> bool:
    """Require a concrete code/dispatch token on a noncomment line."""
    return (isinstance(marker, str) and 8 <= len(marker) <= 240
            and "\n" not in marker and
            any(marker in line and not line.lstrip().startswith(
                ("#", "//", "/*", "*", "<!--"))
                for line in source.splitlines()))


def _automatic_remedy_errors(entry: dict, ident: str, root: Path) -> list[str]:
    """Fail closed when a 'resolved' fix is test-only or not normally dispatched.

    This check verifies repository wiring plus existing executable regressions;
    it cannot by itself prove semantic runtime correctness or merge/deployment.
    """
    if ident < AUTO_REMEDY_CUTOVER:
        return []
    remedy = entry.get("automaticRemedy")
    if not isinstance(remedy, dict):
        return [ident + " lacks automatic runtime remedy"]
    allowed = {"runtimePath", "triggerMarker", "remedyMarker", "normalEntryPoints"}
    if set(remedy) != allowed:
        return [ident + " automatic runtime remedy has missing/unrecognized fields"]
    runtime_name = remedy.get("runtimePath")
    if (not isinstance(runtime_name, str)
        or not runtime_name.startswith(NORMAL_RUNTIME_PREFIXES)
        or not runtime_name.endswith((".py", ".js"))
        or _repo_file(root, runtime_name) is None):
        return [ident + " automatic runtime remedy lacks safe normal source path"]
    source = _repo_file(root, runtime_name).read_text(encoding="utf-8")
    trigger = remedy.get("triggerMarker")
    fix = remedy.get("remedyMarker")
    if not _active_marker(source, trigger):
        return [ident + " automatic trigger is absent from runtime source"]
    if not _active_marker(source, fix) or trigger == fix:
        return [ident + " automatic remedy is absent from runtime source"]
    dispatchers = remedy.get("normalEntryPoints")
    if not isinstance(dispatchers, list) or not dispatchers:
        return [ident + " automatic remedy has no normal entrypoint"]
    unique: set[str] = set()
    errors = []
    for dispatch in dispatchers:
        if not isinstance(dispatch, dict) or set(dispatch) != {"path", "marker"}:
            errors.append(ident + " malformed normal entrypoint declaration")
            continue
        path = dispatch.get("path")
        marker = dispatch.get("marker")
        if (not isinstance(path, str) or path in unique
            or not path.startswith(NORMAL_DISPATCH_PREFIXES)
            or not path.endswith((".html", ".js", ".py", ".yml", ".yaml"))
            or _repo_file(root, path) is None):
            errors.append(ident + " invalid normal entrypoint")
            continue
        unique.add(path)
        dispatch_source = _repo_file(root, path).read_text(encoding="utf-8")
        if not _active_marker(dispatch_source, marker):
            errors.append(ident + " normal entrypoint missing executable dispatcher")
            continue
        # The declared dispatch must specifically load/run THIS remedy, not
        # merely point at any unrelated valid script or HTML resource.
        if path.endswith(".html"):
            linked = (runtime_name.endswith(".js")
                      and marker == 'src="' + Path(runtime_name).name + '"')
        elif path.endswith((".yml", ".yaml")):
            linked = runtime_name in marker
        else:
            linked = path == runtime_name or Path(runtime_name).stem in marker
        if not linked:
            errors.append(ident + " normal entrypoint does not dispatch remedy runtime")
    return errors


def _normal_pipeline_recovery_errors(root: Path) -> list[str]:
    """Keep the owner's auto-recovery rule active in ordinary PR/push CI."""
    path = _repo_file(root, "docs/normal_pipeline_recovery_contract.json")
    decision = _repo_file(root, NORMAL_RECOVERY_DECISION)
    agents = _repo_file(root, "AGENTS.md")
    if path is None or decision is None:
        return ["normal pipeline recovery contract missing"]
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return ["normal pipeline recovery contract weakened"]
    expected = {
        "schemaVersion": 1,
        "decision": NORMAL_RECOVERY_DECISION,
        "principle": NORMAL_RECOVERY_PRINCIPLE,
        "requirements": {name: True for name in NORMAL_RECOVERY_REQUIREMENTS},
        "terminalExternalStatuses": list(NORMAL_RECOVERY_TERMINAL),
        "completionMeaning": "REAL_AUTHORIZED_EXECUTION_EVIDENCE_REQUIRED",
    }
    errors = []
    if policy != expected or NORMAL_RECOVERY_PRINCIPLE not in (
            decision.read_text(encoding="utf-8")):
        errors.append("normal pipeline recovery contract weakened")
    if agents is None or NORMAL_RECOVERY_DECISION not in agents.read_text(
            encoding="utf-8"):
        errors.append("normal pipeline recovery instructions missing")
    return errors


def verify(root: Path = ROOT) -> list[str]:
    root = root.resolve()
    errors: list[str] = _normal_pipeline_recovery_errors(root)
    registry_path = _repo_file(root, "docs/recurrence_registry.json")
    ledger_path = _repo_file(root, "docs/FAILURE_TO_FIX_LEDGER.md")
    workflow_path = _repo_file(root, ".github/workflows/validate.yml")
    if not all((registry_path, ledger_path, workflow_path)):
        return ["registry, ledger and validation workflow must exist"]
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError):
        return ["recurrence registry is not valid UTF-8 JSON"]
    if not isinstance(registry, dict):
        return ["recurrence registry must be a JSON object"]
    if type(registry.get("schemaVersion")) is not int or registry["schemaVersion"] != 1:
        errors.append("unsupported recurrence registry schema version")
    if registry.get("cutoverIncident") != CUTOVER:
        errors.append("recurrence cutover cannot be silently weakened")
    if registry.get("policyDecision") != "docs/decisions/0027-regression-immunity-and-recovery.md":
        errors.append("regression contract decision path mismatch")
    elif _repo_file(root, registry["policyDecision"]) is None:
        errors.append("approved contract decision is missing")

    workflow = workflow_path.read_text(encoding="utf-8")
    if STANDARD_PYTHON_CI not in workflow or GUARD_CI not in workflow:
        errors.append("full Python discovery and recurrence contract guard must run in CI")

    entries = registry.get("incidents")
    if not isinstance(entries, list):
        return errors + ["incidents must be a JSON list"]
    ledger = ledger_path.read_text(encoding="utf-8")
    ledger_counts = Counter(LEDGER_RE.findall(ledger))
    registered: set[str] = set()

    for position, entry in enumerate(entries):
        prefix = f"incident[{position}]"
        if not isinstance(entry, dict):
            errors.append(prefix + " must be an object")
            continue
        ident = entry.get("id")
        if not isinstance(ident, str) or not ID_RE.fullmatch(ident):
            errors.append(prefix + " has invalid incident ID")
            continue
        if ident in registered:
            errors.append(ident + " duplicates registry incident ID")
            continue
        registered.add(ident)
        earlier = {
            previous["id"]: previous
            for previous in entries[:position]
            if isinstance(previous, dict) and isinstance(previous.get("id"), str)
        }
        errors.extend(_family_history_errors(entry, ident, earlier))
        if ledger_counts[ident] == 0:
            errors.append(ident + " missing from failure-to-fix ledger")
        if ident >= CUTOVER and ledger_counts[ident] != 1:
            errors.append(ident + " must occur exactly once in new ledger entries")
        if not isinstance(entry.get("class"), str) or len(entry["class"]) < 3:
            errors.append(ident + " has no failure class")
        status = entry.get("status")
        if status not in ("resolved", "active"):
            errors.append(ident + " has unknown status")
            continue
        if status == "active":
            if not isinstance(entry.get("nextAction"), str) or len(entry["nextAction"].strip()) < 12:
                errors.append(ident + " active issue lacks actionable next step")
            continue
        # A test and ledger entry cannot close the same blocker if the
        # remedy is absent from the normal executable flow.
        errors.extend(_automatic_remedy_errors(entry, ident, root))
        cases = entry.get("regressions")
        if not isinstance(cases, list) or not cases:
            errors.append(ident + " resolved incident lacks regression cases")
            continue
        for case in cases:
            if not isinstance(case, dict):
                errors.append(ident + " regression entry must be an object")
                continue
            name, kind, marker = case.get("path"), case.get("kind"), case.get("marker")
            test_file = _repo_file(root, name)
            if (not isinstance(name, str) or not name.startswith("tests/test_") or
                    test_file is None):
                errors.append(ident + " references missing or unsafe regression test")
                continue
            if not isinstance(marker, str):
                errors.append(ident + " regression marker missing")
                continue
            source = test_file.read_text(encoding="utf-8")
            if kind == "python" and name.endswith(".py"):
                if not _python_has_test(source, marker):
                    errors.append(ident + " Python test method is missing: " + marker)
            elif kind == "javascript" and name.endswith(".js"):
                if not _js_has_assertion(source, marker):
                    errors.append(ident + " JS assertion is missing: " + marker)
                if f"node {name}" not in workflow:
                    errors.append(ident + " JS regression must run directly in CI: " + name)
            else:
                errors.append(ident + " has unsupported regression kind")

    for ident in sorted(REQUIRED_BASELINE - registered):
        errors.append(ident + " protected baseline recurrence entry was deleted")
    for ident in sorted(ledger_counts):
        if ident >= CUTOVER and ident not in registered:
            errors.append(ident + " new incident absent from recurrence registry")
    return errors


def main() -> int:
    problems = verify()
    if problems:
        for problem in problems[:50]:
            print("RECURRENCE CONTRACT FAIL:", problem)
        return 1
    print("Recurrence contract passed: registered incidents, executable tests and CI coverage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
