# 事实清单 — mumax3 复刻 NE 2020 皮秒脉冲 SOT 翻转

- 项目路径：`E:\_SOT_MARM`
- 整理日期：2026-09-15；依据：`README.md`、`resource/notes/*.md`、`resource/simulations/mumax3_sot/` 现行脚本与 `runs/summary.csv`
- 标记：【论文】原论文事实｜【已核实】本仓库跑通并验证｜【约定】建模/脚本约定｜【历史】已废弃或易误解的旧信息

## 1. 目标与文献

1. 目标：用 [mumax3](https://mumax.github.io/) 复现 Jhuria et al., *"Spin-orbit torque switching of a ferromagnet with picosecond electrical pulses"*, Nature Electronics **3**, 680–686 (2020)，doi:10.1038/s41928-020-00488-3。【论文】
2. 仓库另收录：NE_2020 原文 PDF + `NE_2020.md`、NC 2026（250 MTJ 概率 Ising machine）、AM 2023（拓扑绝缘体驱动 PMA 低功耗存储）、mumax3 原始论文/教程（`resource/papers/`）。
3. 引用要求：原论文 + A. Vansteenkiste et al., *AIP Advances* **4**, 107133 (2014)。【约定】

## 2. 运行环境

1. mumax3 v3.12（CUDA 12.9），exe 路径 `E:\mumax3.12_windows_cuda12.9\mumax3.exe`；`run_case.py` 中 `MUMAX` 常量写死该路径。【约定】
2. 记录到的硬件：`error.md` 为 RTX 5060 Laptop 8 GB；交接文档称目标机为 RTX 4070 SUPER（sm_89）。两处来源不同，未在 README 复述。
3. Python 3.12 + numpy / matplotlib（pandas 用于 `table.txt` 后处理）。【约定】
4. 运行中 GUI：`http://127.0.0.1:35367`；常用参数 `-o` 输出目录、`-f` 覆盖、`-vet` 仅查语法、`-i` 交互 GUI。【约定】

## 3. 论文关键参数（复现输入）

| 量 | 值 | 备注 |
|---|---|---|
| 叠层 | Ta(5)/Pt(4)/Co(1)/Cu(1)/Ta(4)/Pt(1) nm | Co 为 PMA 层；Pt、Ta 自旋霍尔角反号、转矩相加 |
| 器件 | 磁条 20×4 µm；过流窗口 5×4 µm | 仿真取过流窗口 |
| 各向异性场 Ha | ≈ 1 T | 由 FMR 周期 ~40 ps 反推 |
| Keff | ≈ 8.2×10⁵ J/m³ | 正文反推值 |
| 自旋霍尔角 | θ_DL = 0.20；θ_FL = 0.05 | 宏自旋拟合值 |
| 脉冲 | sech²；翻转实验 FWHM = 6 ps；时间分辨 FWHM = 3.7 ps | |
| 面内辅助场 | Hx = ±160 mT | Hx ≈ 120 mT 时不翻转 |
| 电流密度 | 准静态（100 µs）Jc ≈ 2×10¹¹ A/m²；皮秒上限 Jc ≈ 6×10¹² A/m²；阈值偏压 ΔV ≈ 40 V | 6e12 为能量上限估计 |
| 能量预算 | < 50 pJ（6 ps 脉冲） | Methods 能耗节 |
| Ms / Aex / α | 主文未给出 | 在 SI；脚本用典型值替代 |

【论文】以上均出自正文/Methods；关键实验结论：单个 6 ps 脉冲可确定性翻转垂直 Co 膜；翻转结果由脉冲极性与 Hx 方向的组合决定（Fig. 3）。

## 4. 建模约定（现行脚本，已核实）

1. **SOT 接入**（mumax3 无原生 SOT）：Slonczewski 模块等效，内核只读 `J` 的 z 分量。【已核实：对照 `cuda/slonczewski2.cu` + 数值自检】
   ```go
   FixedLayer   = vector(0, 1, 0)   // sigma 沿 y（电流沿 x 的 SOT 几何）
   Pol          = 0.20              // = theta_DL
   EpsilonPrime = 0.05              // = theta_FL
   Lambda       = 1                 // 此时 epsilon = Pol/2，等于标准自旋霍尔 DL 因子
   J            = vector(0, 0, J_SOT)
   DisableZhangLiTorque = true
   FreeLayerThickness   = 1e-9
   ```
2. **极性约定**：`J_z = -I_sign*Jp*脉冲(t)`（macrospin）；实测 `sign(mz_final) = -sign(Hx*I)`，与初始态无关；Hx = 0 时不翻转。【已核实】
3. **各向异性**：`Msat` 必须显式赋值（mumax3 默认 0）；`Ku1 = Keff + ½μ₀Ms²`，`Keff = 0.5*Ms*Ha_T`（Ha_T 用 T）；Ms = 1.3e6、Ha = 1 T → Keff = 6.5e5、Ku1 ≈ 1.71e6 J/m³，退磁相减后净 PMA 场 = 1 T。【已核实】
4. **B_ext 单位是特斯拉**，不是 A/m（Hx = 160 mT → `B_ext = vector(0.160, 0, 0)`）。【已核实】
5. **精确时间步**：`SetSolver(4)` + `FixDt = 5e-14`；脉冲写成内置时间 `t` 的函数；温度 ODE 用实测经过时间 `tb - tprev` 积分。默认自适应 RK45 会拉长脉冲（曾把 6 ps 拉成 27.6 ps，见 §6 末）。【已核实】
6. **加热模型（唯象）**：一阶低通 `h_th` 积分 `dT ∝ (J/J_ref)²`，归一化使峰值 J = J_ref 的脉冲终到 `T_amb + dT_ref`；`H_peak = 0.756*tp/tau_cool`；`Ms(T) = Ms0*((Tc-T)/(Tc-T0))^0.34`；`Ku(T) = Ku0*(Ms/Ms0)^KuExp`；Tc = 800 K，T > Tc 时 frac 截断为 0；`tau_cool` 冷却时间常数。【约定】
7. **语法/接口坑**：标识符大小写不敏感（`T` 会覆盖内置 `t`）；表达式不能跨行；`AutoSave` 与 `AutoSnapshot` 共用槽位（只用一个）；`Pol=0` 被 `AddSTTorque` 断言拦截，θ=0 测试用 `Pol=1e-4` + `EpsilonPrime=0`。【历史】

## 5. 脚本与几何

| 脚本 | 网格/几何 | 脉冲 | 关键默认值 | 用途 |
|---|---|---|---|---|
| `macrospin_switch.mx3` | 64×64，cell 5 nm（320×320 nm），Co 1 nm | sech²；`RunDynamics=0` → 6 ps，`=1` → 3.7 ps | α=0.15，Jp=6e12，J_ref=6e12，dT_ref=300 K，tau_cool=100 ps，KuExp=3，t_free=400 ps | 快速开关模板（带 Jp/dT_ref/KuExp/θ/Heating 旋钮） |
| `fig3_switching.mx3` | 500×400，cell 10×10×1 nm（5×4 µm 过流区） | 高斯 6 ps，t0=5 ps | α=0.1，Jpk=1.2e13，dTpk=400 K，tauC=100 ps，echo=0 | 单脉冲翻转/四象限 |
| `fig4_dynamics.mx3` | 64×64，cell 16 nm，PBC(16,16,0) 无限薄膜 | 高斯 3.7 ps，t0=5 ps | α=0.1，Jpk=4e12，dTpk=20 K，tauC=200 ps，echo/ted 可调 | 时域 ΔMz(t) |

工具脚本：`run_case.py`（参数替换 + 归档 + `summary.csv`）、`plot_table.py`、`plot_phase.py`、`plot_fig4.py`、`plot_mechanism.py`、`plot_quadrants.py`、`energy_check.py`。

## 6. 已核实定量结果

1. **时间精确性**：6 ps 档实测 FWHM = 5.85 ps；∫J²dt = 1.63×10¹⁴ → Jp = 6e12 时 **39.7 pJ**（ρ = 81 µΩ·cm，V = 5×4 µm²×15 nm），与论文 40 pJ 口径一致。
2. **弛豫平衡态**：Hx = 160 mT 时 mz ≈ 0.988 ≈ cos[atan(Hx/Ha)]。
3. **B1 单脉冲开关**（`J_ref = Jp`，dT ∝ J²）：

   | Jp (A/m²) | dT_ref | Tmax | mz 过零 | 末态 mz | 能量 | 结论 |
   |---|---|---|---|---|---|---|
   | 6e12 | 300 K | 583 K | — | +0.988 | 39.7 pJ | 不翻转 |
   | 8e12 | 450 K | 725 K | 58.6 ps | −0.988 | 70.6 pJ | 翻转 |
   | 1.0e13 | 300 K | 583 K | 88.8 ps | −0.11 | — | 部分 |
   | 1.2e13 | 450 K | 725 K | 50.1 ps | −0.988 | 158.9 pJ | 翻转 |
   | 2.0e13 | 450 K | 725 K | **39.0 ps（最快）** | −0.988 | 441 pJ | 翻转（论文模型最快 16 ps） |

4. **四象限极性**（fig3 默认：Jpk = 1.2e13、dTpk = 400 K、Tmax = 680 K）：q1 (Hx+,I+) → −0.956；q2 (Hx−,I+) → +0.987；q3 (Hx+,I−) → +0.987；q4 (Hx−,I−) → −0.956；末态为均匀单畴（无畴壁/成核，近相干翻转）。
5. **C2 对称性对照**（与 b1_Jp8_dT450 完全同参，仅 Hx = 0）：瞬态最低 mz = 0.80（40.2 ps）后恢复，末态 +1.0000、无过零 → Hx ≠ 0 为翻转的必要条件。
6. **B2 θ≈0**（Pol = 1e-4，EpsilonPrime = 0，Jp = 8e12）：dT = 300 K 不翻；dT = 450/600/800 K 分别在 **85.9/92.3/122.4 ps** 过零（Tmax = 725/867/1056 K）→ 仅热各向异性力矩也能翻转，但更慢、更热。
7. **B3 Ku(T) 开关**：`KuExp = 0`（Ku 不随 T 变）到 Jp = 1.4e13 仍不翻；`KuExp = 3` 在 1e13 部分/1.2e13 完全翻转 → 热各向异性力矩为必要项，阈值能量比 ≥ 2。
8. **C0 Heating = 0**（6/8/10e12）：三档均不翻（T 恒 300 K），峰值瞬态下拉仅 −8.1%/−12.4%/−17.6%（≈33 ps）→ 6–10e12 的确定性翻转完全依赖焦耳热。
9. **C1 相图边界**：9e12/300 K 不翻（末态 +0.933）；8e12/375 K 翻 66.5 ps（654 K）；7e12/450 K 翻 61.0 ps；6e12/600 K 翻 80.5 ps。边界：Tmax = 583 K 线上 Jc ∈ (9,10]e12；Jp = 8e12 竖线上 dTc ∈ (300,375] K。
10. **b0_8e12**（J_ref = 6e12，dT_ref = 300 K → Tmax = 804 K）：54.5 ps 翻转。
11. **Fig. 4 动力学**（a_f4_* / f4_*）：进动周期 ≈ 37 ps（论文 Ha≈1 T 对应 ~40 ps）；平行组下冲 −4.8% @15.8 ps、反平行组上冲 +1.3%；Hx = 0 时 ±I 曲线重合且无振荡；400 ps 后恢复至 ≈ −0.25%；echo = 0.3、ted = 24 ps 在 T(t) 上产生次级峰。`dyn_Jp1e12_Ip`（RunDynamics=1、3.7 ps、1e12、Tmax ≈ 308 K）：末态 +0.9879，不翻转。
12. **历史修正**：早期自适应步长脚本的"Jp = 6e12 翻转"是脉冲被拉长到 27.6 ps 的假象（积分对应 189 pJ）；旧输出已删除，等效案例用修正脚本重跑（开关型 `runs/b0_6e12`、动力学型 `runs/dyn_Jp1e12_Ip`）。

## 7. 输出与归档

1. 每个 case：`runs/<tag>/<tag>.mx3`（实际运行的脚本副本）+ `runs/<tag>/out/`（仅保留 `table.txt`、`log.txt`、`m_initial.ovf`、`m_final.ovf`）。中间帧 `m0*.ovf`、`gui`、`references.bib` 属可再生的运行产物，已清理并列入 `.gitignore`。【约定】
2. `table.txt` 列（macrospin）：`t`(s), `mx`, `my`, `mz`, `E_total`, `J`(A/m²), `T`(K)；fig3/fig4 脚本另有 `Ms`(A/m)。
3. `summary.csv` 列：`tag, time, t_end_ps, mz_final, switched, Tmax_K, Hx, Isign, t_cross_ps, recov_50ps, Jp, J_ref, dT_ref, Pol, EpsilonPrime, KuExp, echo, ted, Heating, RunDynamics, Hx_mT`。
4. `recov_50ps` = |mz(t_cross + 50 ps)| / |mz_final|（`run_case.py` 定义；无过零则留空）。
5. 定稿图：`runs/phase_map.png`、`phase_traces.png`、`phase_speed.png`、`fig4_full.png`、`fig4_like.png`、`mechanism_compare.png`、`heating_on_off.png`、`q_quadrants.png`。
6. OVF 后处理：`mumax3-convert -png out/m_final.ovf`（或 `-vtk` 给 ParaView）。【约定】

## 8. 已知局限与未决

1. 均匀 Ku1 模型，无晶粒/随机性/热噪声统计 → 未做 P_sw(Jp)、成核路径与概率翻转统计。
2. 加热为唯象模型，`Ms(T)/Ku(T)` 幂律、dTpk、tauC 为拟合旋钮；论文 SI 参数未公开。
3. 本模型最快 39 ps（vs 论文模型 16 ps）；能翻转的案例能量 70–441 pJ，均超论文 < 50 pJ 预算；Jp = 6e12 在本模型不翻转。
4. 论文准静态 Jc(Hx)（100 µs，依赖热激活）不适合直接长时间 LLG 复现。
5. 传输线反射（echo）用叠加延迟脉冲近似。
6. 论文实际为 20×4 µm 磁条，仿真只取 5×4 µm 过流区。
7. 【历史】交接文档中的旧参数（Keff ≈ 8.2e5 且 Ku1 ≈ 1.88e6、脚本 `SOT_ps_switching.mx3`）已废弃，勿回退；现行脚本用 Ku1 ≈ 1.71e6。

## 9. 引用

- doi:10.1038/s41928-020-00488-3
- A. Vansteenkiste et al., *AIP Advances* **4**, 107133 (2014).
