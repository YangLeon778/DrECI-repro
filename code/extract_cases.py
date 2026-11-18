"""从真实运行结果中抽取样例：2 个正确样例 + 5 个错例（含原文、事件、真值、预测）。

用法：python code/extract_cases.py --exp E1 --split test --out results/E1/cases.md
"""

import argparse
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def render(item, pred_rec, idx):
    w = item["words"]
    ev = item["events"]
    src = " ".join(w[i] for i in ev[0])
    tgt = " ".join(w[i] for i in ev[1])
    gold = "有因果" if int(item["bi_causal_label"]) == 1 else "无因果"
    pred = "有因果" if pred_rec.get("pred") == "Yes" else "无因果"
    return (
        f"### {idx}. 样本 `{item['subset_id']}`（doc: `{os.path.basename(item['doc_name'])}`）\n\n"
        f"- **原文**：{ ' '.join(w) }\n"
        f"- **源事件**：{src}　**目标事件**：{tgt}\n"
        f"- **真实标签**：{gold}　**预测标签**：{pred}\n"
        f"- **决策路径**：{pred_rec.get('decision_path')}（q={pred_rec.get('q')}，"
        f"Z={str(pred_rec.get('z'))[:120]}）\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="E1")
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    subset = load_jsonl(os.path.join(PROJECT_ROOT, "data_info", f"subset_{args.split}.jsonl"))
    preds = {
        r["sample_id"]: r
        for r in load_jsonl(
            os.path.join(PROJECT_ROOT, "results", args.exp, f"predictions_{args.split}.jsonl")
        )
    }
    by_id = {it["subset_id"]: it for it in subset}

    correct, wrong_fp, wrong_fn = [], [], []
    for sid, p in preds.items():
        it = by_id.get(sid)
        if not it or p.get("pred") not in ("Yes", "No"):
            continue
        gold = int(it["bi_causal_label"])
        pred = 1 if p["pred"] == "Yes" else 0
        if gold == pred:
            correct.append((sid, it, p))
        elif gold == 0 and pred == 1:
            wrong_fp.append((sid, it, p))
        else:
            wrong_fn.append((sid, it, p))

    correct.sort(key=lambda x: x[0])
    wrongs = (wrong_fp[:3] + wrong_fn[:3])[:5]

    lines = [f"# {args.exp} / {args.split} 真实运行样例\n"]
    lines.append("## 一、正确样例（2 个）\n")
    for i, (sid, it, p) in enumerate(correct[:2], 1):
        lines.append(render(it, p, i))
    lines.append("\n## 二、错例（5 个）\n")
    for i, (sid, it, p) in enumerate(wrongs, 1):
        lines.append(render(it, p, i))

    text = "\n".join(lines)
    out = args.out or os.path.join(PROJECT_ROOT, "results", args.exp, f"cases_{args.split}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"已写出 {out}（正确 {len(correct)}，错误 FP {len(wrong_fp)}，FN {len(wrong_fn)}）")


if __name__ == "__main__":
    main()
