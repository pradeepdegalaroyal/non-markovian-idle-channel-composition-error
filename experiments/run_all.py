"""Reproduce every result and figure.  ``python experiments/run_all.py [--quick]``."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bathmem import experiment as ex  # noqa: E402
from bathmem import plotting as pl  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="small smoke run (< 1 minute)")
    ap.add_argument("--out", default=None, help="output root (default: repository root)")
    args = ap.parse_args()

    cfg = ex.Config.quick() if args.quick else ex.Config()
    out = Path(args.out) if args.out else (ROOT / "quick_out" if args.quick else ROOT)
    res, fig = out / "results", out / "figures"
    res.mkdir(parents=True, exist_ok=True)
    fig.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    grid, seq = ex.run_grid(cfg)
    grid = ex.add_relative(grid)
    abl = ex.run_truncation_ablation(cfg)
    pulse = ex.run_pulse_sweep(cfg)
    summ = ex.summarise(grid, cfg)
    table, stats = summ["table"], summ["stats"]
    stats["max_dev_pseudomode_vs_closed_form"] = ex.validate_against_closed_form(cfg)
    stats["critical_kappa_tau_composed"] = ex.critical_kappa_tau(table, "rel_composed_idle", 0.1)
    stats["critical_kappa_tau_markov_fit"] = ex.critical_kappa_tau(table, "rel_markov_fit", 0.1)
    stats["runtime_seconds"] = round(time.time() - t0, 1)
    stats["quick"] = bool(args.quick)

    grid.to_csv(res / "grid_per_seed.csv", index=False)
    seq.to_csv(res / "per_sequence_errors.csv", index=False)
    abl.to_csv(res / "truncation_ablation.csv", index=False)
    pulse.to_csv(res / "pulse_error_sweep.csv", index=False)
    table.to_csv(res / "summary_table.csv", index=False)
    (res / "summary_stats.json").write_text(json.dumps(stats, indent=2))

    pl.fig_relative_error(grid, cfg.m_ref, fig / "fig1_relative_error_vs_kappa_tau.png")
    settings = [(cfg.kappas[min(2, len(cfg.kappas) - 1)], cfg.tau_ref), (cfg.kappas[-2], cfg.tau_ref)]
    pl.fig_ecdf(seq, settings, fig / "fig2_ecdf_sequence_error.png")
    pl.fig_truncation(abl, fig / "fig3_truncation_ablation.png")
    pl.fig_pulse_sweep(pulse, fig / "fig4_pulse_error_sweep.png")
    pl.fig_shots(table, fig / "fig5_shots_to_resolve.png")
    print(json.dumps(stats, indent=2))
    print(f"done in {time.time() - t0:.1f}s -> {out}")


if __name__ == "__main__":
    main()
