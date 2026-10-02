"""Provider-neutral contracts for independent physics verification.

Concrete Wolfram/Gemini adapters belong to later integration work. This module keeps
the content/visual contract independent of any chat plugin or hosted service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

VERIFICATION_KINDS = frozenset({
    "symbolic_equivalence",
    "conservation_invariant",
    "trajectory_relation",
    "graph_relation",
    "sign_or_limit",
    "dimensional_consistency",
    "reference_values",
})


@dataclass(frozen=True)
class PhysicsVerificationRequest:
    activity_id: str
    check_id: str
    kind: str
    statement: str
    inputs: Mapping[str, Any] = field(default_factory=dict)
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.activity_id or not self.check_id or not self.statement:
            raise ValueError("verification request identifiers and statement must be non-empty")
        if self.kind not in VERIFICATION_KINDS:
            raise ValueError(f"unsupported verification kind: {self.kind}")


@dataclass(frozen=True)
class PhysicsVerificationResult:
    check_id: str
    passed: bool
    provider: str
    summary: str
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.check_id or not self.provider or not self.summary:
            raise ValueError("verification result identifiers, provider, and summary must be non-empty")


class PhysicsVerifier(Protocol):
    """Adapter boundary for Wolfram or another approved independent verifier."""

    @property
    def provider_name(self) -> str: ...

    def verify(self, request: PhysicsVerificationRequest) -> PhysicsVerificationResult: ...


def assert_matching_result(
    request: PhysicsVerificationRequest, result: PhysicsVerificationResult
) -> None:
    """Reject a verifier response that cannot be tied to the requested check."""
    if result.check_id != request.check_id:
        raise ValueError(
            f"verification result check_id {result.check_id!r} does not match request {request.check_id!r}"
        )
