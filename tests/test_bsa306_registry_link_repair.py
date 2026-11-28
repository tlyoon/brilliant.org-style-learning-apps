"""BSA306 executable historical-link repair: exact and fail closed."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase

from app_generator.runtime.v3_staged_incident_link_repair import (
    repair_staged_known_incident_links,
)

def _run(repo,*args):
    p=subprocess.run(["git",*args],cwd=repo,capture_output=True,
                     check=False,timeout=30)
    if p.returncode:
        raise AssertionError(p.stderr.decode("utf8","replace"))

def _records():
    ids=[
      "BSA-20261127-289","BSA-20261127-294",
      "BSA-20261128-299","BSA-20261128-300",
      "BSA-20261128-301","BSA-20261128-302",
    ]
    a=[{"id":i,"relatedIncidentIds":[]} for i in ids]
    a[3]["relatedIncidentIds"]=[
        "BSA-20261128-299","BSA-20261128-294"]
    a[5]["relatedIncidentIds"]=[
        "BSA-20261128-301","BSA-20261128-289"]
    return {"schemaVersion":1,"incidents":a}

class KnownIncidentLinkRecovery(TestCase):
    def test_repairs_two_known_wrong_dates_then_idempotently_passes(self):
        with TemporaryDirectory() as td:
            repo=Path(td)
            _run(repo,"init","-q")
            path=repo/"docs"/"recurrence_registry.json"
            path.parent.mkdir()
            path.write_text(json.dumps(_records(),indent=2)+"\n",encoding="utf8")
            _run(repo,"add","--all")
            decision=repair_staged_known_incident_links(repo)
            self.assertEqual(decision["status"],
                             "BSA306_EXACT_HISTORICAL_LINKS_REPAIRED")
            self.assertEqual(decision["fixed"],[
                "BSA-20261128-300","BSA-20261128-302"])
            self.assertFalse(decision["academicPASS"])
            after=json.loads(path.read_text("utf8"))
            rows={x["id"]:x for x in after["incidents"]}
            self.assertIn("BSA-20261127-294",
                          rows["BSA-20261128-300"]["relatedIncidentIds"])
            self.assertIn("BSA-20261127-289",
                          rows["BSA-20261128-302"]["relatedIncidentIds"])
            self.assertEqual(repair_staged_known_incident_links(repo)["status"],
                             "BSA306_ALREADY_VALID")
            staged=subprocess.run(["git","diff","--cached","--name-only"],
                                  cwd=repo,capture_output=True,text=True)
            self.assertIn("docs/recurrence_registry.json",staged.stdout)

    def test_missing_historical_incident_does_not_auto_forge(self):
        with TemporaryDirectory() as td:
            repo=Path(td)
            _run(repo,"init","-q")
            path=repo/"docs"/"recurrence_registry.json"
            path.parent.mkdir()
            source=_records()
            source["incidents"]=[
                r for r in source["incidents"]
                if r["id"]!="BSA-20261127-294"]
            raw=json.dumps(source,indent=2)+"\n"
            path.write_text(raw,encoding="utf8")
            _run(repo,"add","--all")
            with self.assertRaisesRegex(ValueError,
                                        "UNKNOWN_HISTORICAL_LINK_PATTERN"):
                repair_staged_known_incident_links(repo)
            self.assertEqual(path.read_text("utf8"),raw)

    def test_unstaged_or_wrong_pattern_never_changed(self):
        with TemporaryDirectory() as td:
            repo=Path(td)
            _run(repo,"init","-q")
            path=repo/"docs"/"recurrence_registry.json"
            path.parent.mkdir()
            wrong=_records()
            wrong["incidents"][3]["relatedIncidentIds"]=[
                "BSA-20261128-299","BSA-20261128-199"]
            raw=json.dumps(wrong)+"\n"
            path.write_text(raw,encoding="utf8")
            self.assertEqual(repair_staged_known_incident_links(repo)["status"],
                             "BSA306_NO_STAGED_REGISTRY")
            _run(repo,"add","--all")
            with self.assertRaisesRegex(ValueError,"UNKNOWN_HISTORICAL"):
                repair_staged_known_incident_links(repo)
            self.assertEqual(path.read_text("utf8"),raw)
