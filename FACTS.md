# PicoSOT 事实清单 — mumax3 复刻 NE 2020 皮秒脉冲 SOT 翻转

- 项目路径：`E:\_SOT_MARM`
- 整理日期：2026-09-16（SI 参数版）；依据：`docs/si_replica.md`、`docs/RESULTS.md`、现行脚本与 `runs/summary.csv`
- 标记：【论文】原论文/SI 事实｜【已核实】本仓库跑通并验证｜【约定】建模/脚本约定｜【历史】legacy（已废弃参数）或易误解的旧信息

## 1. 目标与文献

1. 目标：用 [mumax3](https://mumax.github.io/) 复现 Jhuria et al., *"Spin-orbit torque switching of a ferromagnet with picosecond electrical pulses"*, Nature Electronics **3**, 680–686 (2020)，doi:10.1038/s41928-020-00488-3，**含其 Supplementary Note 3 的宏观自旋模型**。【论文】
2. 仓库另收录：NE_2020 原文 PDF、SI 全文提取（本地 `notes/NE_2020SI/`，不入库）、NC 2026、AM 2023、mumax3 原始论文/教程（`papers/`）。
3. 引用要求：原论文 + A. Vansteenkiste et al., *AIP Advances* **4**, 107133 (2014)。【约定】

## 2. 运行环境

1. mumax3 v3.12（CUDA 12.9），exe 默认路径 `E:\mumax3.12_windows_cuda12.9\mumax3.exe`；`run_case.py` 的 `MUMAX` 可用环境变量 `MUMAX3_BIN` 或 `--mumax` 覆盖。【约定】
2. 记录到的硬件：RTX 5060 Laptop 8 GB（本机实测）；交接文档称目标机为 RTX 4070 SUPER。宏自旋 run ≈ 29 s，全器件（500×400）≈ 28 s。【已核实】
3. Python 3.12 + numpy 2.5.1 / matplotlib 3.11.0；依赖见 `requirements.txt`。【约定】
4. 运行中 GUI：`http://127.0.0.1:35367`；常用参数 `-o` 输出目录、`-f` 覆盖、`-vet` 仅查语法。【约定】

## 3. 论文/SI 关键参数（现行脚本输入）

| 量 | 值 | 来源 |
|---|---|---|
| 叠层 | Ta(5)/Pt(4)/Co(1)/Cu(1)/Ta(4)/Pt(1) nm（16 nm 总厚） | 【论文】 |
| 器件 | 磁条 20×4 µm；过流窗口 5×4 µm | 【论文】 |
| Ms(300 K) | **1.0×10⁶ A/m** | 【论文】SI Table S1（VSM） |
| B<sub>K</sub>(300 K) | **0.8 T**（Kz=1×10⁶ J/m³） | 【论文】SI 拟合（TR-MOKE） |
| α | **0.23** | 【论文】SI 拟合（含非均匀展宽） |
| θ<sub>DL</sub> / θ<sub>FL</sub> | 0.2 / 0.05（主文拟合）；SI Fig.3–5 强电流模拟用 **0.3** | 【论文】 |
| Tc | 800 K | 【论文】SI 拟合 |
| Ms(T) | Ms(0)[1−(T/Tc)^1.7]，Ms(0)=1.23×10⁶ A/m | 【论文】SI Eq. S6 |
| Kz(T) | Kz(0)(Ms/Ms0)³，Kz(0)=1.87×10⁶ J/m³ | 【论文】SI Eq. S7 |
| 加热 | C∂T/∂t=Λ∂²T/∂x²+ρJ²；C=2.6×10⁶ J/m³K、Λ=9 W/mK、G=170 MW/m²K（sapphire；glass 100） | 【论文】SI Eq. S4–S5 |
| ρ | 81 µΩ·cm | 【论文】四点法 |
| 脉冲 | sech²（本仓库约定）；翻转 6 ps、时域 3.7 ps FWHM | 【论文】（波形未给，见 si_replica §4.1） |
| 面内辅助场 | Hx = ±160 mT（SI Fig.5：Hx=0 时纯热也不翻） | 【论文】 |
| 能量预算 | < 50 pJ ↔ Jc ≈ 6×10¹²（上限口径） | 【论文】Methods |

## 4. 建模约定（现行 SI 脚本，已核实）

1. **SOT 接入**：Slonczewski 模块等效，`Pol=θ_DL、Lambda=1、EpsilonPrime=θ_FL、FixedLayer=σ、J 沿 z`；内核 `slonczewski2.cu` 只读 J.z；DL 速率与 SI 的 θ<sub>DL</sub>·C<sub>s</sub> 一致（差来自 1/(1+α²)≈0.95）。【已核实：内核源码 + 数值】
2. **各向异性**：`Ku1 = Kz(T)` 直接赋值（配合 mumax3 薄膜退磁恰好实现 SI 的 H<sub>z</sub>=(2Kz/μ0Ms−Ms)m<sub>z</sub>）。legacy 的 `Ku1=Keff+½μ0Ms²` 写法不再使用。【已核实：relax mz=cos(atan(Hx/B<sub>K</sub>))=0.981】
3. **SI 温度律**：`fr=1−(T/Tc)^1.7` 截断为 ≥0；`Msat=Ms0·fr`、`Ku1=Kz0·fr³`（分解旋钮 `ScaleMs/ScaleKz` 可冻结任一项）。【约定】
4. **加热（0D 等效通道）**：`dTdev/dt = ρJ²/C − Tdev/τ`，τ=C·d/G=244.7 ps；与 `heat_model.py` 的 1D FD 解最大偏差 5.1%。Jp=6×10¹²/6 ps → **Tmax≈350 K**；Tmax ≈ 300+50.4·(Jp/6×10¹²)² K。【已核实】
5. **B<sub>ext</sub> 单位是特斯拉**；`Temp`（Langevin 噪声）默认 0，`Noise=1` 时循环内 `Temp=T(t)`；mumax3 噪声为固定种子，重复 run 结果相同。【已核实】
6. **精确时间步**：`SetSolver(4)`+`FixDt=5e-14`；脉冲写成内置 t 的函数；温度 ODE 用实测经过时间积分。【已核实（沿用）】
7. **语法/接口坑**（沿用）：标识符大小写不敏感（勿用单字母 T）；`AutoSave` 与 `AutoSnapshot` 共用槽位；`Pol=0` 被 `AddSTTorque` 断言拦截，θ≈0 测试用 `ThetaDL=1e-4`+`EpsilonPrime=0`。【历史】

## 5. 脚本与几何

| 脚本 | 网格/几何 | 脉冲 | 关键默认值（SI） | 用途 |
|---|---|---|---|---|
| `macrospin_switch.mx3` | 64×64，cell 5 nm（320×320 nm），Co 1 nm | sech²，`tp_ps=6`（dynamics 3.7） | Ms300=1×10⁶、BK300=0.8 T、α=0.23、θ=0.20、SI 热通道、`Noise/ScaleMs/ScaleKz` 旋钮、t<sub>free</sub>=400 ps | 阈值/机制扫描模板 |
| `fig3_switching.mx3` | 500×400，cell 10×10×1 nm（5×4 µm 过流区） | 高斯 6 ps，t0=5 ps | Jpk=1.2×10¹³、echo=0；SI 材料与热通道 | 单脉冲翻转/四象限 |
| `fig4_dynamics.mx3` | 64×64，cell 16 nm，PBC(16,16,0) 无限薄膜 | 高斯 3.7 ps，t0=5 ps | Jpk=4×10¹²、echo/ted 可调；SI 材料与热通道 | 时域 ΔMz(t) |
| `heat_model.py` | 16 nm 叠层 1D FD | sech² | SI C/Λ/G/ρ | 热模型标定与 `docs/figures/heat_model.png` |

工具脚本：`run_case.py`（参数替换 + 归档 + `summary.csv` 带 `model` 列）、`plot_table.py`、`plot_phase.py`、`plot_fig4.py`、`plot_mechanism.py`、`plot_quadrants.py`、`energy_check.py`、`plot_energy.py`。

## 6. 已核实定量结果（2026-09-16，SI 模型）

1. **热模型**：6×10¹²/6 ps → 峰值 +50.4 K、τ≈245 ps；0D 通道与 FD 最大偏差 5.1%。SI 自述 6×10¹² 时峰值 ~60 K（含 15 K 电子–声子失配）→ 口径一致。【已核实】
2. **自检**：Hx=160 mT 时 relax mz=0.981=cos(atan(0.16/0.8))；无加热时 T≡300 K；`Hx=0` 时任何电流都不翻（宏自旋 + 全器件均验证）。【已核实】
3. **阈值（宏自旋，6 ps，Hx=160 mT）**：

   | 系列 | 阈值 Jc（mz<sub>final</sub><−0.5） | 对应 Tmax | 备注 |
   |---|---|---|---|
   | θ=0.2，SI 加热 | (9, 10]×10¹² | (411,438] K | 10×10¹² 起翻，t<sub>cross</sub> 68.3 ps |
   | θ=0.2，无加热 | 20×10¹²（19×10¹² 变多畴，已剔除） | 300 K | **纯 SOT 无加热可翻** |
   | θ=0.3，SI 加热 | (8, 9]×10¹² | (388,411] K | |
   | θ=0.3，无加热 | (12, 14]×10¹²（13×10¹² 变多畴，已剔除） | 300 K | |

   加热/无加热阈值比：θ=0.2 → 2.0（能量 4×）；θ=0.3 → ~1.5（能量 ~2.3×）。
   **与 SI Fig. 4 的 9×10¹²→6×10¹²（能量 ~2×）定量一致**；绝对值整体偏高 ~1.5×，
   归因于脉冲波形/反射口径（见 si_replica §4）。【已核实】

4. **非单调窗口（2026-09-17 修正）**：加热下 θ=0.2 在 **15–17×10¹²** 为单畴不翻
   （|⟨m⟩|=1.000，末态稳定 +0.981），θ=0.3 在 **14–17×10¹²**（14×10¹² 为多畴伪影）；
   18×10¹² 恢复翻转。用 1.5 ns 自由弛豫复核（T 回 ~300 K），并把 θ=0.2 扫到 30×10¹²
   （1e12 步长、加热开/关）：**未再出现第二个窗口**（27×10¹² 加热档为多畴伪影）。
   早前"15–16×10¹²（mz=+0.96）"是未弛豫快照，已被本修正取代。【已核实】
5. **脉宽窗口（θ=0.2，10×10¹²，无加热）**：6/8/10/12 ps 不翻；**15 ps 部分翻（−0.93）、20/30 ps 完全翻** → 半周期条件（FMR 半周期 ≈18–19 ps）成立，与论文"FMR 半周期 <20 ps"的说法一致。【已核实】
6. **α 敏感性**：10×10¹² 无加热、α=0.05/0.10/0.30 均不翻（阈值对 α 不敏感，20×10¹² 附近才翻）。【已核实】
7. **机制分解（SI 热通道，θ=0.2）**：
   - `ScaleKz=0`（Kz 冻结 300 K，Ms(T) 仍变）：10/12/14×10¹² **全不翻** → Kz(T) 塌缩是必要项；
   - `ScaleMs=0`（Ms 冻结，Kz(T) 变）：10×10¹² 部分 +0.45、12×10¹² 部分 −0.46 → 单靠 Kz 塌缩接近翻转；
   - `ThetaDL=1e-4, EpsilonPrime=0`（纯热各向异性力矩）：12×10¹² 翻（122.5 ps）、14×10¹² 翻（80.2 ps）→ 与 SI Fig. 5 一致（SI：θ=0 时 Hx=160 mT 能翻、Hx=0 不能）；
   - `Hx=0`：宏自旋与全器件（Jpk=12×10¹²）均不翻（+1.0000）。【已核实】
8. **四象限（全器件 5×4 µm，Jpk=1.2×10¹³，Tmax=497 K）**：q1 (Hx+,I+)→−0.971；q2 (Hx−,I+)→+0.970；q3 (Hx+,I−)→+0.970；q4 (Hx−,I−)→−0.971 → `sign(mz_final)=−sign(Hx·I)`，末态均匀单畴（仅开边界边缘列钉扎）。【已核实，与论文 Fig. 3 一致】
9. **器件阈值**：8/9×10¹² 不翻、10×10¹² 起翻（θ=0.2 加热）→ 与宏自旋阈值一致，未见明显成核降阈（10 nm 网格、无缺陷）。【已核实】
10. **Fig. 4 动力学（3.7 ps，Jpk=4×10¹²，echo=0.3/ted=24 ps）**：平行组下冲 −5.9% @~29 ps；反平行组仅 −1.9% @~17 ps、无正上冲；Hx=0 无振荡、只剩退磁；进动周期 ≈44 ps（论文 ~40 ps 口径）；Tmax=314 K（+14 K，与 heat_model 预测 13.8 K 一致）；~400 ps 恢复。【已核实】
11. **能耗**（`energy_check.py`，ρ=81 µΩcm、V=5×4×15 nm³）：6×10¹²→39.7 pJ（与论文口径一致）；SI 模型阈值 10×10¹² → **110 pJ**；θ=0.3 口径 9×10¹² → 90 pJ；纯 SOT 20×10¹² → 441 pJ。当前模型阈值能量**高于**论文 50 pJ 预算（论文用 6×10¹²/θ=0.3 上限口径）。【已核实】
12. **噪声 spot check**：`Noise=1` 时 Jp=9×10¹² 从不翻变为部分翻（−0.32）、10×10¹² 翻转幅度略变（−0.94）；重复 run 结果逐位相同（固定种子）→ 只能做开关对照，不能做 P<sub>sw</sub> 统计。【已核实】

## 7. 输出与归档

1. 每个 case：`runs/<tag>/<tag>.mx3`（实际运行脚本副本）+ `runs/<tag>/out/`（保留 `table.txt`、`log.txt`、`m_initial.ovf`、`m_final.ovf`）。`runs/` **仅本地**（已在 `.gitignore`，运行数据不进仓库；仓库只含代码、文档与 `docs/figures/` 定稿图）。【约定】
2. `summary.csv` 列含 `model`（`si`/`legacy`）；新 run 由 `run_case.py --model` 写入（默认 si）。`switched = InitMz·mz_final < −0.5`；`t_cross` 为首次过零（含"过零又弹回"的情况，判定以 mz<sub>final</sub> 为准）。【约定】
3. 定稿图（SI 版）：`docs/figures/`（heat_model、phase_map、phase_traces、phase_speed、fig4_full、mechanism_compare、q_quadrants、energy_bars 等）。旧版备份在本地 `runs/legacy/`（不入仓库）。【约定】
4. OVF 后处理：`mumax3-convert -png out/m_final.ovf`（或 `-vtk` 给 ParaView）。【约定】

## 8. 已知局限与未决

1. 均匀 Ku1/无晶粒随机性 → 未做 P<sub>sw</sub>(Jp) 概率统计（mumax3 Langevin 为固定种子，需内核/驱动改造，见 ROADMAP P1）。
2. 脉冲波形按 sech² 约定；SI 未给出波形与反射的精确序列 → 绝对阈值偏高 ~1.5×（相对比值已对上）。
3. Jp≳1.9×10¹³ 时 Tmax>Tc、Ms 截断为 0，属 HAMR 型情形（论文实验排除），解读需谨慎。
4. 论文准静态 Jc(Hx)（100 µs，热激活）不适合长时间 LLG 复现。
5. 网格/材料敏感性（Aex=3×10⁻¹¹ 为典型值，SI 未给 A）未系统扫描（ROADMAP P3）。
6. **多畴伪影**：64×64 帧（5 nm 胞元，√(A/Kz)≈5 nm 同量级）在近阈值/极强电流下会出现条畴，|⟨m⟩|≈0.28–0.58，此时平均 mz 不代表单畴翻转 → 判定标准是 `m_final.ovf` 的 |⟨m⟩|<0.9 即剔除（phase_map 灰叉）。已确认的多畴点：无加热 19e12（θ=0.2）、无加热 13e12（θ=0.3）、加热 14e12（θ=0.3）、加热 27e12（θ=0.2）。
7. 【历史】legacy 结论（2026-09-15 版）：dT<sub>ref</sub> 旋钮加热下"6–10×10¹² 完全依赖焦耳热"、宏自旋最快 39 ps、阈值能量 39.7–441 pJ 等，均基于猜测参数（Ms=1.3×10⁶、Ha=1 T、α=0.15、dT∝J² 旋钮），已被 SI 参数版取代；旧 runs/图以 legacy 保留，勿与新结果混用。

## 9. 引用

- doi:10.1038/s41928-020-00488-3
- A. Vansteenkiste et al., *AIP Advances* **4**, 107133 (2014).
