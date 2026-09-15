# PicoSOT

**English** | [简体中文](README.zh-CN.md)

**mumax3 replica: spin-orbit torque switching with picosecond electrical pulses**

![license: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)
![docs: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey.svg)
![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)
![mumax3 v3.12](https://img.shields.io/badge/mumax3-v3.12-orange.svg)

A [mumax3](https://mumax.github.io/) replica of:

> K. Jhuria, J. Hohlfeld, ... J. Gorchon,
> **"Spin-orbit torque switching of a ferromagnet with picosecond electrical pulses"**,
> *Nature Electronics* **3**, 680-686 (2020).
> doi: [10.1038/s41928-020-00488-3](https://doi.org/10.1038/s41928-020-00488-3)

Stack: `Ta(5)/Pt(4)/Co(1)/Cu(1)/Ta(4)/Pt(1) nm` with a perpendicularly magnetized
Co layer (PMA). Key paper parameters: anisotropy field `Ha ≈ 1 T`,
`theta_DL = 0.20`, `theta_FL = 0.05`, in-plane bias field `Hx = ±160 mT`,
time-resolved pulse `3.7 ps`, switching pulse `6 ps`, and a picosecond
current-density ceiling `Jc ≈ 6e12 A/m^2`.

## Results at a glance

| ![](simulations/mumax3_sot/runs/phase_map.png) | ![](simulations/mumax3_sot/runs/mechanism_compare.png) |
|---|---|
| **Phase map**: `Jp–Tmax` switching boundary (`plot_phase.py`) | **Mechanism controls**: heating on/off, θ≈0, Ku(T) frozen (`plot_mechanism.py`) |

| ![](simulations/mumax3_sot/runs/fig4_full.png) | ![](simulations/mumax3_sot/runs/q_quadrants.png) |
|---|---|
| **Fig. 4 dynamics**: ΔMz(t) for 6 Hx/I combinations + echo (`plot_fig4.py`) | **Quadrants**: final states, uniform single domain (`plot_quadrants.py`) |

---

## 1. Repository layout

```
README.md                              # project overview (this file, English)
README.zh-CN.md                        # Chinese version
FACTS.md                               # fact sheet: parameters / conventions / verified results (Chinese)
CITATION.cff                           # citation metadata (GitHub "Cite this repository")
LICENSE                                # MIT (code)
LICENSE-docs                           # CC BY 4.0 (documentation)
requirements.txt                       # Python dependencies for post-processing scripts
docs/
├─ RESULTS.md                          # full experiment log (verified results, English)
└─ ROADMAP.md                          # improvement plan and TODO list (Chinese)
papers/                                # references (PDFs are not redistributed)
├─ README.md                           # DOI list for NE 2020 / NC 2026 / AM 2023
└─ mumax3_docs/                        # mumax3 papers, tutorial and related refs (local only)
notes/                                 # working notes; only error.md is published
└─ error.md                            # mumax3 replica pitfalls (published)
simulations/
└─ mumax3_sot/                         # main workdir: time-exact scripts + batch results
   ├─ fig4_dynamics.mx3                # Fig.4 dynamics: PBC infinite film + echo + RK4
   ├─ fig3_switching.mx3               # Fig.3 5x4 um device single-pulse switching (fixed step)
   ├─ macrospin_switch.mx3             # 64x64 fast-switching template (Jp/dT_ref/KuExp/theta knobs)
   ├─ run_case.py                      # batch run + archive: runs\<tag>\{<tag>.mx3, out\}
   ├─ plot_table.py                    # table.txt -> dMz/Ms, dT curves
   ├─ plot_phase.py                    # summary.csv -> Jp-Tmax phase map and boundary curves
   ├─ plot_fig4.py                     # a_f4_* -> Fig.4 dMz(t) (parallel/antiparallel/no Hx)
   ├─ plot_mechanism.py                # c0/b0, b2, b3 mechanism comparison, 3 panels
   ├─ plot_quadrants.py                # q1-q4 m_final.ovf -> final-state 2x2 panels
   ├─ energy_check.py                  # energy accounting \int J^2 dt rho V (vs paper <50 pJ)
   ├─ fig3_switching.out/              # Fig.3 device reference run output
   ├─ fig4_dynamics.out/               # Fig.4 reference run output
   └─ runs/                            # batch results: summary.csv + final figures + per-case table/log/ovf
```

* `simulations/mumax3_sot/fig4_dynamics.mx3` — models an infinite film with `SetPBC`,
  a Gaussian pulse and an optional transmission-line echo; outputs `T(t)`, `J(t)`, `Ms(t)`
  for direct comparison with the paper's Fig. 4a/4b.
* Other notes (paper translation, handover doc, slide outline, ...) are local working
  drafts and are not published; the only published note is `notes/error.md`.

## 2. Quick start

Requirements: Python 3.12 (`pip install -r requirements.txt`) and
[mumax3](https://mumax.github.io/) v3.12 (CUDA 12.9, NVIDIA GPU).

```powershell
# Recommended: run through run_case.py (auto-archiving + parameter substitution)
# If mumax3 is not at the default path: set MUMAX3_BIN, or pass --mumax <path>
python simulations/mumax3_sot/run_case.py `
    simulations/mumax3_sot/macrospin_switch.mx3 b1_Jp8dT450 `
    --set Jp=8e12 J_ref=8e12 dT_ref=450
```

All knobs live in the **user parameter block** at the top of `macrospin_switch.mx3`:

| Variable | Meaning |
|---|---|
| `RunDynamics` | 0 = 6 ps switching experiment; 1 = 3.7 ps time-domain response |
| `I_sign` | current polarity, `+1` corresponds to the paper's `+I` |
| `InitMz` | initial state, `+1` (up) / `-1` (down) |
| `Hx_mT` | in-plane bias field (mT) |
| `Jp` | peak current density (A/m²) |
| `Heating` / `dT_ref` / `J_ref` / `tau_cool` | Joule-heating model switch and calibration |
| `KuExp` | `Ku(T)=Ku0·(Ms(T)/Ms0)^KuExp`; `0` disables Ku(T) (used for B3) |
| `t_free` | free evolution time after the pulse |

## 3. Two key conventions (pitfalls)

1. **Anisotropy**: mumax3's `Ku1` is the *total* uniaxial anisotropy, so the thin-film
   demagnetizing energy has to be added explicitly:

   ```go
   Keff  := 0.5*Ms*Ha_T                  // Ha_T in tesla as a B field; Keff = 1/2*Ms*Ha_T
   Ku1    = Keff + 0.5*mu0*Ms*Ms         // Ms=1.3e6, Ha=1T -> Keff=6.5e5, Ku1=1.71e6 J/m^3
   ```

   Writing `0.5*mu0*Ms*1.0` (treating 1 T as A/m) yields `Ku1 ≈ mu0*Ms²/2`:
   PMA disappears, the magnetization relaxes in-plane, and it **looks like
   "switching is impossible"**.

2. **How SOT is injected**: mumax3 has no native SOT, so the standard approach uses the
   Slonczewski module — but the `cuda/slonczewski2.cu` kernel **reads only the
   z component of the current density**, hence:

   ```go
   FixedLayer   = vector(0, 1, 0)   // spin polarization sigma along y (SOT geometry, current along x)
   Pol          = 0.20              // = theta_DL
   EpsilonPrime = 0.05              // = theta_FL
   Lambda       = 1                 // Slonczewski efficiency eps = Pol/2 = standard spin-Hall factor
   J            = vector(0, 0, J_eff)
   DisableZhangLiTorque = true      // Xi only affects Zhang-Li, irrelevant to SOT
   ```

   With `J = vector(Jc, 0, 0)` the torque is identically zero.

**Polarity calibration** (measured in-script, consistent with the paper's Fig. 3):

| Hx | I_sign | final state |
|---|---|---|
| +160 mT | +1 | −Mz |
| +160 mT | −1 | +Mz |
| −160 mT | +1 | +Mz |
| −160 mT | −1 | −Mz |

i.e. `sign(mz_final) = -sign(Hx·I)` (all current batch runs start from +Mz; "independent of
the initial state" is the paper's conclusion, not separately reproduced here); `Hx = 0`
does not switch (symmetry breaking is required).

## 4. Verified results (2026-09-15, time-exact 6 ps pulse)

> Full experiment log (all controls and energy accounting) in [`docs/RESULTS.md`](docs/RESULTS.md).

`macrospin_switch.mx3` (64×64, 5 nm cells, `Ms=1.3e6 A/m`, `Ha=1 T`, `alpha=0.15`,
sech² pulse FWHM=6 ps, measured 5.85 ps). Energy accounting (`energy_check.py`,
ρ=81 µΩ cm, V=5×4 µm²×15 nm): **39.7 pJ at Jp=6e12**, consistent with the paper's 40 pJ.

**B1 switching (J_ref=Jp, dT ∝ J²)**

| Condition | Tmax | mz zero crossing | Final mz | Energy | Outcome |
|---|---|---|---|---|---|
| Jp=6e12, dT=300 K | 583 K | – | +0.988 | 39.7 pJ | **no switching** (not even at the paper's current ceiling) |
| Jp=8e12, dT=450 K | 725 K | 58.6 ps | −0.988 | 70.6 pJ | switches |
| Jp=1.2e13, dT=450 K | 725 K | 50.1 ps | −0.988 | 158.9 pJ | switches |
| Jp=2.0e13, dT=450 K | 725 K | **39.0 ps (fastest)** | −0.988 | 441 pJ | paper's model predicts 16 ps; gap comes from SI parameters |

**Controls and mechanism experiments**

* **Quadrants**: `sign(mz_final) = −sign(Hx·I)`; `Hx=0` does not switch (C2, `runs/q_quadrants.png`).
  Final states are uniform single domains (no domains walls; only the open-boundary edge
  columns stay pinned).
* **B2 θ≈0** (`Pol=1e-4, EpsilonPrime=0`, Jp=8e12): no switching at dT=300 K; switches at
  dT=450/600/800 K after **85.9/92.3/122.4 ps** → qualitatively reproduces SI Fig. 5
  (thermal anisotropy torque alone can switch, but slower and hotter).
* **B3 Ku(T) switch-off**: `KuExp=0` (T-independent Ku) does not switch even at Jp=1.4e13;
  `KuExp=3` partially switches at 1e13 (final −0.11) and fully at 1.2e13 → the thermal
  anisotropy torque is essential, threshold energy ratio ≥ 2 (the paper's "2× lower energy").
* **C0 Heating=0 control** (same parameters as `b0_6e12`/`b0_8e12`/`b1_Jp10_dT300`, heating off):
  Jp=6/8/10e12 all fail to switch (final mz≈+0.988, T=300 K), transient dip only
  −8.1%/−12.4%/−17.6% (relative to the relaxed equilibrium 0.988, ≈33 ps) → deterministic
  switching at 6–10e12 fully relies on Joule-heating-induced thermal anisotropy torque
  (`runs/c0_noh_*`, `runs/heating_on_off.png`).
* **C1 phase-boundary midpoints** (J_ref=Jp): no switch at 9e12/300 K (final +0.933);
  8e12/375 K switches at 66.5 ps; 7e12/450 K at 61.0 ps; 6e12/600 K at 80.5 ps.
  Boundaries: `Jc∈(9,10]e12` on the Tmax≈583 K line; `dTc∈(300,375]K` on the Jp=8e12 line.
  Final figures `runs/phase_map.png`, `phase_traces.png`, `phase_speed.png` (`plot_phase.py`).
* **C2 Hx=0 symmetry control** (`runs/c2_Hx0_Jp8_dT450`, identical parameters to
  `b1_Jp8_dT450` except `Hx_mT=0`): transient minimum mz=0.80 (40.2 ps), then recovery;
  final **+1.0000**, no zero crossing (Tmax=725 K) → contrast with the 58.6 ps switching at
  `Hx=+160 mT`; `Hx≠0` is required for symmetry breaking.
* **Mechanism overview** `runs/mechanism_compare.png` (`plot_mechanism.py`): three panels
  (a) c0/b0 heating on/off, (b) b2 θ≈0, (c) b3 Ku(T) frozen; solid/dashed lines are the
  control arms, thin dash-dotted lines of the same color show T(t).
* **Fig. 4 dynamics** (echo `echo=0.3, ted=24 ps`; `runs/fig4_full.png`, `plot_fig4.py`;
  legend grouped into parallel / antiparallel / no Hx): `Hx=0` ± I curves coincide with no
  oscillation; the parallel group (Hx+,I+) and (Hx−,I−) coincide and the antiparallel group
  (Hx+,I−) and (Hx−,I+) coincide, with opposite ΔMz phase (antiparallel shows no positive
  overshoot, ΔMz minimum −3.5% @31.8 ps; the +1.3% spike at t=0 is an un-relaxed first-row
  artifact); the echo appears as a secondary peak in T(t) at ~29 ps (t0+ted).
* **Corrected re-runs of the early reference** (`RunDynamics=1`, 3.7 ps FWHM, Jp=1e12):
  `runs/dyn_Jp1e12_Ip` gives Tmax≈308 K, mz_final=+0.9879 (no switching), consistent with
  the early reference; the switching-type reference is `runs/b0_6e12`.

> ⚠ **Historical note**: the early adaptive-step "Jp=6e12 switching" was an artifact of the
> pulse being stretched to 27.6 ps (see `notes/error.md` §1.11). Those outputs were deleted
> and re-run with the corrected scripts (switching `runs/b0_6e12`, dynamics
> `runs/dyn_Jp1e12_Ip`); the table above reflects the fixed-step + real-time pulse
> (`SetSolver(4)+FixDt` + `J(t)`) re-runs.

## 5. Output and post-processing

Each run produces:

* `out/table.txt` — columns: `t, mx, my, mz, E_total, J, T` (time in s, J in A/m², T in K;
  the fig3/fig4 scripts have no `E_total` and use an `Ms` (A/m) column instead)
* `out/m_*.ovf` — magnetization snapshots (`OVF2_BINARY`)
* `out/log.txt` — console log with the average mz after relax/pulse

```python
import pandas as pd
df = pd.read_csv("out/table.txt", sep="\t")
df.columns = [c.lstrip("# ").strip() for c in df.columns]
df["t_ps"] = df["t (s)"] * 1e12
```

```powershell
mumax3-convert -png out/m_final.ovf      # quick figure
mumax3-convert -vtk out/m_final.ovf      # for ParaView
```

Parameter sweep (example: switching threshold vs Jp, `J_ref=Jp` means `dT ∝ J²`):

```powershell
foreach ($Jp in "6e12","8e12","1.2e13") {
    python simulations/mumax3_sot/run_case.py `
        simulations/mumax3_sot/macrospin_switch.mx3 "b1_Jp$Jp" `
        --set "Jp=$Jp" "J_ref=$Jp" dT_ref=450
}
# each run appends to runs/summary.csv (tag, t_cross_ps, recov_50ps, mz_final, ...)
```

## 6. Simulation roadmap

1. **Self-checks**: after `relax`, `mz ≈ cos[atan(Hx/Ha)] ≈ 0.988`; confirm that `Hx=0` does
   not switch, that reversing the current polarity reverses the final state, and that
   6/8/10e12 do not switch with heating off (`runs/c0_noh_*`).
2. **Time-domain dynamics (Fig. 4a,b)**: `RunDynamics=1` (or `fig4_dynamics.mx3`), 6 Hx/I
   combinations (Hx∈{0,±160 mT} × I±, all starting from +Mz), plot `ΔMz(t)`; without Hx the
   oscillation disappears and ±current are 180° out of phase.
3. **Single-pulse switching (Fig. 3/4d)**: `macrospin_switch.mx3` (or the full device
   `fig3_switching.mx3`), `RunDynamics=0`; for the real 6 ps pulse: `Jc∈(9,10]e12` on the
   `Tmax≈583 K` line, and at `dT=450 K` even `7e12` switches (C1). Quadrants are batch-verified
   (`runs/q1–q4`, `runs/a_f4_*`); scanning Hx qualitatively reproduces `Jc ∝ 1/Hx`.
4. **Heating-model calibration**: the heating model here is phenomenological (`dT ∝ J²`
   low-pass + `Ms(T)`/`Ku(T)` scaling, `Tc=800 K`). Calibration targets: 1–2% demagnetization
   at low current and recovery in ~300–400 ps. mumax3's `Temp` only adds Langevin noise and
   does not scale `Ms/Ku`, so `Msat` and `Ku1` are updated step by step in-script.
5. **Micromagnetics and probability (optional)**: move to 1024×800 (5×4 µm device) + Voronoi
   grain anisotropy disorder, and collect `P_sw(Jp)` over random seeds, corresponding to the
   paper's >91% switching probability and nucleation images.
6. **Energy estimate**: `python simulations/mumax3_sot/energy_check.py runs/<tag>` integrates
   the real `J(t)` from the table (`rho=81 µΩ cm`, `V=5×4 µm²×15 nm`); 6e12/6 ps → 39.7 pJ
   (consistent with the paper); switching cases in this model cost 39.7–441 pJ
   (54.1 pJ @7e12/dT450; 39.7 pJ @6e12/dT600 with Tmax=867 K > Tc, close to the HAMR-like
   regime the paper excludes).

Planned and deferred work (probability statistics, heating calibration, CI, release/Zenodo,
...) is tracked in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## 7. Known limitations

* Early adaptive-step outputs (pulse stretched to ~28 ps, `notes/error.md` §1.11) were
  **deleted**; equivalent cases were re-run with the corrected scripts (switching
  `runs/b0_6e12`, dynamics `runs/dyn_Jp1e12_Ip`). All conclusions now come from the corrected
  scripts.
* `macrospin_switch.mx3` / `fig3_switching.mx3` use a uniform-Ku model without nucleation,
  domain walls or disorder.
* Heating is phenomenological (`dT ∝ J²` low-pass + `Ms(T)/Ku(T)` scaling); exact fitting
  should follow the paper's SI.
* Transmission-line reflection (echo) is approximated by a delayed, superposed pulse.
* The paper's quasi-static `Jc(Hx)` (100 µs pulses) relies on thermal activation and is not
  directly reproducible with long LLG runs.

## 8. Citing

If you use this repository, please cite the original paper and mumax3 (both are included in
[`CITATION.cff`](CITATION.cff), also available via GitHub's "Cite this repository"):

* doi:10.1038/s41928-020-00488-3
* A. Vansteenkiste et al., *AIP Advances* **4**, 107133 (2014).

## 9. License

* **Code** (`.py` / `.mx3` under `simulations/`, `requirements.txt`): MIT, see [`LICENSE`](LICENSE);
* **Documentation** (README, `FACTS.md`, `docs/`, `notes/error.md`): CC BY 4.0, see [`LICENSE-docs`](LICENSE-docs);
* The paper PDFs in `papers/` remain the copyright of their authors and publishers, are
  **not redistributed** in this repository, and are not covered by the licenses above.
