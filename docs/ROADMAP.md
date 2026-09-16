# PicoSOT 完善计划（ROADMAP）

本文件记录仓库的待办与改进方向，按主题分组、按优先级排序。
勾选表示已完成；每条尽量给出**验收标准**与涉及文件，便于直接照着做。

**优先级**：`P0` 必做（影响科研结论或复现完整性）｜`P1` 重要｜`P2` 锦上添花｜`P3` 可选
**成本**：`S` ≤ 1 小时｜`M` ≤ 1 天｜`L` > 1 天

## 最近完成（2026-09）

- [x] 双许可：代码 MIT（`LICENSE`）+ 文档 CC BY 4.0（`LICENSE-docs`）
- [x] README 英文主版 + 中文版（`README.md` / `README.zh-CN.md`），含结果图
- [x] 完整实验记录 `docs/RESULTS.md`、引用元数据 `CITATION.cff`、`requirements.txt`、`papers/README.md`
- [x] `run_case.py`：`MUMAX3_BIN` 环境变量；`switched` 判定改为基于初态符号（`mz*mz0 < -0.5`）
- [x] 结果一致性修正（反平行组无正上冲、t=0 伪影、弛豫基准）
- [x] GitHub About：description + 9 个 topics
- [x] **SI 参数复刻（2026-09-16）**：三个 .mx3 模板改为 SI Note 3/Table S1 参数与
      温度律；加热改为 SI 热扩散 0D 等效通道（`heat_model.py`，6×10¹²→+50.4 K、τ=245 ps、
      FD 偏差 5.1%）；`run_case.py` 加 `model` 列；纯 SOT/加热阈值、机制分解
      （ScaleKz/ScaleMs/θ≈0/Hx=0/噪声）、脉宽窗口、全器件四象限与器件阈值、
      定稿图全量刷新；旧结果标 `model=legacy`、旧图备份 `runs/legacy/`；
      新增 `docs/si_replica.md`。

---

## R. 发布与追溯

- [ ] **R1（P1, M）发布 v1.0.0**
  - 打 tag + Release notes（摘要已验证结果与已知局限）
  - 验收：GitHub Releases 出现 v1.0.0；README 徽章区可加 release 徽章
- [ ] **R2（P1, M）Zenodo 归档 + DOI**
  - 开启 Zenodo-GitHub 集成，新增 `.zenodo.json`；把 DOI、`version`、`date-released` 写回 `CITATION.cff`
  - 验收：`CITATION.cff` 含 DOI；GitHub "Cite this repository" 显示版本号
- [ ] **R3（P1, S）`summary.csv` 增加 provenance 列**
  - 每个 run 自动记录：mumax3 版本、`git rev-parse HEAD`、GPU 名称、模板脚本 sha256、run_case 版本
  - 涉及：`simulations/mumax3_sot/run_case.py`
  - 验收：新 run 的 CSV 行含以上字段；旧行留空不报错
- [ ] **R4（P2, S）社交预览图**
  - 上传 `simulations/mumax3_sot/runs/phase_map.png`（Settings → Social preview）
  - 验收：仓库链接卡片显示相图

## T. 可复现性与工具

- [ ] **T1（P1, M）一键重建定稿图 `run_all.py`**
  - 从 `runs/summary.csv` 依次调用 `plot_phase` / `plot_fig4` / `plot_mechanism` / `plot_quadrants` 等
  - 验收：删掉 `runs/*.png` 后一条命令恢复全部定稿图
- [ ] **T2（P1, S）`run_case.py` 增强**
  - 跑前 `mumax3 -vet` 预检语法；stdout/stderr 落盘到 `runs/<tag>/`；加 `--dry-run`
  - 验收：失败的 case 保留日志现场；`--dry-run` 只写脚本不调用 mumax3
- [ ] **T3（P1, M）测试与 CI**
  - `pytest`（`substitute` 正则、`read_table` 边界：NaN/部分翻转/首行伪影）+ `ruff`
  - GitHub Actions：ruff + pytest + CITATION 校验（`cffconvert`）；用 fake mumax3 stub 跑通 pipeline smoke test（runner 无 GPU，真实仿真不跑）
  - 验收：Actions 全绿；新增 PR 自动跑测试
- [ ] **T4（P2, S）依赖版本固定**
  - 在 `requirements.txt` 标注已验证版本（Python 3.12.10 / numpy 2.5.1 / matplotlib 3.11.0）
  - 验收：按冻结版本可复现全部后处理图
- [ ] **T5（P2, S）环境信息去个人化**
  - README/FACTS 中的绝对路径、GUI 端口等只保留示例；确认 `--help` 与文档一致
  - 验收：换机器按 README 可直接跑通

## P. 物理与验证

- [ ] **P1（P0, L）概率翻转统计 `P_sw(Jp)`**
  - 1024×800（5×4 µm 过流区）+ Voronoi 晶粒各向异性扰动 + 热噪声（sLLG），多随机种子统计
  - 前置：mumax3 的 Langevin 噪声为固定种子（重复 run 逐位相同），需给 mumax3 打
    补丁/外部驱动注入种子，或改用自写 sLLG
  - 对标论文 >91% 翻转概率与成核图像
  - 验收：`P_sw(Jp)` 曲线 + 与论文对比图
- [x] **P2（P1, M）热模型标定与敏感性**（2026-09-16 完成）
  - 已按 SI Eq. S4–S5 实现：C=2.6×10⁶、Λ=9 W/mK、G=170 MW/m²K、q=ρJ²；
    `heat_model.py` 1D FD 标定，.mx3 内 0D 通道偏差 5.1%（`runs/heat_model.png`）
  - 剩余敏感性（移入 P8）：G<sub>int</sub>（100 vs 170 MW/m²K，glass/sapphire）、
    C/Λ 不确定度对 Tmax 与阈值的影响
- [ ] **P3（P1, M）收敛性与敏感性**
  - 网格 5 nm vs 2.5 nm、`Aex`（SI 未给，现取 3×10⁻¹¹）、`alpha`（宏自旋下已扫 0.05–0.30，
    阈值不敏感；全器件未扫）、宏自旋 vs 全器件；FixDt 5×10⁻¹⁴ vs 1×10⁻¹⁴ 高温收敛性
  - 验收：对照表 + 结论不变的说明
- [ ] **P4（P1, M）脉宽扫描：速度–能量权衡**
  - 已有 θ=0.2/无加热 @10×10¹² 的窗口（12 ps 不翻、15 ps 起翻）；待补加热下
    6→30 ps 扫描与延迟/能量曲线，对照论文 Fig. 4d 与 SI Fig. 3
  - 验收：`runs/` 新定稿图 + README/RESULTS 更新
- [x] **P5（P2, S）SOT 等效性推导文档**（2026-09-16，并入 `docs/si_replica.md`）
  - 已给出 Slonczewski 内核（ε=Pol/2、β=ħ/e）与 SI 的 θ<sub>DL</sub>·C<sub>s</sub> 的数值换算
    （有效因子 ≈Pol/(1+α²)=θ<sub>DL</sub>），含 DL 速率数值对照
- [ ] **P6（P2, L）更真实物理（可选）**
  - Oersted 场、DMI、传输线反射系数标定（SI Fig. 4a/b 的 echo 序列）；远期给
    mumax3 打补丁实现原生 SOT
  - 验收：至少一版含 Oersted 场的对照运行与结论
- [ ] **P7（P2, S）`Jc(Hx) ∝ 1/Hx` 定性验证**
  - 固定 SI 热通道，扫描 Hx 找阈值，验证幂律趋势
  - 验收：`Jc(Hx)` 图 + 数据表
- [ ] **P8（P1, S）脉冲波形/反射标定**
  - 绝对阈值比 SI 高 ~1.5×；扫描波形（sech² vs 高斯 vs 方波）与 echo 序列
    （幅值/延迟），估计对 Jc 的影响区间，写回 `docs/si_replica.md` §4
  - 验收：波形-阈值对照表

## D. 文档与传播

- [ ] **D1（P1, M）英文踩坑笔记 `docs/pitfalls.md`**
  - 以 `notes/error.md` 为基础摘译（重点 §1.11 脉冲拉长、Ku1 单位坑、SOT 的 J 分量坑）
  - 验收：英文读者可独立避开三大坑；README 链接该文档
- [ ] **D2（P2, M）Notebook 教程**
  - 读取仓库内现成 `table.txt`（无需 GPU）演示 ΔMz/ΔT/相图/能量
  - 验收：`docs/tutorial.ipynb` 可直接在 Colab 运行
- [ ] **D3（P2, M）技术报告 / 博客 + Zenodo 存档**
  - 整理为可引用的技术报告（中/英），覆盖方法、坑、已验证结果与局限
  - 验收：Zenodo 条目 + DOI，README §8 链接
- [ ] **D4（P2, S）硬件与实测耗时表**
  - RTX 5060 Laptop 8 GB / RTX 4070S 的宏自旋与全器件运行时间、显存占用
  - 验收：README 环境的表格化补充
- [ ] **D5（P3, S）图件统一与英文标注**
  - 定稿图统一字号/配色；如需国际读者，出英文标注版本
  - 验收：`plot_*.py` 可切换 `LANG=en/zh`

## H. 杂项

- [ ] **H1（P2, S）本地仓库压缩**
  - 本地 `.git` 有 ~110 MB 松散对象：`git gc --aggressive --prune=now`
  - 验收：`git count-objects -vH` 体积明显下降
- [ ] **H2（P2, S）备份策略**
  - 仓库 + `papers/` PDF + `runs/` 原始产物的异地备份（网盘/移动硬盘），定期执行
  - 验收：形成书面清单与周期
- [ ] **H3（P3, M）中间产物归档**
  - OVF/table 等可再生大文件打包到 Release/Zenodo，仓库只保留定稿与摘要
  - 验收：仓库体积可控且归档可下载

---

*如需调整优先级或新增条目，直接编辑本文件即可；完成后把 `[ ]` 改为 `[x]` 并注明日期。*
