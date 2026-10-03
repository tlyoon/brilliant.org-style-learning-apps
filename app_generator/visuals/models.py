"""Compatibility facade for the original physics motion-model import path.

The implementation now belongs to the active domain profile. Existing callers keep
working while new domain-aware code resolves models from the domain manifest.
"""

from pathlib import Path

from app_generator.domains import resolve_domain

_ROOT = Path(__file__).resolve().parents[2]
_DOMAIN_MODELS = resolve_domain(_ROOT).load_module("simulations", "modelsModule")

Motion1DState = _DOMAIN_MODELS.Motion1DState
evaluate_motion_1d = _DOMAIN_MODELS.evaluate_motion_1d

__all__ = ["Motion1DState", "evaluate_motion_1d"]
