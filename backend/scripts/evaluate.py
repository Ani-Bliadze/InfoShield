"""Evaluate a gate and find its optimal threshold on a labeled CSV.

Scores every row with one gate, then reports precision / recall / F1, ROC-AUC,
PR-AUC, a threshold sweep, and three recommended operating points
(max-F1, Youden's J, target-precision). See docs/EVALUATION.md for the method.

CSV format: columns `text,label`  (label: 1 = hate/manipulation, 0 = not).

Examples:
    python backend/scripts/evaluate.py --task hate --data hate.csv --subset 0.1
    python backend/scripts/evaluate.py --task manipulation --data persuasion.csv --subset 0.2
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_rows(path: str) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            text = (r.get("text") or "").strip()
            raw = str(r.get("label") or "").strip()
            if not text or raw == "":
                continue
            try:
                label = int(float(raw))
            except ValueError:
                continue
            rows.append((text, 1 if label >= 1 else 0))
    return rows


def stratified_subset(rows, fraction, seed):
    if fraction >= 1.0:
        return rows
    rng = random.Random(seed)
    pos = [r for r in rows if r[1] == 1]
    neg = [r for r in rows if r[1] == 0]
    rng.shuffle(pos)
    rng.shuffle(neg)
    keep = pos[: max(1, int(len(pos) * fraction))] + neg[: max(1, int(len(neg) * fraction))]
    rng.shuffle(keep)
    return keep


def score_rows(rows, task):
    scores = []
    if task == "hate":
        from classifier import get_classifier

        clf = get_classifier()
        clf.load()
        for i, (text, _) in enumerate(rows, 1):
            scores.append(float(clf.classify(text)["confidence"]))
            if i % 25 == 0:
                print(f"  scored {i}/{len(rows)}", file=sys.stderr)
    else:  # manipulation (local propaganda model -- the gate score)
        from manip_classifier import get_manip_classifier

        clf = get_manip_classifier()
        clf.load()
        for i, (text, _) in enumerate(rows, 1):
            scores.append(float(clf.classify(text)["confidence"]))
            if i % 25 == 0:
                print(f"  scored {i}/{len(rows)}", file=sys.stderr)
    return np.array(scores), np.array([lbl for _, lbl in rows])


def metrics_at(scores, labels, t):
    pred = scores >= t
    tp = int(np.sum(pred & (labels == 1)))
    fp = int(np.sum(pred & (labels == 0)))
    fn = int(np.sum(~pred & (labels == 1)))
    tn = int(np.sum(~pred & (labels == 0)))
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    tpr = rec
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return {"t": t, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": prec, "recall": rec, "f1": f1, "tpr": tpr, "fpr": fpr}


def roc_auc(scores, labels):
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    # Mann-Whitney U (counts ties as 0.5).
    gt = np.sum(pos[:, None] > neg[None, :])
    eq = np.sum(pos[:, None] == neg[None, :])
    return float((gt + 0.5 * eq) / (len(pos) * len(neg)))


def pr_auc(scores, labels):
    order = np.argsort(-scores)
    y = labels[order]
    tp = np.cumsum(y == 1)
    fp = np.cumsum(y == 0)
    npos = int(np.sum(labels == 1))
    if npos == 0:
        return float("nan")
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / npos
    recall = np.concatenate([[0.0], recall])
    precision = np.concatenate([[1.0], precision])
    return float(np.sum((recall[1:] - recall[:-1]) * precision[1:]))  # average precision


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["hate", "manipulation"], required=True)
    ap.add_argument("--data", required=True, help="CSV with columns: text,label")
    ap.add_argument("--subset", type=float, default=1.0, help="stratified fraction, e.g. 0.1")
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--target-precision", type=float, default=0.85)
    ap.add_argument("--steps", type=int, default=101)
    args = ap.parse_args()

    rows = stratified_subset(load_rows(args.data), args.subset, args.seed)
    if not rows:
        raise SystemExit("No usable rows (need columns text,label).")
    print(f"\nTask: {args.task} | rows: {len(rows)} "
          f"(pos={sum(l for _, l in rows)}, neg={sum(1 - l for _, l in rows)})")

    scores, labels = score_rows(rows, args.task)
    sweep = [metrics_at(scores, labels, t) for t in np.linspace(0, 1, args.steps)]

    best_f1 = max(sweep, key=lambda m: m["f1"])
    youden = max(sweep, key=lambda m: m["tpr"] - m["fpr"])
    prec_ok = [m for m in sweep if m["precision"] >= args.target_precision and m["recall"] > 0]
    target = min(prec_ok, key=lambda m: m["t"]) if prec_ok else best_f1

    print(f"\nROC-AUC: {roc_auc(scores, labels):.3f}   PR-AUC (AP): {pr_auc(scores, labels):.3f}")
    print("\nOperating points:")
    print(f"  {'criterion':<22}{'thr':>6}{'P':>8}{'R':>8}{'F1':>8}")
    for name, m in [("max-F1", best_f1), ("Youden's J", youden),
                    (f"precision>={args.target_precision:.2f}", target)]:
        print(f"  {name:<22}{m['t']:>6.2f}{m['precision']:>8.3f}{m['recall']:>8.3f}{m['f1']:>8.3f}")

    r = target
    print(f"\nRecommended threshold = {r['t']:.2f} (precision-first). Confusion @ thr:")
    print(f"  TP={r['tp']}  FP={r['fp']}  FN={r['fn']}  TN={r['tn']}")
    print("\nPaste the operating-points table into docs/EVALUATION.md > Key results.\n")


if __name__ == "__main__":
    main()
