"""Trusted deterministic physics models used to verify simulation primitives."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Motion1DState:
    position: float
    velocity: float
    time: float


def evaluate_motion_1d(initial_position: float, velocity: float, time: float) -> Motion1DState:
    """Evaluate bounded constant-velocity motion x = x0 + v t."""
    values = tuple(float(value) for value in (initial_position, velocity, time))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("motion inputs must be finite")
    x0, v, t = values
    if t < 0:
        raise ValueError("motion time must be non-negative")
    return Motion1DState(position=x0 + v * t, velocity=v, time=t)
