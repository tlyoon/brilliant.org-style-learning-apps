import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app_generator.coordinator.client import JobLease
from app_generator.coordinator.drive import DriveCoordinatorClient, _JobState, _Marker
from app_generator.errors import LeaseLostError, NoAvailableJob


NOW = datetime(2026, 9, 22, 10, 0, tzinfo=UTC)


def client():
    item = object.__new__(DriveCoordinatorClient)
    item.project_name = "test-project"
    item.worker_id = "pc-a"
    item.lease_seconds = 60
    item.max_job_attempts = 3
    item.timeout = 30
    item.sleeper = lambda _: None
    item.state_folder_id = "state-folder"
    return item


def source(job_key="job-1"):
    return SimpleNamespace(
        job_key=job_key,
        file_id="source-file",
        subchapter_id="8.2",
        relative_path="8/8.2/source.pdf",
        source_version="corpus-v1",
        parent_folder_id="topic-folder",
    )


def marker(file_id, *, created_offset=0, modified_offset=0, attempt="a", attempt_no=1, kind="claim"):
    return _Marker(
        file_id=file_id,
        kind=kind,
        job_key="job-1",
        attempt_id=attempt,
        created_at=NOW + timedelta(seconds=created_offset),
        modified_at=NOW + timedelta(seconds=modified_offset),
        attempt_no=attempt_no,
    )


class DriveCoordinationTests(unittest.TestCase):
    def test_three_active_claims_elect_earliest_server_created_time_then_file_id(self):
        c = client()
        rows = [
            marker("z-last", created_offset=2),
            marker("b-tie", created_offset=0),
            marker("a-tie", created_offset=0),
        ]
        with patch.object(c, "_marker_rows", return_value=(rows, NOW + timedelta(seconds=10))):
            active, _ = c._active_claims("job-1")
        self.assertEqual(["a-tie", "b-tie", "z-last"], [item.file_id for item in active])

    def test_losing_concurrent_claim_deletes_only_its_own_marker(self):
        c = client()
        winner = marker("other", created_offset=0, attempt="other")
        with patch.object(c, "_job_state", return_value=_JobState("queued", 0)), \
             patch.object(c, "_create_json", return_value={"id": "mine"}), \
             patch.object(c, "_active_claims", return_value=([winner], NOW)), \
             patch.object(c, "_delete") as delete:
            with self.assertRaises(NoAvailableJob):
                c.claim_auto((source(),))
        delete.assert_called_once_with("mine")

    def test_winning_claim_must_win_two_consecutive_elections(self):
        c = client()
        mine = marker("mine", attempt="mine")
        with patch.object(c, "_job_state", return_value=_JobState("queued", 0)), \
             patch.object(c, "_create_json", return_value={"id": "mine"}), \
             patch.object(c, "_active_claims", side_effect=[([mine], NOW), ([mine], NOW)]):
            lease = c.claim_auto((source(),))
        self.assertEqual("mine", lease.lease_token)
        self.assertEqual("mine", lease.attempt_id)

    def test_expired_claim_cannot_be_resurrected_by_heartbeat(self):
        c = client()
        lease = JobLease(
            job_key="job-1", drive_file_id="source-file", subchapter_id="8.2",
            relative_path="8/8.2/source.pdf", source_version="corpus-v1",
            worker_id="pc-a", lease_expires_at="", attempt_count=1,
            lease_token="mine", attempt_id="mine",
        )
        with patch.object(c, "_active_claims", return_value=([], NOW)), \
             patch.object(c, "_update_json") as update:
            with self.assertRaises(LeaseLostError):
                c.heartbeat(lease)
        update.assert_not_called()

    def test_checkpoint_replay_survives_worker_attempt_changes(self):
        c = client()
        events = [
            marker("1", created_offset=1, attempt="old", kind="checkpoint"),
            marker("2", created_offset=2, attempt="old", kind="checkpoint"),
            marker("3", created_offset=3, attempt="new", attempt_no=2, kind="checkpoint"),
            marker("4", created_offset=4, attempt="new", attempt_no=2, kind="checkpoint"),
        ]
        payloads = {
            "1": {"operation": "save", "stage": "source-analysis", "document": {"v": 1}},
            "2": {"operation": "save", "stage": "activity-plan", "document": {"v": 1}},
            "3": {"operation": "delete", "stage": "activity-plan"},
            "4": {"operation": "save", "stage": "activity-plan", "document": {"v": 2}},
        }
        lease = SimpleNamespace(job_key="job-1")
        with patch.object(c, "_marker_rows", return_value=(events, NOW)), \
             patch.object(c, "_read_json", side_effect=lambda file_id: payloads[file_id]):
            stages = c.checkpoint_load(lease)
        self.assertEqual({"source-analysis": {"v": 1}, "activity-plan": {"v": 2}}, stages)

    def test_retry_event_resets_terminal_attempt_budget(self):
        c = client()
        failed = _JobState("failed", 3, "GEMINI_TRANSIENT_ERROR")
        with patch.object(c, "_job_state", return_value=failed), \
             patch.object(c, "_create_json") as create:
            result = c.retry_failed(source())
        self.assertEqual("interrupted", result.status)
        self.assertEqual(3, result.previous_attempt_count)
        self.assertEqual("GEMINI_TRANSIENT_ERROR", result.previous_error_code)
        self.assertEqual("retry", create.call_args.args[0])

    def test_failed_attempt_is_counted_after_claim_file_is_released(self):
        c = client()
        failure = marker("failure", attempt="same", attempt_no=2, kind="failure")
        with patch.object(c, "_marker_rows") as rows, \
             patch.object(c, "_latest_retry_time", return_value=None):
            rows.side_effect = lambda job_key, kind=None: (([], NOW) if kind == "claim" else ([failure], NOW))
            attempts = c._attempt_markers("job-1")
        self.assertEqual(1, len(attempts))
        self.assertEqual(2, attempts[0].attempt_no)


if __name__ == "__main__":
    unittest.main()
