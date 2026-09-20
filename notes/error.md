# mumax3 复刻 NE 2020《Spin-orbit torque switching of a ferromagnet with picosecond electrical pulses》踩坑记录

论文：Jhuria et al., *Nature Electronics* **3**, 680–686 (2020), doi:10.1038/s41928-020-00488-3
环境：mumax3 v3.12 (CUDA 12.9)，`E:\mumax3.12_windows_cuda12.9\mumax3.exe`，RTX 5060 Laptop 8 GB，Python 3.12 + numpy/matplotlib

```text
E:\_SOT_MARM\
├─ slides\
│  └─ PicoSOT_组会汇报.pptx          组会汇报讲稿（本地生成，不入库）
├─ README.md
├─ FACTS.md
├─ docs\                            结果记录与论文映射（RESULTS.md / paper_replica.md / figures\）
├─ notes\
│  └─ error.md                      本踩坑记录
└─ simulations\
   └─ mumax3_sot\                   主工作目录（已跑通）
      ├─ fig4_dynamics.mx3          图 4：宏自旋超快动力学（SOT + 焦耳加热）
      ├─ fig3_switching.mx3         图 3：5×4 µm 器件单脉冲确定性翻转
      ├─ macrospin_switch.mx3       64×64 快速翻转模板（时间精确，Heating/θ 旋钮）
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

> 注：2026-09-15 目录整理：文献/笔记/仿真统一归入项目根目录；本文中所有命令路径已同步更新。

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

### 1.3 弛豫后磁矩跑到面内（mz≈0）
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
- 现象：按论文正文能直接读到的参数（θ<sub>DL</sub>=0.2、能量上限 6e12、Ha≈1 T）跑宏自旋，6 ps 脉冲翻不过来。
- 原因：论文正文只给了能量上限估计和拟合出的 θ；完整宏观自旋模型（Ms、α、`Ms(T)`/`Ku(T)` 幂律、热学参数与热弛豫）都在论文里。
- 解决：逐项按论文取参（映射与标定见 `docs/paper_replica.md`）；本复现的全部结果均基于论文参数模型。


### 1.11 `Pol=0` 会被断言拦截（做 θ=0 测试时）
- 现象：设 `Pol=0` + J≠0 时仿真直接中止。
- 原因：mumax3 源码 `AddSTTorque` 在 J≠0 时先执行 `AssertMsg(!Pol.isZero(), ...)`，早于 `DisableSlonczewskiTorque` 判断。
- 解决：用 `Pol=1e-4`（等效零 SOT）+ `EpsilonPrime=0` 做“仅热各向异性力矩”测试。

---

## 2. 运行与数据整理

### 2.1 运行

```powershell
$mx = "E:\mumax3.12_windows_cuda12.9\mumax3.exe"
& $mx -vet simulations\mumax3_sot\fig4_dynamics.mx3                    # 只查语法
& $mx -f -o "simulations\mumax3_sot\runs\fig4_dynamics.out" simulations\mumax3_sot\fig4_dynamics.mx3
& "E:\mumax3.12_windows_cuda12.9\mumax3-convert.exe" -png simulations\mumax3_sot\runs\...\m0*.ovf
python simulations\mumax3_sot\plot_table.py "simulations\mumax3_sot\runs\...\table.txt" --out fig4_sim.png
& $mx -i simulations\mumax3_sot\fig4_dynamics.mx3                      # 带浏览器实时 GUI
```

常用参数：`-o` 指定输出目录、`-f` 覆盖已有目录、`-vet` 只检查、`-s` 静默、`-i` 交互 GUI（http://127.0.0.1:35367/）。

### 2.1.1 批量运行与归档（推荐）

`run_case.py` 把"模板脚本 + 参数替换"写成独立目录并自动汇总：

```powershell
python simulations\mumax3_sot\run_case.py simulations\mumax3_sot\macrospin_switch.mx3 si_h_t20_Jp8 --set Jp=8e12 Heating=1
python simulations\mumax3_sot\run_case.py simulations\mumax3_sot\fig4_dynamics.mx3 si_a_f4_Hx0_Ip --set Jpk=4e12 --no-run
```

生成的目录结构（每个物理条件一套，脚本可溯源）：

```text
simulations\mumax3_sot\runs\
  summary.csv                  # 每个 case 一行：参数 + mz_final + switched + Tmax
  si_h_t20_Jp8\
    si_h_t20_Jp8.mx3              # 实际运行的脚本（参数已替换）
    out\table.txt, log.txt, *.ovf, ...
```

### 2.2 输出目录内容

| 文件 | 内容 |
|------|------|
| `table.txt` | 时间序列：t、mx、my、mz、E<sub>total</sub>、T、J、Ms（`#` 开头的表头行含列名+单位） |
| `log.txt` | 完整脚本回显 + 运行信息（版本、GPU、编译信息）——溯源用 |
| `references.bib` | mumax3 自动生成的文献引用（可再生，不保留） |
| `m_initial.ovf / m_final.ovf / *.png` | 初态与末态磁化分布（AutoSave 的中间帧 `m0*.ovf` 已清理，可再生） |
| `gui/` | 在线 GUI 数据（可再生，不保留） |

---

## 3. 脚本状态说明

- `macrospin_switch.mx3`（主模板）：64×64 快速版，时间精确（实测 FWHM=5.85 ps @6 ps 档），带 `Jp / tp_ps / Heating / ScaleMs / ScaleKz / Noise / ThetaDL / I_sign / InitMz / Hx_mT / RunDynamics / t_free` 旋钮；配合 `run_case.py` 批量运行，`summary.csv` 自动记录 `t_cross_ps`（过零时刻）与 `recov_50ps`（过零后 50 ps 恢复率）。
- `fig3_switching.mx3` / `fig4_dynamics.mx3`：5×4 µm 全器件与宏自旋动力学脚本，时间精确，继续作主力。

## 4. 复现复核与多畴伪影（2026-09-17）

### 4.1 非单调窗口复核：15–16e12 → **15–17e12**
- 现象：phase_map 上 θ=0.2 加热档在 15、16e12 不翻（末态 +0.96），18e12 恢复；怀疑是快照未弛豫。
- 复核：同参数重跑 `si_h_t20_Jp15`，table 与已归档 table 最大差 2.5×10⁻⁷（GPU 归约舍入级，确定性）；再把自由演化从 0.4 ns 延到 **1.5 ns**（T 回 ~300 K），15/16/17e12 末态稳定在 **+0.981**（单畴 |⟨m⟩|=1.000），14/18e12 为 −0.981 → **窗口实为 15–17e12**，θ=0.3 为 14–17e12，18e12 恢复。
- 高电流扫描（θ=0.2，21–30e12，1e12 步长，加热开/关）：再无第二个窗口（27e12 加热档见 4.2）。步长减半（FixDt 25 fs）结论不变。
- 结论：0.4 ns 快照的“15–16e12、+0.96”不是稳定末态；1.5 ns 复核后窗口稳定为 15–17e12（+0.981），复核数据以 `*_lr1500` 标签归档。

### 4.2 多畴伪影：|⟨m⟩| < 0.9 的判定
- 现象：个别近阈值/极强电流点的末态 `mz` 平均值很小（如 t30/Jp14 +0.05、t20/Jp27 +0.10、无加热 t20/Jp19 −0.18），像“卡在赤道”。
- 原因：这些末态的 `m_final.ovf` 是**条畴**（mz 从 −0.99 到 +0.99 交替，|⟨m⟩|≈0.28–0.58），不是单畴停住——64×64 帧的胞元 5 nm 与畴壁宽 √(A/Kz)≈5 nm 同量级，近阈值时边缘天然破缺会长成条纹。
- 解决：`plot_phase.py` 读取 `m_final.ovf` 计算 |⟨m⟩|，<0.9 的点从曲线剔除、画灰叉并标注 `multidomain (excluded)`。已确认：加热 27e12 / 14e12（θ=0.3）、无加热 19e12（θ=0.2）/ 13e12（θ=0.3）。
- 结论：phase_map 上的“部分翻转”（mz≈−0.47/−0.10）多数是多畴伪影，不应作为单畴部分翻转解读；单畴判定的窗口点不受影响。

### 4.3 数据归档策略（2026-09-17）
- `runs/`（summary.csv、table.txt、log、ovf、case 脚本）**仅本地保留**；定稿图拷入 `docs/figures/` 统一归档，README/RESULTS/FACTS 引用同步更新。
