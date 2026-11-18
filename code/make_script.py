"""生成汇报讲稿（逐页讲稿，每页标注时间建议）。"""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "第八组_DrECI_汇报讲稿.docx"

doc = Document()
# 页面设置：A4，边距 2cm
section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.left_margin = Cm(2.2)
section.right_margin = Cm(2.2)
section.top_margin = Cm(2.2)
section.bottom_margin = Cm(2.2)


def set_font(run, size=11, bold=False, color=None):
    run.font.size = Pt(size); run.font.bold = bold
    run.font.name = "微软雅黑"
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    if color:
        run.font.color.rgb = color


from docx.oxml.ns import qn


def page_header(slide_num, title, time_hint):
    p = doc.add_paragraph()
    run = p.add_run(f"第 {slide_num} 页：{title}  （建议 {time_hint}）")
    set_font(run, size=13, bold=True, color=RGBColor(0x44, 0x72, 0xC4))


def talk(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_font(run, size=11)
    p.paragraph_format.line_spacing = 1.6
    p.paragraph_format.first_line_indent = Cm(0.6)


def section_h(text):
    p = doc.add_paragraph()
    run = p.add_run(f"【{text}】")
    set_font(run, size=11, bold=True, color=RGBColor(0xED, 0x7D, 0x31))


# ============================================================
# 封面
# ============================================================
page_header(1, "封面", "30 秒")
talk("各位老师、同学大家好，我们是第八组，今天给大家带来的汇报是 Dr.ECI 算法的复现。Dr.ECI 是 COLING 2025 发表的一篇关于事件因果关系识别的论文，我们用 deepseek-flash 模型重新实现了它的四智能体分解推理框架，并在 ESL 数据集上做了 E0、E1、E2 三组对照实验。下面开始我们的汇报。")

# ============================================================
# 目录
# ============================================================
page_header(2, "汇报目录", "20 秒")
talk("今天的汇报分八个部分：先讲任务和论文选定，然后讲方法原理、实验设置，接着是 dev 和 test 两组结果，重点是第六页的双口径审计——这是我们复现过程中最有价值的发现，最后是样例分析、局限和贡献。")

# ============================================================
# 任务与论文选定
# ============================================================
page_header(3, "任务与论文选定", "1 分钟")
section_h("ECI 任务定义")
talk("事件因果关系识别，英文 Event Causality Identification，简称 ECI。给定一段自然语言文本和文本里已经定位好的两个事件，判断它们之间是否存在因果关系。这是一个二分类任务。难点在于因果关系可能是显式的，比如 because、due to 这些连接词，也可能是隐式的，需要常识推理和时序判断。")
section_h("为什么选 Dr.ECI 这篇论文")
talk("我们选这篇论文有几个原因：第一，它的架构很清晰——四个智能体协作，从发现到推理分两阶段，prompt 是开源的，复现可行性高；第二，它有 ESL 这个公开数据集；第三，它的核心设计决策——用三次不同提问的 Yes 次数 q 来做过滤阈值——让我们可以很自然地做消融实验。")
section_h("四智能体流程图讲解")
talk("这张图是 Dr.ECI 的核心流水线。最左边是 Causal Explorer，它对每个事件对问三次不同的问题——有没有因果关系、causation、causality——每次回答 Yes 或 No。三次 Yes 的次数记为 q。q=0 的样本直接判无因果，跳过后面所有步骤。q 大于等于阈值的才进入 Mediator Detector 找中介实体 Z，然后 Reasoner 用八条因果规则逐一检查原文加事件加 Z。任何一条规则命中就判 Yes。")

# ============================================================
# 方法原理
# ============================================================
page_header(4, "方法原理（四个智能体逐一拆解）", "2 分钟")
section_h("Causal Explorer")
talk("三次提问的设计意图是用措辞变体来测 LLM 对同一事件对因果性判断的稳定性。三次都答 Yes 的我们置信度更高。三次 No 直接过滤节省后续开销。原论文没说为什么选这三个词，我们也保持一致不改 prompt。")
section_h("Mediator Detector")
talk("四步调用：先让 LLM 找源事件相关的实体，再找目标事件相关的，然后找和两者都相关的，最后选最可能的中介 Z。这个 Z 是 Reasoner 的输入。如果找不到中介怎么办？原仓库里没说，我们观察到 LLM 有时候会硬编一个，有时候输出空。")
section_h("Reasoner 八条规则")
talk("这八条规则是 Dr.ECI 的核心贡献：显式因果连接词、隐式因果连接词、时序顺序、共指、因果链、碰撞、分叉，还有一个综合判断。任意一条命中就判 Yes。这个设计的好处是让 LLM 的判断有了可解释的依据；坏处是没有加权，一条偶然命中就会 FP。")
section_h("E0 是什么")
talk("E0 是我们的匹配基线——就是跳过上面全套，直接让 LLM 单轮回答这个事件对有没有因果。这其实是很多 ECI baseline 的做法，也让我们能对比 Dr.ECI 全套到底值不值。")

# ============================================================
# 实验设置
# ============================================================
page_header(5, "实验设置", "1.5 分钟")
section_h("数据划分")
talk("数据集是 ESL v2.0，233 篇文档，17,998 对事件。我们用文档级 seed=42 划分，保证 train/dev/test 文档完全不重叠——这是防止数据泄露的基本操作。因为跑 17,998 对太贵，我们从每个集合里分层抽了 300 对（正例保持比例），作为快速评估子集。test 集一旦选定就冻结了，只评一次——这是课程设计的学术规范，防止调参到测试集上。")
section_h("LLM 配置与工程实现")
talk("底层模型是 deepseek-flash。原论文用的 deepseek-chat 2025 年已经下线了。这个模型有个坑——它会做隐藏推理，reasoning_effort 默认 high 会生成 7000+ token 的隐藏推理，挤占输出预算，导致 Reasoner 被截断。所以我们必须设成 low，max_tokens 给到 16384。另外我们实现了并发 8 路、SHA256 磁盘缓存、raw_responses.jsonl 全量留档、自动计费——这些都是让复现可追溯可复算的工程基础设施。")
section_h("三组对照设计")
talk("E0 是基线，E1 是完整 Dr.ECI 流程 q≥1，E2 只改阈值 q≥2。E2 的设计意图是隔离「阈值高低」这一个变量的影响。")

# ============================================================
# dev 结果
# ============================================================
page_header(6, "结果一：dev 集（阈值选择）", "1.5 分钟")
section_h("dev 集指标表讲解")
talk("dev 集 300 对，正例 50。E0 F1=0.397，E1=0.233，E2=0.175。Dr.ECI 全套方法在 dev 上 F1 反而比直接提示低！这让我们一开始很困惑。")
section_h("dev 上的问题")
talk("两个原因叠加：第一，q=0 的正例被 Explorer 三次都答 No 直接过滤掉了，这是 Recall 暴跌的主因；第二，dev 上还发生了 35 次 API 超时——底层网络不稳定，丢失了不少正例。")
section_h("选阈值决策")
talk("选 E1(q≥1) 为完整方法——虽然 Recall 只有 0.20，但比 E2 的 0.14 高。E2 作为只改阈值的消融保留着，看 test 上会不会有不同表现。")

# ============================================================
# test 结果
# ============================================================
page_header(7, "结果二：test 集（冻结后独立评估）", "1.5 分钟")
section_h("test 集指标表讲解")
talk("test 集 300 对，正例 55。E0 F1=0.544 依然最高。E1=0.427，E2=0.450。这里有一个关键现象：E1 和 E2 的 Recall 完全一样——都是 0.4545，TP 都是 25。这跟我们在 dev 上看到的「阈值越高 Recall 越低」完全不同。")
section_h("test 上的观察")
talk("E2 的 Precision 比 E1 高（0.446 vs 0.403），FP 从 37 降到 31。这意味着阈值从 q≥1 提高到 q≥2，过滤掉了一些 FP，但没多过滤任何正例。所以 E2 的 F1 反而比 E1 高。")
section_h("为什么和原论文 README 的结论方向相反")
talk("原论文 README 说「q 越大 Recall 越高」——但我们全集口径看到的是完全不同的图景。这就是第六页双口径审计要回答的问题。另外注意 cost：E0 只花了 ¥0.18，E1 花了 ¥2.07，E2 因为全部缓存命中花了 ¥0。")

# ============================================================
# 双口径审计（关键页）
# ============================================================
page_header(8, "双口径审计：为什么我们和原论文结论「看起来相反」", "2 分钟 · 重点页")
section_h("核心发现（读表格）")
talk("看这张表。第一行 E1 全集 Recall=0.4545；第二行 E1 过筛子集 Recall=0.6757。E2 全集 Recall 还是 0.4545，但过筛子集涨到 0.7812。最下面 q≥3 层——Explorer 三次全答 Yes 的那些样本——Recall 高达 0.889。所以：")
talk("结论一：在过筛子集内，阈值越高 Recall 越高 ✓ ✓ ✓——这和原论文 README 的观察完全一致。")
talk("结论二：但全集 Recall 是持平的——E1=0.4545，E2=0.4545。为什么？")
section_h("真正限制全集 Recall 的元凶")
talk("因为 test 集 55 个正例里，有 18 个（占 32.7%）被 Causal Explorer 三次都答 No，q=0 直接过滤了！这些正例不管阈值设成 q≥1 还是 q≥2，都进不了 Mediator 和 Reasoner。所以提高阈值不会让 Recall 掉——本来就没进过筛子集的那些正例，阈值提高后还是不会进。但阈值提高能过滤更多 FP，因为那些 FP 也被 Explorer 三次都答 No 了或者只答了一次 Yes。")
section_h("原仓库 core.py 的解析 Bug（额外发现）")
talk("还有一个意外发现：原仓库 agent3/core.py 里的 contains_yes_answer 函数——名字叫「检测 Yes 答案」，实际正则匹配的是 {\"Answer\":\"No\"}！但更致命的是，Reasoner 根本不输出 Yes/No，它输出 8 条规则的 JSON 数组。也就是说原作者根本没有正确解析 Reasoner 的输出——这也是我们担心原论文实验结果的原因之一。我们自己重写了 parse.py 来正确分层解析规则 JSON。")

# ============================================================
# 样例与错例
# ============================================================
page_header(9, "真实样例与错例分析", "1 分钟")
section_h("正确样例")
talk("两个正确样例都是 E1 正确判为「无因果」。它们的共同模式是：Causal Explorer 三次都答 No，q=0，直接过滤。这说明 Explorer 对容易判的负例还是挺有效的。")
section_h("错例模式 F1/F2/F3（FP）")
talk("F1：\"arrested on suspicion of DUI\"——Reasoner 的 Causal Order 或 Implicit Connective 规则触发了，虽然 suspicion 到 arrested 之间并没有标注的因果。F2：\"killing after high-speed chase\"——chase 在 killing 之前发生，被常识链式因果误判。F3：\"died when slipped and fell\"——slipped→died 被 Chain 规则触发了。这三个都是 Reasoner 规则过于宽松导致的 FP。")
section_h("错例模式 F4/F5（FN）")
talk("F4：\"20 year sentence for indecency\"——标注有因果，但 Explorer 三次都答 No。F5 也是同样模式。这说明 Causal Explorer 本身就漏检了不少真因果——这也是 32.7% 正例被 q=0 过滤的直接来源。")

# ============================================================
# 局限 + 贡献 + 致谢
# ============================================================
page_header(10, "局限、改进方向、成员贡献 + 致谢", "1 分钟")
section_h("局限")
talk("局限有四个。第一，三次提问过于接近——causal relationship / causation / causality——三次几乎总是同时 Yes 或同时 No，计数 q 没有真正起到区分作用。第二，Reasoner 八条规则没有加权投票，任意一条命中即判 Yes，常识先后容易误触发。第三，Recall 的最大瓶颈是 q=0 正例（32.7%），不是阈值高低。第四，dev 和 test 指标差异大，dev 上还发生了 35 次 API 超时，小样本方差显著。")
section_h("改进方向")
talk("未来改进：把三次扩展到 4-5 次不同提示变体增加判别力；Reasoner 规则需要至少两条同时触发才判 Yes；多 Reasoner 输出投票；引入 few-shot 示例指导；把子集扩量到 dev 3840 / test 3440。")
section_h("成员贡献")
talk("罗杨阳负责数据划分、E0 基线、评估脚本、结果图表、报告撰写和双口径审计。廖兴易负责 LLM 调用层（并发、重试、缓存、留档、计费）、E1/E2 流程、解析器重写、PPTX 制作。两人共同核对 prompt、冻结测试集、人工分析错例、写 README 和 contribution.md。")
section_h("致谢")
talk("以上就是我们的全部汇报，代码已开源在 GitHub，所有 raw responses、predictions、metrics 全量留档可追溯。谢谢王邦老师的指导，欢迎大家提问！")

# ============================================================
doc.save(str(OUT))
print(f"OK -> {OUT}")
print(f"   size = {OUT.stat().st_size:,} bytes")
