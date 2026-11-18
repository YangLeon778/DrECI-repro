"""Dr.ECI 汇报 PPTX（第八组，14 页，充实版）。

结构：先讲原论文方法与框架 → 再讲我们的实现 → 再对比原论文结果与我们的发现。
纯原生 python-pptx，PowerPoint COM 兼容。
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
PAPER_IMG = ROOT / "results" / "figures"
OUT = ROOT / "第八组_DrECI_汇报.pptx"

ACCENT1 = RGBColor(0x44, 0x72, 0xC4)
ACCENT2 = RGBColor(0xED, 0x7D, 0x31)
HEADER_BAR = RGBColor(0x5E, 0x9E, 0xFF)
HEADER_BAR2 = RGBColor(0xC4, 0xD6, 0xEB)
PINK_TIP = RGBColor(0xFF, 0xEB, 0xFA)
DARK = RGBColor(0x22, 0x22, 0x22)
GRAY = RGBColor(0x66, 0x66, 0x66)
LGRAY = RGBColor(0xE7, 0xE6, 0xE6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def _I(x):
    return int(x)


def make_prs():
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    return prs


def add_page_header(slide, title_text):
    b1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, _I(0), _I(0), _I(Inches(13.33)), _I(Pt(60)))
    b1.fill.solid(); b1.fill.fore_color.rgb = HEADER_BAR; b1.line.fill.background()
    b2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, _I(0), _I(Pt(60)), _I(Inches(13.33)), _I(Pt(8)))
    b2.fill.solid(); b2.fill.fore_color.rgb = HEADER_BAR2; b2.line.fill.background()
    b3 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, _I(Inches(11.8)), _I(0), _I(Inches(1.53)), _I(Pt(60)))
    b3.fill.solid(); b3.fill.fore_color.rgb = PINK_TIP; b3.line.fill.background()
    tb = slide.shapes.add_textbox(_I(Inches(0.5)), _I(Pt(12)), _I(Inches(12.3)), _I(Pt(40)))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = title_text; r.font.size = Pt(28); r.font.bold = True
    r.font.color.rgb = RGBColor(0x44, 0x54, 0x6A); r.font.name = "微软雅黑"


def add_text(slide, text, x, y, w, h, size=14, bold=False, color=None, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(_I(x), _I(y), _I(w), _I(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = Emu(0); tf.margin_right = Emu(0); tf.margin_top = Emu(0); tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]; p.alignment = align
    run = p.add_run(); run.text = text; run.font.size = Pt(size); run.font.bold = bold
    run.font.color.rgb = color or DARK; run.font.name = "微软雅黑"
    return tb


def add_bullets(slide, bullets, x, y, w, h, size=12, color=None):
    tb = slide.shapes.add_textbox(_I(x), _I(y), _I(w), _I(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.bullet = True; p.level = 0
        run = p.add_run(); run.text = b; run.font.size = Pt(size)
        run.font.color.rgb = color or DARK; run.font.name = "微软雅黑"
    return tb


def add_table(slide, headers, rows, x, y, w, h, font_size=9):
    ncol = len(headers); nrow = len(rows) + 1
    tbl = slide.shapes.add_table(nrow, ncol, _I(x), _I(y), _I(w), _I(h)).table
    for i, h0 in enumerate(headers):
        cell = tbl.cell(0, i); cell.text = ""
        p = cell.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = str(h0); r.font.size = Pt(font_size); r.font.bold = True
        r.font.color.rgb = WHITE; r.font.name = "微软雅黑"
        cell.fill.solid(); cell.fill.fore_color.rgb = ACCENT1
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    for ri, row in enumerate(rows, 1):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci); cell.text = ""
            p = cell.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
            r = p.add_run(); r.text = str(val); r.font.size = Pt(font_size - 1 if font_size > 9 else font_size)
            r.font.color.rgb = DARK; r.font.name = "微软雅黑"
            if ri % 2 == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = LGRAY
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    return tbl


# ==========================================================================
def main():
    prs = make_prs()
    blank = prs.slide_layouts[6]

    # ==================================================================
    # SLIDE 1: 封面
    # ==================================================================
    s = prs.slides.add_slide(blank)
    deco = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, _I(0), _I(Inches(6.9)),
                               _I(Inches(13.33)), _I(Inches(0.6)))
    deco.fill.solid(); deco.fill.fore_color.rgb = HEADER_BAR; deco.line.fill.background()

    # 左装饰竖条
    deco2 = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, _I(Inches(3.5)), _I(Inches(1.4)),
                                _I(Inches(0.15)), _I(Inches(5.0)))
    deco2.fill.solid(); deco2.fill.fore_color.rgb = ACCENT2; deco2.line.fill.background()

    add_text(s, "Dr.ECI", Inches(1), Inches(1.5), Inches(11.33), Inches(1.2),
             size=64, bold=True, color=ACCENT2, align=PP_ALIGN.CENTER)
    add_text(s, "Decomposed Reasoning for Event Causality Identification",
             Inches(1), Inches(2.7), Inches(11.33), Inches(0.5),
             size=16, color=RGBColor(0x44, 0x54, 0x6A), align=PP_ALIGN.CENTER)
    add_text(s, "多智能体分解推理框架 · 事件因果关系识别 · 算法复现与分析",
             Inches(1), Inches(3.25), Inches(11.33), Inches(0.5),
             size=18, bold=True, color=ACCENT1, align=PP_ALIGN.CENTER)
    add_text(s, "原论文：COLING 2025  |  代码：GitHub · Cai et al.",
             Inches(1), Inches(4.0), Inches(11.33), Inches(0.4),
             size=12, color=GRAY, align=PP_ALIGN.CENTER)
    add_text(s, "机器智能课程设计 · 第八组",
             Inches(1), Inches(4.6), Inches(11.33), Inches(0.5),
             size=16, color=GRAY, align=PP_ALIGN.CENTER)
    add_text(s, "罗杨阳  ·  廖兴易  |  指导：王邦  |  2026.11",
             Inches(1), Inches(5.15), Inches(11.33), Inches(0.5),
             size=13, color=RGBColor(0x88, 0x88, 0x88), align=PP_ALIGN.CENTER)

    # ==================================================================
    # SLIDE 2: 目录
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "汇报目录")

    add_text(s, "第一部分：原论文方法与框架",
             Inches(0.5), Inches(1.2), Inches(6), Inches(0.5),
             size=16, bold=True, color=ACCENT1)
    items1 = [
        "01  原论文讲了什么？任务 + 贡献",
        "02  Dr.ECI 框架图（原论文 Figure 直接展示）",
        "03  因果模式分类 + 八规则 Reasoner",
        "04  原论文的实验设置与自己报告的结果",
    ]
    for i, txt in enumerate(items1):
        add_text(s, txt, Inches(0.5), Inches(1.75 + i * 0.45),
                 Inches(12.33), Inches(0.4), size=14, color=DARK)

    add_text(s, "第二部分：我们的复现与发现",
             Inches(0.5), Inches(3.6), Inches(6), Inches(0.5),
             size=16, bold=True, color=ACCENT2)
    items2 = [
        "05  我们的实现：数据划分 / 模型配置 / 三组对照",
        "06  dev 集结果（阈值选择）",
        "07  test 集结果（冻结独立评估）",
        "08  结果对比：原论文趋势 vs 我们看到的",
        "09  双口径审计 + 原仓库 core.py Bug",
        "10  真实样例与错例分析",
        "11  局限、改进、成员贡献",
    ]
    for i, txt in enumerate(items2):
        add_text(s, txt, Inches(0.5), Inches(4.15 + i * 0.45),
                 Inches(12.33), Inches(0.4), size=14, color=DARK)

    # ==================================================================
    # SLIDE 3: 任务 + 原论文贡献
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "1. 任务定义 + 原论文核心贡献")

    # 左：任务
    add_text(s, "▶ 事件因果关系识别（ECI）",
             Inches(0.5), Inches(1.2), Inches(6.3), Inches(0.4),
             size=15, bold=True, color=ACCENT1)
    add_bullets(s, [
        "输入：一段自然语言文本 + 文本中已定位的两个事件 e_s（源）、e_t（目标）",
        "输出：二分类 —— e_s 是否导致 e_t 的发生（Yes / No）",
        "难点：因果关系可以是显式的（because、due to、as a result of），",
        "       也可以是隐式的（需要常识推理、时序判断、事件链推断）",
        "评估粒度：事件对级别，不考虑文档级全局事件链",
        "常用数据集：EventStoryLine (ESL)、Causal-TimeBank、MAVEN-ERE",
    ], Inches(0.5), Inches(1.65), Inches(6.3), Inches(2.6), size=11.5)

    # 右：原论文
    add_text(s, "▶ Dr.ECI 原论文信息",
             Inches(7.0), Inches(1.2), Inches(5.8), Inches(0.4),
             size=15, bold=True, color=ACCENT2)
    add_bullets(s, [
        "全称：Dr.ECI —— Decomposed Reasoning for Event Causality Identification",
        "作者：Cai R., Yu S., Zhang J., Chen W., Xu B., Zhang K.",
        "发表：COLING 2025（ACL 系列会议）",
        "核心主张：现有 LLM 对因果推理能力不足，",
        "       需要注入结构化因果知识 + 分阶段多智能体协作",
        "开源：GitHub 上提供完整 prompt + agent1/2/3 代码",
    ], Inches(7.0), Inches(1.65), Inches(5.8), Inches(2.6), size=11)

    add_text(s, "▶ 原论文三项核心贡献",
             Inches(0.5), Inches(4.4), Inches(12.33), Inches(0.4),
             size=15, bold=True, color=ACCENT1)
    add_bullets(s, [
        "(1) 多智能体分解推理框架 Dr.ECI：Discovery Stage（Causal Explorer + Mediator Detector）+ Reasoning Stage（Direct Reasoner + Indirect Reasoner）",
        "(2) 用因果图理论系统总结了 ECI 中的显式 / 隐式因果模式（Direct vs Indirect Causal Patterns），共 8 条规则",
        "(3) 在 EventStoryLine 和 Causal-TimeBank 两个数据集上，相比 LLM baseline 和传统监督方法取得 SOTA",
    ], Inches(0.5), Inches(4.85), Inches(12.33), Inches(2.0), size=11.5)

    # ==================================================================
    # SLIDE 4: 原论文框架图（直接放原文 methods.png）
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "2. 原论文 Dr.ECI 框架（Figure 1 直接展示）")

    img = PAPER_IMG / "paper_methods.png"
    if img.exists():
        iw, ih = 13.33, 4.8  # 大图铺满
        i_ratio = 1644 / 598
        h = iw / i_ratio
        if h > 4.8:
            h = 4.8; iw = h * i_ratio
        x = (13.33 - iw) / 2
        s.shapes.add_picture(str(img), _I(Inches(x)), _I(Inches(1.1)), width=Inches(iw))

    add_text(s, "原图来自 Dr.ECI 论文 Figure 1（COLING 2025）。两阶段四智能体架构：",
             Inches(0.5), Inches(6.0), Inches(12.33), Inches(0.4),
             size=12, bold=True, color=ACCENT1)
    add_bullets(s, [
        "Discovery Stage：Causal Explorer 用 N={causal relationship, causation, causality} 三次提问初筛，通过阈值 q 门控后 Mediator Detector 找中介实体 E_st",
        "Reasoning Stage：Direct Reasoner（无中介时）/ Indirect Reasoner（有中介时）用因果模式规则做最终判决",
        "我们的复现用了相同的四阶段，但把 Direct + Indirect Reasoner 合并成一个 Reasoner 走 8 条规则",
    ], Inches(0.5), Inches(6.4), Inches(12.33), Inches(1.0), size=11)

    # ==================================================================
    # SLIDE 5: 因果模式分类 + 八规则
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "3. 因果模式分类 + Reasoner 八条规则")

    # 左：因果模式分类图
    img = PAPER_IMG / "paper_causal_patterns.png"
    if img.exists():
        iw = 6.3
        i_ratio = 1644 / 598  # 近似宽高比，原是 403KB
        h = 3.2
        s.shapes.add_picture(str(img), _I(Inches(0.5)), _I(Inches(1.1)), width=Inches(iw), height=Inches(h))
    add_text(s, "原论文 Figure 2：ECI 因果模式分两类",
             Inches(0.5), Inches(4.35), Inches(6.3), Inches(0.4),
             size=11, color=GRAY)

    # 右：八条规则
    add_text(s, "▶ Dr.ECI Reasoner 的 8 条因果规则",
             Inches(7.0), Inches(1.1), Inches(5.8), Inches(0.4),
             size=14, bold=True, color=ACCENT2)
    add_table(s,
              ["#", "规则名", "类型", "触发条件"],
              [
                  ["1", "Causal Connective", "显式", "因果连接词（because/due to/as a result of 等）"],
                  ["2", "Implicit Connective", "隐式", "隐式因果暗示（lead to/cause/trigger 等）"],
                  ["3", "Temporal Order", "时序", "e_s 发生在 e_t 之前，且时间间隔合理"],
                  ["4", "Co-reference", "共指", "两个事件共享主语/宾语实体"],
                  ["5", "Causal Chain", "链", "e_s → e_m → e_t 的链式因果"],
                  ["6", "Collision", "碰撞", "两事件共享宾语且动作冲突"],
                  ["7", "Fork", "分叉", "一事件导致多个结果"],
                  ["8", "Comprehensive", "综合", "以上多条件综合判断"],
              ],
              Inches(7.0), Inches(1.55), Inches(5.8), Inches(4.7), font_size=9.5)

    add_text(s, "规则触发逻辑：任意一条规则命中 → 判 Yes；全部未命中 → 判 No。我们观察到这是 FP 的重要来源——常识先后（killing after chase）容易被 Causal Chain / Causal Order 误触发。",
             Inches(0.5), Inches(6.1), Inches(12.33), Inches(0.6),
             size=11, color=DARK)

    # ==================================================================
    # SLIDE 6: 原论文实验设置 + 原论文自己报告的结果
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "4. 原论文的实验设置与自己报告的结果")

    add_text(s, "▶ 原论文用了两个独立实验 setting（来自 README）",
             Inches(0.5), Inches(1.2), Inches(12.33), Inches(0.4),
             size=14, bold=True, color=ACCENT1)
    add_bullets(s, [
        "Setting 1 —— Zhang et al. 测试设置：在 EventStoryLine (全量 train/dev/test) 上训练 + 评估，对比 supervised baselines（CHEER、SENDIR、ERGO）和 LLM baselines（GPT-3.5 0-shot）",
        "Setting 2 —— Gao et al. 开发设置：用 DeepSeek 系列模型做 LLM 推理，报告 dev 集的对比结果",
        "DeepSeek 模型：原论文用 deepseek-chat（已于 2025 年下线），我们换成 deepseek-flash",
        "关键参数：原论文没公开 temperature / max_tokens / reasoning_effort，我们设 temp=0.0, max_tokens=16384, reasoning_effort=low",
    ], Inches(0.5), Inches(1.65), Inches(12.33), Inches(2.2), size=11.5)

    # 原论文关键结果（文字描述 + 图片提示）
    add_text(s, "▶ 原论文自己报告的关键发现（README + Analysis.png）",
             Inches(0.5), Inches(4.0), Inches(12.33), Inches(0.4),
             size=14, bold=True, color=ACCENT2)

    # 左：Analysis.png
    img = PAPER_IMG / "paper_analysis.png"
    if img.exists():
        s.shapes.add_picture(str(img), _I(Inches(0.5)), _I(Inches(4.5)), width=Inches(5.8))

    add_text(s, "原论文 Analysis.png 说明：",
             Inches(6.6), Inches(4.5), Inches(6.3), Inches(0.4),
             size=12, bold=True, color=ACCENT2)
    add_bullets(s, [
        "✅ **核心发现**：q 越高，Recall 越高。",
        "三次全答 Yes 的事件对（q=3），Recall 明显高于",
        "只答两次的（q=2）和只答一次的（q=1）。",
        "",
        "✅ 原论文在 EventStoryLine 全量评估上 F1 达到 SOTA。",
        "",
        "✅ Dr.ECI 在跨句因果（Inter-F1）上的优势尤其明显，",
        "说明 Discovery Stage 的 Mediator 设计有效捕获了间接因果。",
        "",
        "⚠️ 注意：Analysis.png 的结果是在过筛子集上画的，",
        "**原论文没有报告全集口径**。这是我们发现的关键差异。",
    ], Inches(6.6), Inches(4.95), Inches(6.3), Inches(2.5), size=11.5)

    # ==================================================================
    # SLIDE 7: 我们的实现总览 + 三组对照设计
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "5. 我们的实现 + 三组对照实验设计")

    add_text(s, "▶ 数据划分（ESL 17,998 对 / 233 文档）",
             Inches(0.5), Inches(1.2), Inches(12.33), Inches(0.4),
             size=14, bold=True, color=ACCENT1)
    add_table(s, ["集合", "事件对", "正例", "正例比例", "说明"],
              [["train", "10,718", "1,912", "17.8%", "文档级 seed=42 划分，与 dev/test 文档不重叠"],
               ["dev (全量)", "3,840", "636", "16.6%", "用于选阈值，但我们只抽 300 对迭代"],
               ["test (全量)", "3,440", "636", "18.5%", "**冻结后只评一次**，学术规范"],
               ["固定子集", "dev=300 / test=300", "50 / 55", "分层抽样 seed=2026", "小样本快速评估"],
              ],
              Inches(0.5), Inches(1.65), Inches(12.33), Inches(2.0), font_size=10)

    add_text(s, "▶ 与原仓库的关键差异 + 工程实现",
             Inches(0.5), Inches(3.85), Inches(12.33), Inches(0.4),
             size=14, bold=True, color=ACCENT2)
    add_table(s, ["方面", "原仓库", "我们的实现", "为什么不同"],
              [["底层模型", "deepseek-chat", "deepseek-flash", "前者 2025 年已下线"],
               ["推理档位", "(未公开)", "reasoning_effort=low", "默认 high 会挤占输出预算（Reasoner 被截断）"],
               ["温度 / max_tokens", "(未公开)", "temp=0.0 / 16384", "确定性输出 + 充足长度"],
               ["解析器", "只匹配 {\"Answer\":\"No\"}", "分层匹配规则 JSON", "原仓库 core.py 有 Bug（见第 9 页）"],
               ["测试集", "(未说明冻结)", "冻结、只评一次", "课程设计学术规范"],
               ["工程", "裸 python", "并发 8 路 + SHA256 缓存 + raw_responses 留档 + 自动计费", "可追溯、可复算、节省费用"],
              ],
              Inches(0.5), Inches(4.3), Inches(12.33), Inches(2.6), font_size=9.5)

    # 三组对照
    add_text(s, "▶ 三组对照实验（严格控制变量）",
             Inches(0.5), Inches(7.0), Inches(12.33), Inches(0.4),
             size=14, bold=True, color=ACCENT1)
    # 在表格下方加一行
    add_table(s, ["实验", "改动", "阈值", "目的"],
              [["E0", "匹配 baseline", "—", "单轮直接问「两事件有因果吗」= 无推理的纯 LLM 基线"],
               ["E1", "完整 Dr.ECI 流程", "q≥1", "复现论文完整方法：Explorer→Mediator→Reasoner"],
               ["E2", "只改阈值的消融", "q≥2", "隔离「阈值高低」这一个变量的影响"]],
              Inches(0.5), Inches(7.45), Inches(12.33), Inches(0.6))

    # ==================================================================
    # SLIDE 8: dev 结果
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "6. dev 集结果（阈值选择）")

    add_text(s, "300 对，正例 50；dev 用于选 E1/E2 阈值，test 集完全独立、冻结、仅评一次",
             Inches(0.5), Inches(1.15), Inches(12.33), Inches(0.35),
             size=11, color=GRAY)

    add_table(s,
              ["实验", "改动", "P", "R", "F1", "Acc", "TP", "FP", "FN", "TN", "被过滤", "API失败"],
              [["E0", "匹配基线", "0.3485", "0.4600", "0.3966", "0.7667", "23", "43", "27", "207", "0", "0"],
               ["E1", "q≥1 完整", "0.2778", "0.2000", "0.2326", "0.7800", "10", "26", "40", "224", "225", "35"],
               ["E2", "q≥2 阈值", "0.2333", "0.1400", "0.1750", "0.7800", "7", "23", "43", "227", "245", "35"]],
              Inches(0.5), Inches(1.55), Inches(12.33), Inches(1.4))

    img = RESULTS / "figures" / "metrics_dev.png"
    if img.exists():
        s.shapes.add_picture(str(img), _I(Inches(0.5)), _I(Inches(3.1)), width=Inches(6.5))

    add_text(s, "▶ dev 集关键观察", Inches(7.2), Inches(3.05), Inches(5.3), Inches(0.4),
             size=13, bold=True, color=ACCENT2)
    add_bullets(s, [
        "E0 F1=0.397 显著高于 E1(0.233) / E2(0.175)",
        "两个原因叠加：",
        "  ① q=0 的正例被 Explorer 三次都答 No 直接过滤",
        "  ② dev 上 35 次 API 超时丢失正例",
        "",
        "阈值越高 Recall 越低（dev 上 q≥2 比 q≥1 Recall 更低）",
        "—— 这和原论文 Analysis.png 趋势**相反**，因为我们全集口径",
        "",
        "选 E1(q≥1) 为完整方法（Recall 更高），E2(q≥2) 消融保留",
    ], Inches(7.2), Inches(3.5), Inches(5.1), Inches(3.0), size=11)

    # ==================================================================
    # SLIDE 9: test 结果
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "7. test 集结果（冻结后一次性独立评估）")

    add_text(s, "300 对，正例 55；E0/E1/E2 使用完全相同的划分、标签、阈值与随机种子",
             Inches(0.5), Inches(1.15), Inches(12.33), Inches(0.35),
             size=11, color=GRAY)

    add_table(s,
              ["实验", "改动", "P", "R", "F1", "Acc", "TP", "FP", "FN", "TN", "被过滤", "耗时", "费用"],
              [["E0", "匹配基线", "0.4857", "0.6182", "0.5440", "0.8100", "34", "36", "21", "209", "0", "82s", "¥0.18"],
               ["E1", "q≥1 完整", "0.4032", "0.4545", "0.4274", "0.7767", "25", "37", "30", "208", "213", "744s", "¥2.07"],
               ["E2", "q≥2 阈值", "0.4464", "0.4545", "0.4505", "0.7967", "25", "31", "30", "214", "230", "3.7s*", "¥0.00**"]],
              Inches(0.4), Inches(1.5), Inches(12.5), Inches(1.4))
    add_text(s, "* E2 耗时 3.7s 因为其过筛样本 ⊂ E1，全部命中磁盘缓存；** E2 的 Mediator + Reasoner 全部命中缓存",
             Inches(0.4), Inches(2.9), Inches(12.5), Inches(0.35), size=9, color=RGBColor(0x88, 0x88, 0x88))

    img = RESULTS / "figures" / "metrics_test.png"
    if img.exists():
        s.shapes.add_picture(str(img), _I(Inches(0.4)), _I(Inches(3.35)), width=Inches(6.3))

    add_text(s, "▶ test 集观察", Inches(7.0), Inches(3.3), Inches(5.5), Inches(0.4),
             size=13, bold=True, color=ACCENT2)
    add_bullets(s, [
        "E0 F1=0.544 仍然最高——纯单轮提示在这个小样本上就很强",
        "E1 vs E2：Recall 完全相同（0.4545=25/55）",
        "但 E2 FP 从 37→31（-6），Recall 没损失",
        "→ F1 从 0.427→0.450，E2 反而更好",
        "",
        "dev → test 指标大幅跳升：",
        "  E0 F1 dev=0.397 vs test=0.544（差 0.15）",
        "  test 正例可能本身更容易被 Explorer 识别",
        "  小样本方差大 + dev 上 35 次 API 失败",
    ], Inches(7.0), Inches(3.75), Inches(5.3), Inches(2.8), size=11)

    # ==================================================================
    # SLIDE 10: 结果对比 —— 原论文趋势 vs 我们的发现
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "8. 结果对比：原论文报告的趋势 vs 我们实际看到的")

    # 左：原论文 Analysis.png
    img = PAPER_IMG / "paper_analysis.png"
    if img.exists():
        s.shapes.add_picture(str(img), _I(Inches(0.5)), _I(Inches(1.2)), width=Inches(5.8))
    add_text(s, "原论文 Analysis.png：q 越高 Recall 越高",
             Inches(0.5), Inches(5.2), Inches(5.8), Inches(0.4),
             size=12, bold=True, color=ACCENT2, align=PP_ALIGN.CENTER)
    add_bullets(s, [
        "原论文观察方向：Recall(q=3) > Recall(q=2) > Recall(q=1)",
        "Recall(q≥2) > Recall(q≥1) 全集也涨",
        "暗示阈值应该越高越好",
        "✓ 但这张图是在**过筛子集**上画的",
    ], Inches(0.5), Inches(5.6), Inches(5.8), Inches(1.6), size=10.5)

    # 右：我们的对比表
    add_text(s, "▶ 我们 test 集：全集 vs 过筛子集双口径",
             Inches(6.6), Inches(1.2), Inches(6.3), Inches(0.4),
             size=14, bold=True, color=ACCENT1)
    add_table(s,
              ["实验", "口径", "n", "pos", "TP", "FN", "Recall", "F1"],
              [["E1", "全集", "300", "55", "25", "30", "0.4545", "0.4274"],
               ["E1", "过筛", "87", "37", "25", "12", "0.6757", "0.5051"],
               ["E2", "全集", "300", "55", "25", "30", "0.4545", "0.4505"],
               ["E2", "过筛", "70", "32", "25", "7", "0.7812", "0.5682"],
               ["—", "q≥3 层", "54", "27", "24", "3", "0.8889", "0.6234"]],
              Inches(6.6), Inches(1.65), Inches(6.3), Inches(1.9), font_size=9)

    add_text(s, "▶ 对比结论", Inches(6.6), Inches(3.7), Inches(6.3), Inches(0.4),
             size=13, bold=True, color=ACCENT2)
    add_bullets(s, [
        "过筛子集内：阈值↑→Recall↑ ✓ ✓ ✓ 与原论文一致！",
        "（0.676 → 0.781 → 0.889）",
        "",
        "但全集 Recall **持平**：E1=E2=0.4545",
        "—— 阈值提高没让 Recall 掉，但也没涨",
        "",
        "真正的瓶颈：q=0 的正例！",
        "test 55 正例中 **18 个（32.7%）** 被 Explorer",
        "三次都答 No 直接过滤。这些正例根本进不了",
        "过筛子集，提高阈值对它们无能为力。",
    ], Inches(6.6), Inches(4.1), Inches(6.3), Inches(3.0), size=11)

    # ==================================================================
    # SLIDE 11: 双口径审计详解 + core.py Bug
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "9. 双口径审计详解 + 原仓库 Bug 发现")

    add_text(s, "▶ 双口径审计：全集 vs 过筛子集 vs q=0 被过滤层",
             Inches(0.5), Inches(1.2), Inches(12.33), Inches(0.4),
             size=14, bold=True, color=ACCENT1)
    add_table(s,
              ["实验", "评估层级", "说明", "Recall", "F1"],
              [["E0", "全集", "无过滤，所有 300 对都判", "0.6182", "0.5440"],
               ["E1", "全集 (q≥1)", "300 对都判（213 个过滤为 No）", "0.4545", "0.4274"],
               ["E1", "q=0 被过滤层", "213 对，含 18 个正例全部 FN", "0.0000", "—"],
               ["E1", "q≥1 过筛子集", "87 对（正例 37），才是 Mediator+Reasoner 真正评估的范围", "0.6757", "0.5051"],
               ["E2", "全集 (q≥2)", "300 对都判（230 个过滤为 No）", "0.4545", "0.4505"],
               ["E2", "q=0 被过滤层", "213 对，含 18 个正例全部 FN", "0.0000", "—"],
               ["E2", "q=1 被过滤层", "17 对（新增被过滤），0 个正例损失", "—", "—"],
               ["E2", "q≥2 过筛子集", "70 对（正例 32）", "0.7812", "0.5682"],
               ["—", "q≥3 层", "Explorer 三次全 Yes（最可信）", "0.8889", "0.6234"]],
              Inches(0.5), Inches(1.65), Inches(12.33), Inches(3.2), font_size=9)

    add_text(s, "▶ 原仓库 agent3/core.py 解析 Bug（意外发现）",
             Inches(0.5), Inches(5.0), Inches(7.3), Inches(0.4),
             size=14, bold=True, color=ACCENT2)
    add_bullets(s, [
        "函数名 contains_yes_answer，意图是「检测 Yes 答案」",
        "但实际代码用正则匹配字符串 {\"Answer\":\"No\"}",
        "然后整个 reasoner 评估逻辑用 if total_yes_count < 1 判正例",
        "",
        "更致命：Reasoner 根本不输出 {\"Answer\":\"Yes\"/\"No\"}",
        "它输出的是 8 条规则的 JSON 数组，每条规则含 \"Result\" 字段",
        "原作者根本没有正确解析 Reasoner 的输出！",
        "",
        "这意味着 Dr.ECI 原论文的 reasoner 评估可能有严重偏差。",
        "我们重写了 parse.py，分层匹配规则 JSON 里的 No / 非 No 值。",
    ], Inches(0.5), Inches(5.45), Inches(7.3), Inches(2.0), size=10.5)

    add_text(s, "▶ 为什么这很重要",
             Inches(8.2), Inches(5.0), Inches(4.5), Inches(0.4),
             size=13, bold=True, color=ACCENT1)
    add_bullets(s, [
        "原论文 Dr.ECI 的 Reasoner 评估逻辑有 bug →",
        "  它报告的 F1/P/R 可能不是真实性能",
        "",
        "q=0 正例占比 32.7% 是全集 Recall 的天花板",
        "  阈值从 q≥1 升到 q≥2 无法突破这个天花板",
        "",
        "三次提问过于接近导致 q 缺乏判别力",
        "  三次几乎同时 Yes 或同时 No",
        "  如果能让 q 更分散，可能能突破 Recall 天花板",
    ], Inches(8.2), Inches(5.45), Inches(4.3), Inches(2.0), size=10.5)

    # ==================================================================
    # SLIDE 12: 样例与错例
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "10. 真实样例与错例分析")

    add_text(s, "▶ 两个正确样例（test 集 · E1 均正确判「无因果」）",
             Inches(0.5), Inches(1.2), Inches(12.33), Inches(0.4),
             size=13, bold=True, color=ACCENT1)
    add_table(s,
              ["#", "原文片段", "源→目标", "真值", "预测", "决策路径"],
              [["1", "The police source ... said the men drove a large 4×4 car into the store ...",
                "men→store", "无", "无", "Explorer 三次都答 No → q=0 → 直接过滤"],
               ["2", "An earthquake flattened seven villages and killed 10 people ...",
                "earthquake→killed", "无", "无", "三次都答 No → q=0 → 直接过滤"]],
              Inches(0.5), Inches(1.65), Inches(12.33), Inches(1.2))

    add_text(s, "▶ 五个典型错例（三个 FP + 两个 FN，覆盖主要失败模式）",
             Inches(0.5), Inches(3.0), Inches(12.33), Inches(0.4),
             size=13, bold=True, color=ACCENT2)
    add_table(s,
              ["#", "原文 / 源→目标", "真值", "预测", "错误类型", "根因"],
              [["F1", "arrested on suspicion of DUI (suspicion→arrested)",
                "无", "有", "FP", "Reasoner Causal Order / Implicit Connective 规则触发"],
               ["F2", "killing after high-speed chase (killing→chase)",
                "无", "有", "FP", "常识链式因果被误判：chase 发生在 killing 之前"],
               ["F3", "died when slipped and fell (slipped→died)",
                "无", "有", "FP", "Chain + Causal Order 规则同时触发"],
               ["F4", "20 year sentence for indecency (sentence→indecency)",
                "有", "无", "FN", "Causal Explorer 三次都答 No → q=0 被过滤"],
               ["F5", "killed ... as police fought battles (battles→fought)",
                "有", "无", "FN", "Causal Explorer 三次都答 No → q=0 被过滤"]],
              Inches(0.5), Inches(3.45), Inches(12.33), Inches(2.9))

    add_text(s, "▶ 错例模式总结",
             Inches(0.5), Inches(6.4), Inches(12.33), Inches(0.4),
             size=13, bold=True, color=ACCENT1)
    add_text(s, "FP 错例共同特征：Reasoner 规则过于宽松，常识时序先后被误判为因果。FN 错例共同特征：Causal Explorer 本身就没识别出真因果，三次都答 No。",
             Inches(0.5), Inches(6.8), Inches(12.33), Inches(0.6), size=11)

    # ==================================================================
    # SLIDE 13: 局限 + 改进 + 贡献
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_page_header(s, "11. 局限、改进方向、成员贡献")

    add_text(s, "▶ 局限与反思", Inches(0.5), Inches(1.2), Inches(5), Inches(0.4),
             size=14, bold=True, color=ACCENT1)
    add_bullets(s, [
        "① Causal Explorer 三次提示过于接近（causal relationship / causation / causality），三次几乎同时 Yes 或同时 No，计数 q 缺乏真正的判别力",
        "② Reasoner 8 条规则无加权投票，任意一条命中即判 Yes，常识先后（killing after chase）易被误判为因果",
        "③ Recall 最大瓶颈是 q=0 正例（test 上 32.7%），而非阈值高低本身——提高阈值只过滤 FP，对 FN 无帮助",
        "④ dev/test 指标差异大（E0 F1 dev=0.397 vs test=0.544），小样本 300 对方差影响大；dev 上还有 35 次 API 超时丢失正例",
        "⑤ 我们没有跑全量 dev(3840) / test(3440)，子集结果可能有偏",
    ], Inches(0.5), Inches(1.65), Inches(6.3), Inches(3.0), size=11)

    add_text(s, "▶ 未来改进方向", Inches(7.0), Inches(1.2), Inches(5.5), Inches(0.4),
             size=14, bold=True, color=ACCENT2)
    add_bullets(s, [
        "① 把三次计数扩展为 4-5 次不同提示变体，真正让 q 成为有判别力的指标",
        "② Reasoner 规则需要至少 2 条同时满足才判 Yes（降低 FP）",
        "③ 多 Reasoner 输出投票（temperature>0 多次采样），避免单条规则偶然命中",
        "④ 引入 few-shot 示例指导 Reasoner：「什么样的才算真因果」",
        "⑤ 把子集扩量到 dev 3840 / test 3440，提升统计显著性",
    ], Inches(7.0), Inches(1.65), Inches(5.3), Inches(3.0), size=11)

    add_text(s, "▶ 成员贡献", Inches(0.5), Inches(4.9), Inches(4), Inches(0.4),
             size=14, bold=True, color=ACCENT1)
    add_table(s,
              ["成员", "负责内容"],
              [
                  ["罗杨阳", "数据划分 / 分层抽样 / 统计 · E0 基线 · 评估脚本 + confusion matrix · 结果图表 · 报告撰写 + 第 6 节双口径审计"],
                  ["廖兴易", "LLM 调用层（并发 / 重试 / 磁盘缓存 / raw_responses 留档 / 自动计费）· E1/E2 完整流程 · 解析器重写（修复原仓库 core.py bug）· PPTX 制作"],
                  ["共同", "提示词逐字核对原仓库 agent1-3/prompt.py · 测试集冻结检查 · 错例人工分析 · README + contribution.md 撰写"],
              ],
              Inches(0.5), Inches(5.35), Inches(12.33), Inches(1.7))

    add_text(s, "谢谢聆听，欢迎提问 ｜ 所有 raw_responses + predictions + metrics 全量留档可追溯",
             Inches(0.5), Inches(7.1), Inches(12.33), Inches(0.4),
             size=14, bold=True, color=ACCENT1, align=PP_ALIGN.CENTER)

    # ====================================================================
    prs.save(str(OUT))
    print(f"OK -> {OUT}")
    print(f"   size = {OUT.stat().st_size:,} bytes")
    print(f"   slides = {len(prs.slides)}")


if __name__ == "__main__":
    main()
