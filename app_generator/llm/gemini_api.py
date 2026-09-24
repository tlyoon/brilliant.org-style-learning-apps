"""Gemini API backend for deterministic PDF-grounded generation."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

from app_generator.config import GeneratorConfig
from app_generator.errors import AuthenticationRequired, GeminiApiError, ResponseContractError, TransientGeminiError

VERTEX_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


def _write_token_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload.rstrip() + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _client_project_id(client_file: Path) -> str:
    try:
        document = json.loads(client_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    for container in ("installed", "web"):
        value = document.get(container, {}) if isinstance(document, dict) else {}
        project_id = value.get("project_id") if isinstance(value, dict) else None
        if project_id:
            return str(project_id)
    return ""


def build_gemini_sdk_client(config: GeneratorConfig) -> Any:
    """Create a Gemini Developer API-key client or OAuth Vertex AI client."""

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise AuthenticationRequired(
            "Gemini API dependencies are missing. Run: python -m pip install -e ."
        ) from exc

    timeout_ms = config.gemini_api_timeout_seconds * 1000
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        return genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=timeout_ms),
        )

    if not config.drive_oauth_client_file.is_file():
        raise AuthenticationRequired(
            "Gemini API needs GOOGLE_API_KEY/GEMINI_API_KEY or the configured desktop OAuth client file: "
            f"{config.drive_oauth_client_file}"
        )
    project_id = _client_project_id(config.drive_oauth_client_file)
    if not project_id:
        raise AuthenticationRequired("The configured desktop OAuth client does not identify a Google Cloud project")

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise AuthenticationRequired("Google OAuth dependencies are missing. Run: python -m pip install -e .") from exc

    credentials = None
    token_file = config.gemini_api_token_file
    if token_file.is_file():
        try:
            stored = json.loads(token_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            stored = {}
        stored_scopes = stored.get("scopes", []) if isinstance(stored, dict) else []
        if isinstance(stored_scopes, str):
            stored_scopes = stored_scopes.split()
        if VERTEX_SCOPE in stored_scopes:
            credentials = Credentials.from_authorized_user_file(str(token_file), scopes=[VERTEX_SCOPE])
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(config.drive_oauth_client_file), scopes=[VERTEX_SCOPE]
        )
        print(
            "Authorize Gemini Vertex API access in the browser window. "
            f"Use {config.oauth_login}. This token is stored only at {token_file}."
        )
        credentials = flow.run_local_server(
            host="127.0.0.1",
            port=0,
            open_browser=True,
            authorization_prompt_message="Open this URL if the browser did not open:\n{url}",
            success_message="Gemini Vertex API authorization completed. You may close this tab.",
        )
    _write_token_atomic(token_file, credentials.to_json())
    return genai.Client(
        vertexai=True,
        project=project_id,
        location=config.gemini_api_location,
        credentials=credentials,
        http_options=types.HttpOptions(api_version="v1", timeout=timeout_ms),
    )


def _localized_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {key: {"type": "string"} for key in ("en", "ms", "zh")},
        "required": ["en", "ms", "zh"],
        "additionalProperties": False,
    }


def response_schema_for_stage(stage: str) -> dict[str, Any] | None:
    """Return strict schemas for high-value stages; repository validators remain authoritative."""

    if stage == "source-analysis":
        localized = _localized_schema()
        return {
            "type": "object",
            "properties": {
                "sectionTitle": {"type": "string"},
                "learningObjectives": {
                    "type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 8
                },
                "prerequisites": {
                    "type": "array", "minItems": 1, "maxItems": 6,
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"}, "description": localized, "recovery": localized
                        },
                        "required": ["id", "description", "recovery"], "additionalProperties": False,
                    },
                },
                "misconceptionCatalogue": {
                    "type": "array", "minItems": 3, "maxItems": 10,
                    "items": {
                        "type": "object",
                        "properties": {"id": {"type": "string"}, "description": localized},
                        "required": ["id", "description"], "additionalProperties": False,
                    },
                },
                "scopeNotes": {
                    "type": "object",
                    "properties": {
                        "includedConcepts": {
                            "type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 8
                        },
                        "excludedConcepts": {
                            "type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 8
                        },
                    },
                    "required": ["includedConcepts", "excludedConcepts"], "additionalProperties": False,
                },
            },
            "required": [
                "sectionTitle", "learningObjectives", "prerequisites", "misconceptionCatalogue", "scopeNotes"
            ],
            "additionalProperties": False,
        }
    if stage == "activity-plan":
        return {
            "type": "object",
            "properties": {
                "activities": {
                    "type": "array", "minItems": 18, "maxItems": 18,
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "type": {"type": "string", "enum": ["mcq", "interactive"]},
                            "difficulty": {"type": "string", "enum": ["easy", "moderate", "challenging"]},
                            "objective": {"type": "string"},
                            "misconceptions": {"type": "array", "items": {"type": "string"}},
                            "prerequisiteId": {"type": "string"},
                            "interactionMode": {
                                "anyOf": [
                                    {"type": "string", "enum": ["classification", "matching", "ordering", "selection"]},
                                    {"type": "null"},
                                ]
                            },
                        },
                        "required": [
                            "id", "type", "difficulty", "objective", "misconceptions",
                            "prerequisiteId", "interactionMode"
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["activities"], "additionalProperties": False,
        }
    if "audit" in stage:
        return {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "activityId": {"type": "string"},
                            "severity": {"type": "string", "enum": ["blocker", "warning"]},
                            "code": {"type": "string"}, "message": {"type": "string"},
                        },
                        "required": ["activityId", "severity", "code", "message"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["findings"], "additionalProperties": False,
        }
    return None


def _status_code(exc: BaseException) -> int | None:
    for attribute in ("status_code", "code"):
        value = getattr(exc, attribute, None)
        if callable(value):
            try:
                value = value()
            except Exception:
                continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _retryable(exc: BaseException) -> bool:
    code = _status_code(exc)
    if code is not None:
        return code in {408, 409, 429} or code >= 500
    text = str(exc).casefold()
    return any(
        token in text
        for token in ("timeout", "temporar", "unavailable", "reset", "connection", "overloaded", "resource exhausted")
    )


class GeminiApiClient:
    """Conversation-compatible Gemini API client using inline controlled PDF bytes."""

    provider = "gemini_api"

    def __init__(
        self,
        config: GeneratorConfig,
        source_paths: tuple[Path, ...],
        *,
        sdk_client: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.source_paths = tuple(Path(path) for path in source_paths)
        self.sdk_client = sdk_client
        self.sleep = sleep
        self.source_documents: list[bytes] = []
        self.master_prompt = (config.repo_root / "config" / "gem_instructions.md").read_text(encoding="utf-8").strip()
        self.prompt_sha256 = hashlib.sha256(self.master_prompt.encode("utf-8")).hexdigest()

    @property
    def actual_model(self) -> str:
        return self.config.gemini_api_model

    def _client(self) -> Any:
        if self.sdk_client is None:
            self.sdk_client = build_gemini_sdk_client(self.config)
        return self.sdk_client

    def prepare(self) -> None:
        if not self.source_paths:
            raise ResponseContractError("Gemini API requires at least one controlled PDF")
        documents: list[bytes] = []
        for path in self.source_paths:
            if path.suffix.casefold() != ".pdf" or not path.is_file():
                raise ResponseContractError(f"Gemini API source is not an existing PDF: {path}")
            data = path.read_bytes()
            if not data.startswith(b"%PDF"):
                raise ResponseContractError(f"Gemini API source does not have a PDF signature: {path}")
            documents.append(data)
        self.source_documents = documents
        self._client()  # Fail authentication/API setup before local temporary PDFs are removed.

    def ask(self, prompt: str, *, stage: str | None = None) -> str:
        if not self.source_documents:
            raise ResponseContractError("Gemini API source files were not prepared before generation")
        try:
            from google.genai import types
        except ImportError as exc:
            raise AuthenticationRequired("google-genai is not installed") from exc

        schema = response_schema_for_stage(stage or "")
        contents: list[Any] = [
            types.Part.from_bytes(data=document, mime_type="application/pdf")
            for document in self.source_documents
        ]
        stage_prompt = prompt
        if schema is not None:
            stage_prompt += (
                "\n\nAPI TRANSPORT NOTE: structured JSON is enforced by the API. "
                "Return the requested JSON object only; the local client restores BEGIN_JSON/END_JSON framing."
            )
        contents.append(stage_prompt)
        config_kwargs: dict[str, Any] = {
            "system_instruction": self.master_prompt,
            "thinking_config": types.ThinkingConfig(
                thinking_level=self.config.gemini_api_thinking_level.upper()
            ),
        }
        if schema is not None:
            config_kwargs.update(
                response_mime_type="application/json",
                response_json_schema=schema,
            )
        generation_config = types.GenerateContentConfig(**config_kwargs)

        last_error: BaseException | None = None
        for attempt in range(1, self.config.gemini_api_max_attempts + 1):
            try:
                response = self._client().models.generate_content(
                    model=self.actual_model,
                    contents=contents,
                    config=generation_config,
                )
                text = str(getattr(response, "text", "") or "").strip()
                if not text:
                    raise ResponseContractError("Gemini API returned no text output")
                if "BEGIN_JSON" in text and "END_JSON" in text:
                    return text
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    return text
                return "BEGIN_JSON\n" + json.dumps(parsed, ensure_ascii=False) + "\nEND_JSON"
            except ResponseContractError:
                raise
            except Exception as exc:
                if not _retryable(exc):
                    code = _status_code(exc)
                    if code in {401, 403}:
                        raise AuthenticationRequired(
                            f"Gemini API authentication/authorization failed ({code}): {exc}"
                        ) from exc
                    status = f" (HTTP {code})" if code is not None else ""
                    raise GeminiApiError(f"Gemini API request failed{status}: {exc}") from exc
                last_error = exc
                if attempt >= self.config.gemini_api_max_attempts:
                    break
                self.sleep(self.config.gemini_api_retry_backoff_seconds * (2 ** (attempt - 1)))
        raise TransientGeminiError(
            f"Gemini API request failed after {self.config.gemini_api_max_attempts} attempt(s): {last_error}"
        ) from last_error
