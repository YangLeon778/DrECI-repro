"""数据准备：文档级划分 + 固定子集抽样 + 数据统计。

课程要求 E0/E1/E2 使用同一份划分、同一批样本、同一随机种子；测试集冻结后只评一次。
本脚本产出：
  data_info/split.json         文档级 train/dev/test 划分（E0/E1/E2 共用）
  data_info/subset_dev.jsonl   开发集固定子集（用于选阈值等参数）
  data_info/subset_test.jsonl  测试集固定子集（冻结，只评一次）
  data_info/statistics.json    样本规模、正负比、句内/跨句、文档重叠、重复对检查
"""

import argparse
import collections
import json
import os
import random

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_esl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def doc_level_split(rows, seed, dev_ratio, test_ratio):
    """按文档划分，并以「正例数量」为目标做贪心均衡，保证三个集合正例比例接近。"""
    doc_stats = collections.defaultdict(lambda: [0, 0])  # doc -> [n_pairs, n_pos]
    for r in rows:
        doc_stats[r["doc_name"]][0] += 1
        doc_stats[r["doc_name"]][1] += int(r["bi_causal_label"])

    docs = list(doc_stats.keys())
    rng = random.Random(seed)
    rng.shuffle(docs)
    # 稳定排序：正例多的文档先分配，同数量时保持打乱后的顺序
    docs.sort(key=lambda d: -doc_stats[d][1])

    total_pos = sum(v[1] for v in doc_stats.values())
    targets = {
        "train": total_pos * (1 - dev_ratio - test_ratio),
        "dev": total_pos * dev_ratio,
        "test": total_pos * test_ratio,
    }
    cur = {"train": 0, "dev": 0, "test": 0}
    assign = {}
    for d in docs:
        best = min(
            cur.keys(),
            key=lambda k: (cur[k] + doc_stats[d][1]) / max(targets[k], 1e-9),
        )
        assign[d] = best
        cur[best] += doc_stats[d][1]

    return assign, doc_stats


def stratified_subset(rows, n, seed):
    """按标签比例分层抽样固定子集。"""
    rng = random.Random(seed)
    pos = [r for r in rows if int(r["bi_causal_label"]) == 1]
    neg = [r for r in rows if int(r["bi_causal_label"]) == 0]
    if n >= len(rows):
        out = list(rows)
    else:
        n_pos = max(1, round(n * len(pos) / len(rows)))
        n_pos = min(n_pos, len(pos))
        n_neg = min(n - n_pos, len(neg))
        out = rng.sample(pos, n_pos) + rng.sample(neg, n_neg)
    rng.shuffle(out)
    return out


def subset_stats(rows, docs_in_subset):
    n = len(rows)
    n_pos = sum(int(r["bi_causal_label"]) for r in rows)
    intra = sum(1 for r in rows if r.get("sent_in_doc_id") is not None)  # ESL 全部为句内
    keys = collections.Counter(
        (r["doc_name"], r.get("sent_in_doc_id"), tuple(r.get("events_id", []))) for r in rows
    )
    dup = sum(1 for v in keys.values() if v > 1)
    return {
        "n_pairs": n,
        "n_docs": len(docs_in_subset),
        "n_pos": n_pos,
        "n_neg": n - n_pos,
        "pos_ratio": round(n_pos / n, 4) if n else 0.0,
        "intra_sentence": intra,
        "cross_sentence": n - intra,
        "duplicate_pair_groups": dup,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(PROJECT_ROOT, "configs", "default.yaml"))
    args = ap.parse_args()

    import yaml

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    esl_path = os.path.normpath(os.path.join(PROJECT_ROOT, cfg["data"]["esl_path"]))
    rows = load_esl(esl_path)
    sc = cfg["split"]

    assign, doc_stats = doc_level_split(
        rows, sc["seed"], float(sc["dev_ratio"]), float(sc["test_ratio"])
    )

    split_rows = collections.defaultdict(list)
    for r in rows:
        split_rows[assign[r["doc_name"]]].append(r)

    # 固定子集（dev/test）
    dev_sub = stratified_subset(split_rows["dev"], int(sc["dev_subset"]), sc["subset_seed"])
    test_sub = stratified_subset(split_rows["test"], int(sc["test_subset"]), sc["subset_seed"])

    # 写出子集
    info_dir = os.path.join(PROJECT_ROOT, "data_info")
    os.makedirs(info_dir, exist_ok=True)

    for name, sub, split_name in [
        ("subset_dev.jsonl", dev_sub, "dev"),
        ("subset_test.jsonl", test_sub, "test"),
    ]:
        with open(os.path.join(info_dir, name), "w", encoding="utf-8") as f:
            for i, r in enumerate(sub):
                rec = dict(r)
                rec["subset_id"] = f"{split_name}_{i:04d}"
                rec["split"] = split_name
                rec["scope"] = "intra"
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    doc_splits = collections.defaultdict(list)
    for d, s in assign.items():
        doc_splits[s].append(d)

    split_info = {
        "dataset": cfg["data"]["dataset"],
        "source_file": cfg["data"]["esl_path"],
        "seed": sc["seed"],
        "ratios": {"dev": sc["dev_ratio"], "test": sc["test_ratio"]},
        "docs": {k: sorted(v) for k, v in doc_splits.items()},
    }
    with open(os.path.join(info_dir, "split.json"), "w", encoding="utf-8") as f:
        json.dump(split_info, f, ensure_ascii=False, indent=2)

    stats = {
        "dataset": cfg["data"]["dataset"],
        "source_file": cfg["data"]["esl_path"],
        "total_pairs": len(rows),
        "total_docs": len(doc_stats),
        "total_pos": int(sum(int(r["bi_causal_label"]) for r in rows)),
        "label_distribution": dict(
            collections.Counter(int(r["bi_causal_label"]) for r in rows)
        ),
        "tri_label_distribution": dict(
            collections.Counter(int(r["tri_causal_label"]) for r in rows)
        ),
        "splits": {},
        "doc_overlap_check": {},
        "subsets": {
            "dev": subset_stats(dev_sub, {r["doc_name"] for r in dev_sub}),
            "test": subset_stats(test_sub, {r["doc_name"] for r in test_sub}),
        },
        "subset_seed": sc["subset_seed"],
        "note": "ESL（EventStoryLine）中所有事件对均来自同一句子，故只有句内（intra-sentence）指标，跨句为 0。",
    }
    for sp in ["train", "dev", "test"]:
        rs = split_rows[sp]
        stats["splits"][sp] = {
            "n_pairs": len(rs),
            "n_docs": len({r["doc_name"] for r in rs}),
            "n_pos": sum(int(r["bi_causal_label"]) for r in rs),
            "pos_ratio": round(
                sum(int(r["bi_causal_label"]) for r in rs) / len(rs), 4
            ) if rs else 0.0,
        }

    keys = [set(doc_splits[a]) for a in ["train", "dev", "test"]]
    for a, b in [("train", "dev"), ("train", "test"), ("dev", "test")]:
        stats["doc_overlap_check"][f"{a}-{b}"] = len(
            set(doc_splits[a]) & set(doc_splits[b])
        )

    with open(os.path.join(info_dir, "statistics.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
