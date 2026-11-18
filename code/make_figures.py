"""生成结果图：三实验 P/R/F1 对比 + 混淆矩阵。

用法：python code/make_figures.py --split dev
"""

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    args = ap.parse_args()

    exps = ["E0", "E1", "E2"]
    res = {}
    for e in exps:
        p = os.path.join(PROJECT_ROOT, "results", e, f"metrics_{args.split}.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                res[e] = json.load(f)
    if not res:
        print("没有可用的 metrics 文件")
        return

    fig_dir = os.path.join(PROJECT_ROOT, "results", "figures")
    os.makedirs(fig_dir, exist_ok=True)

    # ---- 图 1：P / R / F1 分组柱状图
    labels = list(res.keys())
    metrics = ["P", "R", "F1", "Acc"]
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
    x = np.arange(len(labels))
    w = 0.2
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=200)
    for i, m in enumerate(metrics):
        vals = [res[e][m] for e in labels]
        bars = ax.bar(x + (i - 1.5) * w, vals, w, label=m, color=colors[i])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}",
                    ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score")
    ax.set_title(f"Dr.ECI reproduction on ESL ({args.split} subset, n={res[labels[0]]['n']})")
    ax.legend(ncol=4, fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.10))
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f"metrics_{args.split}.png"), bbox_inches="tight")
    plt.close(fig)

    # ---- 图 2：混淆矩阵（2x3）
    fig, axes = plt.subplots(1, len(labels), figsize=(3.4 * len(labels), 3.0), dpi=200)
    if len(labels) == 1:
        axes = [axes]
    for ax, e in zip(axes, labels):
        r = res[e]
        cm = np.array([[r["TN"], r["FP"]], [r["FN"], r["TP"]]])
        ax.imshow(cm, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                        fontsize=12, color="white" if cm[i, j] > cm.max() / 2 else "black")
        ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
        ax.set_xticklabels(["Pred No", "Pred Yes"])
        ax.set_yticklabels(["Gold No", "Gold Yes"])
        ax.set_title(f"{e}  F1={r['F1']:.3f}")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f"confusion_{args.split}.png"), bbox_inches="tight")
    plt.close(fig)

    print(f"图已保存到 {fig_dir}")


if __name__ == "__main__":
    main()
