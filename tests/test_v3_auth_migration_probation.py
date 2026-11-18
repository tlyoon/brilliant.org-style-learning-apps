"""BSA-199: real-API migration gate, exact old-claim no-replay stress tests.

Provider calls are never faked as genuine PASS. In a disposable checkpoint,
create two old source-bound, statusless ClientError roles plus the old
original ValueError role. The source-free shared capacity gate must remain
STOP unless exact hashes are explicitly passed through the narrow migration
probation path. Later unrelated unknowns or actual denials still STOP.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from app_generator.validation.v3_server_error_recovery import provider_capacity_gate


class MigratedAuthProbationTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.private=Path(t.name)
        self.parent="1"*64
        self.slice="2"*64
        self.extra="3"*64
        self.sourceProgress=[{"packageSha256":self.parent}]
        self.old=self.store(self.parent,5,0,"ValueError")
        self.one=self.store(self.slice,0,0,"ClientError")
        self.two=self.store(self.slice,0,1,"ClientError")
        self.orig=(self.parent,self.old[1])
        self.witness=((self.slice,self.one[1],0),
                      (self.slice,self.two[1],1))

    def store(self, digest, index, role, reason, *,
              state="AMBIGUOUS", activity="test-original-activity",
              http=None):
        path=(self.private/("v3-generated-"+digest)/"batches"/
              f"v3-review-{digest[:12]}-{index:03d}-{role}.json")
        path.parent.mkdir(parents=True,exist_ok=True)
        data={"packageSha256":digest,"roleIndex":role,
              "activityId":activity,"providerId":"gemini_api",
              "state":state,"reasonCode":reason}
        if http is not None:
            data["providerHttpStatus"]=http
            data["providerFailureClass"]="AUTH_OR_PROJECT_DENIED"
        raw=json.dumps(data,sort_keys=True).encode("utf8")
        path.write_bytes(raw)
        return path,sha256(raw).hexdigest()

    def gate(self, migrated=(), original=None):
        return provider_capacity_gate(
            self.private,self.sourceProgress,
            additional_package_shas=(self.slice,self.extra),
            quarantined_historical_claim=original,
            quarantined_migrated_clienterrors=migrated)

    def test_default_never_quarantines_unclassified_submitted_roles(self):
        self.assertEqual(self.gate()["status"],
                         "STOP_UNCLASSIFIED_PROVIDER_REVIEW")
        self.assertEqual(self.gate(original=self.orig)["status"],
                         "STOP_UNCLASSIFIED_PROVIDER_REVIEW")

    def test_exact_two_known_roles_only_under_narrow_witness(self):
        status=self.gate(self.witness,self.orig)
        self.assertEqual(status["status"],
                         "READY_RESTRICTED_HISTORICAL_QUARANTINE")
        self.assertEqual(status["historicalUnrecoverableClaimsQuarantined"],1)
        self.assertEqual(status["migratedUnreconciledClientErrorsQuarantined"],2)
        self.assertEqual(self.gate()["status"],
                         "STOP_UNCLASSIFIED_PROVIDER_REVIEW")
        for file in (self.old[0],self.one[0],self.two[0]):
            self.assertEqual(json.loads(file.read_text())["state"],
                             "AMBIGUOUS")

    def test_a_third_unknown_after_migration_reopens_stop(self):
        self.store(self.extra,0,0,"ClientError",activity="NEW_UNCLASSIFIED")
        self.assertEqual(self.gate(self.witness,self.orig)["status"],
                         "STOP_UNCLASSIFIED_PROVIDER_REVIEW")

    def test_explicit_project_denial_stops_even_with_exact_witness(self):
        self.store(self.extra,0,0,"ClientError",http=403)
        self.assertEqual(self.gate(self.witness,self.orig)["status"],
                         "BLOCKED_EXTERNAL_REVIEW_TRANSPORT")

    def test_corruption_of_either_historical_role_stops(self):
        for file in (self.one[0],self.two[0]):
            with self.subTest(role=file.name):
                old=file.read_bytes()
                file.write_bytes(old+b" ")
                with self.assertRaisesRegex(
                        ValueError,"MIGRATION_WITNESS_MISMATCH"):
                    self.gate(self.witness,self.orig)
                file.write_bytes(old)

    def test_known_status_code_cannot_be_laundered_as_old_unknown(self):
        old=self.two[0].read_bytes()
        role=json.loads(old)
        role["providerHttpStatus"]=403
        self.two[0].write_text(json.dumps(role))
        with self.assertRaisesRegex(ValueError,"MIGRATION_WITNESS_MISMATCH"):
            self.gate(self.witness,self.orig)
        self.two[0].write_bytes(old)

    def test_incomplete_wrong_role_or_reordered_witness_rejected(self):
        for candidate in ((self.witness[0],),
                          (self.witness[0],self.witness[0]),
                          ((self.slice,self.one[1],0),
                           (self.slice,self.two[1],0))):
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(
                        ValueError,"MIGRATION_WITNESS_INVALID"):
                    self.gate(candidate,self.orig)

    def test_post_migration_progress_requires_two_actual_complete_sha_roles(self):
        # BSA-200 real-shaped restart fixture. Explicitly synthetic role
        # hashes are injected only into this isolated verification helper;
        # the production planner uses pinned hashes from live Yoga6.
        from app_generator.runtime.v3_provider_restoration import (
            _verified_restored_index7, _PARENT, _RESTORED_SLICE7,
        )
        folder=(self.private/("v3-generated-"+_RESTORED_SLICE7)/"batches")
        folder.mkdir(parents=True,exist_ok=True)
        files=[]
        hashes=[]
        for role_index in (0,1):
            file=folder/f"v3-review-{_RESTORED_SLICE7[:12]}-000-{role_index}.json"
            record={
                "packageSha256":_RESTORED_SLICE7,
                "roleIndex":role_index,
                "state":"COMPLETE","providerId":"gemini_api",
                "activityId":"mcq-chal-hollow-geometry-cm",
                "responseSha256":"c"*64,
            }
            raw=json.dumps(record,sort_keys=True).encode("utf8")
            file.write_bytes(raw)
            files.append(file)
            hashes.append(sha256(raw).hexdigest())
        tail={
            "sourcePackageSha256":_PARENT,
            "next":{"index":8},
            "supplemental":{"passed":1,"uncertain":1,"failed":0,"reserved":0},
            "rows":[{"index":7,"slicePackageSha256":_RESTORED_SLICE7,
                     "state":"GENUINE_SUPPLEMENTAL_CONSENSUS_PASS"}],
        }
        expected=tuple(hashes)
        self.assertTrue(_verified_restored_index7(
            self.private,tail,expected_role_shas=expected))
        # Old singleton or altered source-bound role never proves readiness.
        old=files[1].read_bytes()
        files[1].write_bytes(old+b" ")
        self.assertFalse(_verified_restored_index7(
            self.private,tail,expected_role_shas=expected))
        files[1].write_bytes(old)
        bad={**tail,"rows":[{**tail["rows"][0],
                            "state":"SUPPLEMENTAL_UNCERTAIN_NO_REPLAY"}]}
        self.assertFalse(_verified_restored_index7(
            self.private,bad,expected_role_shas=expected))
        for changes in (
            {"next":{"index":7}},
            {"supplemental":{**tail["supplemental"],"uncertain":2}},
            {"supplemental":{**tail["supplemental"],"failed":1}},
            {"sourcePackageSha256":"f"*64},
        ):
            self.assertFalse(_verified_restored_index7(
                self.private,{**tail,**changes},expected_role_shas=expected))

    def test_migrated_auth_witness_without_new_role_auth_is_not_broad_gate(self):
        # Scope protection is enforced at the real, exact-source
        # plan_authorized_independent_recovery_trial() entrypoint, which
        # defaults to STOP when no metadata / AQ migration witness exists.
        from app_generator.runtime.v3_provider_restoration import (
            _verified_migrated_auth_keys,
        )
        self.assertEqual(_verified_migrated_auth_keys(
            self.private,None,7),())
        self.assertEqual(_verified_migrated_auth_keys(
            self.private,{"status":"MODEL_GENERATION_ACTION_DECLARED_QUOTA_UNVERIFIED",
                          "paidModelCalls":0,"sourceFree":True},6),())


if __name__=="__main__":
    unittest.main()
