# 模型与数据说明（MODEL）

本文档**单列**回答"仿真用了什么模型、什么数据"。读完全篇即可独立理解本项目的
物理模型、数值方法、判定标准与数据产物，无需翻脚本。

| 想了解 | 去哪 |
|---|---|
| 模型总览（本文） | `docs/MODEL.md`（本文） |
| 论文公式 ↔ mumax3 实现逐项映射 | `docs/paper_replica.md` |
| 实验记录与结论 | `docs/RESULTS.md` |
| 参数速查 / 已核实事实 | `FACTS.md` |

复刻对象：Jhuria et al., *Nature Electronics* **3**, 680–686 (2020)
（皮秒电脉冲 SOT 翻转，Ta/Pt/Co/Cu/Ta/Pt 叠层）。

---

## 1. 模型一句话

**宏观自旋（单畴）LLG 方程 + Slonczewski 形式 SOT 力矩 + 0D 集总热通道**，
在 64×64（5 nm 胞元）伪宏自旋网格上用 mumax3.12（RK4 固定步长 50 fs）求解；
外加面内偏置场 Hx = 160 mT，6 ps sech² 电流脉冲，脉后自由弛豫 0.4–1.5 ns。

## 2. 磁动力学

### 2.1 LLG + SOT

$$
\frac{d\mathbf{m}}{dt} = -\gamma\, \mathbf{m}\times\mathbf{H}_{eff} + \alpha\, \mathbf{m}\times\frac{d\mathbf{m}}{dt}
+ \tau_{DL}\, \mathbf{m}\times(\mathbf{p}\times\mathbf{m})
+ \tau_{FL}\, \mathbf{m}\times\mathbf{p}
$$

* **SOT 接入方式**：mumax3 的 Slonczewski 模块等效。
  `Pol=θ_DL`、`Lambda=1`、`EpsilonPrime=θ_FL=0.05`、`FixedLayer=σ=(0,1,0)`（σ 沿 y）、
  电流 `J=(0,0,±Jp)` 沿 z。内核 `slonczewski2.cu` **只读 J 的 z 分量**——这是本项目
  踩过的最大的坑（见 notes/error.md）。
* **符号约定**：`I_sign=+1` 时 `J_z<0`，DL 力矩把 m 拉向 **−y**；末态极性满足
  `sign(m_z) = −sign(Hx·I)`（全器件四象限已验证，对应论文 Fig. 3）。
* **数值一致性**：DL 速率与论文 θ_DL·C_s 定义一致（6×10¹² A/m²、Ms=1×10⁶ 时
  论文 1.04×10¹¹ s⁻¹ vs mumax3 0.99×10¹¹ s⁻¹，差来自 1/(1+α²)）。
* Zhan-Li 力矩显式关闭（`DisableZhangLiTorque=true`，宏自旋无横向电流梯度）。

### 2.2 温度依赖的材料参数

统一约化因子 `fr(T) = 1 − (T/Tc)^1.7`（Tc=800 K，**截断 ≥0**，即 T≥Tc 时 Ms=0）：

| 量 | 律 | 300 K 值 | 外推零温值 |
|---|---|---|---|
| Msat | Ms0·fr | 1.0×10⁶ A/m（VSM） | Ms0 = 1.23×10⁶ A/m |
| Kz（PMA） | Kz0·fr³ | 1.0×10⁶ J/m³（B_K=0.8 T，TR-MOKE） | Kz0 = 1.87×10⁶ J/m³ |
| α | 常数 | 0.23（TR-MOKE 拟合，含非均匀展宽） | — |

**关键实现约定**：`Ku1 = Kz(T)` **直接赋值**（不是 `Keff+½μ0Ms²`），配合 mumax3
薄膜退磁恰好实现论文 Eq. S3 的 H_z = (2Kz/μ0Ms − Ms)·m_z，且温度标度分解不被
破坏。自检：relax 后 m_z = cos(atan(Hx/B_K)) = 0.981 ✔。

**本模型里温度如何影响开关（理解异常回翻的钥匙）**：

| 通道 | 标度 | 效果 |
|---|---|---|
| Kz(T)↓ | fr³ | 各向异性势阱消失，H_k(T)=B_K·fr² 随温度快速下降 |
| Msat(T)↓ | fr | Slonczewski 力矩 ∝ J/Ms 被热放大（T=610 K 时 ×2.7） |
| 两者都通过降温恢复 | — | 势阱在降温中"重新出现"，捕获点决定末态极性 |

### 2.3 热通道（0D 集总）

论文 Eq. S4 为 1D 热扩散 C∂T/∂t = Λ∂²T/∂x² + ρJ²（C=2.6×10⁶ J/m³K，
Λ=9 W/mK，上表面绝热，底面界面热导 G=170 MW/m²K，叠层 16 nm）。
本项目降维成单节点 ODE：

$$
\frac{dT_{dev}}{dt} = \frac{\rho_e J^2(t)}{C} - \frac{T_{dev}}{\tau},\qquad
\tau = \frac{C\,d}{G} = 244.7\ \text{ps},\quad \rho_e = 81\ \mu\Omega\cdot\text{cm}
$$

与 `heat_model.py` 的一维隐式 Euler 有限差分解最大偏差 **5.1%**（0–450 ps）。
6 ps sech² 脉冲下峰值温升只由 Jp 决定：**Tmax ≈ 300 + 50.4·(Jp/6×10¹²)² K**
（Jp=6×10¹² → Tmax≈350 K，与论文自述 ~60 K 口径一致）。

### 2.4 外场与脉冲

* **Hx = 160 mT（沿 +x）**：唯一的 ±z 对称破缺来源。Hx=0 时任何电流都不翻
  （宏自旋 + 全器件均验证）；Hx 也是脉后捕获相位的"进动轴"（见 anomaly.md）。
* **脉冲**：sech²(1.763·(t−t0)/tp)，FWHM=tp=6 ps，中心 t0=4tp=24 ps，
  电流窗口 8tp=48 ps。论文未给波形 → 绝对阈值偏高 ~1.5×，相对比值与论文一致。
* **噪声**：`Noise=1` 时循环内 `Temp=T(t)`（Langevin）。mumax3.12 噪声 RNG 固定
  种子（`RandSeed()` 不影响噪声路径，已实测）→ 系综统计用 **FixDt 微抖动**
  （±4–6%，收敛步长内不改变确定性物理，但改变噪声采样路径）生成独立样本。

### 2.5 数值设置

| 项 | 值 | 说明 |
|---|---|---|
| 求解器 | `SetSolver(4)` 经典 RK4 | 自适应求解器会把 ps 脉冲步长拉爆（error.md §3） |
| 步长 | `FixDt=5e-14`（50 fs） | 40 ps 进动周期下足够；25 fs 对照无差异 |
| 网格 | 64×64×1，cell 5×5×1 nm | 伪宏自旋；√(A/Kz)≈5 nm 为分辨极限（见 §6 多畴） |
| 表格输出 | 每 0.1 ps | t, mx, my, mz, E_total, J, T |
| 温度 ODE 积分 | 每步解析更新 | dT/dt 用实测经过时间（非假设步长） |
| 环路步长 | 脉冲段 `stp`=0.2 ps，自由演化段 `dtrun`=10 ps | T/Ms/Kz 每步更新一次 → 表格里的 T 是零阶保持（阶梯）；节点值本身是解析解的采样点（τ 拟合 244.7 ps vs 解析 245 ps），绘图用 `figstyle.destair` 在表格时间栅格上重采样还原曲线 |

## 3. 判定标准与观测量（summary.csv 列）

| 列 | 定义 |
|---|---|
| `mz_final` | 最后一个表格行的平均 m_z |
| `switched` | `InitMz·mz_final < −0.5`（相对初态翻转到反侧） |
| `Tmax_K` | 全程温度峰值（由 Jp 确定，见 §2.3） |
| `t_cross_ps` | **首次**过零时间——注意"过零又弹回"也会记录（异常窗口的正确解读见 anomaly.md） |
| `recov_50ps` | 过零 50 ps 后的 \|m_z\| / 末态 \|m_z\|（回弹程度的粗指标） |
| 多畴剔除 | `m_final.ovf` 的 \|⟨m⟩\| < 0.9 → 判该点为条带多畴伪影，**不作为宏自旋结论、也不绘制**（折线直接连接相邻实测点；剔除清单见 FACTS §8.6） |

## 4. 数据产物与命名规则

```
simulations/mumax3_sot/
├─ runs/summary.csv          全部 case 一行一条（run_case.py 自动追加）
├─ runs/<tag>/<tag>.mx3      实际运行的脚本副本（参数替换后）
├─ runs/<tag>/out/table.txt  时间序列（0.1 ps 采样）
├─ runs/<tag>/out/m_final.ovf 末态磁矩分布（多畴判据来源）
└─ *.json                    run_batch.py 的批量计划（ablation/sweep/noise）
```

**tag 命名规则**：

| 前缀/后缀 | 含义 | 例 |
|---|---|---|
| `si_{h,noh}_t{20,30}_Jp{N}` | 主系列：加热/不加热 × θ_DL=0.2/0.3 × Jp（10¹² A/m²） | `si_h_t20_Jp14` |
| `Jp{n}p5` | 半步长点（0.5×10¹²） | `si_h_t20_Jp15p5` |
| `_lr1500` | 长弛豫重跑（t_free=1.5 ns，T 回 ~300 K），边界点以此为准 | `si_h_t20_Jp14_lr1500` |
| `_dt25` / `ab_dt*` | 步长减半/微抖动对照 | `si_h_t20_Jp16_lr1500_dt25` |
| `ab_*` | 异常归因消融：`ab_hx{mT}_Jp{N}`（改 Hx）、`ab_G{...}`（改 G_int）、`ab_Tc{K}_Jp{N}`（改 Tc） | `ab_hx040_Jp15` |
| `ns_*_r{n}` | 噪声系综（Noise=1 + FixDt 抖动第 n 个独立样本） | `ns_h_t20_Jp15_r3` |
| `si_q1..q4` | 全器件四象限；`si_a_f4_*` Fig.4 动力学 | — |
| `si_Kzfr_*` / `si_Msfr_*` | 机制分解：冻结 Kz(T) / 冻结 Ms(T) | — |

**复现单个 case**：
`python run_case.py macrospin_switch.mx3 si_h_t20_Jp8 --set Jp=8e12 Heating=1`
**批量复现**：`python run_batch.py ablation_plan.json`（可续跑，跳过已存在 tag）

## 5. 模型有效域与局限

1. **宏自旋有效性**：网格均匀、无缺陷、无晶粒随机性 → 结果代表理想单畴；
   近阈值/极强电流会出现条带多畴伪影（判据 §3，已确认点见 FACTS §8.6）。
2. **T≥Tc 区间**（Jp≳19×10¹²，6 ps）：Ms 截断为 0，本质是 HAMR 型翻转，
   论文实验已排除该情形，解读需谨慎。
3. **绝对阈值**偏高 ~1.5×（脉冲波形/反射口径未知），相对比值（加热/无加热
   阈值比、能量比）与论文一致。
4. **噪声统计**：FixDt 抖动系综（§2.4）为 mumax3 固定种子限制下的等价替代，
   独立性已由确定性对照（抖动不改变结果）验证。
5. Aex=3×10⁻¹¹ J/m 为典型值（论文未给 A），未做系统敏感性扫描。
6. **自由演化段的 10 ps 温度台阶**（§2.5）：该段 Ms(T)、Kz(T) 也随 T 一起
   每 10 ps 才更新一次，所以期间势阱深度被量化到 10 ps。异常窗口的判据
   （末次过零时 Hₖ≈1.1 Hₓ）不受影响，但由曲线读出的 T\*(Hₓ) 穿越时刻只有
   10 ps 量级的分辨率；需要更细的时间分辨时应把 `dtrun` 调小重跑。
