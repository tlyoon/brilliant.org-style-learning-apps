import os
import unittest
import warnings
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.coordinator.client import CoordinatorClient
from app_generator.errors import CoordinatorError
from app_generator.sources.google_drive import PDF_MIME, ResolvedDriveSource


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.request = None

    def post(self, url, json, timeout):
        self.request = {"url": url, "json": json, "timeout": timeout}
        return FakeResponse(self.payload)


class GeneratorCoordinatorTests(unittest.TestCase):
    def config(self):
        return SimpleNamespace(
            project_name="ExampleProject",
            coordinator_token_env="TEST_COORDINATOR_TOKEN",
            coordinator_url="https://script.google.com/macros/s/test/exec",
            coordinator_timeout_seconds=10,
            worker_id="pc-one",
            lease_seconds=3600,
            max_job_attempts=3,
        )

    def test_claim_sends_stable_drive_identity_and_returns_lease(self):
        source = ResolvedDriveSource(
            "drive-file-id", "source.pdf", "Serway_8_14/8/8.1/source.pdf",
            PDF_MIME, 100, "abc123", "8.1",
        )
        response = {
            "ok": True,
            "lease": {
                "job_key": source.job_key,
                "drive_file_id": source.file_id,
                "subchapter_id": "8.1",
                "relative_path": source.relative_path,
                "source_version": "abc123",
                "worker_id": "pc-one",
                "lease_expires_at": "2026-08-21T12:00:00.000Z",
                "attempt_count": 1,
            },
        }
        session = FakeSession(response)
        with patch.dict(os.environ, {"TEST_COORDINATOR_TOKEN": "secret"}, clear=False):
            lease = CoordinatorClient(self.config(), session=session).claim((source,))
        self.assertEqual(source.job_key, lease.job_key)
        self.assertEqual("claim", session.request["json"]["action"])
        self.assertEqual("secret", session.request["json"]["token"])
        self.assertEqual("ExampleProject", session.request["json"]["project_name"])
        self.assertEqual(source.file_id, session.request["json"]["candidates"][0]["drive_file_id"])

    def test_transient_redirect_404_retries_result_without_reposting_action(self):
        class RedirectFailure:
            status_code = 404
            url = "https://script.googleusercontent.com/macros/echo?result=temporary"

            def raise_for_status(self):
                raise RuntimeError("redirected endpoint returned 404")

        class FlakySession:
            def __init__(self):
                self.post_calls = 0
                self.get_calls = 0

            def post(self, url, json, timeout):
                del url, json, timeout
                self.post_calls += 1
                return RedirectFailure()

            def get(self, url, timeout):
                del url, timeout
                self.get_calls += 1
                return FakeResponse({"ok": True, "coordinator_version": 4})

        session = FlakySession()
        sleeps = []
        with patch.dict(os.environ, {"TEST_COORDINATOR_TOKEN": "secret"}, clear=False):
            CoordinatorClient(
                self.config(),
                session=session,
                sleeper=sleeps.append,
            ).health()

        self.assertEqual(1, session.post_calls)
        self.assertEqual(1, session.get_calls)
        self.assertEqual([1.0], sleeps)

    def test_transient_empty_redirect_result_is_retried_without_reposting_action(self):
        class EmptyRedirectResult:
            url = "https://script.googleusercontent.com/macros/echo?result=temporary"

            def raise_for_status(self):
                return None

            def json(self):
                raise ValueError("empty response")

        class FlakySession:
            def __init__(self):
                self.post_calls = 0
                self.get_calls = 0

            def post(self, url, json, timeout):
                del url, json, timeout
                self.post_calls += 1
                return EmptyRedirectResult()

            def get(self, url, timeout):
                del url, timeout
                self.get_calls += 1
                return FakeResponse({"ok": True, "coordinator_version": 4})

        session = FlakySession()
        sleeps = []
        with patch.dict(os.environ, {"TEST_COORDINATOR_TOKEN": "secret"}, clear=False):
            CoordinatorClient(
                self.config(),
                session=session,
                sleeper=sleeps.append,
            ).health()

        self.assertEqual(1, session.post_calls)
        self.assertEqual(1, session.get_calls)
        self.assertEqual([1.0], sleeps)

    def test_empty_post_response_replays_same_protocol_v4_request(self):
        class EmptyResponse:
            url = "https://script.google.com/macros/s/test/exec"

            def raise_for_status(self):
                return None

            def json(self):
                raise ValueError("empty response")

        class FlakySession:
            def __init__(self):
                self.requests = []

            def post(self, url, json, timeout):
                del url, timeout
                self.requests.append(dict(json))
                if len(self.requests) == 1:
                    return EmptyResponse()
                return FakeResponse({"ok": True, "coordinator_version": 4})

        session = FlakySession()
        sleeps = []
        with patch.dict(os.environ, {"TEST_COORDINATOR_TOKEN": "secret"}, clear=False):
            CoordinatorClient(
                self.config(),
                session=session,
                sleeper=sleeps.append,
            ).health()

        self.assertEqual(2, len(session.requests))
        self.assertEqual(session.requests[0]["request_id"], session.requests[1]["request_id"])
        self.assertEqual(4, session.requests[0]["protocol_version"])
        self.assertEqual([1.0], sleeps)

    def test_post_timeout_replays_same_protocol_v4_request(self):
        class FlakySession:
            def __init__(self):
                self.requests = []

            def post(self, url, json, timeout):
                del url, timeout
                self.requests.append(dict(json))
                if len(self.requests) == 1:
                    raise TimeoutError("coordinator timed out")
                return FakeResponse({"ok": True, "coordinator_version": 4})

        session = FlakySession()
        sleeps = []
        with patch.dict(os.environ, {"TEST_COORDINATOR_TOKEN": "secret"}, clear=False):
            CoordinatorClient(
                self.config(),
                session=session,
                sleeper=sleeps.append,
            ).health()

        self.assertEqual(2, len(session.requests))
        self.assertEqual(session.requests[0]["request_id"], session.requests[1]["request_id"])
        self.assertEqual([1.0], sleeps)

    def test_health_requires_the_live_coordinator_protocol_version(self):
        with patch.dict(os.environ, {"TEST_COORDINATOR_TOKEN": "secret"}, clear=False):
            current = CoordinatorClient(
                self.config(),
                session=FakeSession({"ok": True, "coordinator_version": 4}),
            )
            current.health()
            stale = CoordinatorClient(
                self.config(),
                session=FakeSession({"ok": True, "coordinator_version": 3}),
            )
            with self.assertRaisesRegex(CoordinatorError, "protocol is v3; v4 is required"):
                stale.health()

    def test_snapshot_parses_exact_target_failure_diagnostics(self):
        snapshot = CoordinatorClient._snapshot({
            "snapshot": {
                "total": 1,
                "counts": {"failed": 1},
                "next_candidate": None,
                "target_state": {
                    "status": "failed",
                    "attempt_count": 3,
                    "error_code": "LEASE_EXPIRED",
                },
            }
        })
        self.assertEqual("failed", snapshot.target_status)
        self.assertEqual(3, snapshot.target_attempt_count)
        self.assertEqual("LEASE_EXPIRED", snapshot.target_error_code)

    def test_retry_failed_sends_exact_source_identity_and_returns_audit_summary(self):
        source = ResolvedDriveSource(
            "drive-file-id", "source.pdf", "Serway_8_14/9/9.1/source.pdf",
            PDF_MIME, 100, "abc123", "9.1",
        )
        session = FakeSession({
            "ok": True,
            "status": "interrupted",
            "previous_attempt_count": 3,
            "previous_error_code": "LEASE_EXPIRED",
        })
        with patch.dict(os.environ, {"TEST_COORDINATOR_TOKEN": "secret"}, clear=False):
            result = CoordinatorClient(self.config(), session=session).retry_failed(source)
        self.assertEqual("retry_failed", session.request["json"]["action"])
        self.assertEqual(source.job_key, session.request["json"]["job_key"])
        self.assertEqual(source.file_id, session.request["json"]["drive_file_id"])
        self.assertEqual(source.source_version, session.request["json"]["source_version"])
        self.assertEqual("9.1", session.request["json"]["subchapter_id"])
        self.assertEqual("interrupted", result.status)
        self.assertEqual(3, result.previous_attempt_count)
        self.assertEqual("LEASE_EXPIRED", result.previous_error_code)

    def test_default_project_can_read_legacy_token_during_migration(self):
        config = self.config()
        config.project_name = "BrilliantContentGenerator"
        with patch.dict(os.environ, {"BRILLIANT_COORDINATOR_TOKEN": "legacy"}, clear=True):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                client = CoordinatorClient(config, session=FakeSession({"ok": True}))
        self.assertEqual("legacy", client.token)
        self.assertTrue(any("deprecated" in str(item.message) for item in caught))


if __name__ == "__main__":
    unittest.main()
