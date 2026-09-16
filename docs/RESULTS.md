# PicoSOT — verified results (experiment log)

Detailed record of the mumax3 replica of Jhuria et al., *"Spin-orbit torque switching
of a ferromagnet with picosecond electrical pulses"*, Nature Electronics **3**, 680–686
(2020), doi:10.1038/s41928-020-00488-3.

All results below come from the corrected, time-exact scripts (`SetSolver(4)+FixDt` +
real-time `J(t)`); see the historical note at the end.

> **Status (2026-09-16):** sections 0.x are the current results, obtained with the
> **SI-parameter model** (Supplementary Note 3 of the paper; see `docs/si_replica.md`).
> Sections 1–8 further below are the **legacy** record (guessed parameters:
> Ms=1.3e6, Ha=1 T, alpha=0.15, free dT_ref knob) kept for traceability; those
> conclusions are superseded wherever they conflict with section 0.

## 0. SI-parameter replica (2026-09-16) — current results

The paper's own Supplementary Information (local copy: `notes/NE_2020SI/`) specifies
the complete macrospin model. All three .mx3 templates were refactored to it
(`model=si` in `runs/summary.csv`); the legacy runs are kept with `model=legacy`.

### 0.1 Thermal model validation (`heat_model.py`)

* 1D FD solution of the SI heat equation (C=2.6e6 J/m³K, Λ=9 W/mK, G=170 MW/m²K,
  q=ρJ², adiabatic top): **peak Co rise +50.4 K at Jp=6e12 / 6 ps**, decay τ≈245 ps
  (=C·d/G). The paper states ~60 K average peak rise at 6e12 (incl. ~15 K
  electron–phonon non-equilibrium) → consistent.
* The 0D channel used inside the .mx3 loops (`dT/dt = ρJ²/C − T/τ`) deviates from
  the FD solution by at most **5.1%** over 0–450 ps.
* Consequence: `Tmax ≈ 300 + 50.4 K (Jp/6e12)²` is now fixed by physics; the legacy
  free knob `dT_ref=300–600 K` (peak 583–867 K, i.e. ~6× too hot) is gone.
* Figure: `runs/heat_model.png`.

### 0.2 Switching thresholds (macrospin, 6 ps sech², Hx=160 mT)

| series | threshold Jc (mz_final < −0.5) | Tmax at threshold |
|---|---|---|
| θ_DL=0.2, SI heating | (9,10]e12 (switches from 10e12, t_cross 68.3 ps) | (411,438] K |
| θ_DL=0.2, heating off | 20e12 (19e12 partial, −0.47) | 300 K |
| θ_DL=0.3, SI heating | (8,9]e12 | (388,411] K |
| θ_DL=0.3, heating off | (12,14]e12 (13e12 partial, −0.10) | 300 K |

* **Pure SOT does switch without Joule heating** — at ~2× the heated threshold
  (θ=0.2: 20 vs 10e12, energy ratio 4×; θ=0.3: ~13.5 vs ~8.5e12, energy ratio ~2.3×).
  This matches the paper's SI Fig. 3/4 statement (pure LLG 9e12 vs heated 6e12,
  energy ratio ~2×) **in ratio**; the absolute thresholds are ~1.5× higher here,
  most plausibly from the unknown pulse waveform/reflection sequence in the SI.
* Non-monotonic precessional windows: with heating, θ=0.2 does **not** switch at
  15–16e12 (mz_final +0.96) but switches again at 18/20e12; θ=0.3 heated is partial
  at 14e12 (+0.20).
* Figures: `runs/phase_map.png`, `phase_speed.png`, `phase_traces.png`.

### 0.3 Pulse-width window (θ=0.2, Jp=10e12, heating off)

No switching for 6/8/10/12 ps; **15 ps partial (−0.93), 20/30 ps full reversal** →
the half-precession-period condition (~18–19 ps) appears exactly where the paper
puts the energy minimum ("10–20 ps", SI Note 3.5).

### 0.4 Mechanism decomposition (SI heating, θ=0.2)

| control | setting | result |
|---|---|---|
| Kz(T) frozen | `ScaleKz=0` (Ms(T) still on) | **no switching up to 14e12** → Kz(T) collapse is the necessary channel |
| Ms(T) frozen | `ScaleMs=0` (Kz(T) on) | 10e12 partial +0.45, 12e12 partial −0.46 → Kz collapse alone nearly switches |
| θ≈0 (thermal-anisotropy torque only) | `ThetaDL=1e-4, EpsilonPrime=0` | switches at 12e12 (122.5 ps) and 14e12 (80.2 ps) → SI Fig. 5 behaviour (slower, hotter) |
| Hx=0 | `Hx_mT=0` | never switches (macrospin and full device, +1.0000) |
| Langevin noise | `Noise=1` | Jp=9e12: no-flip → partial (−0.32); Jp=10e12 −0.94; repeat runs are bit-identical (fixed seed) → no P_sw statistics possible in-script |

Figure: `runs/mechanism_compare.png`.

### 0.5 Full device (5×4 µm, 10 nm cells)

* Four quadrants at Jpk=1.2e13 (Tmax=497 K): q1 −0.971, q2 +0.970, q3 +0.970,
  q4 −0.971 → `sign(mz_final) = −sign(Hx·I)` (paper Fig. 3), uniform single domains.
* Device threshold with SI heating (θ=0.2): no switching at 8/9e12, switching from
  10e12 — consistent with the macrospin threshold; no nucleation-induced reduction
  on this clean 10 nm grid.
* Figures: `runs/q_quadrants.png`.

### 0.6 Fig. 4 dynamics (3.7 ps, Jpk=4e12, echo=0.3/ted=24 ps)

* Parallel group: dip −5.9% at ~29 ps; antiparallel: −1.9% at ~17 ps, no positive
  overshoot; Hx=0: pure demagnetization, no oscillation. Precession period ≈44 ps
  (paper: ~40 ps). Peak ΔT = +13.9 K (heat model predicts 13.8 K).
* Figure: `runs/fig4_full.png`.

### 0.7 Energy

6e12 → 39.7 pJ (paper's budget scale); SI-model threshold 10e12 (θ=0.2) → **110 pJ**;
θ=0.3 threshold 9e12 → 90 pJ; pure-SOT 20e12 → 441 pJ. The model therefore exceeds
the paper's <50 pJ budget at its own switching threshold (the paper's budget
corresponds to 6e12). Figure: `runs/energy_bars.png`.

### 0.8 Caveats

* Pulse waveform: SI never specifies it; we keep sech². Absolute Jc carries a
  ~1.5× uncertainty relative to the SI's 9e12/6e12.
* θ_DL: main-text fit 0.2, SI Figs. 3–5 use 0.3; both are provided (`ThetaDL`).
* Jp ≳ 1.9e13 drives the SI heat model through Tc (Ms→0): HAMR-like regime, which
  the paper excludes experimentally — treat such cases as model artefacts.
* Langevin noise uses a fixed seed in mumax3 → deterministic repeats; P_sw
  statistics require kernel/driver work (ROADMAP P1).

## 1. Model and timing calibration (legacy)

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
