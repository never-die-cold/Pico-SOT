# PicoSOT

[English](README.md) | **简体中文**

**mumax3 replica: spin-orbit torque switching with picosecond electrical pulses (paper-parameter model)**

用 [mumax3](https://mumax.github.io/) 复现：

> K. Jhuria, J. Hohlfeld, ... J. Gorchon,
> **"Spin-orbit torque switching of a ferromagnet with picosecond electrical pulses"**,
> *Nature Electronics* **3**, 680-686 (2020).
> doi: [10.1038/s41928-020-00488-3](https://doi.org/10.1038/s41928-020-00488-3)

**当前状态（2026-09-16）**：材料/热模型已逐项对齐论文（
见 [`docs/paper_replica.md`](docs/paper_replica.md)）：Ms(300 K)=1.0×10⁶ A/m、B<sub>K</sub>=0.8 T、α=0.23、
Ms(T)=Ms(0)[1−(T/Tc)^1.7]、Kz(T)∝Ms³、加热为论文热扩散方程的 0D 等效通道
（6×10¹²/6 ps → 峰值 +50.4 K、τ=245 ps）。

## 结果速览

| ![](docs/figures/heat_model.png) | ![](docs/figures/phase_map.png) |
|---|---|
| **热模型标定**：1D 热扩散 FD vs .mx3 的 0D 通道（`heat_model.py`） | **阈值图**：mz<sub>final</sub> vs Jp（4 系列，`plot_phase.py`） |

| ![](docs/figures/mechanism_compare.png) | ![](docs/figures/fig4_full.png) |
|---|---|
| **机制分解**：加热开/关、θ≈0、Kz(T)/Ms(T) 冻结（`plot_mechanism.py`） | **Fig. 4 动力学**：6 种 Hx/I 组合的 ΔMz(t)（`plot_fig4.py`） |

| ![](docs/figures/q_quadrants.png) | ![](docs/figures/energy_bars.png) |
|---|---|
| **四象限**：5×4 µm 器件末态均匀单畴（`plot_quadrants.py`） | **能耗**：∫J²dt·ρV（`plot_energy.py`） |

## 1. 核心结论（论文参数模型）

* **纯 SOT 无加热可以翻转**：θ=0.2 时阈值 20×10¹²（θ=0.3 时 ~13.5×10¹²）；
  开热通道后降到 10×10¹² / ~8.5×10¹² → **加热把阈值电流降低 ~2×（能量 ~2.3–4×）**，
  与论文给出的"纯 LLG 9×10¹² → 含热 6×10¹²（能量 ~2×）"比值一致。
* **极性规则** `sign(mz_final) = −sign(Hx·I)`（全器件四象限验证）；`Hx=0` 永不翻转
  （对称性破缺必需，宏自旋与全器件均验证）。
* **机制分解**：Kz(T) 冻结 → 14×10¹² 仍不翻（必要通道）；只冻结 Ms(T)（Kz 塌缩保留）
  → 接近翻转；θ≈0 纯热各向异性力矩 → 12×10¹² 起翻但更慢（与论文一致）。
* **脉宽窗口**：10×10¹² 无加热时 12 ps 不翻、15 ps 起翻 → FMR 半周期条件复现。
* **能耗**：模型阈值（10×10¹²/θ=0.2）→ 110 pJ，高于论文 <50 pJ 预算口径（6×10¹²）；
  绝对阈值整体比论文高 ~1.5×，最可能是论文未给脉冲波形/反射序列。
* **局限**：Jp≳1.9×10¹³ 时模型温升超过 Tc（HAMR 型，论文实验已排除）；mumax3 的
  Langevin 噪声为固定种子，无法做 P<sub>sw</sub>(Jp) 统计。

完整定量记录见 [`docs/RESULTS.md`](docs/RESULTS.md)。

## 2. 目录结构

```
README.md                              # 项目说明（英文主版）
README.zh-CN.md                        # 项目说明（本文件，中文版）
FACTS.md                               # 事实清单：参数/约定/已核实结果（中文）
LICENSE / LICENSE-docs                 # MIT（代码）/ CC BY 4.0（文档）
requirements.txt                       # 后处理脚本的 Python 依赖
slides/
├─ build_ppt.py                        # 汇报 PPT 生成脚本
├─ assets/device_stack.png             # 器件示意图
└─ PicoSOT_组会汇报.pptx                # 生成的讲稿（本地，不入库）
docs/
├─ RESULTS.md                          # 完整英文实验记录
├─ paper_replica.md                       # 论文 ↔ mumax3 逐项映射与热模型标定（中文）
└─ figures/                            # 定稿图（上方嵌入用）
notes/
└─ error.md                            # mumax3 复刻踩坑记录
simulations/mumax3_sot/                # 主工作目录
   ├─ macrospin_switch.mx3             # 64×64 快速模板（论文参数 + 热模型 + 旋钮）
   ├─ fig3_switching.mx3               # 5×4 µm 全器件单脉冲翻转
   ├─ fig4_dynamics.mx3                # Fig.4 动力学（PBC 无限薄膜 + echo）
   ├─ heat_model.py                    # 论文 1D 热扩散 FD 标定（→ docs/figures/heat_model.png）
   ├─ run_case.py                      # 批量运行+归档
   ├─ plot_phase.py / plot_fig4.py / plot_mechanism.py / plot_quadrants.py
   ├─ plot_table.py / plot_energy.py / energy_check.py
   └─ runs/                            # 本地运行归档：summary.csv + 各 case
```

## 3. 快速开始

环境：Python 3.12（`pip install -r requirements.txt`）+
[mumax3](https://mumax.github.io/) v3.12（CUDA 12.9，需 NVIDIA GPU）。

```powershell
# 推荐：用 run_case.py 运行（自动归档 + 参数替换）
# mumax3 不在默认路径时：设置环境变量 MUMAX3_BIN，或加 --mumax <路径>
python simulations/mumax3_sot/run_case.py `
    simulations/mumax3_sot/macrospin_switch.mx3 si_h_t20_Jp8 `
    --set Jp=8e12 Heating=1
```

参数集中在 `macrospin_switch.mx3` 文件头的**用户参数区**：

| 变量 | 含义 |
|---|---|
| `Jp` / `tp_ps` | 电流密度峰值 / 脉冲 FWHM (ps) |
| `ThetaDL` | θ<sub>DL</sub>（0.20 主文拟合；0.30 = 强电流模拟口径） |
| `Hx_mT` / `I_sign` / `InitMz` | 面内辅助场 / 电流极性 / 初态 |
| `Heating` | 1 = 热通道（Ms/Kz 随 T）；0 = 冻结 300 K（纯 LLG） |
| `ScaleMs` / `ScaleKz` | 分别冻结 Ms(T) / Kz(T)（机制分解） |
| `Noise` | 1 = 开 Langevin 噪声（Temp=T(t)；固定种子） |
| `t_free` | 脉冲后自由演化时间 |

热学常数（ρ、C、Λ、G、d<sub>stack</sub>）与 Ms(T)/Kz(T) 律写死在脚本内，来源见
`docs/paper_replica.md`；`heat_model.py` 可独立复算并出图。

## 4. 两个关键约定（踩坑记录，详见 notes/error.md）

1. **各向异性**：现行脚本直接 `Ku1 = Kz(T)`（论文的 Kz），配合 mumax3 的薄膜退磁
   恰好实现论文的 `H_z=(2Kz/μ0Ms−Ms)m_z`。**不要**写成
   `Ku1=Keff+½μ0Ms²`，更不要把 1 T 当 A/m 用（会得到 Ku1≈μ0Ms²/2，PMA 消失）。
2. **SOT 如何接入**：mumax3 无原生 SOT，用 Slonczewski 模块等效，而
   `cuda/slonczewski2.cu` 内核**只读取电流密度的 z 分量**，因此：

   ```go
   FixedLayer   = vector(0, 1, 0)   // 自旋极化 sigma 沿 y（面内电流沿 x 的 SOT 几何）
   Pol          = ThetaDL           // = θ_DL（0.2 或 0.3）
   EpsilonPrime = 0.05              // = θ_FL
   Lambda       = 1
   J            = vector(0, 0, J_eff)
   DisableZhangLiTorque = true
   FreeLayerThickness   = 1e-9
   ```

   写成 `J = vector(Jc, 0, 0)` 时转矩恒为零。

**极性标定**（全器件实测，与论文 Fig. 3 一致）：

| Hx | I<sub>sign</sub> | 终态 |
|---|---|---|
| +160 mT | +1 | −Mz |
| +160 mT | −1 | +Mz |
| −160 mT | +1 | +Mz |
| −160 mT | −1 | −Mz |

即 `sign(mz_final) = -sign(Hx·I)`（现行批量 run 均为 +Mz 初态；"与初始态无关"为
论文结论，本项目未单独跑负初态）；`Hx = 0` 时不翻转。

## 5. 已核实结果（2026-09-16，论文参数）

**阈值（宏自旋 64×64、6 ps sech²、Hx=160 mT；Tmax=300+50.4(Jp/6×10¹²)² K）**

| 系列 | 阈值 Jc | 说明 |
|---|---|---|
| θ=0.2，加热 | (9, 10]×10¹² | Tmax (411,438] K；10×10¹² 起翻（68.3 ps） |
| θ=0.2，无加热 | 20×10¹²（19×10¹² 变多畴，已剔除） | **纯 SOT 可翻** |
| θ=0.3，加热 | (8, 9]×10¹² | |
| θ=0.3，无加热 | (12, 14]×10¹²（13×10¹² 变多畴，已剔除） | |

加热后 **15–17×10¹²** 为单畴"不翻窗口"（相干进动回捕；θ=0.3 同为 14–17×10¹²，
其中 14×10¹² 是多畴伪影），18×10¹² 恢复翻转并一直到 30×10¹²（1.5 ns 长弛豫复核，
未再出现新窗口；27×10¹² 加热档为多畴伪影）。0.4 ns 快照的 +0.96 为未弛豫值，1.5 ns 复核后稳定在 +0.981。

**机制分解**（加热，θ=0.2）：

| 对照 | 结果 |
|---|---|
| `ScaleKz=0`（Kz 冻结） | 10/12/14×10¹² 全不翻 → Kz(T) 塌缩必要 |
| `ScaleMs=0`（只留 Kz 塌缩） | 10×10¹² +0.45、12×10¹² −0.46（接近翻转） |
| θ≈0（纯热各向异性力矩） | 12×10¹² 翻 122.5 ps、14×10¹² 翻 80.2 ps（与论文一致） |
| `Hx_mT=0` | 任何电流都不翻 |

**全器件（5×4 µm，Jpk=1.2×10¹³，Tmax=497 K）**：四象限极性 ✓、阈值 (9, 10]×10¹²
与宏自旋一致、`Hx=0`（12×10¹²）不翻。

**Fig.4 动力学**：平行组下冲 −5.9% @29 ps、反平行 −1.9%、Hx=0 无振荡、
周期 ≈44 ps、ΔT 峰值 +13.9 K（热模型预测 13.8 K）。

**能耗**：6×10¹² → 39.7 pJ（论文口径）；10×10¹² → 110 pJ；20×10¹² → 441 pJ。

## 6. 输出与后处理

每次运行输出 `out/table.txt`（列：`t, mx, my, mz, E_total, J, T`）、`out/m_initial.ovf`、
`out/m_final.ovf`、`out/log.txt`；`run_case.py` 自动写 `runs/summary.csv`。**`runs/` 仅本地保留：
交付内容只含代码、文档与定稿图（`docs/figures/`）。** 批量扫描示例：

```powershell
foreach ($Jp in 6,8,10,12) {
    python simulations/mumax3_sot/run_case.py `
        simulations/mumax3_sot/macrospin_switch.mx3 "si_h_t20_Jp$Jp" `
        --set "Jp=${Jp}e12" Heating=1
}
```

定稿图一键重建：`heat_model.py` → `plot_phase.py` → `plot_fig4.py` →
`plot_mechanism.py` → `plot_quadrants.py` → `plot_energy.py`（在
`simulations/mumax3_sot/` 下运行，再拷入 `docs/figures/`）。

## 7. 仿真路线

1. ~~自检~~（已完成）：relax mz=cos(atan(Hx/B<sub>K</sub>))=0.981；`Hx=0` 不翻；加热关闭阈值 20×10¹²。
2. ~~时域动力学（Fig.4a,b）~~（已完成，论文参数）：见 `docs/figures/fig4_full.png`。
3. ~~单脉冲翻转（Fig.3）~~（已完成）：四象限 + 器件阈值 (9, 10]×10¹²。
4. ~~热模型标定~~（已完成）：`heat_model.py` 按论文热方程标定，0D 通道误差 5.1%。
5. **微磁与概率（待做）**：Voronoi 晶粒 + 随机种子改造（mumax3 Langevin 固定种子）
   → P<sub>sw</sub>(Jp) 统计，对应论文 >91% 翻转概率。
6. **能耗估计**：`energy_check.py runs/<tag>` 直接对 table 的 J(t) 积分。


## 8. 已知局限

* 脉冲波形为 sech² 约定（论文未给）→ 绝对阈值比论文高 ~1.5×（比值已对上）；
* 均匀 Ku 模型，无成核/畴壁与随机性统计（P<sub>sw</sub> 未做）；64×64 帧在近阈值/极强
  电流下会长出条畴（|⟨m⟩|<0.9，胞元 5 nm 与 √(A/Kz)≈5 nm 同量级），此时平均 mz
  不能当作单畴翻转结果，phase_map 中已剔除并标灰叉；
* Jp≳1.9×10¹³ 时 Tmax>Tc（HAMR 型，论文实验排除），解读需谨慎；
* 传输线反射（echo）以叠加延迟脉冲近似；
* 论文的准静态 `Jc(Hx)`（100 µs 脉冲）依赖热激活，不适合直接长时间 LLG 复现；

## 9. 引用

若使用本成果，请引用原论文与 mumax3：

* doi:10.1038/s41928-020-00488-3
* A. Vansteenkiste et al., *AIP Advances* **4**, 107133 (2014).

## 10. 许可

* **代码**（`simulations/` 下的 `.py` / `.mx3`、`requirements.txt`）：MIT，见 [`LICENSE`](LICENSE)；
* **文档**（README、`FACTS.md`、`docs/`、`notes/error.md`）：CC BY 4.0，见 [`LICENSE-docs`](LICENSE-docs)；
* 引用的第三方文献版权归原作者与期刊所有，不在上述许可范围内。
