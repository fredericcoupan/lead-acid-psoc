# Stratification-aware lead–acid PSoC analysis

Reproducible code for **Figure 2** of:

> Frédéric Coupan, Ahmed Abbas, *Stratification-Aware Modelling of Lead–Acid Batteries under
> Partial-State-of-Charge Renewable Duty*, Journal of Energy Storage (submitted, 2026).

The script compares the **full porous-electrode** lead–acid model with its
**leading-order reduced-order** approximation (LOQS) under partial-state-of-charge
(PSoC) duty, using the open-source [PyBaMM](https://www.pybamm.org) framework.
All results use default parameters with **no fitting**; the comparison is
illustrative (numerical), not an experimental validation.

## What it computes

| Panel | Quantity |
|-------|----------|
| (a) | Terminal voltage under a PSoC cycle (Full vs. LOQS) and their RMSE |
| (b) | Reduced-order voltage RMSE vs. discharge current, with the LOQS/Full speed-up |
| (c) | Terminal-voltage signature of electrolyte convection (driver of stratification) |

The central finding supporting the paper: enabling electrolyte convection in the
full model changes the terminal voltage by **< 1 mV**, i.e. stratification is a
hidden internal state with almost no terminal-measurement signature.

## Installation

```bash
python -m venv venv && source venv/bin/activate    # optional
pip install -r requirements.txt
```

## Usage

```bash
python simulation_pybamm_psoc.py
```

## Outputs

The script saves **each simulation as its own file** (PNG + vector PDF) and also a
combined figure, so the code reproduces the manuscript whether the panels are shown
as one three-panel figure or as separate figures:

- `Figure2a_PSoC_cycle.png` / `.pdf` — terminal voltage under a PSoC cycle (Full vs. LOQS).
- `Figure2b_error_vs_rate.png` / `.pdf` — reduced-order RMSE vs. discharge current.
- `Figure2c_convection_signature.png` / `.pdf` — terminal-voltage signature of convection.
- `Figure_PyBaMM_analysis.png` / `.pdf` — the combined three-panel figure.
- `results_summary.csv` — the numerical values (RMSE, per-current speed-ups, max |dV|).

**Note on the speed-up.** The Full-vs-LOQS speed-up is a wall-clock measurement and
therefore depends on the computing environment (it has been observed in the range of
roughly x4–9 on different machines). For this reason the figures use a neutral,
machine-independent label ("several-fold"), while the exact per-current values measured
on a given run are written to `results_summary.csv`. The accuracy metrics (RMSE, dV)
are deterministic and reproducible across machines.

The flags `SAVE_PANELS` and `SAVE_COMBINED` at the top of the script control
which figures are written.


## Environment

Tested with Python 3.11 and the versions pinned in `requirements.txt`
(PyBaMM 26.6.2.0). Results are deterministic; values may shift at the
millivolt level with other PyBaMM releases.

## Citation

If you use this code, please cite the article above and PyBaMM
(Sulzer et al., *Journal of Open Research Software*, 2021).

## License

MIT — see `LICENSE`.
