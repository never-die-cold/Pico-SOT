# PicoSOT — verified results (experiment log)

Detailed record of the mumax3 replica of Jhuria et al., *"Spin-orbit torque switching
of a ferromagnet with picosecond electrical pulses"*, Nature Electronics **3**, 680–686
(2020), doi:10.1038/s41928-020-00488-3.

All results below come from the corrected, time-exact scripts (`SetSolver(4)+FixDt` +
real-time `J(t)`); see the historical note at the end.

## 1. Model and timing calibration

* `macrospin_switch.mx3`: 64×64 cells, 5 nm cell size (320×320 nm), Co thickness 1 nm,
  `Ms=1.3e6 A/m`, `Ha=1 T`, `alpha=0.15`, sech² pulse with FWHM=6 ps.
* Measured pulse width: **5.85 ps**.
* Relaxed equilibrium with `Hx=160 mT`: `mz ≈ 0.988 ≈ cos[atan(Hx/Ha)]`, as expected for
  the tilted equilibrium state.
* Energy accounting (`energy_check.py`, ρ=81 µΩ cm, V=5×4 µm²×15 nm): `∫J²dt` for the
  6 ps pulse gives **39.7 pJ at Jp=6e12**, consistent with the paper's 40 pJ.

## 2. B1 — switching threshold (J_ref=Jp, dT ∝ J²)

| Jp (A/m²) | dT_ref | Tmax | mz zero crossing | Final mz | Energy | Outcome |
|---|---|---|---|---|---|---|
| 6e12 | 300 K | 583 K | – | +0.988 | 39.7 pJ | no switching |
| 8e12 | 450 K | 725 K | 58.6 ps | −0.988 | 70.6 pJ | switches |
| 1.0e13 | 300 K | 583 K | 88.8 ps | −0.11 | – | partial |
| 1.2e13 | 450 K | 725 K | 50.1 ps | −0.988 | 158.9 pJ | switches |
| 2.0e13 | 450 K | 725 K | **39.0 ps (fastest)** | −0.988 | 441 pJ | switches (paper's model: 16 ps) |

At the paper's current ceiling (6e12) the model does not switch with dT=300 K; the
remaining 16 ps vs 39 ps gap and the energy gap trace back to the unpublished SI
parameters.

## 3. Four-quadrant polarity check (Fig. 3)

`fig3_switching.mx3` defaults: `Jpk=1.2e13`, `dTpk=400 K`, `Tmax=680 K` (< Tc); mz crosses
zero within ~50 ps; final |mz|≈0.96.

| Case | Hx | I_sign | Final mz |
|---|---|---|---|
| q1 | +160 mT | +1 | −0.956 |
| q2 | −160 mT | +1 | +0.987 |
| q3 | +160 mT | −1 | +0.987 |
| q4 | −160 mT | −1 | −0.956 |

i.e. `sign(mz_final) = −sign(Hx·I)`, matching the paper's Fig. 3. Final-state panels
(`runs/q_quadrants.png`, `plot_quadrants.py`) show uniform single domains in all four
quadrants (no domain walls; only the open-boundary edge columns remain pinned). All batch
runs start from the +Mz state; the paper's "independent of initial state" claim was not
separately re-run here.

## 4. C2 — Hx=0 symmetry control

`runs/c2_Hx0_Jp8_dT450`, identical to `b1_Jp8_dT450` (`Jp=8e12`, `dT_ref=450`,
`I_sign=+1`) except `Hx_mT=0`: transient minimum mz=0.80 at 40.2 ps, then recovery; final
**+1.0000**, no zero crossing (`t_cross` empty, Tmax=725 K). Contrast with the 58.6 ps
switching at `Hx=+160 mT` → `Hx≠0` is required to break the symmetry.

## 5. B2 — θ≈0 control

`Pol=1e-4`, `EpsilonPrime=0`, `Jp=8e12`:

* dT=300 K: no switching.
* dT=450/600/800 K: switching with zero crossings at **85.9/92.3/122.4 ps**
  (Tmax = 725/867/1056 K).

Thermal anisotropy torque alone can switch the magnet, but more slowly and with stronger
heating; qualitatively consistent with the paper's SI Fig. 5.

## 6. B3 — Ku(T) switch-off

* `KuExp=0` (temperature-independent Ku): no switching even at Jp=1.4e13.
* `KuExp=3` (Ku ∝ Ms³): partial switching at 1e13 (final −0.11), full switching at 1.2e13.

The thermal anisotropy torque is essential in this model; the threshold energy ratio is
≥ 2, matching the paper's "2× lower energy" statement.

## 7. C0 — Heating=0 control

Same parameters as `b0_6e12` / `b0_8e12` / `b1_Jp10_dT300`, heating off
(`runs/c0_noh_*`, `runs/heating_on_off.png`):

| Jp (A/m²) | T | Final mz | Peak transient dip |
|---|---|---|---|
| 6e12 | 300 K | +0.988 | −8.1% |
| 8e12 | 300 K | +0.988 | −12.4% |
| 10e12 | 300 K | +0.988 | −17.6% |

All three fail to switch. The transient dip (~33 ps) is measured relative to the relaxed
equilibrium mz=0.988 (the first table row at t=0 is the un-relaxed mz=1 state and must not
be used as a baseline). Deterministic switching at 6–10e12 therefore relies entirely on
the Joule-heating-induced thermal anisotropy torque.

## 8. C1 — phase-boundary midpoints (J_ref=Jp)

| Jp (A/m²) | dT_ref | Tmax | Outcome | Zero crossing | Energy |
|---|---|---|---|---|---|
| 9e12 | 300 K | 583 K | no switch (final +0.933) | – | – |
| 8e12 | 375 K | 654 K | switches | 66.5 ps | – |
| 7e12 | 450 K | 725 K | switches | 61.0 ps | 54.1 pJ |
| 6e12 | 600 K | 867 K | switches | 80.5 ps | 39.7 pJ (Tmax > Tc) |

Boundary localization: `Jc ∈ (9,10]e12` on the Tmax≈583 K line; `dTc ∈ (300,375] K` on the
Jp=8e12 line. 7e12 switches at Tmax=725 K; 6e12 needs Tmax≳867 K (hotter and slower).
Final figures: `runs/phase_map.png`, `runs/phase_traces.png`, `runs/phase_speed.png`
(`plot_phase.py`; the grey diamonds in the phase map are the C2 Hx=0 control points and are
excluded from the boundary fit).

Additional point: `b0_8e12` (`J_ref=6e12`, `dT_ref=300 K` → Tmax=804 K) switches at
54.5 ps.

## 9. Fig. 4 dynamics

`runs/a_f4_*` (Hx ∈ {0,±160 mT} × I±, `echo=0.3`, `ted=24 ps`), combined figure
`runs/fig4_full.png` (`plot_fig4.py`, legend grouped into parallel / antiparallel / no Hx):

* Precession period ≈ 37 ps (paper: ~40 ps for Ha≈1 T).
* `Hx=0`: ±I curves coincide, no oscillation (simple dip + slow recovery).
* Parallel group (Hx+,I+) and (Hx−,I−) coincide: dip −4.8% @15.8 ps followed by
  out-of-phase precession.
* Antiparallel group (Hx+,I−) and (Hx−,I+) coincide: **no positive overshoot** in the
  plotted ΔMz/Ms (minimum −3.5% @31.8 ps); the raw mz rises from 0.987 to 0.999 but this is
  masked by the drop in Ms(T). The +1.3% spike at t=0 in figures/tables is an un-relaxed
  first-row (mz=1) artifact present in every Hx≠0 curve, not an antiparallel feature.
* All curves recover to ≈ −0.25% after 400 ps.
* The echo appears as a secondary peak in T(t) at ~29–31 ps (main pulse t0=5 ps, so
  t0+ted ≈ 29 ps) and gives the magnetization a secondary kick.

Early-reference re-run: `runs/dyn_Jp1e12_Ip` (`RunDynamics=1`, 3.7 ps FWHM, Jp=1e12) gives
Tmax≈308 K, mz_final=+0.9879 (no switching), consistent with the early reference; the
switching-type reference is `runs/b0_6e12`.

## 10. Mechanism overview figure

`runs/mechanism_compare.png` (`plot_mechanism.py`) shows three panels side by side:
(a) c0/b0 heating on/off, (b) b2 θ≈0, (c) b3 Ku(T) frozen. Solid/dashed lines are the
control arms of each condition; thin dash-dotted lines of the same color show the
corresponding T(t).

## 11. Energy summary

| Case | Energy | Note |
|---|---|---|
| 6e12, dT=300 K | 39.7 pJ | no switching |
| 6e12, dT=600 K | 39.7 pJ | switches, Tmax=867 K > Tc (HAMR-like regime the paper excludes) |
| 7e12, dT=450 K | 54.1 pJ | switches; lowest energy that switches without exceeding Tc |
| 8e12, dT=450 K | 70.6 pJ | switches |
| 1.2e13, dT=450 K | 158.9 pJ | switches |
| 2.0e13, dT=450 K | 441 pJ | switches, fastest (39 ps) |

The model can switch at the paper's current ceiling (6e12) and fall back under the <50 pJ
budget only with strong (above-Tc) heating; without exceeding Tc the lowest switching
energy observed is 54.1 pJ at 7e12/dT450.

## 12. Historical correction

The early adaptive-step "Jp=6e12 switching" was an artifact of the pulse being stretched
to 27.6 ps (corresponding to 189 pJ). Those outputs were deleted and equivalent cases were
re-run with the corrected scripts (switching `runs/b0_6e12`, dynamics `runs/dyn_Jp1e12_Ip`).
See `notes/error.md` §1.11 for details.

---

Documentation in this file is licensed under CC BY 4.0 (see `LICENSE-docs`).
