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
  - 对标论文 >91% 翻转概率与成核图像
  - 验收：`P_sw(Jp)` 曲线 + 与论文对比图；README 路线图第 5 条可标记完成
- [ ] **P2（P1, M）热模型标定与敏感性**
  - 扫描 `tau_cool` / `Tc` / `beta_cc` / `dT_ref`，对齐「低电流退磁 1–2%、脉冲后恢复 ~300–400 ps」
  - 验收：标定参数表 + 敏感性热图；给出推荐默认值
- [ ] **P3（P1, M）收敛性与敏感性**
  - 网格 5 nm vs 2.5 nm、`Aex`、`alpha`、宏自旋 vs 全器件；确认结论不依赖离散化/材料猜测
  - 验收：对照表 + 结论不变的说明
- [ ] **P4（P1, M）脉宽扫描：速度–能量权衡**
  - 6→30 ps 扫描，画延迟/能量曲线，对照论文 Fig. 4d
  - 验收：`runs/` 新定稿图 + README/RESULTS 更新
- [ ] **P5（P2, S）SOT 等效性推导文档 `docs/sot_emulation.md`**
  - 说明 Slonczewski 模块 + `Lambda=1`/`Pol=θ_DL`/`EpsilonPrime=θ_FL` 与标准 DL/FL 力矩的等效条件（`eps=Pol/2`）及适用范围
  - 验收：公式推导 + 与现有一致性自检数值对照
- [ ] **P6（P2, L）更真实物理（可选）**
  - Oersted 场、DMI、传输线反射系数标定；远期可给 mumax3 打补丁实现原生 SOT
  - 验收：至少一版含 Oersted 场的对照运行与结论
- [ ] **P7（P2, S）`Jc(Hx) ∝ 1/Hx` 定性验证**
  - 固定 `dT_ref`，扫描 `Hx` 找阈值，验证幂律趋势
  - 验收：`Jc(Hx)` 图 + 数据表

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
