"""Dr.ECI 复现报告（第八组）——生成 DOCX。"""
import json
import os
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt, Cm, RGBColor

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"


def set_run_font(run, size=12, bold=False, color=None, font_cn="微软雅黑", font_en="Times New Roman"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = font_en
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_cn)
    if color:
        run.font.color.rgb = RGBColor(*color)


def heading(doc, text, level=1):
    p = doc.add_heading(level=level)
    r = p.add_run(text)
    if level == 1:
        set_run_font(r, size=18, bold=True, color=(31, 78, 121))
    elif level == 2:
        set_run_font(r, size=15, bold=True, color=(31, 78, 121))
    else:
        set_run_font(r, size=13, bold=True, color=(31, 78, 121))
    return p


def para(doc, text, bold=False, size=12, indent=None):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Cm(indent)
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold)
    return p


def table(doc, headers, rows, col_widths=None, header_fill="D5E8F0"):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    # header
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(str(h))
        set_run_font(r, size=10, bold=True, color=(255, 255, 255))
        hdr[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), header_fill)
        hdr[i]._tc.get_or_add_tcPr().append(shd)
    # rows
    for ri, row in enumerate(rows, 1):
        cells = t.rows[ri].cells
        for ci, val in enumerate(row):
            cells[ci].text = ""
            p = cells[ci].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(str(val))
            set_run_font(r, size=10, bold=False)
    if col_widths:
        for ri in range(1 + len(rows)):
            for ci, w in enumerate(col_widths):
                t.rows[ri].cells[ci].width = Cm(w)
    return t


def section_cover(doc):
    for _ in range(4):
        doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("事件因果关系识别")
    set_run_font(r, size=26, bold=True, color=(31, 78, 121))
    title2 = doc.add_paragraph()
    title2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title2.add_run("Dr.ECI 算法复现实验报告")
    set_run_font(r, size=20, bold=True, color=(31, 78, 121))
    doc.add_paragraph()
    info = [
        ("课程", "机器智能课程设计 · NLP 方向"),
        ("所选论文", "Dr.ECI: Infusing Large Language Models with Causal Knowledge for Decomposed Reasoning in Event Causality Identification  (COLING 2025)"),
        ("小组", "第八组"),
        ("成员", "罗杨阳、廖兴易"),
        ("教师", "王邦"),
        ("日期", "2026.11"),
    ]
    for k, v in info:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rk = p.add_run(k + "：")
        set_run_font(rk, size=12, bold=True)
        rv = p.add_run(v)
        set_run_font(rv, size=12)
    doc.add_page_break()


def section_intro(doc):
    heading(doc, "1 背景与任务定义", 1)
    heading(doc, "1.1 事件因果关系识别", 2)
    para(doc, "事件因果关系识别（Event Causality Identification, ECI）回答一个具体问题：给定一段文本与其中已定位的两个事件，判断二者之间是否存在因果关系。与信息抽取只取出触发词、施事、受事不同，ECI 要回答的是「谁导致了谁」，这是构建事件图谱、故事理解、舆情诱因分析等下游应用的基础。", indent=0.74)
    para(doc, "本任务处理的是成对事件，识别的是文本中标注的因果关系——它是叙事中被作者明确/隐式表达的因果，不是干预实验证实的现实因果。两个事件是否共现、是否构成句子级显式或跨句隐式因果，都会影响判断。", indent=0.74)

    heading(doc, "1.2 论文：Dr.ECI", 2)
    para(doc, "Dr.ECI 将因果发现与推理拆成两个阶段，由四个协作 LLM Agent 完成。发现阶段包含 Causal Explorer 和 Mediator Detector，推理阶段包含 Direct Reasoner 与 Indirect Reasoner。其设计动机是：单纯的提示式问答难以显式建模中介事件（mediator）与多种因果模式（显式/隐式连接词、时序顺序、共指事件、链/碰撞/分叉等因果图结构），Dr.ECI 把这些结构编码进各 Agent 的提示词里。", indent=0.74)

    heading(doc, "1.3 本复现目标", 2)
    para(doc, "本实验在 EventStoryLine 上完整复现 E0（单轮直接提示）、E1（Dr.ECI 完整四智能体）、E2（只改一处：把 Mediator Detector 触发阈值从 q ≥ 1 提高到 q ≥ 2）三组实验，报告 P/R/F1、样本规模、耗时和费用，留档提示词、原始响应与解析记录，展示 2 个真实样例与 5 个错例，并分析与原论文结论的差异原因。", indent=0.74)


def section_method(doc):
    heading(doc, "2 方法原理", 1)
    heading(doc, "2.1 Causal Explorer", 2)
    para(doc, "以三次近乎相同的提示分别提问：Is there a causal relationship / causation / causality between source and target？每条回答格式化为 JSON {\"Answer\":\"Yes\"/\"No\"}。三次 Yes 的次数记为 q。原作者的观察是：三次问句覆盖了不同触发词的概率，q 越大样本越可能有因果，以此作为后续 Mediator Detector 的门控。", indent=0.74)

    heading(doc, "2.2 Mediator Detector", 2)
    para(doc, "对 q ≥ 阈值（E1 用 1，E2 用 2）的样本，再用单轮提示让 LLM 先找与源事件相关的实体/事件、再找与目标事件相关的实体/事件、再找出两者同时相关的实体，最后以 JSON 列表输出「同时相关的实体」，若无则回答 {\"No\"}。这些同时相关实体即候选中介 Z。", indent=0.74)

    heading(doc, "2.3 Reasoner（8 条因果规则）", 2)
    para(doc, "把原文、源事件、目标事件与候选 Z 交给 Reasoner，逐条检查 8 条因果规则：(1) 显式因果连接词 cause/lead/due to 等；(2) 隐式连接词 spark/aggravate/trigger 等；(3) 常识时序顺序；(4) X 的共指事件与 Y 有因果；(5) Y 的共指事件与 X 有因果；(6) 链结构 X→Z→Y；(7) 碰撞结构 X→Z←Y；(8) 分叉结构 Z→X, Z→Y。满足任意一条即判 Yes；全部不满足判 No。Reasoner 的输出是每条规则一个 JSON 对象，最终答案取「任一规则满足」为有因果。", indent=0.74)

    heading(doc, "2.4 E2：只改一处", 2)
    para(doc, "阈值从 q ≥ 1 改为 q ≥ 2。它直接影响 Mediator Detector 的触发率：只有三次提问中至少两次判 Yes 的样本才会进入后续的中介查找与规则推理。原论文的消融分析显示阈值越高 Recall 会上升，这一现象在本复现中没有复现，在第 6 节分析原因。", indent=0.74)


def section_setup(doc):
    heading(doc, "3 实验设置", 1)

    heading(doc, "3.1 环境", 2)
    table(doc,
          ["项", "值"],
          [
              ["操作系统", "Windows 11 / PowerShell 5"],
              ["Python", "3.12.7 (Anaconda)"],
              ["关键依赖", "openai 3.37.0, httpx, pyyaml, pandas, matplotlib, python-docx, python-pptx"],
              ["GPU", "无；所有推理走 DeepSeek API"],
              ["项目路径", "DrECI_repro/（独立工程，不改动原仓库）"],
          ],
          col_widths=[4, 12])

    heading(doc, "3.2 与原论文/原仓库的差异", 2)
    table(doc,
          ["项", "原论文/原仓库", "本复现", "原因"],
          [
              ["底层模型", "DeepSeek (deepseek-chat)", "deepseek-flash (DeepSeek-V4.1-Flash)", "deepseek-chat 已下线；官方模型列表中只有 deepseek-flash / deepseek-v4-pro"],
              ["推理档位", "无（常规生成）", "reasoning_effort = low", "deepseek-flash 默认 high，隐藏推理可达 7k+ token，会挤占输出预算"],
              ["温度", "1.0", "0.0", "便于三方对比可复现"],
              ["max_tokens", "8192", "16384", "reasoner 的隐藏推理计入输出预算，必须留足空间"],
              ["规模", "全量 ESL + 其他数据集", "dev/test 各固定 300 对分层子集", "课程设计要求先跑通再扩量；所有子集与划分完全固定"],
              ["解析", "只匹配 {\"Answer\":\"No\"}", "分层解析 + 解析失败单独计数", "原实现会误判 reasoner 的规则 JSON 输出"],
              ["评价口径", "只在过筛样本上算 P/R/F", "在全集上算（被过滤记为无因果）", "原口径偏乐观；课程要求如实报告"],
              ["实验预算", "未说明", "E0 ¥0.19/¥0.18；E1 ¥1.84/¥2.07；E2 缓存命中 ¥0", "报告需包含费用"],
          ],
          col_widths=[2.5, 4.5, 4, 4])

    heading(doc, "3.3 数据划分", 2)
    para(doc, "ESL (EventStoryLine) 原始数据共 17,998 事件对、233 篇文档，正例 3,184（17.7%）。按文档级随机划分（seed=42），train/dev/test 比例 60%/20%/20%，避免同文档泄漏。三个集合的正例比例与原始分布接近，文档重叠为 0。所有子集、阈值、随机种子、模型参数在 E0/E1/E2 之间完全一致；测试集冻结后只评一次。", indent=0.74)
    table(doc,
          ["集合", "事件对", "文档", "正例", "正例比例"],
          [
              ["train", "10,718", "136", "1,912", "17.84%"],
              ["dev", "3,840", "51", "636", "16.56%"],
              ["dev 子集", "300", "43", "50", "16.67%"],
              ["test", "3,440", "46", "636", "18.49%"],
              ["test 子集", "300", "45", "55", "18.33%"],
          ],
          col_widths=[2.5, 3, 2.2, 2.2, 2.5])
    para(doc, "ESL 中所有事件对均来自同一句子，因此句内指标等于总体指标；跨句项写「不适用」。", indent=0.74)

    heading(doc, "3.4 E0/E1/E2 定义", 2)
    table(doc,
          ["实验", "改动", "说明"],
          [
              ["E0", "匹配基线", "单轮直接提示：system = Causal Explorer 的 system prompt，user = causal(...) + vanilla_formal；是 Dr.ECI 可比较的最公平基线"],
              ["E1", "完整方法", "Causal Explorer 三次提问（causal/causation/causality）→ q 计数 → q ≥ 1 触发 Mediator Detector → 抽取 Answer to subquestion 4 作为 Z → Reasoner 8 条规则 → 解析最终答案；q < 1 的样本直接判无因果"],
              ["E2", "只改一处", "将 Mediator Detector 触发阈值从 q ≥ 1 改为 q ≥ 2，其余与 E1 完全相同"],
          ],
          col_widths=[1.5, 3, 8])


def section_results(doc):
    heading(doc, "4 结果", 1)

    heading(doc, "4.1 结果汇总（test 集，冻结后一次性独立评估）", 2)
    table(doc,
          ["实验", "改动", "P", "R", "F1", "Acc", "TP", "FP", "FN", "TN", "被过滤", "耗时", "费用"],
          [
              ["E0", "匹配基线", "0.4857", "0.6182", "0.5440", "0.8100", "34", "36", "21", "209", "0", "82s", "¥0.18"],
              ["E1", "完整方法 q≥1", "0.4032", "0.4545", "0.4274", "0.7767", "25", "37", "30", "208", "213", "744s", "¥2.07"],
              ["E2", "阈值 q≥2", "0.4464", "0.4545", "0.4505", "0.7967", "25", "31", "30", "214", "230", "3.7s*", "¥0.00**"],
          ],
          col_widths=[1.5, 3, 0.9, 0.9, 0.9, 0.9, 0.7, 0.7, 0.7, 0.7, 1.4, 1.1, 1])
    para(doc, "* E2 耗时仅 3.7s 是因为其过筛样本完全包含于 E1 过筛样本，全部命中磁盘缓存。", indent=0.74)
    para(doc, "** E2 测试集中 Mediator Detector 与 Reasoner 的调用全部命中缓存，因此费用为 ¥0。", indent=0.74)

    heading(doc, "4.2 dev 集结果（用于选阈值）", 2)
    table(doc,
          ["实验", "P", "R", "F1", "Acc", "TP", "FP", "FN", "TN", "被过滤", "请求失败", "解析失败"],
          [
              ["E0", "0.3485", "0.4600", "0.3966", "0.7667", "23", "43", "27", "207", "0", "0", "0"],
              ["E1", "0.2778", "0.2000", "0.2326", "0.7800", "10", "26", "40", "224", "225", "35", "3"],
              ["E2", "0.2333", "0.1400", "0.1750", "0.7800", "7", "23", "43", "227", "245", "35", "2"],
          ],
          col_widths=[1.5, 0.9, 0.9, 0.9, 0.9, 0.7, 0.7, 0.7, 0.7, 1.4, 1.1, 1.1])

    heading(doc, "4.3 关键观察", 2)
    items = [
        "dev 上 E1/E2 的 Recall 比 E0 显著低（E1 Recall 0.20 vs E0 0.46），主要因为 q < 1 的正例被直接过滤；E0 对这些样本一律跑了完整 LLM 调用。",
        "test 上三者 Recall 接近（E0 0.62、E1/E2 均 0.45），说明 test 子集里的正例更容易被 Causal Explorer 三次均判 Yes，从而进入后续 Mediator + Reasoner。",
        "E2 比 E1 少了 17 个样本进入 Mediator Detector（230 vs 213），但 FP 降了 6（31 vs 37），因此 Precision 提升（0.446 vs 0.403）而 Recall 持平，F1 微升。这与原论文「阈值越高 Recall 越高」的观察相反——test 上 q≥2 没有进一步过滤更多正例。",
        "dev 上 E1/E2 各有 35 次 API 请求失败（DeepSeek 在 reasoner 长提示 + 长推理下偶发超时），test 上完全没有，说明随机波动会显著影响小样本指标。",
        "解析失败总体很少（dev 2–3 条，test 0–1 条），说明分层解析器能正确处理 8 条规则的 JSON 输出。",
    ]
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(it)
        set_run_font(r, size=11)


def section_cases(doc):
    heading(doc, "5 真实样例与错例（test 集 · E1）", 1)
    para(doc, "以下样例均来自 test 冻结评估的真实运行，非手工构造。为节省篇幅展示 E1 的正确与错误；同一条样本在 E2 上的结果可能不同。", indent=0.74)

    heading(doc, "5.1 两个正确样例", 2)
    table(doc,
          ["#", "原文 / 源事件 / 目标事件", "真值", "预测", "决策路径"],
          [
              ["1", "原文：The police source ... said the men drove a large 4×4 car into the store ... and grabbed jewellery ...\n源事件：estimated\n目标事件：said", "无因果", "无因果", "q=0 → 直接过滤"],
              ["2", "原文：An earthquake measuring ... shook a sparsely populated area ... flattening seven villages and killing 10 people, officials said .\n源事件：said\n目标事件：earthquake", "无因果", "无因果", "q=0 → 直接过滤"],
          ],
          col_widths=[0.6, 9, 1, 1, 3])

    heading(doc, "5.2 五个错例", 2)
    table(doc,
          ["#", "原文 / 源事件 / 目标事件", "真值", "预测", "决策路径", "分析"],
          [
              ["F1", "原文：Vincent Jackson was arrested ... on suspicion of driving under the influence ...\n源事件：on suspicion\n目标事件：arrested", "无因果", "有因果", "q=3, Z=None → Reasoner 触发", "Reasoner 规则 3（Causal Order）或 2（Implicit Causation Words）被误触发，driving under influence 与 arrested 之间确实有常识先后关系，但数据集标注为无因果"],
              ["F2", "原文：... was arrested after a high-speed chase ... authorities said .\n源事件：killing\n目标事件：chase", "无因果", "有因果", "q=3, Z=None → Reasoner 触发", "句子里 killing → chase 是合理的链式常识，但作者未标注为因果边"],
              ["F3", "原文：... died when he slipped and fell around 200ft from a ridge ...\n源事件：slipped\n目标事件：died", "无因果", "有因果", "q=3, Z=None → Reasoner 触发", "slipped → fell → died 是典型链式因果，Reasoner 的 Chain 或 Causal Order 规则触发；但该标注来自另一条独立叙事"],
              ["F4", "原文：... new 20 year sentence .\n源事件：sentence\n目标事件：indecency", "有因果", "无因果", "q=0 → 直接过滤", "这是标注为有因果的样本，但 Causal Explorer 的三次提问都没看出因果，q=0 被直接过滤；Recall 损失的典型原因"],
              ["F5", "原文：... a bank in Greece killed ... as police fought pitched battles ...\n源事件：battles\n目标事件：fought", "有因果", "无因果", "q=0 → 直接过滤", "标注里 fought / battles 是同一事件的不同描述，但 Causal Explorer 三次都答 No"],
          ],
          col_widths=[0.6, 7.5, 0.8, 0.8, 2.5, 4])


def section_limitations(doc):
    heading(doc, "6 局限与分析", 1)
    heading(doc, "6.1 双口径审计：为什么全集 Recall 持平而子集 Recall 上升", 2)
    para(doc, "本复现对评估口径做了双口径审计——全集（所有 300 对）vs 过筛子集（进入 Mediator + Reasoner 的样本）。test 集结果如下：", indent=0.74)
    table(doc,
          ["实验", "口径", "样本", "正例", "TP", "FN", "Recall", "F1"],
          [
              ["E1 (q≥1)", "全集", "300", "55", "25", "30", "0.4545", "0.4274"],
              ["E1 (q≥1)", "过筛子集", "87", "37", "25", "12", "0.6757", "0.5051"],
              ["E2 (q≥2)", "全集", "300", "55", "25", "30", "0.4545", "0.4505"],
              ["E2 (q≥2)", "过筛子集", "70", "32", "25", "7", "0.7812", "0.5682"],
              ["q≥3 层", "explorer 三次全 Yes", "54", "27", "24", "3", "0.8889", "0.6234"],
          ],
          col_widths=[2.5, 2.5, 1.5, 1.2, 0.8, 0.8, 1.5, 1.5])
    para(doc, "关键发现：", indent=0.74)
    items = [
        "在过筛子集上，阈值越高 Recall 确实越高（E1 子集 0.676 → E2 子集 0.781 → q≥3 层 0.889），与原论文 README 的观察一致。",
        "但全集 Recall 持平（E1=0.4545, E2=0.4545），因为真正限制 Recall 的不是阈值高低，而是 q=0 的正例数量——test 上 55 个正例里有 18 个 q=0（占 32.7%），被 Causal Explorer 三次都判 No 直接过滤。",
        "原论文报告的 Analysis.png 图实际上只看了过筛子集，没有显式报告全集口径。这是本复现与原论文结论最关键的差异点。",
        "E2 全集 F1 反而略高于 E1（0.450 vs 0.427），因为阈值提高过滤了更多 FP（E1 FP=37 → E2 FP=31），而正例损失只有 0 个（E2 没多过滤正例）。",
    ]
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(it)
        set_run_font(r, size=11)

    heading(doc, "6.2 原仓库 core.py 的解析 Bug", 2)
    para(doc, "原仓库 agent3/core.py 中的 contains_yes_answer 函数名意图是「检测 Yes 答案」，但实际代码匹配的是 {\"Answer\":\"No\"}，然后整个 reasoner 评估逻辑用 if total_yes_count < 1 来判断正例——这意味着原作者根本没有正确解析 Reasoner 的 8 条规则 JSON 输出（Reasoner 不输出 {\"Answer\":\"Yes\"/\"No\"}，而是每条规则一个 JSON 对象）。本复现重写了解析器 parse.py，分层匹配规则 JSON 中的 No/非 No 值。这也是原论文实验结果可能存在偏差的原因之一。", indent=0.74)

    heading(doc, "6.3 Dev vs Test 指标差异", 2)
    para(doc, "dev 上 E0 F1=0.397，test 上 E0 F1=0.544，差距 0.15。可能原因：(a) test 子集里的正例本身更容易被 Causal Explorer 识别；(b) dev 上有 35 次 API 失败直接损失正例，test 上 0 次，使得 test 更乐观。小样本（300 对）本身的方差也不可忽视。", indent=0.74)

    heading(doc, "6.4 指标上限与设计取舍", 2)
    items = [
        "E0 是 vanilla 提示，本身没有引入领域知识或示例，在小样本上可能已经接近「无检索、无示例」的合理上限；原论文报告的 Dr.ECI 在全量 ESL 上 F1 也未显著超过 E0 风格的基线。",
        "Causal Explorer 的三次提问存在冗余：三次 Yes 的计数 q 是后续 Mediator Detector 的唯一门控，一旦 q=0 直接走过滤。三次提问覆盖的触发词（causal relationship / causation / causality）过于接近，可能导致三次几乎总是同时 Yes 或同时 No。",
        "Reasoner 的 8 条规则没有加权：只要命中任意一条就判 Yes，容易把常识先后当成标注因果（见 F1/F2/F3）。如果改成「至少命中两条」能显著降低 FP，但会进一步损失 Recall。",
    ]
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(it)
        set_run_font(r, size=11)

    heading(doc, "6.5 未来改进方向", 2)
    items = [
        "把 q 的三次计数扩展为 4–5 次不同的提示变体，增加 Yes 的判别力。",
        "引入检索示例（few-shot）来指导三次提问的判据，降低常识先后被误判为因果的概率。",
        "用多个 Reasoner 输出做投票，避免单条规则的偶然命中。",
    ]
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(it)
        set_run_font(r, size=11)


def section_contributions(doc):
    heading(doc, "7 成员贡献", 1)
    table(doc,
          ["成员", "负责内容"],
          [
              ["罗杨阳", "数据划分与统计（文档级 split、固定子集抽样）、E0 基线实现、评估脚本、结果图表、报告撰写"],
              ["廖兴易", "LLM 调用层（并发 / 重试 / 缓存 / 留档）、E1/E2 流程实现、提示词核对、解析器、PPTX 汇报"],
          ],
          col_widths=[2.5, 13])
    para(doc, "两人共同完成：提示词逐字核对待原仓库、测试集冻结一致性检查、错例分析与定稿、贡献说明。", indent=0.74)


def main():
    doc = Document()

    # 默认字体配置
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

    section_cover(doc)
    section_intro(doc)
    section_method(doc)
    section_setup(doc)
    section_results(doc)
    section_cases(doc)
    section_limitations(doc)
    section_contributions(doc)

    out = ROOT / "第八组_DrECI_复现报告.docx"
    doc.save(str(out))
    print("OK ->", out, "size =", out.stat().st_size)


if __name__ == "__main__":
    main()
