# mumax3 复刻 NE 2020《Spin-orbit torque switching of a ferromagnet with picosecond electrical pulses》踩坑记录

论文：Jhuria et al., *Nature Electronics* **3**, 680–686 (2020), doi:10.1038/s41928-020-00488-3
环境：mumax3 v3.12 (CUDA 12.9)，`E:\mumax3.12_windows_cuda12.9\mumax3.exe`，RTX 5060 Laptop 8 GB，Python 3.12 + numpy/matplotlib

```text
E:\_SOT_MARM\
├─ README.md
├─ FACTS.md
├─ .gitignore / .gitattributes
├─ papers\                           文献 PDF（NE 2020 / NC 2026 / AM 2023）
│  └─ mumax3_docs\                   mumax3 原始论文、教程与相关文献
├─ notes\
│  ├─ NE_2020.md                    论文 markdown 版
│  ├─ error.md                      本踩坑记录
│  ├─ SOT_mumax3_交接文档.md        项目交接文档
│  ├─ 三篇论文逐句翻译整合.md       论文翻译整合
│  └─ extracted.txt                 论文 PDF 抽取文本
└─ simulations\
   └─ mumax3_sot\                   主工作目录（已跑通）
      ├─ fig4_dynamics.mx3          图 4：宏自旋超快动力学（SOT + 焦耳加热）
      ├─ fig3_switching.mx3         图 3：5×4 µm 器件单脉冲确定性翻转
      ├─ macrospin_switch.mx3       64×64 快速翻转模板（时间精确，KuExp/Heating/θ 旋钮）
      ├─ plot_table.py              table.txt 后处理/绘图
      ├─ plot_phase.py              summary.csv → 定稿相图与边界曲线
      ├─ plot_fig4.py               a_f4_* → Fig.4 ΔMz(t)（平行/反平行/无 Hx）
      ├─ plot_mechanism.py          c0/b0、b2、b3 机制对照三面板
      ├─ plot_quadrants.py          q1–q4 m_final.ovf → 末态 2×2 面板
      ├─ energy_check.py            能量核算（∫J²dt·ρV，对标论文 <50 pJ）
      ├─ run_case.py                批量运行+数据归档（每个参数组合一个目录）
      ├─ runs\                      批量结果：summary.csv + <tag>\<tag>.mx3 + out\
      ├─ fig4_dynamics.out\         图 4 的仿真输出（table.txt / ovf / png / log）
      └─ fig3_switching.out\        图 3 的仿真输出
```

> 注：2026-09-15 目录整理：文献/笔记/仿真先统一归入 `resource\`，后把 `papers\`、`notes\`、`simulations\` 直接放到仓库根目录；本文中所有命令路径已同步更新。

---

## 1. 问题清单（现象 → 原因 → 解决）

### 1.1 论文 PDF 读不进来
- 现象：对话模型不支持 PDF 输入。
- 解决：用 `python -m pip install pypdf` 抽取文本；本次用户已转成 `NE_2020.md`，后续可直接引用。

### 1.2 mumax3 没有 `xiDL` / `xiFL`（原生 SOT 输入）
- 现象：`xiDL = 0.2` 报错 `undefined: xiDL`。
- 原因：mumax3 只有 Zhang–Li 和 Slonczewski 两种自旋力矩模型，没有单独的 SOT 接口。
- 解决：用 Slonczewski 模型等效 SOT（已对照 `cuda/slonczewski2.cu` 源码和数值实验验证）：

```text
Pol          = theta_DL      // 0.2
EpsilonPrime = theta_FL      // 0.05
Lambda       = 1             // 使 epsilon = Pol/2
FixedLayer   = sigma         // 自旋极化方向（Hx>0 时取 (0,-1,0)）
FreeLayerThickness = 1e-9    // Co 层厚度
DisableZhangLiTorque = true
J = vector(0, 0, J_SOT)      // 关键：Slonczewski 内核只读 J 的 z 分量！
```

等效性推导（mumax3 内核）：
`beta = (hbar/e)*J/(t*Ms)`，`epsilon = Pol*Lambda^2 / ((Lambda^2+1)+(Lambda^2-1)(p·m))`；
取 `Lambda=1` 得 `epsilon = Pol/2`，于是
`dm/dt|DL = gamma0 * (hbar/e) * (Pol/2) * J/(t*Ms) = gamma0*(hbar/2e)*Pol*J/(t*Ms)`，
正是标准 SOT damping-like 力矩（`Pol` 即 `theta_DL`）。
数值自检：`Ms=1.3e6, t=1nm, Pol=0.2, Lambda=1, EpsilonPrime=0.05, J=1e12, m=+z, FixedLayer=(0,1,0)`
→ `STTorque = [0.0201, 0.0526, 0] T`，与手算 `beta*(ex,ey)` 完全一致。

### 1.3 弛豫后磁矩跑到面内（mz≈0）—— 旧脚本“失效”的根因
- 现象：`relax()` 后 `m=[1,0,0]`，翻转实验无论多大电流都不动。
- 原因 1：**mumax3 的 `Msat` 默认值是 0**。不显式赋值时各向异性场和退磁场全为 0，`relax()` 是空操作。
- 原因 2：`Ku1` 公式单位错误（多乘了一个 `mu0`），有效 PMA ≈ 0，面内形状各向异性占优。
- 解决：

```text
Msat = Ms0                                        // 必须先赋值！
Ku1  = 0.5*Ms0*Ha0 + 0.5*mu0*Ms0*Ms0              // Ha0 用特斯拉(T)，Keff = Ms*Ha/2
```

### 1.4 标识符大小写不敏感
- 现象：`T0 := 300.0` 报 `already defined: T0`（但 `t0 := 5e-12` 在前）。
- 原因：mumax3 语法大小写不敏感（`msat` 与 `Msat` 相同），`T0` 与 `t0` 冲突；同理 **变量 `T` 会覆盖内置时间 `t`**。
- 解决：用 `Troom`（室温）、`Tcur`（当前温度）等不冲突的名字。

### 1.5 自适应求解器把时间轴拉长（ps 脉冲仿真致命）
- 现象：循环 `run(0.25e-12)` 共 1600 次，但 table 的 `t` 到了 23 ns（预期 0.4 ns），脉冲"变宽"57 倍。
- 原因：默认 RK45 自适应步长在近平衡宏自旋上可取到 ~14 ps；`run(dt)` 每次至少走一个内部步长，步长噪声累积。
- 解决：

```text
SetSolver(4)     // 固定步长 RK4
FixDt = 5e-14    // 0.05 ps
```

并且脉冲电流写成**内置时间 t 的函数**（mumax3 每步重算），温度 ODE 用**实测经过时间** `tb := t; dtr := tb - tprev` 积分，这样即使 `run()` 多走一步，物理时刻也不会漂移。

### 1.6 表达式不能跨行
- 现象：`-vet` 报 `expected ')', found newline`。
- 原因：mumax3 解析器不支持括号内换行。
- 解决：所有长表达式压成一行；修改后用 `mumax3.exe -vet script.mx3` 先检查语法。

### 1.7 `AutoSave` 与 `AutoSnapshot` 冲突
- 现象：同时写 `AutoSave(m,25e-12)` 和 `AutoSnapshot(m,10e-12)`，输出目录里**只有 png，没有 ovf**。
- 原因：二者共用同一个 autosave 槽位，后写的覆盖前者。
- 解决：一次只用一个；需要图像时后处理：`mumax3-convert -png m0*.ovf`（或 `-jpg/-csv/-numpy`）。

### 1.8 转矩符号与四象限（图 3）
- 现象：`FixedLayer=(0,+1,0)` 时宏自旋怎么都不翻转。
- 原因：对 `Hx>0`，SOT 把 m 推向 +y，而进动又把 m 拉回 +z（方向对抗）。
- 解决：取 `FixedLayer=(0,-1,0)` 使 SOT 推向 −y，进动继续把 m 带到 −z；对应论文"平行 (Hx+, I+) → −Mz"。翻转任一符号即可得到其余象限：

| Hx | I | σ = -y 时末态 |
|----|---|----------------|
| +  | + | −Mz（平行，论文） |
| −  | + | +Mz |
| +  | − | +Mz |
| −  | − | −Mz |

### 1.9 归一化磁矩 vs MOKE 可观测量
- 现象：table 里的 `mz` 是单位矢量分量，直接画和图 4 对不上。
- 原因：实验测的是 `M_z = Ms(T) · m_z`，还要除以室温 `Ms0`。
- 解决：脚本里每步把 `Ms(T)` 记录进 table（`TableAddVar(Ms_cur,"Ms","A/m")`），后处理：

```text
dMz/Ms = Ms(T)*mz(t)/Ms0 - mz(t0)      // t0 取脉冲前的参考时刻
```

### 1.10 参数不在正文，模型差异
- 现象：用论文给出的上限 `Jc≈6e12 A/m²`、`θ_DL=0.2`、Ha=1 T 做宏自旋仿真，6 ps 脉冲**翻不过来**（6×10¹²+任何合理加热都不行）。
- 原因：论文正文只给了能量上限估计和拟合出的 θ；加热模型（`Ms(T)`、`Ku(T)` 的具体幂律、`dT`、热弛豫时间）在 Supplementary Information 里，未公开在正文。
- 现状（本工作扫描结果，供起点）：`Jpk ≥ 1.2e13 A/m²` 且 `dTpk ≈ 400 K`（峰值 T≈680 K < Tc=800 K，论文排除了 HAMR 情形）时，~50 ps 内平均 mz 过零、最终 mz≈−0.96；论文模型预测最快 16 ps。**要精确复刻图 3 需从 SI 取参数或自行拟合 Jpk/dTpk/tauC。**

### 1.11 64×64 宏旋脚本的“6 ps”实为 ~28 ps（自适应步长再次踩坑）
- 现象：早期自适应步长脚本在 Jp=6×10¹² 就翻转，看似复现论文上限；但能量核算得 ∫J²dt = 7.76×10¹⁴ → **189 pJ**（名义应 ~40 pJ）。
- 原因：该脚本（上一轮重写版）用循环计数驱动脉冲、未固定步长；默认 RK45 在近平衡宏自旋上内部 dt≈1 ps，`run(0.2 ps)` 实际推进 1 ps → 脉冲在真实时间轴上被拉长到 **FWHM 27.6 ps**，积分增大 4.8 倍。
- 解决：新增 `macrospin_switch.mx3`：脉冲写成内置时间 t 的函数，`SetSolver(4); FixDt=5e-14`，温度 ODE 用实测 Δt 积分。修正后实测 FWHM=5.85 ps、∫J²dt=1.63×10¹⁴（39.7 pJ，与论文 40 pJ 口径一致），**Jp=6×10¹² 不再翻转**。
- 结论：早期两条“参考运行”实为 **~28 ps 脉冲** 的结果，不能当作 6 ps 结论引用；旧输出已废弃删除，等效案例用修正脚本重跑（开关型 `runs/b0_6e12`、动力学型 `runs/dyn_Jp1e12_Ip`）。

### 1.12 `Pol=0` 会被断言拦截（做 θ=0 测试时）
- 现象：设 `Pol=0` + J≠0 时仿真直接中止。
- 原因：mumax3 源码 `AddSTTorque` 在 J≠0 时先执行 `AssertMsg(!Pol.isZero(), ...)`，早于 `DisableSlonczewskiTorque` 判断。
- 解决：用 `Pol=1e-4`（等效零 SOT）+ `EpsilonPrime=0` 做“仅热各向异性力矩”测试。

---

## 2. 运行与数据整理

### 2.1 运行

```powershell
$mx = "E:\mumax3.12_windows_cuda12.9\mumax3.exe"
& $mx -vet simulations\mumax3_sot\fig4_dynamics.mx3                    # 只查语法
& $mx -f -o "simulations\mumax3_sot\runs\fig4_Hxp160_Ip.out" simulations\mumax3_sot\fig4_dynamics.mx3
& "E:\mumax3.12_windows_cuda12.9\mumax3-convert.exe" -png simulations\mumax3_sot\runs\...\m0*.ovf
python simulations\mumax3_sot\plot_table.py "simulations\mumax3_sot\runs\...\table.txt" --out fig4_sim.png
& $mx -i simulations\mumax3_sot\fig4_dynamics.mx3                      # 带浏览器实时 GUI
```

常用参数：`-o` 指定输出目录、`-f` 覆盖已有目录、`-vet` 只检查、`-s` 静默、`-i` 交互 GUI（http://127.0.0.1:35367/）。

### 2.1.1 批量运行与归档（推荐）

`run_case.py` 把"模板脚本 + 参数替换"写成独立目录并自动汇总：

```powershell
python simulations\mumax3_sot\run_case.py simulations\mumax3_sot\fig3_switching.mx3 q1_Hxp_Ip --set Hx=0.160 Isign=1
python simulations\mumax3_sot\run_case.py simulations\mumax3_sot\fig4_dynamics.mx3 f4_lowJ --set Jpk=2e12 dTpk=15 --no-run
```

生成的目录结构（每个物理条件一套，脚本可溯源）：

```text
simulations\mumax3_sot\runs\
  summary.csv                  # 每个 case 一行：参数 + mz_final + switched + Tmax
  q1_Hxp_Ip\
    q1_Hxp_Ip.mx3              # 实际运行的脚本（参数已替换）
    out\table.txt, log.txt, *.ovf, ...
```

### 2.2 输出目录内容

| 文件 | 内容 |
|------|------|
| `table.txt` | 时间序列：t、mx、my、mz、E<sub>total</sub>、T、J、Ms（`#` 开头的表头行含列名+单位） |
| `log.txt` | 完整脚本回显 + 运行信息（版本、GPU、编译信息）——溯源用 |
| `references.bib` | mumax3 自动生成的文献引用（可再生，已列入 `.gitignore`，不保留） |
| `m_initial.ovf / m_final.ovf / *.png` | 初态与末态磁化分布（AutoSave 的中间帧 `m0*.ovf` 已清理，可再生） |
| `gui/` | 在线 GUI 数据（可再生，不保留） |

**组织建议**：一个物理条件 = 一个 `runs\<参数标签>.out` 目录，如
`fig4_Hxp160_Ip_J4.0e12_dT20` / `fig3_Hxn160_Im_J1.2e13_dT400`；
目录内保留一份脚本副本（运行前 `Copy-Item`），把 `table.txt` + 绘图脚本输出放一起。批量扫描时用 PowerShell 循环改脚本参数、输出目录带参数标签即可。

### 2.3 论文关键参数 vs 脚本当前默认值

| 量 | 论文 | 脚本默认（图 4 / 图 3） | 备注 |
|----|------|--------------------------|------|
| 叠层 | Ta5/Pt4/Co1/Cu1/Ta4/Pt1 (nm) | 只建 Co(1 nm) | SOT 等效在 Co 上 |
| Ha (300 K) | ≈ 1 T | 1 T | FMR 半周期 ~18 ps |
| θ<sub>DL</sub> / θ<sub>FL</sub> | 0.2 / 0.05 | 0.2 / 0.05 | 拟合值 |
| Ms, α | VSM 拟合 / 表观 >0.2 | 1.3×10⁶ A/m, 0.1 | 待按 SI/实验拟合 |
| Tc | ~800 K | 800 K | |
| 脉冲 | 6 ps(翻转)/3.7 ps(动力学) | 3.7 ps / 6 ps | sech² 或高斯 FWHM |
| Hx | ±160 mT | +160 mT（负号改 Hx） | <120 mT 不翻转 |
| Jc | 准静态 2×10¹¹；脉冲上限 6×10¹² | 4×10¹² / 1.2×10¹³ | 脉冲值需拟合；见 1.10 |
| dTpk / tauC | SI 未公开 | 20 K/200 ps 与 400 K/100 ps | 拟合旋钮 |
| 器件 | 5×4 µm 过流窗口 | 图 3 网格 500×400×10 nm | 图 4 用 64×64 PBC 宏自旋 |

---

## 3. 已验证结果（2026-09-15）

- **图 4**：`fig4_dynamics.mx3` 跑通（~24 s）。弛豫后 m=[0.155, 0, 0.988]（Ha=1 T、Hx=160 mT 的倾斜平衡态）；脉冲后出现"瞬时下拉 + 进动 + 慢恢复"，**进动周期 37 ps**（与论文 Ha≈1 T 的 ~40 ps 一致），Tmax≈320 K，ΔMz/Ms 最小 ≈ −4.8%，400 ps 后恢复到 −0.3%。幅度可通过 `Jpk/dTpk/tauC` 拟合到论文数据。
- **图 4 三组对照（批量）**：`runs/f4_Hx0_Ip`、`runs/f4_Hxp160_Ip`、`runs/f4_Hxm160_Ip`（Isign=+1），合成图 `runs/fig4_like.png` 复现了 Fig. 4a 的对称性：
  - Hx=0：无振荡，单纯下拉 + 慢恢复（黑）；
  - Hx=+160 mT（平行）：ΔMz 先快速下冲（−4.8% @15.8 ps）再反相振荡；
  - Hx=−160 mT（反平行）：ΔMz 无正上冲（最低 −3.5% @31.8 ps），与平行组反相；原始 mz 会从 0.987 升到 0.999，但被 Ms(T) 下降掩盖；
  - 三者在 ~400 ps 内都恢复到 ≈−0.25%。
- **图 3（四象限验证）**：`fig3_switching.mx3` 跑通（每个 case ~26 s，`run_case.py` 批量）。`Jpk=1.2e13 A/m², dTpk=400 K`（峰值 680 K < Tc）时 ~50 ps 内 mz 过零，最终 |mz|≈0.96：

| case | Hx (mT) | I 符号 | 末态 mz | 对应论文象限 |
|------|---------|--------|---------|--------------|
| q1_Hxp_Ip | +160 | + | **−0.956** | 平行 → −Mz ✓ |
| q2_Hxm_Ip | −160 | + | +0.987 | 反平行 → +Mz ✓ |
| q3_Hxp_Im | +160 | − | +0.987 | 反平行 → +Mz ✓ |
| q4_Hxm_Im | −160 | − | **−0.956** | 平行 → −Mz ✓ |

- **翻转机制**：检查 OVF 快照（`m000003.ovf`，75 ps），整个 5×4 µm 区域 mz 同步过零（均匀灰），即**近相干翻转**，无可见畴壁/成核——与论文"两者皆有可能、该样品接近相干"的讨论一致。当前为均匀 Ku1 模型，后续可加晶粒各向异性涨落（`ext_makegrains` + 逐 region `Ku1.SetRegion`）研究成核路径。

- **图 4 六组合 + 反射（A 阶段）**：`runs/a_f4_*`（Hx∈{0,±160 mT} × I±，`echo=0.3, ted=24 ps`），合成图 `runs/fig4_full.png`。结果与论文 Fig. 4a 对称性完全一致：
  - Hx=0 时 ±I 曲线完全重合，无振荡（单纯下拉 + 慢恢复）；
  - 平行组 (Hx+,I+) 与 (Hx−,I−) 重合：下冲 −4.8% @15.8 ps 后进动；
  - 反平行组 (Hx+,I−) 与 (Hx−,I+) 重合：ΔMz 无正上冲（最低 −3.5% @31.8 ps），与平行组反相进动；图/表首行 t=0 的 +1.3% 是未弛豫态（mz=1）伪影，所有 Hx≠0 曲线都有；
  - 反射在 T(t) 上表现为 ~29 ps（t0+ted）的次级峰，并给磁化一个次级踢动。

- **B1 最快翻转（时间精确的 6 ps 脉冲，J<sub>ref</sub>=Jp、dT∝J²）**：

| case | Jp (A/m²) | dT<sub>ref</sub> | Tmax | 平均 mz 过零 | 过零后 50 ps 恢复 |
|------|-----------|--------|------|--------------|-------------------|
| b1_Jp8_dT300 | 8×10¹² | 300 K | 583 K | 不翻转 | – |
| b1_Jp8_dT450 | 8×10¹² | 450 K | 725 K | 58.6 ps | 92% |
| b1_Jp10_dT300 | 1.0×10¹³ | 300 K | 583 K | 88.8 ps（部分，末态 −0.11） | – |
| b1_Jp12_dT300 | 1.2×10¹³ | 300 K | 583 K | 65.5 ps | 77% |
| b1_Jp12_dT450 | 1.2×10¹³ | 450 K | 725 K | 50.1 ps | 93% |
| b1_Jp16_dT300 | 1.6×10¹³ | 300 K | 583 K | 51.7 ps | 89% |
| b1_Jp16_dT450 | 1.6×10¹³ | 450 K | 725 K | 43.7 ps | 95% |
| **b1_Jp20_dT450** | **2.0×10¹³** | **450 K** | **725 K** | **39.0 ps（最快）** | 97% |

  → 本模型现有最快 ~39 ps（Jp=2×10¹³、dT=450 K；对应能量 ~441 pJ），论文模型预测最快 16 ps；差距来自加热律/幂律参数（SI 未公开）。

- **B2 θ≈0（仅热各向异性力矩）**：`Pol=1e-4, EpsilonPrime=0`、Jp=8×10¹²。dT<sub>ref</sub>=300 K 不翻转；dT<sub>ref</sub>=450/600/800 K（Tmax 725/867/1056 K）分别在 **85.9/92.3/122.4 ps** 翻转 → 定性复现 SI Fig. 5（θ=0 也能翻转），但需要更强加热且更慢。

- **B3 Ku(T) 开关**：`KuExp=3`（Ku∝Ms³）时 Jp=1×10¹³ 部分翻转、1.2×10¹³ 完全翻转；`KuExp=0`（Ku 不随温度变）时到 Jp=1.4×10¹³ 仍不翻转 → 热各向异性力矩是模型中的必要项；阈值能量比 ≥(1.4/1.0)²≈2，与论文"降低 2 倍"定性一致。

- **C0 Heating=0 对照**：与 `b0_6e12`/`b0_8e12`/`b1_Jp10_dT300` 同参数、仅 `Heating=0`。Jp=6/8/10×10¹² 三档均不翻转（末态 mz≈+0.988、T 恒 300 K），最大瞬态下拉 −8.1%/−12.4%/−17.6%（相对弛豫平衡态 0.988，≈33 ps；表首行 t=0 为未弛豫态，勿用作基准）→ 6–10×10¹² 的确定性翻转完全依赖焦耳热致热各向异性力矩。目录 `runs/c0_noh_*`，对照图 `runs/heating_on_off.png`、`runs/mechanism_compare.png`（c0/b0、b2、b3 三面板）。

- **C1 相图边界中间点**（`J_ref=Jp`）：9×10¹²/dT300 不翻（末态 +0.933）；8×10¹²/dT375 翻 66.5 ps；7×10¹²/dT450 翻 61.0 ps；6×10¹²/dT600 翻 80.5 ps → `Tmax≈583 K` 线上 `Jc∈(9,10]e12`，`Jp=8e12` 竖线上 `dTc∈(300,375]K`。定稿图 `runs/phase_map.png`、`phase_traces.png`、`phase_speed.png`（`plot_phase.py`；B2/B3 点自动剔除，C0 无加热点保留在 T=300 K 线上，C2 `Hx=0` 点以灰色菱形单列、不参与边界拟合）。

- **C2 对称性对照 Hx=0**（与 `b1_Jp8_dT450` 同参数 `Jp=8e12, dT_ref=450, I_sign=+1`，仅 `Hx_mT=0`；`runs/c2_Hx0_Jp8_dT450`）：瞬态最低 mz=0.80（40.2 ps）后恢复，末态 **+1.0000**、无过零（t<sub>cross</sub> 空），Tmax=725 K → 与 Hx=+160 mT 的 58.6 ps 翻转对照，确认 `Hx≠0` 为对称性破缺必要条件。

- **F 能量核算（`energy_check.py`，ρ=81 μΩ·cm，V=5×4 µm²×15 nm）**：Jp=6×10¹² → **39.7 pJ**（与论文 40 pJ 口径一致）；能翻转的案例能量 54.1 pJ（7×10¹²/450 K，Tmax=725 K）、39.7 pJ（6×10¹²/600 K，Tmax=867 K>Tc，接近论文排除的 HAMR 情形）、70.6 pJ（8×10¹²/450 K）、158.9 pJ（1.2×10¹³/450 K）、441 pJ（2×10¹³/450 K，最快 39 ps）。即本模型已能靠 6×10¹²（论文上限）+ 强加热翻转并落回 <50 pJ 预算；不依赖过 Tc 加热的最低能量档为 7×10¹²/450 K 的 54.1 pJ。

## 4. 脚本状态说明

- `macrospin_switch.mx3`（**新增规范模板**）：64×64 快速版，时间精确（实测 FWHM=5.85 ps@6 ps 档），带 `Jp / dT_ref / J_ref / tau_cool / Heating / KuExp / Pol / EpsilonPrime / I_sign / InitMz / Hx_mT / RunDynamics` 旋钮；配合 `run_case.py` 批量运行，`summary.csv` 自动记录 `t_cross_ps`（过零时刻）与 `recov_50ps`（过零后 50 ps 恢复率）。
- `fig3_switching.mx3` / `fig4_dynamics.mx3`：5×4 µm 全器件与宏自旋动力学脚本，时间精确，继续作主力。
- 早期自适应步长版本的脚本与输出：**已废弃删除**（存在 1.11 的步长问题，“6 ps”实为 ~28 ps FWHM），等效案例已用修正脚本重跑：开关型 `runs/b0_6e12`（6×10¹² 不翻转）、动力学型 `runs/dyn_Jp1e12_Ip`（Tmax≈308 K）。

## 5. SI 版复核与多畴伪影（2026-09-17）

### 5.1 非单调窗口复核：15–16e12 → **15–17e12**
- 现象：phase_map 上 θ=0.2 加热档在 15、16e12 不翻（末态 +0.96），18e12 恢复；怀疑是快照未弛豫。
- 复核：同参数重跑 `si_h_t20_Jp15`，table 与原档最大差 2.5×10⁻⁷（GPU 归约舍入级，确定性）；再把自由演化从 0.4 ns 延到 **1.5 ns**（T 回 ~300 K），15/16/17e12 末态稳定在 **+0.981**（单畴 |⟨m⟩|=1.000），14/18e12 为 −0.981 → **窗口实为 15–17e12**，θ=0.3 为 14–17e12，18e12 恢复。
- 高电流扫描（θ=0.2，21–30e12，1e12 步长，加热开/关）：再无第二个窗口（27e12 加热档见 5.2）。步长减半（FixDt 25 fs）结论不变。
- 结论：旧图和文档的“15–16e12、+0.96”是 0.4 ns 快照，已被取代；1.5 ns 复核数据以 `*_lr1500` 标签归档。

### 5.2 多畴伪影：|⟨m⟩| < 0.9 的判定
- 现象：个别近阈值/极强电流点的末态 `mz` 平均值很小（如 t30/Jp14 +0.05、t20/Jp27 +0.10、无加热 t20/Jp19 −0.18），像“卡在赤道”。
- 原因：这些末态的 `m_final.ovf` 是**条畴**（mz 从 −0.99 到 +0.99 交替，|⟨m⟩|≈0.28–0.58），不是单畴停住——64×64 帧的胞元 5 nm 与畴壁宽 √(A/Kz)≈5 nm 同量级，近阈值时边缘天然破缺会长成条纹。
- 解决：`plot_phase.py` 读取 `m_final.ovf` 计算 |⟨m⟩|，<0.9 的点从曲线剔除、画灰叉并标注 `multidomain (excluded)`。已确认：加热 27e12 / 14e12（θ=0.3）、无加热 19e12（θ=0.2）/ 13e12（θ=0.3）。
- 结论：phase_map 上的“部分翻转”（mz≈−0.47/−0.10）多数是多畴伪影，不应作为单畴部分翻转解读；单畴判定的窗口点不受影响。

### 5.3 数据入库策略（2026-09-17）
- `runs/`（summary.csv、table.txt、log、ovf、case 脚本）整体加入 `.gitignore`，**仅本地保留**；定稿图拷入 `docs/figures/` 随仓库发布，README/RESULTS/FACTS/ROADMAP 引用同步更新。
- 如需把历史提交里的 run 数据也从 GitHub 彻底移除，需 `git filter-repo` 重写历史 + force push（见 ROADMAP R0 遗留）。
