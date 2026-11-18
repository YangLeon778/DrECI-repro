"""评估：精确率 / 召回率 / F1（总体 + 句内/跨句）、失败计数、规模、耗时与费用。

用法：
  python code/evaluate.py --exp E1 --split dev
  python code/evaluate.py --exp E1 --split test
  python code/evaluate.py --all        # 汇总 results/comparison.csv
"""

import argparse
import csv
import glob
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_jsonl(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def confusion(rows, scope=None):
    tp = fp = fn = tn = 0
    for r in rows:
        if scope is not None and r.get("scope", "intra") != scope:
            continue
        gold = int(r["gold"])
        pred = r.get("pred")
        pred_pos = 1 if pred == "Yes" else 0  # 解析失败按非因果计入，另单独统计
        if gold == 1 and pred_pos == 1:
            tp += 1
        elif gold == 0 and pred_pos == 1:
            fp += 1
        elif gold == 1 and pred_pos == 0:
            fn += 1
        else:
            tn += 1
    return tp, fp, fn, tn


def evaluate_one(exp, split):
    out_dir = os.path.join(PROJECT_ROOT, "results", exp)
    pred_path = os.path.join(out_dir, f"predictions_{split}.jsonl")
    if not os.path.exists(pred_path):
        print(f"跳过 {exp}/{split}：缺少 {pred_path}")
        return None
    rows = load_jsonl(pred_path)

    meta_path = os.path.join(out_dir, f"meta_{split}.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    tp, fp, fn, tn = confusion(rows)
    p, r, f1 = prf(tp, fp, fn)
    acc = (tp + tn) / len(rows) if rows else 0.0

    tp_i, fp_i, fn_i, tn_i = confusion(rows, "intra")
    p_i, r_i, f1_i = prf(tp_i, fp_i, fn_i)
    n_cross = sum(1 for x in rows if x.get("scope") != "intra")
    if n_cross:
        tp_c, fp_c, fn_c, tn_c = confusion(rows, None)
        tp_c -= tp_i
        fp_c -= fp_i
        fn_c -= fn_i
        tn_c -= tn_i
        p_c, r_c, f1_c = prf(tp_c, fp_c, fn_c)
    else:
        tp_c = fp_c = fn_c = tn_c = 0
        p_c = r_c = f1_c = 0.0

    stats = meta.get("stats", {})
    res = {
        "exp": exp,
        "split": split,
        "q_threshold": meta.get("q_threshold"),
        "n": len(rows),
        "n_pos": sum(int(x["gold"]) for x in rows),
        "n_neg": len(rows) - sum(int(x["gold"]) for x in rows),
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "P": round(p, 4),
        "R": round(r, 4),
        "F1": round(f1, 4),
        "Acc": round(acc, 4),
        # 分项：句内 / 跨句
        "intra_n": tp_i + fp_i + fn_i + tn_i,
        "intra_P": round(p_i, 4),
        "intra_R": round(r_i, 4),
        "intra_F1": round(f1_i, 4),
        "cross_n": n_cross,
        "cross_P": round(p_c, 4) if n_cross else None,
        "cross_R": round(r_c, 4) if n_cross else None,
        "cross_F1": round(f1_c, 4) if n_cross else None,
        # 失败计数
        "parse_fail": sum(1 for x in rows if x.get("parse_fail") == 1),
        "api_fail": sum(1 for x in rows if x.get("api_fail")),
        "filtered": sum(1 for x in rows if x.get("decision_path") == "filtered"),
        "exception": sum(1 for x in rows if x.get("decision_path") == "exception"),
        "mediator_found": sum(1 for x in rows if x.get("mediator_ok") == 1),
        # 规模 / 耗时 / 费用
        "llm_calls": stats.get("api_calls", 0),
        "cache_hits": stats.get("cache_hits", 0),
        "tokens_in": stats.get("tokens_in", 0),
        "tokens_out": stats.get("tokens_out", 0),
        "reasoning_tokens": stats.get("reasoning_tokens", 0),
        "cost_cny": round(float(stats.get("cost_cny", 0.0)), 4),
        "wall_time_s": meta.get("wall_time_s", 0.0),
        "truncated": meta.get("truncated", 0),
    }

    with open(os.path.join(out_dir, f"metrics_{split}.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)

    lines = [
        f"实验 {exp} / {split}  (n={res['n']}, 正例={res['n_pos']})",
        f"  P={res['P']:.4f}  R={res['R']:.4f}  F1={res['F1']:.4f}  Acc={res['Acc']:.4f}",
        f"  TP={tp} FP={fp} FN={fn} TN={tn}",
        f"  句内: n={res['intra_n']} P={res['intra_P']:.4f} R={res['intra_R']:.4f} F1={res['intra_F1']:.4f}",
        f"  跨句: n={res['cross_n']}（ESL 数据全部为句内，故无跨句样本）",
        f"  解析失败={res['parse_fail']}  请求失败={res['api_fail']}  被过滤(q<阈值)={res['filtered']}  异常={res['exception']}",
        f"  调用={res['llm_calls']} 缓存命中={res['cache_hits']} token={res['tokens_in']}/{res['tokens_out']}",
        f"  耗时={res['wall_time_s']:.1f}s  费用≈¥{res['cost_cny']:.2f}",
    ]
    print("\n".join(lines))
    return res


FIELDS = [
    "exp", "split", "q_threshold", "n", "n_pos", "n_neg", "TP", "FP", "FN", "TN",
    "P", "R", "F1", "Acc", "intra_n", "intra_P", "intra_R", "intra_F1",
    "cross_n", "cross_P", "cross_R", "cross_F1",
    "parse_fail", "api_fail", "filtered", "exception", "mediator_found",
    "llm_calls", "cache_hits", "tokens_in", "tokens_out", "reasoning_tokens", "cost_cny",
    "wall_time_s", "truncated",
]


def write_comparison(results):
    path = os.path.join(PROJECT_ROOT, "results", "comparison.csv")
    all_rows = []
    # 合并历史结果（按 exp/split 去重）
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as f:
            all_rows = list(csv.DictReader(f))
    key = {(r["exp"], r["split"]): r for r in all_rows}
    for r in results:
        key[(r["exp"], r["split"])] = {k: r.get(k) for k in FIELDS}
    order = {"E0": 0, "E1": 1, "E2": 2}
    merged = sorted(
        key.values(), key=lambda r: (order.get(r["exp"], 9), r["split"])
    )
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(merged)
    print(f"\n汇总已写入 {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", choices=["E0", "E1", "E2"])
    ap.add_argument("--split", default="dev")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.all:
        results = []
        for meta_path in sorted(glob.glob(os.path.join(PROJECT_ROOT, "results", "E*", "meta_*.json"))):
            exp = os.path.basename(os.path.dirname(meta_path))
            with open(meta_path, "r", encoding="utf-8") as f:
                split = json.load(f)["split"]
            r = evaluate_one(exp, split)
            if r:
                results.append(r)
    else:
        r = evaluate_one(args.exp, args.split)
        results = [r] if r else []

    if results:
        write_comparison(results)


if __name__ == "__main__":
    main()
