# PicoSOT — verified results (experiment log)

Detailed record of the mumax3 replica of Jhuria et al., *"Spin-orbit torque switching
of a ferromagnet with picosecond electrical pulses"*, Nature Electronics **3**, 680–686
(2020), doi:10.1038/s41928-020-00488-3.

All results below come from the time-exact scripts (`SetSolver(4)+FixDt` + real-time `J(t)`).

> **Data policy (2026-09-17):** raw run outputs (`simulations/mumax3_sot/runs/`)
> are kept locally — the deliverable carries code, docs and the final figures
> under `docs/figures/`. Paths like `runs/<tag>` below refer to the local run
> archive.

> **Status (2026-09-16):** results obtained with the **paper-parameter model**
> (model and parameters taken from the paper; see `docs/paper_replica.md`).

## Paper-parameter replica (2026-09-16)

The paper specifies
the complete macrospin model. All three .mx3 templates follow it.

### 1. Thermal model validation (`heat_model.py`)

* 1D FD solution of the paper's heat equation (C=2.6×10⁶ J/m³K, Λ=9 W/mK, G=170 MW/m²K,
  q=ρJ², adiabatic top): **peak Co rise +50.4 K at Jp=6×10¹² / 6 ps**, decay τ≈245 ps
  (=C·d/G). The paper states ~60 K average peak rise at 6×10¹² (incl. ~15 K
  electron–phonon non-equilibrium) → consistent.
* The 0D channel used inside the .mx3 loops (`dT/dt = ρJ²/C − T/τ`) deviates from
  the FD solution by at most **5.1%** over 0–450 ps.
* Consequence: `Tmax ≈ 300 + 50.4 K (Jp/6e12)²` is fixed by physics (no free knob).
* Figure: `docs/figures/heat_model.png`.

### 2. Switching thresholds (macrospin, 6 ps sech², Hx=160 mT)

| series | threshold Jc (mz<sub>final</sub> < −0.5) | Tmax at threshold |
|---|---|---|
| θ<sub>DL</sub>=0.2, with heating | (9, 10]×10¹² (switches from 10×10¹², t<sub>cross</sub> 68.3 ps) | (411,438] K |
| θ<sub>DL</sub>=0.2, heating off | 20×10¹² (19×10¹² → multidomain, excluded) | 300 K |
| θ<sub>DL</sub>=0.3, with heating | (8, 9]×10¹² | (388,411] K |
| θ<sub>DL</sub>=0.3, heating off | (12, 14]×10¹² (13×10¹² → multidomain, excluded) | 300 K |

* **Pure SOT does switch without Joule heating** — at ~2× the heated threshold
  (θ=0.2: 20 vs 10×10¹², energy ratio 4×; θ=0.3: ~13.5 vs ~8.5×10¹², energy ratio ~2.3×).
  This matches the ratio stated in the paper (pure LLG 9×10¹² vs heated 6×10¹²,
  energy ratio ~2×) **in ratio**; the absolute thresholds are ~1.5× higher here,
  most plausibly from the unknown pulse waveform/reflection sequence in the paper.
* Non-monotonic precessional windows (uniform single domain, |⟨m⟩|=1.000): with
  heating, θ=0.2 does **not** switch at **15–17×10¹²** and θ=0.3 at **14–17×10¹²**
  (+0.98 recapture); switching recovers at **18×10¹²** and persists to 30×10¹²
  (full scan; no further windows); 0.4 ns snapshots read +0.96 while the
  1.5 ns relaxed value is +0.981.
* The θ=0.3 **no-heating** series was extended from 16 to 30×10¹²
  (Jp = 17, 18, 20, 22, 24, 26, 28, 30×10¹², t_free = 1.5 ns, all uniform
  −0.981; 17/18×10¹² also switch): t_cross falls monotonically from 40.0 ps
  (17×10¹²) to 28.9 ps (30×10¹²), so the green curve in `phase_speed.png` /
  `phase_map.png` now spans the same current range as the θ=0.2 series.
* Figures: `docs/figures/phase_map.png`, `phase_speed.png`, `phase_traces.png`.

### 3. Late-time verification and domain artefacts (2026-09-17)

Motivated by the non-monotonic window, the heated θ=0.2/0.3 series and every
boundary point were re-run with `t_free=1500 ps` (temperature back to ~300 K; all
uniform states settle to |mz|≈0.981):

* **Reproducibility**: re-running `si_h_t20_Jp15` with identical parameters
  reproduces the archived `table.txt` to a maximum deviation of 2.5×10⁻⁷ (GPU
  reduction rounding only); the window is deterministic, and halving `FixDt`
  (25 fs) changes nothing.
* The 0.4 ns snapshot understates |mz| near the boundaries (e.g. θ=0.2 heated
  14×10¹² reads −0.76 vs −0.981 relaxed); the map uses the `*_lr1500` runs
  wherever they exist.
* **Domain artefacts**: at some near-threshold / extreme points the 64×64 film is
  **not** a single domain at the end of the run; the OVF shows stripe domains
  (mz spans ±0.99, |⟨m⟩|≈0.28–0.58, wall width √(A/Kz)≈5 nm ≈ cell size, i.e. the
  pseudo-macrospin is at its resolution limit). Such points are invalid as
  macrospin outcomes and are excluded from the map lines (grey crosses):
  θ=0.2 heated 27×10¹², θ=0.2 no-heat 19×10¹², θ=0.3 heated 14×10¹²,
  θ=0.3 no-heat 13×10¹².
* **High-current scan** (θ=0.2, 21–30×10¹² in 1×10¹² steps, heating on and off):
  all points are uniform switches except the 27×10¹² domain artefact — **no
  second precessional window**. Tmax>Tc from ~19×10¹², so this range is outside
  the calibrated heat model and is quoted as a trend only.
* **Hot-branch re-run (2026-09-17)**: the θ=0.2 heated points 21–30×10¹² were
  re-run from the archived scripts (outputs in `runs/_verify/`). Final states
  (all −0.9807) and t_cross (≤0.1 ps) reproduce. Traces: 7/9 bit-identical
  (≤2×10⁻⁷, GPU rounding), 24/25/26/30 differ by ~10⁻⁴, and 22×10¹² deviates
  transiently by up to 0.16 during the ~400 ps recovery (T≈430 K, |⟨m⟩| small,
  multidomain transient) but converges to the same state. While T≥800 K the
  film is demagnetized (mumax3 prints `Note: Msat = 0`), and the first zero
  crossing sits within a few ps of the time T drops back below Tc
  (e.g. 30×10¹²: 269.6 ps vs 261.7 ps) → the rising t_cross beyond 20×10¹² is
  the cooling time through Tc, not a switching speed. At 20×10¹² the crossing
  (26.2 ps) happens just before T reaches 800 K (26.5 ps), so it is still a
  genuine SOT crossing; the 20→21×10¹² jump marks the onset of the
  demagnetization-dominated regime. `phase_speed.png` therefore cuts every
  heated series at Tmax ≤ Tc (θ=0.2: 19×10¹², θ=0.3: 18×10¹²) and draws the
  excluded points as grey crosses.

### 4. Pulse-width window (θ=0.2, Jp=10×10¹², heating off)

No switching for 6/8/10/12 ps; **15 ps partial (−0.93), 20/30 ps full reversal** →
the half-precession-period condition (~18–19 ps) appears exactly where the paper
puts the energy minimum ("10–20 ps" in the paper).

### 5. Mechanism decomposition (heating on, θ=0.2)

| control | setting | result |
|---|---|---|
| Kz(T) frozen | `ScaleKz=0` (Ms(T) still on) | **no switching up to 14×10¹²** → Kz(T) collapse is the necessary channel |
| Ms(T) frozen | `ScaleMs=0` (Kz(T) on) | 10×10¹² partial +0.45, 12×10¹² partial −0.46 → Kz collapse alone nearly switches |
| θ≈0 (thermal-anisotropy torque only) | `ThetaDL=1e-4, EpsilonPrime=0` | switches at 12×10¹² (122.5 ps) and 14×10¹² (80.2 ps) → paper behaviour (slower, hotter) |
| Hx=0 | `Hx_mT=0` | never switches (macrospin and full device, +1.0000) |
| Langevin noise | `Noise=1` | Jp=9×10¹²: no-flip → partial (−0.32); Jp=10×10¹² −0.94; repeat runs are bit-identical (fixed seed) → no P<sub>sw</sub> statistics possible in-script |

Figure: `docs/figures/mechanism_compare.png`.

### 6. Full device (5×4 µm, 10 nm cells)

* Four quadrants at Jpk=1.2×10¹³ (Tmax=497 K): q1 −0.971, q2 +0.970, q3 +0.970,
  q4 −0.971 → `sign(mz_final) = −sign(Hx·I)` (paper Fig. 3), uniform single domains.
* Device threshold with heating (θ=0.2): no switching at 8/9×10¹², switching from
  10×10¹² — consistent with the macrospin threshold; no nucleation-induced reduction
  on this clean 10 nm grid.
* Figures: `docs/figures/q_quadrants.png`.

### 7. Fig. 4 dynamics (3.7 ps, Jpk=4×10¹², echo=0.3/ted=24 ps)

* Parallel group: dip −5.9% at ~29 ps; antiparallel: −1.9% at ~17 ps, no positive
  overshoot; Hx=0: pure demagnetization, no oscillation. Precession period ≈44 ps
  (paper: ~40 ps). Peak ΔT = +13.9 K (heat model predicts 13.8 K).
* Figure: `docs/figures/fig4_full.png`.

### 8. Energy

6×10¹² → 39.7 pJ (paper's budget scale); model threshold 10×10¹² (θ=0.2) → **110 pJ**;
θ=0.3 threshold 9×10¹² → 90 pJ; pure-SOT 20×10¹² → 441 pJ. The model therefore exceeds
the paper's <50 pJ budget at its own switching threshold (the paper's budget
corresponds to 6×10¹²). Figure: `docs/figures/energy_bars.png`.

### 9. Caveats

* Pulse waveform: the paper never specifies it; we keep sech². Absolute Jc carries a
  ~1.5× uncertainty relative to the paper's 9×10¹²/6×10¹².
* θ<sub>DL</sub>: main-text fit 0.2, strong-current simulations use 0.3; both are provided (`ThetaDL`).
* Jp ≳ 1.9×10¹³ drives the paper's heat model through Tc (Ms→0): HAMR-like regime, which
  the paper excludes experimentally — treat such cases as model artefacts.
* Langevin noise uses a fixed seed in mumax3 → deterministic repeats; P<sub>sw</sub>
  statistics require kernel/driver work.

---

Documentation in this file is licensed under CC BY 4.0 (see `LICENSE-docs`).
