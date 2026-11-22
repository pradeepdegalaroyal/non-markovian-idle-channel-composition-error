"""Non-Markovianity witness (trace-distance revival) and shot-cost helpers."""

from __future__ import annotations

import numpy as np

from .model import closed_form_population


def blp_measure(gamma: float, kappa: float, points: int = 40000) -> float:
    """Breuer-Laine-Piilo measure for the damped Jaynes-Cummings idle.

    The trace distance of |0> and |1> is |G(t)|^2 for this channel; the measure
    is the summed positive increments of that curve.
    """
    t = np.linspace(0.0, 40.0 / kappa, points)
    d = closed_form_population(t, gamma, kappa)
    inc = np.diff(d)
    return float(inc[inc > 0].sum())


def shots_to_resolve(p: float, delta: float, z: float = 3.0) -> float:
    """Binomial shots needed to resolve a survival difference ``delta`` at z sigma."""
    delta = max(abs(delta), 1e-12)
    return float(z**2 * max(p * (1 - p), 1e-6) / delta**2)
