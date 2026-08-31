"""Durable parsed-stage checkpoints stored by the shared coordinator."""

from __future__ import annotations

from app_generator.coordinator.client import CoordinatorClient, JobLease
from app_generator.runtime.run_context import RunContext


class CoordinatorCheckpointStore:
    def __init__(self, client: CoordinatorClient, lease: JobLease) -> None:
        self.client = client
        self.lease = lease

    def restore_into(self, context: RunContext) -> int:
        stages = self.client.checkpoint_load(self.lease)
        context.restore_stages(stages)
        return len(stages)

    def save(self, name: str, document: object) -> None:
        self.client.checkpoint_save(self.lease, name, document)

    def delete(self, name: str) -> None:
        self.client.checkpoint_delete(self.lease, name)

    def clear(self) -> None:
        self.client.checkpoint_clear(self.lease)
