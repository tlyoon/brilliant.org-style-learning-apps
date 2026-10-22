import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app_generator.coordinator.drive import DriveCoordinatorClient, _Marker


class _SharedDrive:
    def __init__(self):
        self.rows = {}
        self.payloads = {}
        self.sequence = 0
        self.base = datetime(2026, 10, 22, 4, 0, tzinfo=UTC)

    @property
    def now(self):
        return self.base + timedelta(milliseconds=self.sequence)

    def create(self, kind, job_key, payload, *, attempt_id="", attempt_no=0):
        self.sequence += 1
        file_id = f"{kind}-{self.sequence:04d}"
        created = self.now
        marker = _Marker(
            file_id=file_id,
            kind=kind,
            job_key=job_key,
            attempt_id=attempt_id,
            created_at=created,
            modified_at=created,
            attempt_no=attempt_no,
        )
        self.rows[file_id] = marker
        self.payloads[file_id] = dict(payload)
        return {"id": file_id}

    def delete(self, file_id):
        self.rows.pop(file_id, None)
        self.payloads.pop(file_id, None)

    def update(self, file_id, payload):
        self.sequence += 1
        marker = self.rows[file_id]
        modified = self.now
        self.rows[file_id] = _Marker(
            file_id=marker.file_id,
            kind=marker.kind,
            job_key=marker.job_key,
            attempt_id=marker.attempt_id,
            created_at=marker.created_at,
            modified_at=modified,
            attempt_no=marker.attempt_no,
        )
        self.payloads[file_id] = dict(payload)
        return {
            "id": file_id,
            "modifiedTime": modified.isoformat().replace("+00:00", "Z"),
        }, self.now

    def markers(self, job_key, kind=None):
        items = [
            marker
            for marker in self.rows.values()
            if marker.job_key == job_key and (kind is None or marker.kind == kind)
        ]
        return sorted(items, key=lambda item: (item.created_at, item.file_id)), self.now


class _MemoryDriveCoordinator(DriveCoordinatorClient):
    def __init__(self, shared, worker_id):
        self.shared = shared
        self.project_name = "production-gate"
        self.worker_id = worker_id
        self.lease_seconds = 60
        self.max_job_attempts = 3
        self.timeout = 30
        self.sleeper = lambda _: None

    def _create_json(
        self, kind, job_key, payload, *, parent_id, attempt_id="", attempt_no=0
    ):
        if not parent_id:
            raise AssertionError("production-gate source must retain its parent folder")
        return self.shared.create(
            kind, job_key, payload, attempt_id=attempt_id, attempt_no=attempt_no
        )

    def _delete(self, file_id):
        self.shared.delete(file_id)

    def _marker_rows(self, job_key, *, kind=None):
        return self.shared.markers(job_key, kind)

    def _read_json(self, file_id):
        return dict(self.shared.payloads[file_id])

    def _update_json(self, file_id, payload):
        return self.shared.update(file_id, payload)


def _source(index):
    section = f"10.{index}"
    return SimpleNamespace(
        job_key=f"job-{section}",
        file_id=f"source-{section}",
        subchapter_id=section,
        relative_path=f"10/{section}/source.pdf",
        source_version=f"corpus-{section}",
        parent_folder_id=f"folder-{section}",
    )


class ThreePcProductionGateTests(unittest.TestCase):
    def test_three_workers_distribute_unique_jobs_and_recover_failed_checkpoint(self):
        shared = _SharedDrive()
        sources = tuple(_source(index) for index in (1, 2, 3))
        dell = _MemoryDriveCoordinator(shared, "dell-115")
        hp = _MemoryDriveCoordinator(shared, "hp")
        yoga = _MemoryDriveCoordinator(shared, "yoga6")

        dell_lease = dell.claim_auto(sources)
        hp_lease = hp.claim_auto(sources)
        yoga_lease = yoga.claim_auto(sources)

        self.assertEqual(
            {"10.1", "10.2", "10.3"},
            {dell_lease.subchapter_id, hp_lease.subchapter_id, yoga_lease.subchapter_id},
        )
        self.assertEqual(
            3,
            len({dell_lease.lease_token, hp_lease.lease_token, yoga_lease.lease_token}),
        )

        dell.checkpoint_save(
            dell_lease,
            "source-analysis",
            {"sectionTitle": "Recovered across PCs", "source": "controlled"},
        )
        self.assertEqual(
            "interrupted",
            dell.mark_failed(
                dell_lease,
                error_code="GEMINI_API_ERROR",
                error_message="synthetic production-gate failure",
            ),
        )

        recovery = _MemoryDriveCoordinator(shared, "hp-recovery")
        recovered_lease = recovery.claim_auto(sources)
        self.assertEqual("10.1", recovered_lease.subchapter_id)
        self.assertEqual(2, recovered_lease.attempt_count)
        self.assertEqual(
            {
                "source-analysis": {
                    "sectionTitle": "Recovered across PCs",
                    "source": "controlled",
                }
            },
            recovery.checkpoint_load(recovered_lease),
        )

        active_tokens = []
        for source in sources:
            active, _ = recovery._active_claims(source.job_key)
            active_tokens.extend(item.file_id for item in active)
        self.assertEqual(len(active_tokens), len(set(active_tokens)))
        self.assertNotIn(dell_lease.lease_token, active_tokens)


if __name__ == "__main__":
    unittest.main()
