"""Provider-neutral contracts for independent subject-matter verification.

Concrete Wolfram/Gemini adapters belong to integration work. Domain profiles decide
which verification kinds are scientifically appropriate. Physics-prefixed names remain
as compatibility aliases for code written before the domain-profile architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Protocol

VERIFICATION_KIND_PATTERN = r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"



@dataclass(frozen=True)
class VerificationRequest:
    activity_id: str
    check_id: str
    kind: str
    statement: str
    inputs: Mapping[str, Any] = field(default_factory=dict)
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.activity_id or not self.check_id or not self.statement:
            raise ValueError("verification request identifiers and statement must be non-empty")
        if not isinstance(self.kind, str) or re.fullmatch(VERIFICATION_KIND_PATTERN, self.kind) is None:
            raise ValueError(f"invalid verification kind: {self.kind!r}")


@dataclass(frozen=True)
class VerificationResult:
    check_id: str
    passed: bool
    provider: str
    summary: str
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.check_id or not self.provider or not self.summary:
            raise ValueError("verification result identifiers, provider, and summary must be non-empty")


class Verifier(Protocol):
    @property
    def provider_name(self) -> str: ...

    def verify(self, request: VerificationRequest) -> VerificationResult: ...


def assert_matching_result(request: VerificationRequest, result: VerificationResult) -> None:
    if result.check_id != request.check_id:
        raise ValueError(
            f"verification result check_id {result.check_id!r} does not match request {request.check_id!r}"
        )


PhysicsVerificationRequest = VerificationRequest
PhysicsVerificationResult = VerificationResult
PhysicsVerifier = Verifier
