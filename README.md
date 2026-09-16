# PicoSOT

English | [简体中文](README.zh-CN.md)

**mumax3 replica: spin-orbit torque switching with picosecond electrical pulses (SI-parameter model)**

![license: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)
![docs: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey.svg)
![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)
![mumax3 v3.12](https://img.shields.io/badge/mumax3-v3.12-orange.svg)

A [mumax3](https://mumax.github.io/) replica of:

> K. Jhuria, J. Hohlfeld, ... J. Gorchon,
> **"Spin-orbit torque switching of a ferromagnet with picosecond electrical pulses"**,
> *Nature Electronics* **3**, 680-686 (2020).
> doi: [10.1038/s41928-020-00488-3](https://doi.org/10.1038/s41928-020-00488-3)

**Status (2026-09-16):** the material and thermal model now follows the paper's
Supplementary Information item by item (SI Note 3 + Table S1, see
[`docs/si_replica.md`](docs/si_replica.md)): Ms(300 K)=1.0e6 A/m, B_K=0.8 T,
alpha=0.23, Ms(T)=Ms(0)[1−(T/Tc)^1.7], Kz(T)∝Ms³, and heating as the 0D equivalent
channel of the SI heat-diffusion model (6e12 / 6 ps → peak +50.4 K, τ=245 ps).
The older runs (guessed parameters, free dT_ref knob) are kept as `model=legacy`
in `runs/summary.csv` and `runs/legacy/`.

## Results at a glance

| ![](simulations/mumax3_sot/runs/heat_model.png) | ![](simulations/mumax3_sot/runs/phase_map.png) |
|---|---|
| **Thermal model**: SI 1D FD vs the 0D .mx3 channel (`heat_model.py`) | **Threshold map**: mz_final vs Jp, 4 series (`plot_phase.py`) |

| ![](simulations/mumax3_sot/runs/mechanism_compare.png) | ![](simulations/mumax3_sot/runs/fig4_full.png) |
|---|---|
| **Mechanism**: heating on/off, θ≈0, Kz(T)/Ms(T) frozen (`plot_mechanism.py`) | **Fig. 4 dynamics**: ΔMz(t) for 6 Hx/I combinations (`plot_fig4.py`) |

| ![](simulations/mumax3_sot/runs/q_quadrants.png) | ![](simulations/mumax3_sot/runs/energy_bars.png) |
|---|---|
| **Four quadrants**: uniform single domains, 5×4 µm device (`plot_quadrants.py`) | **Energy**: ∫J²dt·ρV (`plot_energy.py`) |

## 1. Key findings (SI-parameter model)

* **Pure SOT switches without Joule heating**: threshold 20e12 at θ_DL=0.2
  (~13.5e12 at θ_DL=0.3); with the SI heat channel it drops to 10e12 / ~8.5e12 →
  **heating lowers the threshold current by ~2× (energy by ~2.3–4×)**, matching the
  ratio in the paper's SI Fig. 3/4 (pure LLG 9e12 → with heating 6e12, ~2× energy).
* **Polarity rule** `sign(mz_final) = −sign(Hx·I)` (full-device four quadrants);
  `Hx=0` never switches (symmetry breaking required).
* **Mechanism decomposition**: Kz(T) frozen → no switching up to 14e12 (necessary
  channel); Ms(T) frozen alone → near-switching; θ≈0 (thermal-anisotropy torque
  only) → switches from 12e12, slower (SI Fig. 5 behaviour).
* **Pulse-width window** at 10e12 (heating off): no switching ≤12 ps, switching
  from 15 ps → half-precession-period condition reproduced.
* **Energy**: model threshold (10e12, θ=0.2) → 110 pJ, above the paper's <50 pJ
  budget scale (6e12); absolute thresholds are ~1.5× above the SI values, most
  likely because the SI never specifies the pulse waveform/reflections.
* **Caveats**: Jp≳1.9e13 drives the model through Tc (HAMR-like, excluded by the
  paper's experiment); mumax3's Langevin noise has a fixed seed → no P_sw statistics.

Full quantitative record: [`docs/RESULTS.md`](docs/RESULTS.md) (§0 = SI version,
§1–8 = legacy).

## 2. Repository layout

```
README.md                              # this file
README.zh-CN.md                        # Chinese version
FACTS.md                               # fact sheet: parameters/conventions/results (zh)
CITATION.cff                           # citation metadata
LICENSE / LICENSE-docs                 # MIT (code) / CC BY 4.0 (docs)
requirements.txt                       # Python dependencies for post-processing
docs/
├─ RESULTS.md                          # full experiment log (§0 SI / §1-8 legacy)
├─ ROADMAP.md                          # TODO list (zh)
└─ si_replica.md                       # SI ↔ mumax3 mapping + heat-model calibration (zh)
papers/                                # literature (PDFs not distributed)
notes/
└─ error.md                            # published pitfall log (notes/NE_2020SI is local only)
simulations/mumax3_sot/                # main working directory
   ├─ macrospin_switch.mx3             # 64×64 fast template (SI params + heat + knobs)
   ├─ fig3_switching.mx3               # 5×4 µm full-device single-pulse switching
   ├─ fig4_dynamics.mx3                # Fig.4 dynamics (PBC film + echo)
   ├─ heat_model.py                    # SI 1D heat-diffusion FD calibration
   ├─ run_case.py                      # batch runner/archiver (--model si/legacy)
   ├─ plot_phase.py / plot_fig4.py / plot_mechanism.py / plot_quadrants.py
   ├─ plot_table.py / plot_energy.py / energy_check.py
   └─ runs/                            # summary.csv + figures + cases (si_ prefix)
```

## 3. Quick start

Environment: Python 3.12 (`pip install -r requirements.txt`) +
[mumax3](https://mumax.github.io/) v3.12 (CUDA 12.9, NVIDIA GPU required).

```powershell
# Recommended: run through run_case.py (auto-archiving + parameter substitution)
# If mumax3 is not at the default path: set MUMAX3_BIN, or pass --mumax <path>
python simulations/mumax3_sot/run_case.py `
    simulations/mumax3_sot/macrospin_switch.mx3 si_h_t20_Jp8 `
    --set Jp=8e12 Heating=1
```

Parameters live in the user block at the top of `macrospin_switch.mx3`:

| variable | meaning |
|---|---|
| `Jp` / `tp_ps` | peak current density / pulse FWHM (ps) |
| `ThetaDL` | θ_DL (0.20 main-text fit; 0.30 = SI Fig. 3–5 value) |
| `Hx_mT` / `I_sign` / `InitMz` | in-plane bias field / current polarity / initial state |
| `Heating` | 1 = SI heat channel (Ms/Kz follow T); 0 = frozen 300 K (pure LLG) |
| `ScaleMs` / `ScaleKz` | freeze Ms(T) / Kz(T) independently (mechanism decomposition) |
| `Noise` | 1 = Langevin noise at T(t) (fixed seed) |
| `t_free` | free evolution after the pulse |

Thermal constants (ρ, C, Λ, G, d_stack) and the Ms(T)/Kz(T) laws are hard-coded in
the scripts; see `docs/si_replica.md`. `heat_model.py` re-derives them and plots.

## 4. Two key conventions (pitfalls, see notes/error.md)

1. **Anisotropy**: the current scripts set `Ku1 = Kz(T)` directly (the SI's Kz);
   together with mumax3's thin-film demag this realizes the SI field
   `H_z=(2Kz/μ0Ms−Ms)m_z` exactly. Do **not** use the legacy
   `Ku1=Keff+½μ0Ms²` form, and never treat 1 T as A/m (that yields
   Ku1≈μ0Ms²/2, the PMA disappears).
2. **SOT emulation**: mumax3 has no native SOT; use the Slonczewski module — its
   kernel (`cuda/slonczewski2.cu`) reads **only the z component** of the current:

   ```go
   FixedLayer   = vector(0, 1, 0)   // sigma along y (in-plane current along x)
   Pol          = ThetaDL           // = theta_DL (0.2 or 0.3)
   EpsilonPrime = 0.05              // = theta_FL
   Lambda       = 1
   J            = vector(0, 0, J_eff)
   DisableZhangLiTorque = true
   FreeLayerThickness   = 1e-9
   ```

   `J = vector(Jc, 0, 0)` produces zero torque.

**Polarity calibration** (full device, matches paper Fig. 3):

| Hx | I_sign | final state |
|---|---|---|
| +160 mT | +1 | −Mz |
| +160 mT | −1 | +Mz |
| −160 mT | +1 | +Mz |
| −160 mT | −1 | −Mz |

i.e. `sign(mz_final) = -sign(Hx·I)` (all batch runs start from +Mz; the paper's
"independent of initial state" was not re-run here); `Hx = 0` does not switch.

## 5. Verified results (2026-09-16, SI parameters)

**Thresholds** (macrospin 64×64, 6 ps sech², Hx=160 mT; Tmax=300+50.4(Jp/6e12)² K):

| series | threshold Jc | note |
|---|---|---|
| θ=0.2, SI heating | (9,10]e12 | Tmax (411,438] K; switches from 10e12 (68.3 ps) |
| θ=0.2, heating off | 20e12 (19e12 partial, −0.47) | **pure SOT switches** |
| θ=0.3, SI heating | (8,9]e12 | |
| θ=0.3, heating off | (12,14]e12 (13e12 partial) | |

With heating, 15–16e12 shows a non-monotonic no-switching window (precessional
phase effect); switching resumes at 18/20e12.

**Mechanism decomposition** (SI heating, θ=0.2):

| control | result |
|---|---|
| `ScaleKz=0` (Kz frozen) | no switching at 10/12/14e12 → Kz(T) collapse is necessary |
| `ScaleMs=0` (Kz collapse only) | 10e12 +0.45, 12e12 −0.46 (near switching) |
| θ≈0 (thermal-anisotropy torque only) | switches at 12e12 (122.5 ps), 14e12 (80.2 ps) — SI Fig. 5 |
| `Hx_mT=0` | never switches |

**Full device** (5×4 µm, Jpk=1.2e13, Tmax=497 K): four-quadrant polarity ✓,
threshold (9,10]e12 consistent with macrospin, `Hx=0` (12e12) does not switch.

**Fig. 4 dynamics**: parallel dip −5.9% @29 ps, antiparallel −1.9%, no oscillation
at Hx=0, period ≈44 ps, peak ΔT +13.9 K (heat model predicts 13.8 K).

**Energy**: 6e12 → 39.7 pJ (paper scale); 10e12 → 110 pJ; 20e12 → 441 pJ.

## 6. Output and post-processing

Each run writes `out/table.txt` (columns `t, mx, my, mz, E_total, J, T`),
`out/m_initial.ovf`, `out/m_final.ovf`, `out/log.txt`; `run_case.py` appends to
`runs/summary.csv` (with `model=si/legacy`). Batch scan example:

```powershell
foreach ($Jp in 6,8,10,12) {
    python simulations/mumax3_sot/run_case.py `
        simulations/mumax3_sot/macrospin_switch.mx3 "si_h_t20_Jp$Jp" `
        --set "Jp=${Jp}e12" Heating=1
}
```

One-command figure rebuild: `heat_model.py` → `plot_phase.py` → `plot_fig4.py` →
`plot_mechanism.py` → `plot_quadrants.py` → `plot_energy.py` (run inside
`simulations/mumax3_sot/`).

## 7. Simulation roadmap

1. ~~Self-checks~~ (done): relax mz=cos(atan(Hx/B_K))=0.981; Hx=0 never switches;
   pure-LLG threshold 20e12.
2. ~~Time-resolved dynamics (Fig. 4a,b)~~ (done, SI parameters): `runs/fig4_full.png`.
3. ~~Single-pulse switching (Fig. 3)~~ (done): four quadrants + device threshold (9,10]e12.
4. ~~Thermal-model calibration~~ (done): `heat_model.py` per SI Eq. S4–S5; 0D channel error 5.1%.
5. **Micromagnetics & probability (TODO)**: Voronoi grains + seed control
   (mumax3 Langevin is fixed-seed) → P_sw(Jp), paper's >91% switching probability.
6. **Energy**: `energy_check.py runs/<tag>` integrates the actual J(t).

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## 8. Known limitations

* Pulse waveform assumed sech² (SI does not specify) → absolute thresholds ~1.5×
  above the SI values (ratios match);
* uniform-anisotropy model, no nucleation/domain walls, no switching statistics;
* Jp≳1.9e13 exceeds Tc (HAMR-like, excluded experimentally in the paper);
* transmission-line reflections (echo) approximated by a delayed pulse;
* the paper's quasi-static Jc(Hx) (100 µs pulses) is thermally activated and not
  reproducible by long-time LLG;
* legacy results (guessed parameters) are kept for reference only — do not mix
  with the SI version.

## 9. Citing

If you use this repository, please cite the original paper and mumax3
(`CITATION.cff` carries both; GitHub's "Cite this repository" exports them):

* doi:10.1038/s41928-020-00488-3
* A. Vansteenkiste et al., *AIP Advances* **4**, 107133 (2014).

## 10. License

* **Code** (`.py`/`.mx3` under `simulations/`, `requirements.txt`): MIT, see [`LICENSE`](LICENSE);
* **Docs** (README, `FACTS.md`, `docs/`, `notes/error.md`): CC BY 4.0, see [`LICENSE-docs`](LICENSE-docs);
* Paper PDFs in `papers/` remain with their authors/publishers and are **not
  distributed** with this repository.
