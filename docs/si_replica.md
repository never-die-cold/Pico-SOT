# SI 复刻对照：论文 Supplementary Information ↔ mumax3 实现

本文档记录 2026-09-16 起本仓库对 Jhuria et al., *Nature Electronics* **3**, 680–686 (2020)
补充材料（Supplementary Note 3 + Table S1）的逐项复刻方式，以及与旧版
（legacy，2026-09-15 之前）猜测参数的差异。SI 原文在本地
`notes/NE_2020SI/`（不入库）。

## 1. SI 模型 → mumax3 映射

| SI 项 | SI 公式/取值 | mumax3 实现 | 备注 |
|---|---|---|---|
| LLG | Eq. S1（Gilbert 形式） | 原生 LLG | 同构 |
| SOT–DL | θ<sub>DL</sub>·C<sub>s</sub>，C<sub>s</sub>=(μ<sub>B</sub>/q<sub>e</sub>)(J/d0)(1/Ms) | Slonczewski：`Pol=θ_DL, Lambda=1, EpsilonPrime=θ_FL, FixedLayer=σ, J 沿 z` | 内核 `slonczewski2.cu`：ε=Pol·λ²/((λ²+1)+(λ²−1)m·p)=Pol/2（λ=1），β=ħ/e·J/(t·Ms) → 有效因子 ≈ Pol/(1+α²)=θ<sub>DL</sub>；DL 速率与 θ<sub>DL</sub>·C<sub>s</sub> 数值一致（6×10¹²、Ms=1×10⁶ 时 SI 1.04×10¹¹ s⁻¹ vs mumax3 0.99×10¹¹ s⁻¹，差来自 1/(1+α²)） |
| SOT–FL | θ<sub>FL</sub>=0.05 | `EpsilonPrime=0.05` | 同上映射 |
| H<sub>eff</sub> | Eq. S3：H<sub>z</sub>=(2Kz/(μ0Ms)−Ms)m<sub>z</sub> | `Ku1 = Kz`（各向异性直接用 Kz）+ 薄膜退磁 | 注意：**不再**用 legacy 的 `Ku1=Keff+½μ0Ms²` |
| Ms(T) | Eq. S6：Ms(0)[1−(T/Tc)^1.7]，Ms(300 K)=1.0×10⁶ A/m（VSM） | 循环内 `Msat = Ms0*fr`，fr=1−(T/Tc)^1.7，Ms0=Ms300/fr300=1.23×10⁶ | T≥Tc 时 fr 截断为 0（Ms→0） |
| Kz(T) | Eq. S7：Kz(0)[Ms(T)/Ms(0)]³，Kz(300 K)=1×10⁶ J/m³（B<sub>K</sub>=0.8 T） | `Ku1 = Kz0*fr³`，Kz0=1.873×10⁶ | 形状项 −μ0Ms² 随 Ms 单独缩放；legacy 把总 Ku1 整体按 Ms³ 缩放，不等价 |
| Tc | 800 K | `Tc=800` | |
| α | 0.23（TR-MOKE 拟合，含非均匀展宽） | `alpha=0.23` | legacy 用 0.15 |
| 加热 | Eq. S4：C ∂T/∂t=Λ∂²T/∂x²+q，q=ρJ²；C=2.6×10⁶ J/m³K，Λ=9 W/mK（Wiedemann–Franz），上表面绝热，底面界面热导 G=170 MW/m²K | 0D 等效通道（见 §2） | legacy 用自由旋钮 dT<sub>ref</sub>=300–600 K、τ=100 ps |
| ρ | 81 µΩ·cm（四点法） | `rho_e=81e-8` | |
| 求解步长 | Δt=1 fs（SI） | `SetSolver(4)` + `FixDt=5e-14`（50 fs） | 宏自旋 40 ps 进动周期下 50 fs RK4 足够；未做 1 fs 收敛对照 |

## 2. 热模型：1D FD 精确解与 0D 等效通道

`heat_model.py` 按上表参数对 16 nm 叠层做隐式 Euler 一维有限差分（上绝热、
下 Robin J<sub>Q</sub>=G·T）。归一化 6 ps sech² 脉冲（J(t)=Jp·sech²，源 ∝ J²）下：

* **Jp=6×10¹² 时 Co 层峰值温升 +50.4 K**（Tmax≈350 K）——与 SI 自述口径一致
  （SI Note 3.2：6×10¹² 时平均峰值温升 ~60 K，其中电子–声子失配 ΔT<sub>ep</sub>~15 K 约占 25%）。
* 脉后衰减 τ≈245 ps（=C·d/G；50–400 ps 对数拟合 273 ps）。
* .mx3 内使用的 0D 等效通道 `dT/dt = ρJ²/C − T/τ`，τ=C·d/G=244.7 ps，
  与 FD 解的最大偏差 **5.1%**（0–450 ps 窗口）→ 单通道够用，不再引入双指数。
* Tmax(Jp) 是确定的：**Tmax ≈ 300 + 50.4·(Jp/6×10¹²)² K**（6 ps sech²）。
  legacy 相图里的 (Jp, Tmax) 二维自由度不再存在——温升只由 Jp 决定。

对照：legacy dT<sub>ref</sub>=300 K @6×10¹² → Tmax≈583 K，是 SI 物理值的 ~6 倍；
legacy 的"加热必要性"结论由此被放大（详见 RESULTS）。

## 3. legacy → SI 参数差异一览

| 量 | legacy（猜测） | SI（现行） |
|---|---|---|
| Ms(300 K) | 1.3×10⁶ A/m | **1.0×10⁶ A/m** |
| B<sub>K</sub>(300 K) | 1.0 T（主文口径） | **0.8 T**（Kz=1×10⁶ J/m³） |
| α | 0.15（fig3 用 0.1） | **0.23** |
| Ms(T) | ((Tc−T)/(Tc−T0))^0.34 | 1−(T/Tc)^1.7 |
| Ku(T) | 总 Ku1 ∝ Ms^3（含形状项） | Kz ∝ Ms³、形状项 ∝ Ms²（分开） |
| 加热幅值 | dT<sub>ref</sub>=300–600 K（旋钮） | FD 物理解（6×10¹²→+50 K） |
| tau<sub>cool</sub> | 100 ps（fig4 200 ps） | 245 ps（=C·d/G） |
| 热噪声 | 无（Temp 从未设置） | 默认仍无；`Noise=1` 时开 Langevin（Temp=T(t)） |

旧 runs 保留在 `runs/`（summary.csv 中 `model=legacy`），旧定稿图备份在
`runs/legacy/`。

## 4. 已知残余差异与注意事项

1. **脉冲波形未在 SI 给出**：SI 只说 6 ps 宽脉冲（实验电流迹线用 sech² 3.7 ps
   拟合）；本仓库沿用 sech² 6 ps。绝对阈值因此与 SI 有 ~1.5× 偏差
   （见 RESULTS §"阈值对比"），相对比例（加热/无加热、能量比 ~2×）与 SI 一致。
2. **θ<sub>DL</sub> 双口径**：主文/动力学拟合 0.2；SI Fig. 3–5 的强电流模拟用 0.3。
   本仓库两者都跑（`ThetaDL` 旋钮）。
3. **传输线反射**：fig4 用 `echo=0.3, ted=24 ps` 近似；开关型宏自旋扫描
   `echo=0`。SI 的开关模拟是否含反射未明说，可能是绝对阈值偏差来源之一。
4. **T≥Tc 的 Ms=0**：Jp≳1.9×10¹³（6 ps）时模型温升超过 Tc，Ms 截断为 0。
   该区间的翻转本质是 HAMR 型（论文实验已排除此情形），解读结果时注意。
5. **Langevin 噪声为固定种子**：重复 run 结果逐位相同，无法在 mumax3 内做
   P<sub>sw</sub>(Jp) 统计（需要改内核/外部驱动，见 ROADMAP）。
6. SI 的 Kz(300 K)=1×10⁶ J/m³ 与 B<sub>K</sub>=0.8 T 是 TR-MOKE 拟合值（glass 衬底样本
   G≈100 MW/m²K；开关器件为 sapphire，G=170 MW/m²K）。
