"""Domain-specific failures with stable error codes."""

from __future__ import annotations


class GeneratorError(RuntimeError):
    code = "GENERATOR_ERROR"

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.detail = detail


class ConfigurationError(GeneratorError):
    code = "CONFIGURATION_ERROR"


class RepositoryCompatibilityError(GeneratorError):
    code = "REPOSITORY_COMPATIBILITY_ERROR"


class WorkerLockError(GeneratorError):
    code = "WORKER_LOCK_UNAVAILABLE"


class CoordinatorError(GeneratorError):
    code = "COORDINATOR_ERROR"


class NoAvailableJob(CoordinatorError):
    code = "NO_AVAILABLE_JOB"


class LeaseLostError(CoordinatorError):
    code = "LEASE_LOST"


class AutoJobExecutionError(GeneratorError):
    code = "AUTO_JOB_EXECUTION_FAILED"

    def __init__(self, message: str, *, status: str, original_code: str) -> None:
        super().__init__(message, detail=f"coordinator_status={status}; original_code={original_code}")
        self.status = status
        self.original_code = original_code


class AutoModeBlockedError(GeneratorError):
    code = "AUTO_MODE_BLOCKED"


class BrowserError(GeneratorError):
    code = "BROWSER_ERROR"


class AuthenticationRequired(GeneratorError):
    code = "AUTHENTICATION_REQUIRED"


class WrongAccountError(GeneratorError):
    code = "WRONG_ACCOUNT"


class GemAccessError(GeneratorError):
    code = "GEM_ACCESS_DENIED"


class GemIdentityError(GeneratorError):
    code = "GEM_IDENTITY_MISMATCH"


class UiContractError(GeneratorError):
    code = "GEMINI_UI_CONTRACT_ERROR"


class SourceSetMismatch(GeneratorError):
    code = "SOURCE_SET_MISMATCH"


class DriveAuthenticationError(GeneratorError):
    code = "DRIVE_AUTHENTICATION_FAILED"


class DriveAccessError(GeneratorError):
    code = "DRIVE_ACCESS_FAILED"


class SourceNotFound(GeneratorError):
    code = "SOURCE_NOT_FOUND"


class SourceAmbiguous(GeneratorError):
    code = "SOURCE_AMBIGUOUS"


class SourceDownloadError(GeneratorError):
    code = "SOURCE_DOWNLOAD_FAILED"


class ResponseContractError(GeneratorError):
    code = "RESPONSE_CONTRACT_ERROR"


class TransientGeminiError(GeneratorError):
    code = "GEMINI_TRANSIENT_ERROR"


class ValidationFailure(GeneratorError):
    code = "VALIDATION_FAILED"

    def __init__(self, message: str, errors: list[str]) -> None:
        super().__init__(message, detail="\n".join(errors))
        self.errors = errors


class RepairLimitExceeded(GeneratorError):
    code = "REPAIR_LIMIT_EXCEEDED"


class OutputWriteError(GeneratorError):
    code = "OUTPUT_WRITE_FAILED"


class GitPublishError(GeneratorError):
    code = "GIT_PUBLISH_FAILED"
