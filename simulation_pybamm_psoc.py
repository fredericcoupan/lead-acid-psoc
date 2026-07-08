"""
Reduced-order vs. full porous-electrode lead-acid battery comparison under
partial-state-of-charge (PSoC) renewable duty.

Reproduces the illustrative PyBaMM comparison reported in:

    F. Coupan, A. Abbas, "Stratification-Aware Modelling of Lead-Acid Batteries
    under Partial-State-of-Charge Renewable Duty", Journal of Energy Storage
    (submitted).

It uses the open-source PyBaMM framework, which implements both the lead-acid
porous-electrode model (Full) and its leading-order quasi-static reduced-order
approximation (LOQS). Three panels are computed, all with default parameters
and NO fitting:

  (a) terminal voltage under a PSoC cycle (Full vs. LOQS) and their RMSE;
  (b) reduced-order voltage RMSE vs. discharge current, with the wall-clock
      speed-up of LOQS over Full;
  (c) the terminal-voltage signature of electrolyte convection (the driver of
      stratification), obtained by enabling 'uniform transverse' convection in
      the Full model.

The comparison is illustrative (numerical), not an experimental validation.

Each panel is saved BOTH as a standalone PNG (one figure per simulation) and as
part of a single combined figure, so that the outputs match the manuscript
whether the panels are presented as one three-panel figure or as separate
figures.

Author:  Frederic Coupan
License: MIT (see LICENSE)
Tested:  Python 3.11, PyBaMM 26.6.2.0  (see requirements.txt)
Run:     python simulation_pybamm_psoc.py
Outputs: Figure2a_PSoC_cycle.png, Figure2b_error_vs_rate.png,
         Figure2c_convection_signature.png   (one PNG per simulation)
         Figure_PyBaMM_analysis.png          (combined three-panel figure)
         results_summary.csv                 (numerical values)
"""

import time
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pybamm

pybamm.set_logging_level("ERROR")

NAVY, RUST, GREEN, GREY = "#11365A", "#C1440E", "#2E7D32", "#7A7A7A"

SWEEP_CURRENTS_A = [1, 3, 6, 10, 15]   # discharge currents for panel (b)
PSOC_CURRENT_A   = 6                    # current used for the PSoC cycle (panel a)
CONV_CURRENT_A   = 10                   # current used for the convection test (panel c)
DPI              = 600
SAVE_PANELS      = True                 # save each simulation as its own PNG
SAVE_COMBINED    = True                 # also save the combined three-panel figure


def solve(model, experiment):
    """Solve a PyBaMM model for a given experiment; return (t[min], V, wall_time)."""
    sim = pybamm.Simulation(model, experiment=experiment)
    t0 = time.time()
    sol = sim.solve()
    return sol["Time [h]"].entries * 60.0, sol["Terminal voltage [V]"].entries, time.time() - t0


def rmse_mV(t1, V1, t2, V2, n=400):
    """RMSE (mV) between two voltage traces on a common interpolated grid."""
    tg = np.linspace(max(t1[0], t2[0]), min(t1[-1], t2[-1]), n)
    return np.sqrt(np.mean((np.interp(tg, t1, V1) - np.interp(tg, t2, V2)) ** 2)) * 1000.0


# ----------------------------------------------------------------------------
# Each panel is a plotting function that draws onto a given Axes. The same
# function is reused for the standalone PNG and for the combined figure, so the
# two never diverge.
# ----------------------------------------------------------------------------
def compute_panel_a():
    exp = pybamm.Experiment(
        [("Discharge at %d A for 20 minutes" % PSOC_CURRENT_A, "Rest for 10 minutes",
          "Charge at %d A for 14 minutes" % PSOC_CURRENT_A, "Rest for 10 minutes")] * 2)
    tF, VF, _ = solve(pybamm.lead_acid.Full(), exp)
    tL, VL, _ = solve(pybamm.lead_acid.LOQS(), exp)
    return dict(tF=tF, VF=VF, tL=tL, VL=VL, rmse=rmse_mV(tF, VF, tL, VL))


def draw_a(ax, d):
    ax.plot(d["tF"], d["VF"], color=NAVY, lw=2, label="Full (porous-electrode)")
    ax.plot(d["tL"], d["VL"], color=RUST, lw=1.5, ls="--", label="LOQS (reduced-order)")
    ax.set_xlabel("Time (min)"); ax.set_ylabel("Terminal voltage (V)")
    ax.set_title("(a) PSoC cycle at %d A" % PSOC_CURRENT_A, fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    ax.text(0.97, 0.96, "RMSE = %.1f mV" % d["rmse"], transform=ax.transAxes,
            ha="right", va="top", fontsize=9, color=GREY)


def compute_panel_b():
    rows = []
    for A in SWEEP_CURRENTS_A:
        exp = pybamm.Experiment(["Discharge at %d A for 18 minutes" % A])
        tF, VF, dF = solve(pybamm.lead_acid.Full(), exp)
        tL, VL, dL = solve(pybamm.lead_acid.LOQS(), exp)
        rows.append((A, rmse_mV(tF, VF, tL, VL), dF / dL))
        print("  %5.1f A | RMSE = %6.1f mV | speed-up x%.1f" % rows[-1])
    return np.array(rows)


def draw_b(ax, sweep):
    ax.plot(sweep[:, 0], sweep[:, 1], "o-", color=NAVY, lw=1.9, ms=6)
    ax.set_xlabel("Discharge current (A)"); ax.set_ylabel("Voltage RMSE vs Full (mV)")
    ax.set_title("(b) Reduced-order error vs rate", fontsize=10, loc="left")
    # speed-up is wall-clock and therefore machine-dependent; the figure uses a
    # neutral label and the measured per-current values are written to results_summary.csv
    ax.text(0.05, 0.93, "Speed-up: several-fold\n(machine-dependent)", transform=ax.transAxes,
            ha="left", va="top", fontsize=9, color=RUST)
    ax.grid(alpha=0.25)


def compute_panel_c():
    exp = pybamm.Experiment(["Discharge at %d A for 18 minutes" % CONV_CURRENT_A])
    tN, VN, _ = solve(pybamm.lead_acid.Full(), exp)
    tC, VC, _ = solve(pybamm.lead_acid.Full(options={"convection": "uniform transverse"}), exp)
    tg = np.linspace(max(tN[0], tC[0]), min(tN[-1], tC[-1]), 400)
    dV = (np.interp(tg, tC, VC) - np.interp(tg, tN, VN)) * 1000.0
    return dict(t=tg, dV=dV)


def draw_c(ax, d):
    ax.plot(d["t"], d["dV"], color=GREEN, lw=1.9); ax.axhline(0, color=GREY, lw=0.6)
    ax.set_xlabel("Time (min)"); ax.set_ylabel("ΔV with - without convection (mV)")
    ax.set_title("(c) Convection signature (%d A)" % CONV_CURRENT_A, fontsize=10, loc="left")
    ax.text(0.97, 0.06, "max |dV| = %.1f mV" % np.max(np.abs(d["dV"])), transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9, color=GREY)


def save_standalone(draw, data, fname, figsize=(5.2, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    draw(ax, data)
    plt.tight_layout()
    fig.savefig(fname, dpi=DPI, bbox_inches="tight", facecolor="white")
    fig.savefig(fname.replace(".png", ".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("Saved", fname)


def main():
    plt.rcParams.update({
        "font.size": 10,
        # Elsevier prefers Arial/Helvetica; fall back gracefully for portability
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.linewidth": 0.9,
    })

    print("Panel (a): PSoC cycle (Full vs LOQS) ...")
    a = compute_panel_a(); print("  RMSE under PSoC cycle = %.1f mV" % a["rmse"])
    print("Panel (b): RMSE vs current ...")
    b = compute_panel_b()
    print("Panel (c): convection (stratification) signature ...")
    c = compute_panel_c(); print("  max |dV| = %.2f mV" % np.max(np.abs(c["dV"])))

    # one PNG per simulation
    if SAVE_PANELS:
        save_standalone(draw_a, a, "Figure2a_PSoC_cycle.png")
        save_standalone(draw_b, b, "Figure2b_error_vs_rate.png")
        save_standalone(draw_c, c, "Figure2c_convection_signature.png")

    # combined three-panel figure (same drawing functions)
    if SAVE_COMBINED:
        fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.4), constrained_layout=True)
        draw_a(ax[0], a); draw_b(ax[1], b); draw_c(ax[2], c)
        for x in ax:
            x.tick_params(labelsize=8)
        fig.savefig("Figure_PyBaMM_analysis.png", dpi=DPI, bbox_inches="tight", facecolor="white")
        fig.savefig("Figure_PyBaMM_analysis.pdf", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print("Saved Figure_PyBaMM_analysis.png")

    # machine-readable results
    with open("results_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["panel", "metric", "value", "unit"])
        w.writerow(["a", "RMSE_PSoC_cycle", round(float(a["rmse"]), 2), "mV"])
        for A, r, s in b:
            w.writerow(["b", "RMSE_at_%dA" % int(A), round(float(r), 2), "mV"])
            w.writerow(["b", "speedup_at_%dA" % int(A), round(float(s), 2), "x"])
        w.writerow(["c", "max_abs_dV_convection", round(float(np.max(np.abs(c["dV"]))), 2), "mV"])
    print("Saved results_summary.csv")


if __name__ == "__main__":
    main()
