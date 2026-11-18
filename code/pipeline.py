"""复现主流程：E0（单轮直接提示）/ E1（Dr.ECI 完整流程）/ E2（仅改 q 阈值）。

用法示例：
  $env:DEEPSEEK_API_KEY='...'
  python code/pipeline.py --exp E1 --split dev --limit 50     # 冒烟测试
  python code/pipeline.py --exp E1 --split dev --limit 300
  python code/pipeline.py --exp E0 --split test --limit 300

流程与原仓库一致：
  agent1 Causal Explorer（causal / causation / causality 三次提问）-> q 计数
  agent2 q >= 阈值 的样本才进入 Mediator Detector
  agent3 抽取 "Answer to subquestion 4" -> Reasoner（8 条因果规则）-> 解析最终答案
  q < 阈值的样本直接判为非因果（与原仓库一致）
"""

import argparse
import csv
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

import parse as P
import prompts
from llm import LLMClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_text(item):
    """与原仓库 generate_cot_text 完全一致：事件词用 <source event>/<target event> 包裹。"""
    words = list(item["words"])
    source_indices = item["events"][0]
    target_indices = item["events"][1]
    source_event = " ".join([words[t] for t in source_indices])
    target_event = " ".join([words[t] for t in target_indices])

    words_with_tags = words[:]
    for idx in source_indices:
        words_with_tags[idx] = f"<source event>{words_with_tags[idx]}<source event>"
    for idx in target_indices:
        words_with_tags[idx] = f"<target event>{words_with_tags[idx]}<target event>"
    text = " ".join(words_with_tags)
    return text, source_event, target_event


# --------------------------------------------------------------------------- 各实验
def run_direct(client, item, sample_id):
    """E0：单轮直接提示（与原仓库 explorer 的第一轮相同），是最公平的 vanilla 基线。"""
    text, source, target = build_text(item)
    messages = [
        {"role": "system", "content": prompts.explorer_system},
        {"role": "user", "content": prompts.causal(source, target, text) + prompts.vanilla_formal},
    ]
    r = client.complete(messages, "E0_direct", sample_id)
    label, method = P.parse_answer(r["text"])
    return {
        "pred": label,
        "q": None,
        "decision_path": "direct",
        "parse_method": method,
        "parse_fail": int(label is None),
        "api_fail": int(r["api_error"] is not None),
        "stages": {"direct": r},
    }


def run_dr_eci(client, item, sample_id, q_threshold):
    """E1/E2：Causal Explorer -> Mediator Detector -> Reasoner。"""
    text, source, target = build_text(item)

    explorer_answers = {}
    q = 0
    explorer_parse_fail = 0
    api_fail = 0
    for tag, fn in [
        ("causal", prompts.causal),
        ("causation", prompts.causation),
        ("causality", prompts.causality),
    ]:
        messages = [
            {"role": "system", "content": prompts.explorer_system},
            {"role": "user", "content": fn(source, target, text) + prompts.vanilla_formal},
        ]
        r = client.complete(messages, f"explorer_{tag}", sample_id)
        explorer_answers[tag] = r
        label, _ = P.parse_answer(r["text"])
        if label is None:
            explorer_parse_fail += 1
        q += 1 if label == "Yes" else 0
        api_fail += int(r["api_error"] is not None)

    out = {
        "q": q,
        "explorer_parse_fail": explorer_parse_fail,
        "api_fail": api_fail,
        "stages": {"explorer": explorer_answers},
    }

    # ---- 过滤：与原仓库 choose.py 的 q >= 1 逻辑一致
    if q < q_threshold:
        out.update(
            {
                "pred": "No",
                "decision_path": "filtered",
                "parse_method": "filter_rule",
                "parse_fail": 0,
                "mediator_ok": 0,
                "z": None,
            }
        )
        return out

    # ---- Mediator Detector
    messages = [
        {"role": "system", "content": prompts.mediator_system},
        {"role": "user", "content": prompts.mediator(source, target, text)},
    ]
    rm = client.complete(messages, "mediator", sample_id)
    out["stages"]["mediator"] = rm
    z_value, mediator_ok = P.extract_subq4(rm["text"])
    out["mediator_ok"] = int(mediator_ok)
    out["z"] = z_value
    out["api_fail"] += int(rm["api_error"] is not None)

    # ---- Reasoner
    messages = [
        {"role": "system", "content": prompts.reasoner_system},
        {"role": "user", "content": prompts.reasoner(source, target, text, z_value)},
    ]
    rr = client.complete(messages, "reasoner", sample_id)
    out["stages"]["reasoner"] = rr
    label, method = P.parse_answer(rr["text"])
    out.update(
        {
            "pred": label,
            "decision_path": "reasoner",
            "parse_method": method,
            "parse_fail": int(label is None),
        }
    )
    out["api_fail"] += int(rr["api_error"] is not None)
    return out


# --------------------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(PROJECT_ROOT, "configs", "default.yaml"))
    ap.add_argument("--exp", required=True, choices=["E0", "E1", "E2"])
    ap.add_argument("--split", default="dev", choices=["dev", "test", "train"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--resume", action="store_true", help="跳过已完成的样本")
    args = ap.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    ecfg = cfg["experiments"][args.exp]

    subset_path = os.path.join(PROJECT_ROOT, "data_info", f"subset_{args.split}.jsonl")
    items = []
    with open(subset_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    if args.limit:
        items = items[: args.limit]

    out_dir = os.path.join(PROJECT_ROOT, "results", args.exp)
    os.makedirs(out_dir, exist_ok=True)
    raw_log = os.path.join(out_dir, "raw_responses.jsonl")
    cache_dir = os.path.join(PROJECT_ROOT, "results", "cache")

    client = LLMClient(cfg["llm"], cache_dir, raw_log)
    workers = args.workers or int(cfg["llm"].get("concurrency", 8))

    done_ids = set()
    pred_path = os.path.join(out_dir, f"predictions_{args.split}.jsonl")
    if args.resume and os.path.exists(pred_path):
        with open(pred_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    done_ids.add(json.loads(line)["sample_id"])

    todo = [it for it in items if it["subset_id"] not in done_ids]

    t_start = time.time()
    results = []
    lock_order = {}

    def work(item):
        sid = item["subset_id"]
        if ecfg["type"] == "direct":
            return sid, run_direct(client, item, sid)
        return sid, run_dr_eci(client, item, sid, int(ecfg["q_threshold"]))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(work, it): it for it in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            item = futures[fut]
            try:
                sid, res = fut.result()
            except Exception as e:  # noqa: BLE001
                sid = item["subset_id"]
                res = {
                    "pred": None,
                    "q": None,
                    "decision_path": "exception",
                    "parse_method": "exception",
                    "parse_fail": 1,
                    "api_fail": 1,
                    "error": f"{type(e).__name__}: {e}",
                    "stages": {},
                }
            res.update(
                {
                    "sample_id": sid,
                    "item_id": item["item_id"],
                    "doc_name": item["doc_name"],
                    "events_id": item["events_id"],
                    "gold": int(item["bi_causal_label"]),
                    "scope": item.get("scope", "intra"),
                    "split": args.split,
                }
            )
            results.append(res)
            if i % 20 == 0 or i == len(todo):
                print(f"[{args.exp}/{args.split}] {i}/{len(todo)} done")

    wall = time.time() - t_start

    # 按 sample_id 排序，保证输出稳定
    results.sort(key=lambda x: x["sample_id"])

    with open(pred_path, "a" if args.resume else "w", encoding="utf-8") as f:
        for r in results:
            slim = {k: v for k, v in r.items() if k != "stages"}
            f.write(json.dumps(slim, ensure_ascii=False) + "\n")

    # CSV：样本 ID、真实标签、预测标签
    csv_path = os.path.join(out_dir, f"predictions_{args.split}.csv")
    old = []
    if args.resume and os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            old = list(csv.DictReader(f))
    rows = old + [
        {
            "sample_id": r["sample_id"],
            "item_id": r["item_id"],
            "events_id": "|".join(map(str, r["events_id"])),
            "doc_name": r["doc_name"],
            "scope": r["scope"],
            "gold": r["gold"],
            "pred": r["pred"] if r["pred"] is not None else "PARSE_FAIL",
            "q": r["q"] if r["q"] is not None else "",
            "decision_path": r["decision_path"],
            "parse_method": r["parse_method"],
        }
        for r in results
    ]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    meta = {
        "exp": args.exp,
        "type": ecfg["type"],
        "q_threshold": ecfg.get("q_threshold"),
        "split": args.split,
        "n_samples": len(rows),
        "wall_time_s": round(wall, 2),
        "llm": {
            k: cfg["llm"].get(k)
            for k in ["model", "reasoning_effort", "temperature", "top_p", "max_tokens", "concurrency"]
        },
        "stats": client.stats,
        "truncated": sum(
            1 for r in results for s in r["stages"].values() if isinstance(s, dict) and s.get("finish_reason") == "length"
        ),
    }
    with open(os.path.join(out_dir, f"meta_{args.split}.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    client.close()
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
