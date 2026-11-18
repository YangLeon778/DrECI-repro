"""代码审计 + 双口径评估：全集 vs 过筛样本子集。

关键背景：
- 原仓库 core.py 对 reasoner 输出的解析是有 bug 的（函数名叫 contains_yes_answer
  实际匹配 "No"，但 reasoner 根本不输出 {"Answer":"Yes"/"No"}）
- README 里说"q 越高 Recall 越高"的 Analysis.png 是**在过筛样本子集上**的观察，
  不是全集 Recall。这里同时给出两种口径的数字。
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"e:\Trae CN\projects\machine-WB\DrECI_repro\results")

for exp in ["E0", "E1", "E2"]:
    for split in ["dev", "test"]:
        p = ROOT / exp / f"predictions_{split}.jsonl"
        if not p.exists():
            continue
        rows = [json.loads(l) for l in open(p, encoding="utf-8")]
        gold = [int(r["gold"]) for r in rows]
        pred = [1 if r["pred"] == "Yes" else 0 for r in rows]
        qs = [r.get("q") for r in rows]

        def prf_sub(idx_filter, title):
            g = [gold[i] for i in idx_filter]
            p = [pred[i] for i in idx_filter]
            tp = fp = fn = tn = 0
            for gi, pi in zip(g, p):
                if gi == 1 and pi == 1: tp += 1
                elif gi == 0 and pi == 1: fp += 1
                elif gi == 1 and pi == 0: fn += 1
                else: tn += 1
            n = len(g)
            n_pos = sum(g)
            prec = tp / (tp + fp) if (tp + fp) else 0.0
            rec = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
            print(f"  {title:<30} n={n:3d} pos={n_pos:3d} TP={tp:3d} FP={fp:3d} FN={fn:3d} TN={tn:3d} | P={prec:.4f} R={rec:.4f} F1={f1:.4f}")

        print(f"\n=== {exp} / {split} ===")
        # 全集口径
        prf_sub(list(range(len(rows))), "全集（所有样本）")

        # 过筛子集口径：只看实际进入 Mediator + Reasoner 的样本
        filtered_idx = [i for i, r in enumerate(rows) if r.get("decision_path") == "reasoner"]
        prf_sub(filtered_idx, f"过筛子集（进入 Mediator+Reasoner, q≥阈值）")

        # 按 q 分层（只有 E1/E2 有 q）
        if exp != "E0":
            # q=0 被过滤
            q0_idx = [i for i, r in enumerate(rows) if r.get("q") == 0]
            prf_sub(q0_idx, "q=0 层（被过滤样本）")
            # q>=1 的所有样本
            qp_idx = [i for i, r in enumerate(rows) if (r.get("q") or 0) >= 1]
            prf_sub(qp_idx, "q≥1 层（explorer 至少 1 次 Yes）")
            if exp == "E2":
                q2_idx = [i for i, r in enumerate(rows) if (r.get("q") or 0) >= 2]
                prf_sub(q2_idx, "q≥2 层（explorer 至少 2 次 Yes）")
            if exp == "E1":
                q3_idx = [i for i, r in enumerate(rows) if (r.get("q") or 0) >= 3]
                prf_sub(q3_idx, "q≥3 层（explorer 三次全 Yes）")
