"""Live-health gating for repository-managed coordinator infrastructure."""

from __future__ import annotations

import time
from collections.abc import Callable

from app_generator.config import GeneratorConfig
from app_generator.coordinator.client import CoordinatorClient
from app_generator.coordinator.managed import ensure_managed_coordinator, trigger_managed_deployment
from app_generator.errors import CoordinatorError


def _is_managed(config: GeneratorConfig) -> bool:
    return str(getattr(config, "coordinator_management", "external")).strip().casefold() == "github_actions"


def ensure_coordinator_ready(
    config: GeneratorConfig,
    *,
    sleeper: Callable[[float], None] = time.sleep,
) -> GeneratorConfig:
    """Return a live coordinator config, repairing a current-but-unhealthy managed deployment.

    `ensure_managed_coordinator` handles missing/stale runtime metadata. This second gate
    verifies the actual web app before any queue operation. If a managed deployment is
    current in metadata but unhealthy, every PC may request repair, but GitHub Actions
    serializes those equivalent requests under the project-scoped concurrency group.
    """

    ready = ensure_managed_coordinator(config)
    try:
        CoordinatorClient(ready).health(require_checkpoints=True)
        return ready
    except CoordinatorError as first_error:
        if not _is_managed(config):
            raise
        print("COORDINATOR_REPAIR: managed metadata is current but live health failed; requesting serialized repair.")
        trigger_managed_deployment(config)
        deadline = time.monotonic() + config.coordinator_ensure_timeout_seconds
        last_error: CoordinatorError = first_error
        while time.monotonic() < deadline:
            sleeper(5.0)
            # The managed deployment retains its stable URL/token; re-discovery also
            # picks up a newly created runtime record if the repair had to replace it.
            try:
                ready = ensure_managed_coordinator(config, deploy_if_needed=False)
                CoordinatorClient(ready).health(require_checkpoints=True)
                print("COORDINATOR_READY: managed coordinator passed live health verification.")
                return ready
            except CoordinatorError as exc:
                last_error = exc
        raise CoordinatorError(
            "Managed coordinator remained unhealthy after serialized repair; inspect the "
            f"Ensure managed coordinator workflow. Last error: {last_error}"
        ) from last_error
