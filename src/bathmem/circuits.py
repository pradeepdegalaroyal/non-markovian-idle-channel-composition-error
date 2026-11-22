"""Random Clifford sequences with idle periods, simulated exactly or per channel."""

from __future__ import annotations

import numpy as np

Array = np.ndarray


def clifford_group() -> list[Array]:
    """The 24 single-qubit Cliffords (up to global phase) as 2x2 unitaries."""
    h = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    s = np.diag([1, 1j]).astype(complex)
    found: list[Array] = [np.eye(2, dtype=complex)]
    frontier = [found[0]]
    while frontier:
        nxt = []
        for u in frontier:
            for gen in (h, s):
                v = gen @ u
                if not any(abs(np.trace(w.conj().T @ v)) > 2 - 1e-9 for w in found):
                    found.append(v)
                    nxt.append(v)
        frontier = nxt
    return found


def _rx(angle: float) -> Array:
    c, s = np.cos(angle / 2), np.sin(angle / 2)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)


def random_sequences(
    rng: np.random.Generator, m: int, batch: int, eps: float = 0.0
) -> Array:
    """Batch of ``m`` random Cliffords plus the ideal inverting gate.

    Returns an array (batch, m + 1, 2, 2).  ``eps`` is a coherent X over-rotation
    (radians) appended to every implemented gate, the inverse included.
    """
    group = np.array(clifford_group())
    idx = rng.integers(0, len(group), size=(batch, m))
    gates = np.empty((batch, m + 1, 2, 2), dtype=complex)
    for b in range(batch):
        prod = np.eye(2, dtype=complex)
        for k in range(m):
            gates[b, k] = group[idx[b, k]]
            prod = gates[b, k] @ prod
        gates[b, m] = prod.conj().T
    if eps:
        gates = np.einsum("ij,bkjl->bkil", _rx(eps), gates)
    return gates


def _embed(gates: Array, mode_dim: int) -> Array:
    eye = np.eye(mode_dim, dtype=complex)
    b, k = gates.shape[:2]
    full = np.einsum("bkij,ln->bkiljn", gates, eye)
    return full.reshape(b, k, 2 * mode_dim, 2 * mode_dim)


def _run(gates: Array, idle: Array, mode_dim: int) -> Array:
    """Alternate gate / idle and return the qubit-|0> survival of every sequence."""
    full = _embed(gates, mode_dim)
    batch, steps = full.shape[:2]
    dim = 2 * mode_dim
    rho = np.zeros((batch, dim, dim), dtype=complex)
    rho[:, 0, 0] = 1.0
    for k in range(steps):
        u = full[:, k]
        rho = u @ rho @ np.conj(np.swapaxes(u, 1, 2))
        rho = (rho.reshape(batch, -1) @ idle.T).reshape(batch, dim, dim)
    diag = np.real(np.einsum("bii->bi", rho)).reshape(batch, 2, mode_dim)
    return diag[:, 0, :].sum(axis=1)


def survival_exact(gates: Array, idle_full: Array, nmax: int) -> Array:
    """Survival under the exact qubit (x) mode dynamics (bath memory kept)."""
    return _run(gates, idle_full, nmax + 1)


def survival_channel(gates: Array, idle_qubit: Array) -> Array:
    """Survival when every idle is replaced by the same qubit channel."""
    return _run(gates, idle_qubit, 1)
