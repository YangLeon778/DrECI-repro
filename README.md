# Dr.ECI 复现（第八组）

复现论文：**Dr.ECI: Infusing Large Language Models with Causal Knowledge for Decomposed Reasoning in Event Causality Identification**（COLING 2025）

本仓库为华中科技大学电子信息与通信学院《机器智能课程设计》第 4 个项目（第八组）的算法复现工作，作者：罗杨阳、廖兴易。

本目录是**独立复现工程**，不改动原仓库。原仓库的代理硬编码、API key 占位、`[:2]` 调试切片、路径硬编码、无并发/无重试/无留档等问题已在本工程中重写解决。

---

## 1. 任务设定

- 数据集：**ESL（EventStoryLine）**
  - 数据获取：克隆原论文官方仓库 <https://github.com/DMIRLAB-Group/Dr.ECI>，使用其中的
    `data/ESC/intra_sent_causality.json`（ESL 语料原始出处为 Caselli & Vossen, 2017）
  - 本工程默认按相对路径读取，即把官方仓库放在本工程同级目录、保持文件夹名为 `Dr.ECI`；
    若放在别处，改 `configs/default.yaml` 里的 `data.esl_path` 即可
  - 17,998 个事件对，233 篇文档；正例（`bi_causal_label=1`）3,184（17.7%），负例 14,814
  - 二分类：**有/无因果关系**（遵循 Dr.ECI 的任务设定，不改成 CAUSE/EFFECT 三分类）
- 指标：Precision / Recall / F1 + Accuracy；另报句内/跨句分项、失败计数、规模、耗时、费用

## 2. 流程（与原仓库一致）

```
E0：单轮直接提示
  system = Causal Explorer 的 system prompt
  user   = causal(...) + vanilla_formal
  -> 解析 {"Answer":"Yes"/"No"}

E1：Dr.ECI 完整四智能体
  Causal Explorer：causal / causation / causality 三次提问 -> q = Yes 次数
  q >= 1 才进入 Mediator Detector（否则直接判“无因果”，与原仓库 choose.py 一致）
  Mediator Detector -> 抽取 “Answer to subquestion 4:” 作为 Z
  Reasoner（8 条因果规则）-> 解析最终答案
  q < 1 的样本被过滤，直接记为“无因果”

E2：消融，只改一处
  把过滤阈值 q >= 1 改为 q >= 2，其余与 E1 完全相同
```

所有提示词**逐字复制**自 `Dr.ECI/agent1/prompt.py`、`agent2/prompt.py`、`agent3/prompt.py`，见 `code/prompts.py`。

## 3. 目录

```
code/
  prepare_data.py   文档级划分 + 固定子集抽样 + 统计
  prompts.py        提示词（原仓库逐字复制）
  llm.py            API 封装：并发/重试/缓存/原始响应留档/计费
  parse.py          分层解析（Answer JSON / Rule JSON / 兜底），解析失败单独计数
  pipeline.py       跑 E0 / E1 / E2
  evaluate.py       P/R/F1 + 分项 + 失败计数 + 汇总 comparison.csv
  make_figures.py   结果柱状图 / 混淆矩阵
  extract_cases.py  抽取正确样例与错例
configs/default.yaml
data_info/          split.json、subset_dev.jsonl、subset_test.jsonl、statistics.json
results/
  E0/ E1/ E2/       每实验的 metrics_test.json、meta_test.json、cases_test.md
  comparison.csv    三实验汇总
```

> 体积较大的逐条预测（`predictions_*.{csv,jsonl}`）、原始响应（`raw_responses.jsonl`，约 10 MB）
> 与结果图（`figures/`）未纳入仓库，可按第 4 节命令在本地复跑生成。

## 4. 运行

```powershell
$env:DEEPSEEK_API_KEY='<your key>'      # 只走环境变量，不写入任何文件

python code/prepare_data.py             # 生成划分与固定子集
python code/pipeline.py --exp E0 --split dev --workers 8
python code/pipeline.py --exp E1 --split dev --workers 8
python code/pipeline.py --exp E2 --split dev --workers 8
python code/evaluate.py --all
python code/make_figures.py             # 生成 results/figures/ 结果图
python code/extract_cases.py            # 抽取正确样例与错例
```

- `--limit N` 可只跑前 N 条（冒烟测试）；`--resume` 可断点续跑。
- 相同请求会命中 `results/cache/`，**重复运行不重复计费**。

## 5. 数据划分（E0/E1/E2 共用）

- **文档级**划分，避免同文档事件对泄漏：`seed=42`，train/dev/test = 60%/20%/20%
  - train 10,718 对 / 136 文档（正例 1,912）
  - dev 3,840 对 / 51 文档（正例 636）
  - test 3,440 对 / 46 文档（正例 636）
  - 文档重叠检查：train-dev 0、train-test 0、dev-test 0
- **固定子集**：从 dev / test 中各分层抽 300 对（`subset_seed=2026`）
  - dev 300 对（正例 50，16.7%）
  - test 300 对（正例 55，18.3%）
- 开发集用于确定 E1/E2 的阈值取舍；**测试集冻结，只评一次**。
- 重复事件对检查：子集内重复组 0。

> 说明：ESL 的事件对全部来自同一句子，因此分项指标只有**句内**，跨句项为 0（并非省略，见 `data_info/statistics.json`）。

## 6. 与原论文/原仓库的差异（必须在报告中声明）

| 项 | 原论文/原仓库 | 本复现 | 原因 |
|---|---|---|---|
| 模型 | DeepSeek（`deepseek-chat`） | `deepseek-flash`（DeepSeek-V4.1-Flash） | `deepseek-chat` 已下线 |
| 推理档位 | 无（常规生成） | `reasoning_effort="low"` | 该模型默认 high，隐藏推理可达 7k+ token，会挤占输出预算 |
| 温度 | 1.0 | 0.0 | 便于三方对比可复现 |
| max_tokens | 8192 | 16384 | 推理 token 计入输出预算，防止内容被截断 |
| 规模 | 全量 ESL | dev/test 各 300 对固定子集 | 先跑通再扩量；划分/种子/子集完全固定 |
| q 阈值 | `q>=1` | E1 保持 `q>=1`，E2 改为 `q>=2` | E2 为“只改一处”的消融 |
| 解析 | 只匹配 `{"Answer":"No"}` | 分层解析 + 解析失败单独计数 | 原实现会误判规则输出 |
| 评价范围 | 只在过筛样本上算 P/R/F | 在全集上算 P/R/F（被过滤记为“无因果”） | 原实现口径偏乐观 |

## 7. 结果

见 `results/comparison.csv` 与 `results/E*/metrics_*.json`。

## 8. 环境

- Windows 11 / PowerShell，Python 3.12.7
- `openai 3.37.0`、`httpx`、`pyyaml`、`pandas`
- 无需 GPU；全部推理走 DeepSeek API
