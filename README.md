# mumax3 replica: spin-orbit torque switching with picosecond electrical pulses

用 [mumax3](https://mumax.github.io/) 复现：

> K. Jhuria, J. Hohlfeld, ... J. Gorchon,
> **"Spin-orbit torque switching of a ferromagnet with picosecond electrical pulses"**,
> *Nature Electronics* **3**, 680-686 (2020).
> doi: [10.1038/s41928-020-00488-3](https://doi.org/10.1038/s41928-020-00488-3)

器件：`Ta(5)/Pt(4)/Co(1)/Cu(1)/Ta(4)/Pt(1) nm`，Co 为垂直磁化层 (PMA)；
论文关键参数：各向异性场 `Ha ≈ 1 T`、`theta_DL = 0.20`、`theta_FL = 0.05`、
面内辅助场 `Hx = ±160 mT`、时间分辨脉冲 `3.7 ps`、翻转实验脉冲 `6 ps`、
皮秒翻转电流密度上限 `Jc ≈ 6e12 A/m^2`。

---

## 1. 仓库结构

```
kimi/SOT_ps_switching.mx3             # 主脚本：翻转(switch) / 时域动力学(dynamics) 两种模式
mumax3_sot/fig4_dynamics.mx3          # Fig.4 专用动力学脚本：PBC + 电反射 echo + RK4
kimi/runs/                            # 已验证参考运行 + 参数扫描汇总
  sweep_summary.csv
  2026-09-15_switch_Jp6e12_Hx160mT_Ipos/
      run.mx3
      out/{table.txt, log.txt, m_initial.ovf, m_final.ovf, references.bib}
  2026-09-15_dynamics_Jp1e12_Hx160mT_Ipos/
      ...
mumax3_sot/fig4_dynamics.out/         # Fig.4 脚本的参考运行输出
```

* `kimi/SOT_ps_switching.mx3` — 宏观自旋近似（64×64、5 nm 网格），可快速验证物理与极性；
  `RunDynamics=0` 为 6 ps 单脉冲翻转，`RunDynamics=1` 为 3.7 ps 低电流时域响应。
* `mumax3_sot/fig4_dynamics.mx3` — 用 `SetPBC` 模拟无穷薄膜、Gaussian 脉冲、可叠加传输线反射，
  输出 `T(t)`、`J(t)`、`Ms(t)`，适合直接对照论文 Fig. 4a/4b。

## 2. 快速开始

```powershell
# 依赖：mumax3（本仓库用 3.12 + CUDA 12.9 验证）
mumax3 -f -o runs/my_run/out kimi/SOT_ps_switching.mx3
```

参数集中在文件头的 **用户参数区**：

| 变量 | 含义 |
|---|---|
| `RunDynamics` | 0 = 6 ps 翻转实验；1 = 3.7 ps 时域响应 |
| `I_sign` | 电流极性，`+1` 对应论文的 `+I` |
| `InitMz` | 初始态，`+1` (up) / `-1` (down) |
| `Hx_mT` | 面内辅助场 (mT) |
| `Jp` | 电流密度峰值 (A/m²) |
| `Heating` / `dT_ref` / `J_ref` / `tau_cool` | 焦耳加热模型开关与标定参数 |
| `t_free` | 脉冲后自由演化时间 |

## 3. 两个关键约定（踩坑记录）

1. **各向异性**：mumax3 的 `Ku1` 是总单轴各向异性，需显式加上薄膜退磁场：

   ```go
   Keff  := 0.5*Ms*Ha_T                  // Ha_T 用特斯拉；Keff = mu0*Ms*Ha/2
   Ku1    = Keff + 0.5*mu0*Ms*Ms         // Ms=1.3e6, Ha=1T -> Keff=6.5e5, Ku1=1.71e6 J/m^3
   ```

   若写成 `0.5*mu0*Ms*1.0`（把 1 T 当 A/m）会得到 `Ku1 ≈ mu0*Ms²/2`，
   PMA 消失、磁化弛豫到面内，**看起来像"无法翻转"**。

2. **SOT 如何接入**：mumax3 没有原生 SOT，标准做法是用 Slonczewski 模块，
   而 `cuda/slonczewski2.cu` 内核**只读取电流密度的 z 分量**，因此：

   ```go
   FixedLayer   = vector(0, 1, 0)   // 自旋极化 sigma 沿 y（面内电流沿 x 的 SOT 几何）
   Pol          = 0.20              // = theta_DL
   EpsilonPrime = 0.05              // = theta_FL
   Lambda       = 1                 // 此时 Slonczewski 效率 eps = Pol/2，等于标准自旋霍尔因子
   J            = vector(0, 0, J_eff)
   DisableZhangLiTorque = true      // Xi 只作用于 Zhang-Li，与 SOT 无关
   ```

   写成 `J = vector(Jc, 0, 0)` 时转矩恒为零。

**极性标定**（脚本内实测，与论文 Fig. 3 一致）：

| Hx | I_sign | 终态 |
|---|---|---|
| +160 mT | +1 | −Mz |
| +160 mT | −1 | +Mz |
| −160 mT | +1 | +Mz |
| −160 mT | −1 | −Mz |

即 `sign(mz_final) = -sign(Hx·I)`，且与初始态无关；`Hx = 0` 时不翻转（对称性破缺必需）。

## 4. 已验证结果

64×64、5 nm 网格，`Ms=1.3e6 A/m`、`Ha=1 T`、`alpha=0.15`：

| 条件 | Tmax (K) | mz_final | 结果 |
|---|---|---|---|
| +Hx, +I, Jp=6e12, 加热 | 583 | −0.988 | **翻转 up→down** |
| 同参数，关闭加热 | 300 | +0.988 | 不翻转（与论文"热各向异性转矩使翻转能量减半"一致） |
| Hx=0 | 583 | +1.000 | 不翻转 |
| +Hx, −I | 583 | +0.988 | 不翻转（反平行） |
| +Hx, +I, 初始 down | 583 | −0.988 | 保持 down（终态与初态无关） |
| 无加热、Jp=1.2e13 | — | −0.988 | 纯 LLG 的翻转阈值明显高于 6e12 |
| 低电流 Jp=1e12, 3.7 ps | 308 | 0.988 | ΔMz≈−1.2% 后恢复，无翻转（Fig.4a 型响应） |

## 5. 输出与后处理

每次运行输出：

* `out/table.txt` — 列：`t, mx, my, mz, E_total, J, T`（时间单位 s、J 单位 A/m²、T 单位 K）
* `out/m_*.ovf` — 磁化分布快照（`OVF2_BINARY`）
* `out/log.txt` — 控制台日志，含 relax/脉冲后的平均 mz

```python
import pandas as pd
df = pd.read_csv("out/table.txt", sep="\t")
df.columns = [c.lstrip("# ").strip() for c in df.columns]
df["t_ps"] = df["t (s)"] * 1e12
```

```powershell
mumax3-convert -png out/m_final.ovf      # 快速出图
mumax3-convert -vtk out/m_final.ovf      # 给 ParaView
```

参数扫描（示例：翻转阈值 vs Jp）：

```python
import subprocess, pathlib, re, csv
base = pathlib.Path("kimi/SOT_ps_switching.mx3").read_text(encoding="utf-8")
mx = r"E:\mumax3.12_windows_cuda12.9\mumax3.exe"
rows = []
for Jp in [6e12, 9e12, 1.2e13]:
    d = pathlib.Path("kimi/runs") / f"J{Jp:.0e}_Hx160mT_Ipos"
    d.mkdir(parents=True, exist_ok=True)
    (d / "run.mx3").write_text(base.replace("Jp      := 6e12", f"Jp      := {Jp:g}"),
                               encoding="utf-8")
    subprocess.run([mx, "-f", "-s", "-o", str(d / "out"), str(d / "run.mx3")], check=True)
    log = (d / "out" / "log.txt").read_text(encoding="utf-8", errors="ignore")
    rows.append({"Jp": Jp, "mz_final": float(re.search(r"mz after pulse = (\S+)", log).group(1))})
with open("kimi/runs/sweep_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["Jp", "mz_final"]); w.writeheader(); w.writerows(rows)
```

## 6. 仿真路线

1. **自检**：`relax` 后 `mz ≈ cos[atan(Hx/Ha)] ≈ 0.988`；确认 `Hx=0` 不翻转、电流极性反转终态、关闭加热时 6e12 翻不动。
2. **时域动力学（Fig.4a,b）**：`RunDynamics=1`（或 `fig4_dynamics.mx3`），
   4 种 Hx/I 组合 + ±Mz 初态，画 `ΔMz(t)`；无 Hx 时振荡消失，±电流相位差 180°。
3. **单脉冲翻转（Fig.3/4d）**：`RunDynamics=0, Jp=6e12`，跑 4 象限并扫描 Jp 得到阈值；
   扫描 Hx 可定性复现 `Jc ∝ 1/Hx`。
4. **热模型标定**：本仓库的加热模型是唯象模型（`dT ∝ J²` 低通 + `Ms(T)`/`Ku(T)` 标度律，`
   Tc=800 K`）。标定目标：低电流退磁 1–2%、Jp=6e12 为阈值、脉冲后恢复 ~300–400 ps。
   mumax3 的 `Temp` 只加 Langevin 噪声、不缩放 `Ms/Ku`，所以这里用脚本逐步修改 `Msat`、`Ku1`。
5. **微磁与概率（选做）**：切到 1024×800（5×4 µm 器件）+ Voronoi 晶粒各向异性扰动，
   统计不同随机种子下的 `P_sw(Jp)`，对应论文的 >91% 翻转概率和成核图像。
6. **能耗估计**：由 `E = 0.75·J²·rho·tau_p`（`rho = 81 µΩcm`）估算，Jc=6e12、6 ps 时约 50 pJ。

## 7. 已知局限

* `SOT_ps_switching.mx3` 为宏观自旋近似，不包含成核/畴壁与随机性；
* 加热为唯象模型，论文用的是简化温度依赖 + 电反射，精确拟合应以论文 SI 为准；
* 传输线反射（echo）只在 `fig4_dynamics.mx3` 中以叠加延迟脉冲近似；
* 论文的准静态 `Jc(Hx)`（100 µs 脉冲）依赖热激活，不适合直接长时间 LLG 复现。

## 8. 引用

若使用本仓库，请引用原论文与 mumax3：

* doi:10.1038/s41928-020-00488-3
* A. Vansteenkiste et al., *AIP Advances* **4**, 107133 (2014).
