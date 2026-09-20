"""Build the 13-page PicoSOT group-meeting deck as a .pptx.

Audience: research-group advisor (domain expert, has NOT read this paper in detail).  The deck therefore keeps
full technical notation, but spells out paper-specific context (what the
paper contains)
and avoids internal jargon in the main pages.

Layout is deliberately plain: black text on white, one thin rule under each
title, no rounded cards, no coloured banners, no footer slogan.  Figures and
tables carry the visual weight; the page number is the only decoration.

Usage:
    python slides/build_ppt.py
Output:
    slides/PicoSOT_组会汇报.pptx
"""
import os
import re
import sys

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(os.path.dirname(HERE), "simulations", "mumax3_sot", "runs")
ASSETS = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "PicoSOT_组会汇报.pptx")
if len(sys.argv) > 1:          # optional output override (e.g. while the
    OUT = sys.argv[1]          # main file is open/locked in PowerPoint/WPS)

FONT = "Microsoft YaHei"
MONO = "Consolas"

TEXT = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x55, 0x55, 0x55)
FAINT = RGBColor(0x8A, 0x8A, 0x8A)
RULE = RGBColor(0xBB, 0xBB, 0xBB)
CODEBG = RGBColor(0xF4, 0xF4, 0xF4)
CODELINE = RGBColor(0xCF, 0xCF, 0xCF)
HDRBG = RGBColor(0xE8, 0xE8, 0xE8)
ROWBG = RGBColor(0xF7, 0xF7, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def _font(run, size=16, bold=False, color=TEXT, name=FONT, italic=False):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = color
    f.name = name
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", name)


_SUPSUB = re.compile(r"~sub\{([^}]*)\}|~sup\{([^}]*)\}")


def _runs(p, text, size, bold, color, name=FONT, italic=False):
    """Add runs to paragraph p; ~sub{..} / ~sup{..} become real sub/superscript."""
    pos = 0
    for m in _SUPSUB.finditer(text):
        if m.start() > pos:
            r = p.add_run()
            r.text = text[pos:m.start()]
            _font(r, size=size, bold=bold, color=color, name=name, italic=italic)
        r = p.add_run()
        r.text = m.group(1) if m.group(1) is not None else m.group(2)
        _font(r, size=size, bold=bold, color=color, name=name, italic=italic)
        r._r.get_or_add_rPr().set("baseline",
                                  "-25000" if m.group(1) is not None else "30000")
        pos = m.end()
    if pos < len(text) or pos == 0:
        r = p.add_run()
        r.text = text[pos:]
        _font(r, size=size, bold=bold, color=color, name=name, italic=italic)


def textbox(slide, x, y, w, h, items, anchor=MSO_ANCHOR.TOP,
            align=PP_ALIGN.LEFT, wrap=True):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    first = True
    for it in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = it.get("align", align)
        p.line_spacing = it.get("line_spacing", 1.02)
        p.space_after = Pt(it.get("space_after", 4))
        p.space_before = Pt(it.get("space_before", 0))
        _runs(p, it["text"], size=it.get("size", 16), bold=it.get("bold", False),
              color=it.get("color", TEXT), name=it.get("name", FONT),
              italic=it.get("italic", False))
    return tb


def bullets(lines, size=15, color=TEXT, gap=6):
    items = []
    for ln in lines:
        items.append({"text": "•  " + ln, "size": size, "color": color,
                      "space_after": gap})
    return items


def rule(slide, x, y, w):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                 Inches(w), Inches(0.014))
    bar.fill.solid()
    bar.fill.fore_color.rgb = RULE
    bar.line.fill.background()
    bar.shadow.inherit = False
    return bar


def page_num(slide, idx):
    textbox(slide, 12.35, 7.06, 0.55, 0.28,
            [{"text": str(idx), "size": 10, "color": FAINT,
              "align": PP_ALIGN.RIGHT}])


def title(slide, text, idx):
    textbox(slide, 0.55, 0.26, 12.2, 0.55,
            [{"text": text, "size": 23, "bold": True, "color": TEXT}])
    rule(slide, 0.57, 0.87, 12.2)
    page_num(slide, idx)


def keyline(slide, x, y, w, h, text, size=13):
    """Standalone bold takeaway, no box, no colour."""
    return textbox(slide, x, y, w, h,
                   [{"text": text, "size": size, "bold": True, "color": TEXT,
                     "line_spacing": 1.10}])


def block(slide, x, y, w, h, head, lines, head_size=14, body_size=12):
    items = [{"text": head, "size": head_size, "bold": True, "color": TEXT,
              "space_after": 6}]
    for ln in lines:
        items.append({"text": ln, "size": body_size, "color": GRAY,
                      "space_after": 4})
    return textbox(slide, x, y, w, h, items)


def picture(slide, path, x, y, w, h):
    if not os.path.isfile(path):
        print("WARNING missing figure:", path)
        return None
    iw, ih = Image.open(path).size
    ar = iw / float(ih)
    if w / h > ar:
        ph = h
        pw = h * ar
    else:
        pw = w
        ph = w / ar
    return slide.shapes.add_picture(path, Inches(x + (w - pw) / 2.0),
                                    Inches(y + (h - ph) / 2.0),
                                    Inches(pw), Inches(ph))


def codebox(slide, x, y, w, h, code, size=11):
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                 Inches(w), Inches(h))
    box.fill.solid()
    box.fill.fore_color.rgb = CODEBG
    box.line.color.rgb = CODELINE
    box.line.width = Pt(0.75)
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = Inches(0.14)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.12)
    tf.margin_bottom = Inches(0.06)
    for i, line in enumerate(code.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(0)
        p.line_spacing = 1.0
        r = p.add_run()
        r.text = line if line else " "
        _font(r, size=size, color=RGBColor(0x26, 0x26, 0x26), name=MONO)
    return box


def table(slide, x, y, w, data, col_w=None, font_size=11, row_h=0.34,
          header=True):
    rows, cols = len(data), len(data[0])
    gf = slide.shapes.add_table(rows, cols, Inches(x), Inches(y),
                                Inches(w), Inches(row_h * rows))
    tbl = gf.table
    if col_w:
        total = float(sum(col_w))
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = Inches(w * cw / total)
    for ri, row in enumerate(data):
        tbl.rows[ri].height = Inches(row_h)
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.04)
            cell.margin_top = Inches(0.015)
            cell.margin_bottom = Inches(0.015)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            cell.fill.solid()
            if header and ri == 0:
                cell.fill.fore_color.rgb = HDRBG
                _runs(p, str(val), size=font_size, bold=True, color=TEXT)
            else:
                cell.fill.fore_color.rgb = WHITE if ri % 2 else ROWBG
                _runs(p, str(val), size=font_size, bold=False, color=TEXT)
    return tbl


def notes(slide, text):
    tf = slide.notes_slide.notes_text_frame
    lines = text.strip().split("\n")
    first = True
    for ln in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        _runs(p, ln, size=12, bold=False, color=TEXT)


def add_blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # ------------------------------------------------------------------ P1
    s = add_blank(prs)
    textbox(s, 0.8, 0.85, 11.8, 0.9,
            [{"text": "皮秒电流脉冲 SOT 翻转的 mumax3 复现", "size": 32,
              "bold": True, "color": TEXT, "align": PP_ALIGN.LEFT}])
    textbox(s, 0.8, 1.66, 11.8, 0.45,
            [{"text": "参数取自论文",
              "size": 16, "color": GRAY}])
    textbox(s, 0.8, 2.14, 8.0, 0.4,
            [{"text": "汇报人：______          日期：______", "size": 12,
              "color": FAINT}])
    textbox(s, 0.8, 2.62, 7.6, 2.6, bullets([
        "体系：Ta(5)/Pt(4)/Co(1)/Cu(1)/Ta(4)/Pt(1) nm，Co 是垂直磁化层，过流区 5×4 µm²",
        "论文结论：单个 6 ps 脉冲即可确定性翻转；J~sub{c} 上限 6×10~sup{12} A/m² 出自 50 pJ 能量预算；"
        "转向由 H~sub{x} 与电流的乘积符号决定",
        "模型：宏观自旋 LLG + SOT + 热扩散的 0D 等效通道，参数全部取自论文",
        "数据量：约 130 个 mumax3 run（64×64 宏自旋 + 500×400 全器件）",
    ], size=13, gap=11))
    picture(s, os.path.join(ASSETS, "device_stack.png"), 8.35, 2.55, 4.55, 2.9)
    keyline(s, 0.8, 5.85, 12.0, 1.0,
            "先说结论：不带任何温度依赖时，纯 SOT 阈值 20×10~sup{12} A/m²；加上论文的热通道后降到 10×10~sup{12}，"
            "大致减半，比例和论文里的 9×10~sup{12} 到 6×10~sup{12} 一致。K~sub{z} 随温度塌缩绕不过去，"
            "而绝对阈值比论文高约 1.5 倍，最可能的原因是论文没公开脉冲波形和反射序列。",
            size=13.5)
    notes(s, """老师好。这次汇报的是 Jhuria 那篇 NE 2020，皮秒脉冲翻转垂直磁化。这次的参数和模型完全取自论文：宏观自旋参数和热扩散模型都是论文里的数据。数据量约 130 个 run，64×64 的宏自旋和 5×4 微米的全器件都有。先说结论：纯 SOT、不加任何温度依赖，阈值在 20×10~sup{12}；把论文的热通道加进来降到 10×10~sup{12}，大致减半，这个比例和论文里的 9 掉到 6 是一致的。K~sub{z} 随温度塌缩是必要条件。绝对值比论文高出 1.5 倍左右，我倾向于认为问题出在论文没给脉冲波形和反射序列。下面先看论文里到底给了什么，再讲实现和结果。""")

    # ------------------------------------------------------------------ P2
    s = add_blank(prs)
    title(s, "论文里有哪些可用信息", 2)
    table(s, 0.55, 1.16, 7.7, [
        ["项目", "论文内容"],
        ["器件", "Ta(5)/Pt(4)/Co(1)/Cu(1)/Ta(4)/Pt(1) nm，Co 为 PMA 层"],
        ["脉冲", "翻转 6 ps；时域实验 3.7 ps；含传输线反射"],
        ["实验结论", "单个 6 ps 脉冲确定性翻转；方向 = −sign(H~sub{x}·I)（Fig.3）"],
        ["电流口径", "J~sub{c} ≈ 6×10~sup{12} A/m² 为能量上限估计（<50 pJ，Methods）"],
        ["模型", "宏观自旋 LLG + SOT + 1D 热扩散；θ~sub{DL}=0.2（强电流模拟用 0.3）、θ~sub{FL}=0.05"],
        ["参数", "M~sub{s}(300K)=1.0×10~sup{6} A/m、B~sub{K}=0.8 T、α=0.23、T~sub{c}=800 K、C=2.6×10~sup{6}、Λ=9 W/mK、G=170 MW/m²K"],
        ["论文预测", "纯 LLG J~sub{c}≈9×10~sup{12} A/m²；含热 ≈6×10~sup{12}（能量 ~2×）；最快 16 ps；θ=0 也能翻（Fig.5）"],
    ], col_w=[1.2, 6.9], font_size=10.5, row_h=0.54)
    picture(s, os.path.join(ASSETS, "device_stack.png"), 8.45, 1.16, 4.35, 2.9)
    textbox(s, 0.55, 5.85, 12.25, 1.0, bullets([
        "正文只给了一小部分参数（Ha≈1 T、θ~sub{DL}/θ~sub{FL}、J~sub{c} 上限）；完整模型和热学参数都在论文里，"
        "本工作全部以论文参数与模型为准",
        "要回答四件事：极性对不对、Fig.4 的动力学对不对、阈值里加热占多少、翻转靠哪些机制",
    ], size=12, gap=6))
    notes(s, """这一页把论文里给的信息整理出来，方便后面对照。器件是 Ta/Pt/Co/Cu/Ta/Pt，Co 是垂直磁化层。翻转实验用 6 ps 脉冲，时域测量用 3.7 ps，都带传输线反射。实验的结论有两条：单个 6 ps 脉冲能确定性翻转；方向由 H~sub{x} 和电流乘积的符号决定。注意论文那个 6×10~sup{12} 不是测出来的阈值，是从 50 pJ 能量预算反推的上限。真正的模型在论文里都有：宏观自旋 LLG 加 SOT，再配一维热扩散。θ~sub{DL} 拟合是 0.2，强电流模拟用的是 0.3；M~sub{s}、各向异性、阻尼、居里温度、热容、热导、界面热导这些参数论文都给了。论文自己也有预测：纯 LLG 阈值 9×10~sup{12}，含热 6×10~sup{12}，能量差两倍左右，最快 16 ps，把 SOT 关掉只靠热各向异性力矩也能翻。我们逐条去验。""")

    # ------------------------------------------------------------------ P3
    s = add_blank(prs)
    title(s, "把论文方程搬进 mumax3", 3)
    codebox(s, 0.55, 1.14, 7.55, 3.95, """// SOT：Slonczewski 模块等效（mumax3 无原生 SOT）
FixedLayer   = vector(0, 1, 0)   // σ 沿 y
Pol          = 0.20              // θ_DL（强电流模拟用 0.30）
EpsilonPrime = 0.05              // θ_FL
Lambda       = 1
DisableZhangLiTorque = true
J = vector(0, 0, -I_sign*Jp*sech²)  // 内核只读 J.z

// 各向异性：直接令 Ku1 = Kz(T)
//   H_z = (2Kz/μ0Ms - Ms) m_z 与论文 Eq.S3 一致
// 温标：fr = 1-(T/Tc)^1.7
//   Msat = Ms0*fr;  Ku1 = Kz0*fr^3   （对应论文 Eq.S6-S7）

// 加热：dT/dt = rho*J^2/C - (T-Troom)/tau
//   tau = C*d/G = 245 ps（论文 Eq.S4 的 0D 等效通道）

// 时间精确：RK4 + 固定步长
SetSolver(4);  FixDt = 5e-14     // 0.05 ps""")
    textbox(s, 0.55, 5.28, 7.55, 1.5,
            [{"text": "两处容易踩的地方", "size": 12, "bold": True,
              "color": TEXT, "space_after": 5},
             {"text": "Ku1 直接取 K~sub{z}，不走 Keff+½μ0Ms² 的老写法，这样 M~sub{s} 和 K~sub{z} 的温度标度"
                      "在机制分解时互不牵连。",
               "size": 11, "color": GRAY, "space_after": 4},
             {"text": "J 必须沿 z 写：内核只读 J.z，写成 x 分量转矩恒为零，而且不报错。",
               "size": 11, "color": GRAY}])
    textbox(s, 8.25, 1.20, 4.55, 5.4, bullets([
        "SOT 效率按内核源码核对过：Pol=θ~sub{DL}、Λ=1 时 ε=Pol/2，与论文的 θ~sub{DL}·C~sub{s} 数值一致"
        "（差 1/(1+α²)≈0.95）",
        "令 Ku1=K~sub{z} 后，relax 平衡态 m~sub{z}=0.981，等于 cos[atan(H~sub{x}/B~sub{K})]",
        "加热用 0D 等效通道，与 1D 有限差分解最大偏差 5.1%（0–450 ps）",
        "可调旋钮：tp_ps、ThetaDL、Heating、ScaleMs、ScaleKz、Noise",
    ], size=12, gap=13))
    notes(s, """实现说三点。SOT 这块，mumax3 没有原生项，用 Slonczewski 模块等效，固定层极化沿 y，Pol 和 EpsilonPrime 填 θ~sub{DL} 和 θ~sub{FL}。有个坑：内核只读电流的 z 分量，所以 J 必须沿 z 写，写成 x 分量转矩恒为零，而且不报错。效率我们对着内核源码核过，ε=Pol/2 再乘 ħ/e，合起来正好是有效 θ~sub{DL} 除以 1+α²，和论文的 θ~sub{DL}·C~sub{s} 差 0.95，就是 Gilbert 形式带来的。各向异性这次直接令 Ku1 等于论文的 K~sub{z}，mumax3 的薄膜退磁场加上各向异性场恰好等于论文的 2Kz/μ0Ms 减 M~sub{s}；relax 后 m~sub{z} 是 0.981，跟解析值 cos(atan(H~sub{x}/B~sub{K})) 对得上。热模型论文用的是一维热扩散，我们在脚本里做等效的零维通道，系数照论文取，和一维有限差分最大差 5.1%。""")

    # ------------------------------------------------------------------ P4
    s = add_blank(prs)
    title(s, "加热模型：热扩散与 0D 等效", 4)
    picture(s, os.path.join(RUNS, "heat_model.png"), 0.55, 1.05, 12.25, 4.35)
    textbox(s, 0.55, 5.45, 12.25, 1.5, bullets([
        "按论文的热扩散方程解 1D 热扩散：C=2.6×10~sup{6} J/m³K、Λ=9 W/mK（Wiedemann–Franz）、"
        "G=170 MW/m²K、q=ρJ²、上表面绝热",
        "6×10~sup{12} A/m² / 6 ps 时 Co 层峰值升温 +50.4 K（论文自述约 60 K，其中约 15 K 是电子–声子失配）；"
        "冷却 τ=245 ps",
        "T~sub{max} 由 J~sub{p} 唯一决定：T~sub{max} ≈ 300 + 50.4·(J~sub{p}/6×10~sup{12})² K",
    ], size=12, gap=8))
    notes(s, """这一页是加热模型，按论文的方程和参数来：热容 2.6×10~sup{6}，热导率按 Wiedemann-Franz 取 9，界面热导 170，热源是焦耳热，用一个一维有限差分精确解。6×10~sup{12}、6 ps 的时候 Co 层峰值只升 50 K，论文自己说大约 60 K，其中 15 K 是电子和声子没热平衡的部分，口径是符合的，冷却时间常数 245 ps。脚本里零维通道和这个解差 5%。峰值温度完全由电流决定，所以相图退化成一维阈值问题。""")

    # ------------------------------------------------------------------ P5
    s = add_blank(prs)
    title(s, "极性判据对上论文 Fig.3", 5)
    keyline(s, 0.55, 1.06, 12.25, 0.5,
            "末态符号 = −sign(H~sub{x} · I)。全器件四象限都能对上，本批从 +Mz 出发。", size=15)
    table(s, 0.55, 1.82, 5.7, [
        ["H~sub{x}", "I~sub{sign}", "m~sub{z, final}", "结果"],
        ["+160 mT", "+1", "−0.971", "翻转"],
        ["−160 mT", "+1", "+0.970", "不翻"],
        ["+160 mT", "−1", "+0.970", "不翻"],
        ["−160 mT", "−1", "−0.971", "翻转"],
        ["0（宏自旋/器件）", "±1", "+1.000", "不翻"],
    ], col_w=[1.6, 0.7, 1.5, 0.9], font_size=11, row_h=0.46)
    textbox(s, 0.55, 4.84, 5.7, 2.0,
            [{"text": "全器件：5×4 µm、J~sub{pk}=1.2×10~sup{13}、T~sub{max}=497 K，t~sub{cross}≈32 ps；"
                      "末态为均匀单畴（只有开边界的边缘列被钉扎）。",
              "size": 11, "color": GRAY, "line_spacing": 1.05, "space_after": 6},
             {"text": "H~sub{x}=0 对照：宏自旋（加热 10/12×10~sup{12}、无加热 20×10~sup{12}）与器件（12×10~sup{12}）"
                      "都不翻。面内场确实是必需的对称性破缺。",
              "size": 11, "color": GRAY, "line_spacing": 1.05}])
    picture(s, os.path.join(RUNS, "q_quadrants.png"), 6.35, 1.74, 6.45, 5.0)
    notes(s, """第一组验证看极性，对应论文 Fig.3。全器件 5×4 微米，1.2×10~sup{13}，峰值温度 497 K。四个象限跑下来很干净，末态就等于负的 H~sub{x} 乘电流的符号，都在 32 ps 左右过零，末态是均匀单畴，没有畴壁。H~sub{x}=0 的对照，宏自旋在有加热的 10、12×10~sup{12} 和无加热的 20×10~sup{12} 都不翻，器件 12×10~sup{12} 也不翻，说明面内场这个对称性破缺是必须的。这一页顺带验证了 SOT 接入的方向没搞反，因为极性规则是 SOT 的指纹。""")

    # ------------------------------------------------------------------ P6
    s = add_blank(prs)
    title(s, "时域动力学对上论文 Fig.4", 6)
    picture(s, os.path.join(RUNS, "fig4_full.png"), 0.55, 1.34, 8.3, 4.7)
    textbox(s, 9.05, 1.49, 3.75, 5.2, bullets([
        "3.7 ps、J~sub{p}=4×10~sup{12}：温升峰值 +13.9 K，heat_model 预测 13.8 K，自洽",
        "平行组 (H~sub{x}+,I+) 与 (H~sub{x}−,I−) 重合，29 ps 处下冲 −5.9%",
        "反平行组 (H~sub{x}+,I−) 与 (H~sub{x}−,I+) 重合，只有 −1.9%，没有正上冲",
        "去掉 H~sub{x}：±I 曲线重合，只剩退磁后的恢复，进动周期约 44 ps（论文约 40 ps）",
        "反射按 0.3 幅度、24 ps 延迟叠加，T(t) 在 29 ps 出现次级峰",
    ], size=12, gap=12))
    notes(s, """第二组验证是时域动力学，对的是 Fig.4。电流压到 4×10~sup{12}、脉宽 3.7 ps，避免翻过去：峰值温升 13.9 K，和热模型的 13.8 K 自洽。平行组两条曲线重合，29 ps 处下冲 5.9%；反平行组也重合，但幅度小很多，只有 1.9%，而且没有正上冲。去掉 H~sub{x} 之后，正负电流曲线完全重合，只剩热退磁后的恢复。进动周期 44 ps 左右，论文口径大概 40 ps。反射我们按 30% 幅度、24 ps 延迟叠一个二次脉冲来近似，温度在 29 ps 出现次级峰，位置和论文的 echo 对得上。""")

    # ------------------------------------------------------------------ P7
    s = add_blank(prs)
    title(s, "阈值：纯 SOT 与加热的对比（θ~sub{DL}=0.2 / 0.3）", 7)
    picture(s, os.path.join(RUNS, "phase_map.png"), 0.55, 1.14, 6.7, 5.7)
    textbox(s, 7.45, 1.34, 5.35, 5.4, bullets([
        "四个系列：θ~sub{DL}=0.2 / 0.3，各配加热开、关；温度取 T~sub{max} = 300 + 50.4·(J~sub{p}/6×10~sup{12})²",
        "纯 SOT 阈值：20×10~sup{12} A/m²（θ=0.2）、约 13.5×10~sup{12}（θ=0.3）。不加温度依赖也能翻",
        "加热阈值：(9,10]×10~sup{12}（θ=0.2）、(8,9]×10~sup{12}（θ=0.3），阈值比约 1.5–2 倍",
        "比值与论文的 9→6×10~sup{12}、能量约 2 倍一致；绝对值高约 1.5 倍",
        "15–17×10~sup{12} 有一段非单调的不翻窗口（θ=0.3 是 14–17×10~sup{12}），单畴进动回捕，18×10~sup{12} 后恢复",
        "用 1.5 ns 长弛豫复核，扫到 30×10~sup{12} 没有第二个窗口；27×10~sup{12} 是多畴伪影，已剔除",
    ], size=12.5, gap=11))
    notes(s, """这页是阈值，算这轮的核心结果。因为温升由电流唯一决定，横轴电流、纵轴末态磁化，就能把信息一次画全。四个系列：θ~sub{DL} 取 0.2 和 0.3，加热开和关。三件事。纯 SOT 不加温度依赖也能翻，只是阈值高，θ=0.2 要 20×10~sup{12}，0.3 大概 13.5×10~sup{12}。把论文的热通道打开，阈值掉到 9 到 10×10~sup{12}，θ=0.3 是 8 到 9×10~sup{12}，阈值比 1.5 到 2 倍，和论文的 9 掉到 6 一致，能量比也在论文的两倍量级。绝对值整体还是高 1.5 倍左右，后面会讲原因。另外加热档在 15 到 17×10~sup{12} 有个非单调窗口，翻一半又回去了。我们复核过：同参数重跑逐位一致；自由演化从 0.4 纳秒延到 1.5 纳秒，温度回到 300 K，结论不变，末态是干净的单畴 +0.981；再把 θ=0.2 从 21 扫到 30×10~sup{12}，没有第二个窗口。""")

    # ------------------------------------------------------------------ P8
    s = add_blank(prs)
    title(s, "脉宽窗口与翻转速度", 8)
    picture(s, os.path.join(RUNS, "phase_traces.png"), 0.55, 1.09, 7.0, 2.55)
    picture(s, os.path.join(RUNS, "phase_speed.png"), 0.55, 3.79, 7.0, 2.65)
    textbox(s, 7.85, 1.14, 4.95, 2.6, bullets([
        "θ=0.2、10×10~sup{12}、无加热：12 ps 以内不翻，15 ps 部分翻（−0.93），20/30 ps 完全翻",
        "FMR 半周期约 18–19 ps，与论文说的能量最优 10–20 ps 对得上",
    ], size=12, gap=8))
    table(s, 7.85, 3.34, 4.95, [
        ["J~sub{p}（θ=0.2 加热）", "t~sub{cross}"],
        ["10×10~sup{12}", "68.3 ps"],
        ["12×10~sup{12}", "49.2 ps"],
        ["14×10~sup{12}", "41.1 ps"],
        ["20×10~sup{12}", "26.2 ps"],
    ], col_w=[2.0, 1.2], font_size=10.5, row_h=0.42)
    textbox(s, 7.85, 5.39, 4.95, 1.4,
            [{"text": "速度随电流提升，但 20×10~sup{12} 那档 T~sub{max}=851 K，已过 T~sub{c}，"
                      "进入热模型不保证有效的区间。", "size": 11,
              "color": GRAY, "line_spacing": 1.05}])
    notes(s, """这页是脉宽和速度。左上固定 10×10~sup{12}、无加热，扫脉冲宽度：12 ps 以内不翻，15 ps 翻一半，20 ps 以上完全翻。18 到 19 ps 是 FMR 半周期，也是论文说的能量最优窗口，对得上。这说明论文 6 ps 能翻，是在接近阈值电流下靠加热把势垒压下去的，6 ps 本身只有半周期三分之一，纯 SOT 推不动。下面是加热条件下的过零时间：阈值附近 68 ps，12×10~sup{12} 是 49 ps，20×10~sup{12} 是 26 ps。要注意 20×10~sup{12} 那档峰值温度 851 K，已经超过居里温度，论文的热模型在那一带本来就不保证成立。""")

    # ------------------------------------------------------------------ P9
    s = add_blank(prs)
    title(s, "机制分解：K~sub{z}(T) 塌缩必不可少", 9)
    keyline(s, 0.55, 1.02, 12.25, 0.5,
            "SOT 定方向，K~sub{z}(T) 塌缩不可缺；只留热各向异性力矩也能翻，但更慢、更热。", size=15)
    picture(s, os.path.join(RUNS, "mechanism_compare.png"), 0.55, 1.64, 12.25, 3.65)
    textbox(s, 0.55, 5.44, 6.0, 1.6, bullets([
        "(a) 加热开/关：10×10~sup{12} 只有加热能翻，20×10~sup{12} 无加热也能翻，差别在阈值而不是机制",
        "(b) θ≈0 加加热：12×10~sup{12} 在 122.5 ps 翻、14×10~sup{12} 在 80.2 ps 翻（与论文一致）",
    ], size=11.5, gap=8))
    textbox(s, 6.85, 5.44, 6.0, 1.6, bullets([
        "(c) ScaleKz=0 冻结 K~sub{z}：14×10~sup{12} 不翻；只冻结 M~sub{s}：10×10~sup{12} 到 +0.45、12×10~sup{12} 到 −0.46",
        "H~sub{x}=0 任何条件都不翻；Noise=1（固定种子）时 9×10~sup{12} 变成部分翻（−0.32）",
    ], size=11.5, gap=8))
    notes(s, """这组是机制分解。左边同样的 10×10~sup{12}，关掉加热只掉到 0.7 就弹回来，开加热能翻；但电流加到 20×10~sup{12}，不开加热也翻，所以加热的作用是压阈值，不是机制上绕不开。中间把 SOT 关到接近零，只留热各向异性力矩，12×10~sup{12} 要 122 ps 才翻，14×10~sup{12} 是 80 ps，和论文的结论一致：纯热路径存在，但慢得多、也更热。右边是关键：把 K~sub{z} 的温度标度冻在 300 K，14×10~sup{12} 都翻不了，说明 K~sub{z} 塌缩这条通道必须有；只冻 M~sub{s} 而留着 K~sub{z}(T)，10×10~sup{12} 已经到 +0.45，12×10~sup{12} 到 −0.46，接近翻转，所以 M~sub{s} 下降是帮忙的角色。补两点：H~sub{x}=0 任何条件都不翻；开 Langevin 噪声后 9×10~sup{12} 从不翻变成部分翻，说明阈值附近对噪声敏感，不过 mumax3 噪声是固定种子，重复 run 逐位一样，概率统计暂时做不了。""")

    # ------------------------------------------------------------------ P10
    s = add_blank(prs)
    title(s, "能量核算", 10)
    picture(s, os.path.join(RUNS, "energy_bars.png"), 0.55, 1.24, 6.8, 4.6)
    keyline(s, 7.55, 1.24, 5.25, 0.7,
            "E = ∫ J²(t) dt · ρ · V\n（ρ = 81 µΩ·cm，V = 5×4 µm² × 15 nm）", size=13)
    table(s, 7.55, 2.15, 5.25, [
        ["条件", "能量", "结果"],
        ["6×10~sup{12}（无加热）", "39.7 pJ", "不翻（论文上限口径）"],
        ["10×10~sup{12}（加热）", "110.4 pJ", "翻（模型阈值）"],
        ["12×10~sup{12}（加热）", "158.9 pJ", "翻"],
        ["20×10~sup{12}（无加热）", "441.4 pJ", "翻（纯 SOT）"],
        ["20×10~sup{12}（加热）", "441.4 pJ", "翻（T~sub{max} 851 K > T~sub{c}）"],
    ], col_w=[1.9, 1.0, 2.0], font_size=10.5, row_h=0.50)
    textbox(s, 7.55, 6.09, 5.25, 0.95,
            [{"text": "论文的 <50 pJ 对应 6×10~sup{12} 这个上限口径；本模型最低可翻档是 110 pJ，"
                      "差距来自绝对阈值偏高，下一页归因。",
              "size": 10.5, "color": GRAY, "line_spacing": 1.05}])
    notes(s, """能量用和论文一样的口径：对真实电流波形积分 J²，再乘电阻率和体积。6×10~sup{12}、6 ps 是 39.7 pJ，和论文 40 pJ 的口径一致，但这一档在论文参数下翻不动。能翻的最低档是 10×10~sup{12}、110 pJ，比论文 50 pJ 的预算高。根本原因是绝对阈值高了 1.5 倍，不是核算方法的问题。20×10~sup{12} 不开加热也能翻，能量 441 pJ。阈值档这块的差距是下一轮要优先处理的，我怀疑根子在波形口径上。""")

    # ------------------------------------------------------------------ P11
    s = add_blank(prs)
    title(s, "与论文的逐项比对", 11)
    table(s, 0.55, 1.10, 12.3, [
        ["项目", "论文", "本复现", "判断"],
        ["极性规则", "−sign(H~sub{x}·I)", "−sign(H~sub{x}·I)（宏自旋 + 全器件）", "一致"],
        ["Fig.4 进动周期", "~40 ps", "≈44 ps", "一致"],
        ["纯 LLG 阈值", "9×10~sup{12}（θ=0.3）", "~13.5×10~sup{12}（θ=0.3）/ 20×10~sup{12}（θ=0.2）", "偏高 ~1.5×"],
        ["含热阈值", "6×10~sup{12}", "(8,9]×10~sup{12}（θ=0.3）/ (9,10]×10~sup{12}（θ=0.2）", "偏高 ~1.5×"],
        ["加热/无加热能量比", "~2×", "~2.3–4×", "量级一致"],
        ["纯热翻转（θ=0）", "论文可翻", "12×10~sup{12} / 122 ps、14×10~sup{12} / 80 ps", "一致"],
        ["最快翻转", "16 ps", "26 ps（2×10~sup{13} 加热档，T~sub{max}>T~sub{c}）", "偏高"],
        ["能量预算", "<50 pJ @6×10~sup{12}", "6×10~sup{12} 不翻；阈值档 110 pJ", "未达预算"],
    ], col_w=[1.7, 1.6, 4.3, 1.5], font_size=10, row_h=0.48)
    textbox(s, 0.55, 6.09, 12.3, 1.0,
            [{"text": "主要不确定度有四条：论文没公开 6 ps 脉冲的波形和反射序列，这是绝对阈值偏高最可能"
                      "的原因；J~sub{p}≳1.9×10~sup{13} 时 T~sub{max}>T~sub{c}，M~sub{s} 被截断为 0，属于论文排除的 HAMR 情形；"
                      "均匀宏自旋没有成核和畴壁，近阈值和极强电流下偶发多畴伪影，已用 OVF 剔除；"
                      "概率统计还没做，因为噪声是固定种子。",
              "size": 11, "color": GRAY, "line_spacing": 1.05}])
    notes(s, """这页是逐项比对。对上的有：极性规则、Fig.4 的周期、纯热路径、加热和无加热的能量比量级。没完全对上的是：绝对阈值整体高 1.5 倍，最快翻转 16 对 26 ps，能量预算还没到。偏高最可能是论文没公开脉冲波形和电缆反射，我们只能用 sech² 近似，而波形直接决定注入的角动量。还有高电流区要注意，1.9×10~sup{13} 以上模型温度过 T~sub{c}，M~sub{s} 截断成零，这接近论文用垂直场实验排除的 HAMR 情形，像 20×10~sup{12} 加热档这种结果只能当参考。最后，均匀宏自旋没有成核和畴壁，概率统计因为固定种子也还没做。""")

    # ------------------------------------------------------------------ P12
    s = add_blank(prs)
    title(s, "下一步", 12)
    roadmap = [
        ("概率与成核", "给 Langevin 噪声加种子控制\n上全尺寸器件和晶粒随机性\n做 P~sub{sw}(J~sub{p})，对标 91%"),
        ("波形与反射标定", "试 sech² / 高斯 / 方波 与不同反射序列\n解释绝对阈值高出的 ~1.5 倍\n这一步决定定量结论能不能用"),
        ("阈值律", "验证 J~sub{c}(H~sub{x}) ∝ 1/H~sub{x}\n脉宽 6→30 ps 的速度–能量曲线\n对照论文 Fig.3"),
        ("收敛性", "网格 5→2.5 nm、Aex 的不确定度\nFixDt 5×10~sup{-14}→1×10~sup{-14} 的高温对照\n确认结论不依赖离散化"),
    ]
    for i, (t, body) in enumerate(roadmap):
        x = 0.55 + i * 3.18
        block(s, x, 1.45, 2.95, 3.45, t, body.split("\n"), head_size=14,
              body_size=12)
    textbox(s, 0.55, 5.25, 12.2, 0.8,
            [{"text": "优先级从高到低。前两项决定定量可信度，J~sub{c}(H~sub{x}) 和脉宽曲线可以直接支撑实验设计。",
              "size": 12, "color": GRAY, "align": PP_ALIGN.CENTER}])
    notes(s, """下一步四件事。最优先是概率与成核，把噪声种子改可控，上全尺寸器件和晶粒随机性，做 P~sub{sw}(J~sub{p}) 统计，对论文的 91%。第二是波形和反射标定，试不同波形和反射序列，把高 1.5 倍的原因找出来，这一步做完定量结论才站得住。第三是阈值律，验 J~sub{c} 随 H~sub{x} 的 1/H~sub{x} 关系，还有脉宽 6 到 30 ps 的速度-能量曲线，对照论文 Fig.3，这两条对实验设计最有用。第四是收敛性，网格、交换常数、时间步都做对照，确认结论不依赖离散化。""")

    # ------------------------------------------------------------------ P13
    s = add_blank(prs)
    title(s, "备份：脚本、运行与踩坑", 13)
    codebox(s, 0.55, 1.19, 7.5, 3.15, """脚本（simulations/mumax3_sot/）
  macrospin_switch.mx3   64×64 阈值/机制扫描（主模板）
  fig4_dynamics.mx3      无限薄膜 + 反射，Fig.4 用
  fig3_switching.mx3     500×400×10 nm（5×4 µm 过流区）
  heat_model.py          热扩散 1D FD 标定

运行
  python run_case.py macrospin_switch.mx3 si_h_t20_Jp10 \\
      --set Jp=10e12 Heating=1
  → runs/<tag>/ 自动保存脚本副本与 table/log/ovf
  → summary.csv 汇总（runs/ 为本地结果目录）
  → 定稿图拷入 docs/figures/ 统一归档""", size=10.5)
    textbox(s, 8.25, 1.24, 4.55, 5.4, bullets([
        "各向异性用 Ku1=K~sub{z}(T)；旧写法 Keff+½μ0Ms² 在温度标度分解时不独立",
        "J 沿 x 写会被内核忽略（只读 J.z），转矩恒为零，也不报错",
        "B_ext 单位是 T；cell、dt 是内建名；Pol=0 会被断言拦截，θ≈0 用 1×10~sup{-4}",
        "自适应步长会把 6 ps 脉冲拉到 27.6 ps，必须用固定步长",
        "Langevin 噪声是固定种子，重复 run 结果逐位相同",
        "细节见 notes/error.md、docs/paper_replica.md（论文与 mumax3 的逐项映射）",
    ], size=12, gap=12))
    notes(s, """备份页。左边是脚本分工和跑法：主模板做快速扫描，fig4 脚本做过程曲线，fig3 脚本做全器件，heat_model.py 单独标定加热。run_case.py 管参数替换和归档，能溯源。右边是踩坑速查。最容易搞错的是各向异性的写法，最危险的是自适应步长把 6 ps 拉成 27.6 ps，会得出假结论。噪声固定种子是下一步要解决的。完整的映射写在 docs/paper_replica.md 里。""")

    prs.save(OUT)
    print("saved:", OUT)
    print("slides:", len(prs.slides._sldIdLst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
