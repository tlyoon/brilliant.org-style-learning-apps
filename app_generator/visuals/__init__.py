"""Declarative visual-learning contracts and provider-neutral verification."""

from app_generator.visuals.validation import visual_contract_errors, visual_registry_errors
from app_generator.visuals.verification import (
    VerificationRequest,
    VerificationResult,
    Verifier,
    PhysicsVerificationRequest,
    PhysicsVerificationResult,
    PhysicsVerifier,
    assert_matching_result,
)

__all__ = [
    "VerificationRequest",
    "VerificationResult",
    "Verifier",
    "PhysicsVerificationRequest",
    "PhysicsVerificationResult",
    "PhysicsVerifier",
    "assert_matching_result",
    "visual_contract_errors",
    "visual_registry_errors",
]
