"""Damped Jaynes-Cummings (single Lorentzian bath mode) idle model.

A qubit with excited state |1> is resonantly coupled with strength ``g`` to one
bosonic mode that decays at rate ``kappa``.  Tracing out the mode gives amplitude
damping with memory.  For ``kappa >> gamma`` (``gamma = 4 g^2 / kappa``) the
qubit decay is exponential (Markov limit); for ``kappa < 4 gamma`` it shows
revivals (non-Markovian).  All rates are in units of ``gamma``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm

Array = np.ndarray


@dataclass(frozen=True)
class ModelParams:
    """Bath parameters: Markov-limit decay rate and bath-mode linewidth."""

    gamma: float = 1.0
    kappa: float = 1.0

    @property
    def g(self) -> float:
        """Qubit-mode coupling strength."""
        return coupling_from_rates(self.gamma, self.kappa)


def coupling_from_rates(gamma: float, kappa: float) -> float:
    """Return g such that the Markov-limit decay rate 4 g^2 / kappa equals gamma."""
    return 0.5 * float(np.sqrt(gamma * kappa))


def closed_form_population(t: Array | float, gamma: float, kappa: float) -> Array:
    """Exact excited-state population |G(t)|^2 of the damped Jaynes-Cummings model."""
    t = np.asarray(t, dtype=float)
    g2 = gamma * kappa / 4.0
    omega = np.sqrt(complex(kappa**2 / 16.0 - g2))
    if abs(omega) < 1e-9:  # critical damping
        amp = np.exp(-kappa * t / 4.0) * (1.0 + kappa * t / 4.0)
    else:
        amp = np.exp(-kappa * t / 4.0) * (
            np.cosh(omega * t) + kappa / (4.0 * omega) * np.sinh(omega * t)
        )
    return np.abs(amp) ** 2


def _ops(nmax: int) -> tuple[Array, Array, Array]:
    d = nmax + 1
    a = np.diag(np.sqrt(np.arange(1, d)), k=1).astype(complex)
    sm = np.array([[0, 1], [0, 0]], dtype=complex)  # |0><1|
    return a, sm, np.eye(d, dtype=complex)


def pseudomode_liouvillian(params: ModelParams, nmax: int) -> Array:
    """Row-major vectorised Liouvillian of qubit (x) damped mode, Fock cut ``nmax``."""
    a, sm, i_m = _ops(nmax)
    i_q = np.eye(2, dtype=complex)
    a_f = np.kron(i_q, a)
    sm_f = np.kron(sm, i_m)
    h = params.g * (sm_f.conj().T @ a_f + sm_f @ a_f.conj().T)
    dim = h.shape[0]
    eye = np.eye(dim, dtype=complex)
    ada = a_f.conj().T @ a_f
    lv = -1j * (np.kron(h, eye) - np.kron(eye, h.T))
    lv += params.kappa * (
        np.kron(a_f, a_f.conj()) - 0.5 * np.kron(ada, eye) - 0.5 * np.kron(eye, ada.T)
    )
    return lv


def pseudomode_idle_superop(params: ModelParams, nmax: int, tau: float) -> Array:
    """Superoperator of an idle period of length ``tau`` on qubit (x) mode."""
    return expm(pseudomode_liouvillian(params, nmax) * tau)


def idle_channel_qubit(params: ModelParams, nmax: int, tau: float) -> Array:
    """Qubit-only 4x4 superoperator of one idle from a fresh (vacuum) bath.

    Obtained like process tomography: every matrix unit of the qubit is sent
    through the exact idle map and the mode is traced out.
    """
    sup = pseudomode_idle_superop(params, nmax, tau)
    d = 2 * (nmax + 1)
    vac = np.zeros((nmax + 1, nmax + 1), dtype=complex)
    vac[0, 0] = 1.0
    out = np.zeros((4, 4), dtype=complex)
    for i in range(2):
        for j in range(2):
            e = np.zeros((2, 2), dtype=complex)
            e[i, j] = 1.0
            rho = (sup @ np.kron(e, vac).reshape(-1)).reshape(d, d)
            red = np.einsum("ikjk->ij", rho.reshape(2, nmax + 1, 2, nmax + 1))
            out[:, 2 * i + j] = red.reshape(-1)
    return out


def markov_channel(rate: float, tau: float) -> Array:
    """Qubit amplitude-damping superoperator with constant decay ``rate``."""
    p = 1.0 - np.exp(-rate * tau)
    k0 = np.array([[1, 0], [0, np.sqrt(1 - p)]], dtype=complex)
    k1 = np.array([[0, np.sqrt(p)], [0, 0]], dtype=complex)
    return np.kron(k0, k0.conj()) + np.kron(k1, k1.conj())
