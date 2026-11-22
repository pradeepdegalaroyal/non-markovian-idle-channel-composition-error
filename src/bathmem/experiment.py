"""Experiment drivers: model-error grid, truncation ablation, pulse-error sweep."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from .circuits import random_sequences, survival_channel, survival_exact
from .model import (
    ModelParams,
    closed_form_population,
    idle_channel_qubit,
    markov_channel,
    pseudomode_idle_superop,
)
from .nonmarkov import blp_measure, shots_to_resolve

MODELS = ("markov_fit", "markov_interval", "composed_idle")


@dataclass
class Config:
    """Sweep configuration (rates in units of gamma, times in 1 / gamma)."""

    kappas: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0)
    taus: tuple[float, ...] = (0.05, 0.1, 0.2, 0.4)
    lengths: tuple[int, ...] = (2, 5, 10, 20, 30)
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4)
    batch: int = 60
    nmax_ref: int = 5
    nmax_ablation: tuple[int, ...] = (1, 2, 3, 4)
    nmax_ablation_ref: int = 8
    ablation_kappas: tuple[float, ...] = (0.25, 1.0, 4.0)
    eps_values: tuple[float, ...] = (0.0, 0.02, 0.05, 0.1)
    eps_kappas: tuple[float, ...] = (0.5, 2.0, 8.0)
    tau_ref: float = 0.2
    m_ref: int = 20
    extras: dict = field(default_factory=dict)

    @staticmethod
    def quick() -> "Config":
        return Config(
            kappas=(0.5, 2.0, 8.0),
            taus=(0.2,),
            lengths=(5, 10),
            seeds=(0, 1),
            batch=20,
            nmax_ref=4,
            nmax_ablation=(1, 2),
            nmax_ablation_ref=4,
            ablation_kappas=(1.0,),
            eps_values=(0.0, 0.05),
            eps_kappas=(2.0,),
            m_ref=10,
        )


@lru_cache(maxsize=None)
def _exact_idle(kappa: float, tau: float, nmax: int) -> np.ndarray:
    return pseudomode_idle_superop(ModelParams(1.0, kappa), nmax, tau)


@lru_cache(maxsize=None)
def _composed_idle(kappa: float, tau: float, nmax: int) -> np.ndarray:
    return idle_channel_qubit(ModelParams(1.0, kappa), nmax, tau)


@lru_cache(maxsize=None)
def fitted_markov_rate(kappa: float, gamma: float = 1.0, window: float = 3.0) -> float:
    """Exponential decay rate fitted to the exact excited-state curve on [0, window/gamma].

    This mimics a T1 experiment whose delay range is a few Markov lifetimes.
    """
    t = np.linspace(0.0, window / gamma, 60)
    y = closed_form_population(t, gamma, kappa)
    popt, _ = curve_fit(lambda x, r: np.exp(-r * x), t, y, p0=[gamma])
    return float(popt[0])


def interval_rate(kappa: float, tau: float, gamma: float = 1.0) -> float:
    """Constant rate that reproduces the exact population loss of one idle of length tau."""
    pop = float(closed_form_population(tau, gamma, kappa))
    return float(-np.log(max(pop, 1e-12)) / tau)


def model_predictions(
    gates: np.ndarray, kappa: float, tau: float, nmax_ref: int, gamma: float = 1.0
) -> dict[str, np.ndarray]:
    """Survival of every sequence under the exact reference and three noise models."""
    out = {"exact": survival_exact(gates, _exact_idle(kappa, tau, nmax_ref), nmax_ref)}
    out["markov_fit"] = survival_channel(gates, markov_channel(fitted_markov_rate(kappa, gamma), tau))
    out["markov_interval"] = survival_channel(gates, markov_channel(interval_rate(kappa, tau, gamma), tau))
    out["composed_idle"] = survival_channel(gates, _composed_idle(kappa, tau, nmax_ref))
    return out


def run_grid(cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sweep (kappa, tau, length, seed); return summary rows and per-sequence errors."""
    rows, seq_rows = [], []
    for seed in cfg.seeds:
        for m in cfg.lengths:
            rng = np.random.default_rng(1000 * seed + m)
            gates = random_sequences(rng, m, cfg.batch)
            for kappa in cfg.kappas:
                for tau in cfg.taus:
                    pred = model_predictions(gates, kappa, tau, cfg.nmax_ref)
                    row = dict(kappa=kappa, tau=tau, kappa_tau=kappa * tau, m=m, seed=seed,
                               exact_mean=float(pred["exact"].mean()))
                    for name in MODELS:
                        err = np.abs(pred[name] - pred["exact"])
                        row[f"mae_{name}"] = float(err.mean())
                        row[f"curve_{name}"] = float(abs(pred[name].mean() - pred["exact"].mean()))
                        if m == cfg.m_ref:
                            for e in err:
                                seq_rows.append(dict(kappa=kappa, tau=tau, seed=seed, model=name, abs_err=float(e)))
                    rows.append(row)
    return pd.DataFrame(rows), pd.DataFrame(seq_rows)


def run_truncation_ablation(cfg: Config) -> pd.DataFrame:
    """Error of a Fock-truncated bath mode against a deeper reference truncation."""
    rows = []
    tau, m = cfg.tau_ref, cfg.m_ref
    for seed in cfg.seeds:
        gates = random_sequences(np.random.default_rng(7000 + seed), m, cfg.batch)
        for kappa in cfg.ablation_kappas:
            ref = survival_exact(gates, _exact_idle(kappa, tau, cfg.nmax_ablation_ref), cfg.nmax_ablation_ref)
            for nmax in cfg.nmax_ablation:
                s = survival_exact(gates, _exact_idle(kappa, tau, nmax), nmax)
                rows.append(dict(kappa=kappa, nmax=nmax, seed=seed, mae=float(np.abs(s - ref).mean())))
    return pd.DataFrame(rows)


def run_pulse_sweep(cfg: Config) -> pd.DataFrame:
    """Repeat the model comparison with a coherent X over-rotation on every gate."""
    rows = []
    for seed in cfg.seeds:
        for eps in cfg.eps_values:
            gates = random_sequences(np.random.default_rng(9000 + seed), cfg.m_ref, cfg.batch, eps)
            for kappa in cfg.eps_kappas:
                pred = model_predictions(gates, kappa, cfg.tau_ref, cfg.nmax_ref)
                for name in MODELS:
                    rows.append(dict(eps=eps, kappa=kappa, seed=seed, model=name,
                                     mae=float(np.abs(pred[name] - pred["exact"]).mean())))
    return pd.DataFrame(rows)


def summarise(grid: pd.DataFrame, cfg: Config) -> dict:
    """Aggregate statistics used in the report (all numbers come from this dict)."""
    ref = grid[grid.m == cfg.m_ref]
    agg = ref.groupby(["kappa", "tau"]).agg({f"mae_{n}": "mean" for n in MODELS} | {"exact_mean": "mean"}).reset_index()
    agg["kappa_tau"] = agg.kappa * agg.tau
    lost = (1.0 - agg.exact_mean).clip(lower=1e-6)
    for n in MODELS:
        agg[f"rel_{n}"] = agg[f"mae_{n}"] / lost
    agg["blp"] = [blp_measure(1.0, k) for k in agg.kappa]
    curve = ref.groupby(["kappa", "tau"])[[f"curve_{n}" for n in MODELS]].mean().reset_index()
    agg = agg.merge(curve, on=["kappa", "tau"])
    agg["shots_composed"] = [
        shots_to_resolve(p, d) for p, d in zip(agg.exact_mean, agg.curve_composed_idle)
    ]
    agg["shots_markov_interval"] = [
        shots_to_resolve(p, d) for p, d in zip(agg.exact_mean, agg.curve_markov_interval)
    ]
    out: dict = {"m_ref": cfg.m_ref}
    if len(agg) > 2:
        out["spearman_rel_composed_vs_blp"] = float(agg["rel_composed_idle"].corr(agg["blp"], method="spearman"))
        out["spearman_rel_composed_vs_neg_kappa_tau"] = float(agg["rel_composed_idle"].corr(-agg["kappa_tau"], method="spearman"))
        out["spearman_abs_composed_vs_blp"] = float(agg["mae_composed_idle"].corr(agg["blp"], method="spearman"))
        out["spearman_abs_composed_vs_kappa_tau"] = float(agg["mae_composed_idle"].corr(agg["kappa_tau"], method="spearman"))
        out["max_abs_diff_composed_vs_interval"] = float((agg["mae_composed_idle"] - agg["mae_markov_interval"]).abs().max())
    return {"table": agg, "stats": out}


def add_relative(grid: pd.DataFrame) -> pd.DataFrame:
    """Add per-seed relative error: mean absolute error / mean lost survival."""
    out = grid.copy()
    lost = (1.0 - out.exact_mean).clip(lower=1e-6)
    for n in MODELS:
        out[f"rel_{n}"] = out[f"mae_{n}"] / lost
    return out


def validate_against_closed_form(cfg: Config) -> float:
    """Largest deviation of the simulated qubit idle population from the closed form."""
    worst = 0.0
    for kappa in cfg.kappas:
        for tau in cfg.taus:
            sim = float(_composed_idle(kappa, tau, cfg.nmax_ref)[3, 3].real)
            worst = max(worst, abs(sim - float(closed_form_population(tau, 1.0, kappa))))
    return worst


def critical_kappa_tau(table: pd.DataFrame, column: str = "rel_composed_idle", level: float = 0.1) -> dict:
    """Largest kappa*tau still above ``level`` and smallest one below it (grid values)."""
    above = table[table[column] >= level]
    below = table[table[column] < level]
    return {
        "level": level,
        "max_kappa_tau_above": float(above.kappa_tau.max()) if len(above) else None,
        "min_kappa_tau_below": float(below.kappa_tau.min()) if len(below) else None,
    }
