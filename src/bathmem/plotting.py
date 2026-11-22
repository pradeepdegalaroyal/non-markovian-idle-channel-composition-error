"""Figures (viridis palette, 200 dpi): line+band, empirical CDF, hatched grouped bars."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

VIR = plt.cm.viridis
MARKS = ["o", "s", "^", "D", "v"]
LINES = ["-", "--", "-.", ":"]
HATCH = ["//", "..", "xx", "\\\\"]
LABEL = {
    "markov_fit": "Markov amplitude damping, rate fitted to T1 curve",
    "markov_interval": "Markov amplitude damping, rate matched per idle",
    "composed_idle": "Idle channel from fresh bath, composed",
}


def _save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_relative_error(grid: pd.DataFrame, m_ref: int, path: Path) -> None:
    """Relative survival error vs kappa*tau, one line per idle length, band = std over seeds."""
    g = grid[grid.m == m_ref]
    taus = sorted(g.tau.unique())
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, name in zip(axes, ["markov_fit", "composed_idle"]):
        for i, tau in enumerate(taus):
            sub = g[g.tau == tau].groupby("kappa")[f"rel_{name}"].agg(["mean", "std"]).reset_index()
            x = sub.kappa * tau
            col = VIR(0.1 + 0.8 * i / max(len(taus) - 1, 1))
            ax.plot(x, sub["mean"], LINES[i % 4], marker=MARKS[i % 5], color=col, label=f"idle length {tau} / gamma")
            ax.fill_between(x, sub["mean"] - sub["std"].fillna(0), sub["mean"] + sub["std"].fillna(0), color=col, alpha=0.25)
        ax.axhline(0.1, color="k", lw=0.8, ls=":")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("bath linewidth x idle length, kappa * tau (dimensionless)")
        ax.set_title(LABEL[name], fontsize=9)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel(f"relative survival error at m = {m_ref} Cliffords\n(mean abs. error / lost survival)")
    axes[0].legend(fontsize=8)
    fig.suptitle("Error of memoryless noise models against exact bath dynamics (mean +/- std, seeds)")
    _save(fig, path)


def fig_ecdf(seq: pd.DataFrame, settings: list[tuple[float, float]], path: Path) -> None:
    """Empirical CDF of per-sequence absolute survival error for two models."""
    fig, axes = plt.subplots(1, len(settings), figsize=(5.2 * len(settings), 4.2), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, (kappa, tau) in zip(axes, settings):
        sub = seq[(seq.kappa == kappa) & (seq.tau == tau)]
        for i, name in enumerate(["markov_fit", "composed_idle"]):
            e = np.sort(sub[sub.model == name].abs_err.to_numpy())
            ax.step(e, np.arange(1, len(e) + 1) / len(e), where="post", ls=LINES[i], lw=2,
                    color=VIR(0.15 + 0.6 * i), label=LABEL[name])
        ax.set_xscale("log")
        ax.set_xlabel("absolute survival error per sequence (probability)")
        ax.set_title(f"kappa = {kappa} gamma, idle length {tau} / gamma", fontsize=9)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("empirical cumulative fraction of sequences")
    axes[0].legend(fontsize=7, loc="lower right")
    fig.suptitle("Per-sequence error distribution (all seeds pooled)")
    _save(fig, path)


def fig_truncation(abl: pd.DataFrame, path: Path) -> None:
    """Grouped hatched bars: error of Fock-truncated bath mode vs depth."""
    kappas = sorted(abl.kappa.unique())
    nmaxs = sorted(abl.nmax.unique())
    width = 0.8 / len(nmaxs)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for j, nmax in enumerate(nmaxs):
        vals = [abl[(abl.kappa == k) & (abl.nmax == nmax)].mae for k in kappas]
        mean = [max(v.mean(), 1e-12) for v in vals]
        std = [v.std() if len(v) > 1 else 0.0 for v in vals]
        ax.bar(np.arange(len(kappas)) + j * width, mean, width, yerr=std, capsize=3,
               color=VIR(0.15 + 0.7 * j / max(len(nmaxs) - 1, 1)), edgecolor="k", hatch=HATCH[j % 4],
               label=f"Fock cut {nmax}")
    ax.set_xticks(np.arange(len(kappas)) + width * (len(nmaxs) - 1) / 2)
    ax.set_xticklabels([f"{k} gamma" for k in kappas])
    ax.set_yscale("log")
    ax.set_xlabel("bath linewidth kappa")
    ax.set_ylabel("mean abs. survival error vs deepest cut")
    ax.set_title("Truncation-depth ablation of the exact bath model")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    _save(fig, path)


def fig_pulse_sweep(pulse: pd.DataFrame, path: Path) -> None:
    """Survival error against coherent pulse over-rotation, band = std over seeds."""
    kappas = sorted(pulse.kappa.unique())
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.0), sharey=True)
    for ax, name in zip(axes, ["markov_fit", "composed_idle"]):
        for i, kappa in enumerate(kappas):
            sub = pulse[(pulse.model == name) & (pulse.kappa == kappa)].groupby("eps").mae.agg(["mean", "std"]).reset_index()
            col = VIR(0.1 + 0.8 * i / max(len(kappas) - 1, 1))
            ax.plot(sub.eps, sub["mean"], LINES[i % 4], marker=MARKS[i % 5], color=col, label=f"kappa = {kappa} gamma")
            ax.fill_between(sub.eps, sub["mean"] - sub["std"].fillna(0), sub["mean"] + sub["std"].fillna(0), color=col, alpha=0.25)
        ax.set_xlabel("coherent X over-rotation per gate (rad)")
        ax.set_title(LABEL[name], fontsize=9)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("mean abs. survival error vs exact")
    axes[0].legend(fontsize=8)
    fig.suptitle("Robustness to imperfect pulses (idle length 0.2 / gamma)")
    _save(fig, path)


def fig_shots(table: pd.DataFrame, path: Path) -> None:
    """Grouped hatched bars: shots needed to resolve the composed-model error."""
    taus = sorted(table.tau.unique())
    kappas = sorted(table.kappa.unique())
    width = 0.8 / len(taus)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for j, tau in enumerate(taus):
        vals = [table[(table.kappa == k) & (table.tau == tau)].shots_composed.iloc[0] for k in kappas]
        ax.bar(np.arange(len(kappas)) + j * width, vals, width, color=VIR(0.1 + 0.8 * j / max(len(taus) - 1, 1)),
               edgecolor="k", hatch=HATCH[j % 4], label=f"idle length {tau} / gamma")
    ax.set_xticks(np.arange(len(kappas)) + width * (len(taus) - 1) / 2)
    ax.set_xticklabels([str(k) for k in kappas])
    ax.set_yscale("log")
    ax.set_xlabel("bath linewidth kappa (units of gamma)")
    ax.set_ylabel("shots to resolve model error at 3 sigma")
    ax.set_title("Measurement cost of detecting cross-gate memory")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    _save(fig, path)
