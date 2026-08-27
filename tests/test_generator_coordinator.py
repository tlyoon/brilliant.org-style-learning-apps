import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app_generator.coordinator.client import CoordinatorClient
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


if __name__ == "__main__":
    unittest.main()
