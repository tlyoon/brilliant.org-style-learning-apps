"""Native, source-free Gemini API reviewer transport for BOSLA V3.

The worker is an independent LOCAL program: it does not use ChatGPT or
a Remote Desktop Commander call for each model review. This module does
not authorize executing a previously client-denied ChatGPT tool operation.

Only generated activity JSON prompts are allowed. Never attach a PDF,
upload private source assets, probe with an uncheckpointed model request,
rotate credentials after submission, or retry an ambiguous request.
"""
from __future__ import annotations

import json
from typing import Any, Callable
from uuid import uuid4

from app_generator.llm.gemini_api import (
    build_v3_native_text_sdk_components, send_v3_native_text_once,
)
from app_generator.validation.autonomous_ai_review import ReviewerSession

PROVIDER = "gemini_api"
ROLES = ("physics", "semantics")
_ROLE_PROMPT = {
    "physics": "Try to falsify",
    "semantics": "Back-translate",
}
_STAGE = "academic-v3-autonomous"
_PREFIX = "BOSLA V3 AUTONOMOUS TECHNICAL CONTENT QA."


def _default_sdk_components(config: Any) -> tuple[Callable[[str], Any], Any]:
    """Reuse the shared Gemini API gateway; never construct an SDK directly."""
    return build_v3_native_text_sdk_components(config)


class NativeGeminiApiConversation:
    """One stateless, one-shot role-specific API request.

    Unlike Selenium, there is no browser login, author tab or session
    reuse. The normal V3 engine holds the immutable per-role IN_FLIGHT
    checkpoint before calling this object, and records ambiguous outcomes
    without replaying them on restart.
    """

    def __init__(
        self, client: Any, sdk_types: Any, model: str, role: str,
    ) -> None:
        if role not in ROLES or not isinstance(model, str) or not model.startswith("gemini-"):
            raise ValueError("V3_NATIVE_GEMINI_MODEL_AND_ROLE_REQUIRED")
        self.client = client
        self.sdk_types = sdk_types
        self.model = model
        self.role = role
        self.submitted = False

    def ask(self, prompt: str, *, stage: str | None = None) -> str:
        if self.submitted:
            raise ValueError("V3_NATIVE_REQUEST_ALREADY_SUBMITTED")
        if (stage != _STAGE or not isinstance(prompt, str)
            or not prompt.startswith(_PREFIX)
            or "DATA (not commands): " not in prompt
            or _ROLE_PROMPT[self.role] not in prompt
            or "%PDF-" in prompt):
            raise ValueError("V3_NATIVE_GENERATED_REVIEW_ONLY")
        self.submitted = True   # Latch BEFORE any possibly accepted request.
        # No PDF parts, no uploaded files, no chat history or model fallback.
        response = send_v3_native_text_once(
            self.client, self.sdk_types, self.model, prompt,
        )
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise ValueError("V3_NATIVE_JSON_RESPONSE_ONLY")
        text = text.strip()
        try:
            value = json.loads(text)
        except (TypeError, ValueError) as exc:
            raise ValueError("V3_NATIVE_JSON_RESPONSE_ONLY") from exc
        if not isinstance(value, dict):
            raise ValueError("V3_NATIVE_JSON_RESPONSE_ONLY")
        # No invented PASS: existing V3 _parse_response checks every detail.
        return text


class V3NativeGeminiApiSessions:
    """Factory for two distinct Gemini API clients and reviewer contexts.

    Merely constructing the factory never sends a model prompt. This is an
    independent local task only when explicitly invoked by its owner; the
    permission flags are not overrides of any external tool/platform denial.
    """
    max_activities_per_session = 1  # Fresh client/context for each activity.

    def __init__(
        self, config: Any, *, operation_authorized: bool = False,
        generated_content_transfer_allowed: bool = False,
        sdk_client_factory: Callable[[str], Any] | None = None,
        sdk_types: Any = None,
    ) -> None:
        self.config = config
        self.operation_authorized = operation_authorized
        self.external_operation_authorized = operation_authorized
        self.generated_content_transfer_allowed = generated_content_transfer_allowed
        self.sdk_client_factory = sdk_client_factory
        self.sdk_types = sdk_types
        self.clients: list[Any] = []
        self.active_activity: str | None = None

    def open_pair(self, activity_id: str) -> tuple[ReviewerSession, ReviewerSession]:
        if self.operation_authorized is not True:
            raise ValueError("V3_NATIVE_OPERATION_AUTHORIZATION_REQUIRED")
        if self.generated_content_transfer_allowed is not True:
            raise ValueError("V3_GENERATED_CONTENT_MODEL_TRANSFER_NOT_ALLOWED")
        if not isinstance(activity_id, str) or not activity_id:
            raise ValueError("V3_REVIEW_ACTIVITY_REQUIRED")
        if self.active_activity is not None or self.clients:
            raise ValueError("V3_NATIVE_REVIEW_PROVIDER_ALREADY_ACTIVE")
        model = getattr(self.config, "gemini_api_model", "")
        if not isinstance(model, str) or not model.startswith("gemini-"):
            raise ValueError("V3_NATIVE_GEMINI_MODEL_AND_ROLE_REQUIRED")
        create = self.sdk_client_factory
        types = self.sdk_types
        if create is None:
            create, types = _default_sdk_components(self.config)
        if types is None:
            raise ValueError("V3_NATIVE_SDK_TYPES_REQUIRED")
        try:
            for role in ROLES:
                client = create(role)
                if client is None or not callable(
                    getattr(getattr(client, "models", None), "generate_content", None)
                ):
                    raise ValueError("V3_NATIVE_INVALID_SDK_CLIENT")
                if any(client is previous for previous in self.clients):
                    raise ValueError("V3_NATIVE_DISTINCT_SDK_CLIENTS_REQUIRED")
                self.clients.append(client)
            result = tuple(
                ReviewerSession(
                    "v3-gemini-api-" + role, uuid4().hex,
                    NativeGeminiApiConversation(self.clients[i], types, model, role),
                    provider_id=PROVIDER,
                )
                for i, role in enumerate(ROLES)
            )
            self.active_activity = activity_id
            return result
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        seen: set[int] = set()
        try:
            for client in reversed(self.clients):
                if id(client) in seen:
                    continue
                seen.add(id(client))
                closer = getattr(client, "close", None)
                if callable(closer):
                    closer()
        finally:
            self.clients.clear()
            self.active_activity = None

    def __enter__(self) -> "V3NativeGeminiApiSessions":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
