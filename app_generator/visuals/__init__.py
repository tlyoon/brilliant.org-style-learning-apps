"""Declarative visual-learning contracts and validation."""

from app_generator.visuals.validation import visual_contract_errors, visual_registry_errors
from app_generator.visuals.verification import (
    PhysicsVerificationRequest,
    PhysicsVerificationResult,
    PhysicsVerifier,
    assert_matching_result,
)

__all__ = [
    "PhysicsVerificationRequest",
    "PhysicsVerificationResult",
    "PhysicsVerifier",
    "assert_matching_result",
    "visual_contract_errors",
    "visual_registry_errors",
]
