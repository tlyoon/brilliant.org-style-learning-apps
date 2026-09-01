"""Versioned contract shared by workers and the managed Apps Script coordinator."""

from __future__ import annotations

REQUIRED_COORDINATOR_VERSION = 2
MANAGED_COORDINATOR_FILE_NAME = "learning-app-coordinator-runtime.json"
MANAGED_BY = "learning-app-content-generator"
MANAGED_WORKFLOW = "ensure-coordinator.yml"
ADMIN_SECRET_NAME = "COORDINATOR_ADMIN_TOKEN_JSON"
