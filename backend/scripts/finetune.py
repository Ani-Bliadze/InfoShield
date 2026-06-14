"""OPTIONAL fine-tuning scaffold. The demo does NOT depend on this.

Fine-tunes the primary checkpoint on a small local CSV (columns: text,label
where label is 0=not-hate, 1=hate). Useful if you want to adapt the classifier
to your own examples. Produces a model directory you could point PRIMARY_MODEL at.

Usage:
    python backend/scripts/finetune.py --data my_data.csv --out backend/models/finetuned --epochs 2

Requires: transformers[torch], datasets, accelerate.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import PRIMARY_MODEL  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="CSV with columns: text,label")
    ap.add_argument("--out", default=str(ROOT / "models" / "finetuned"))
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch", type=int, default=8)
    args = ap.parse_args()

    try:
        import numpy as np
        from datasets import load_dataset
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            DataCollatorWithPadding,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:  # noqa: BLE001
        raise SystemExit(
            f"Missing dependency: {exc}. Install with: pip install datasets accelerate"
        )

    tok = AutoTokenizer.from_pretrained(PRIMARY_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(PRIMARY_MODEL, num_labels=2)

    ds = load_dataset("csv", data_files=args.data)["train"].train_test_split(test_size=0.2)
    ds = ds.map(lambda b: tok(b["text"], truncation=True, max_length=256), batched=True)

    def metrics(p):
        preds = np.argmax(p.predictions, axis=-1)
        return {"accuracy": float((preds == p.label_ids).mean())}

    targs = TrainingArguments(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=10,
    )
    trainer = Trainer(
        model=model,
        args=targs,
        train_dataset=ds["train"],
        eval_dataset=ds["test"],
        tokenizer=tok,
        data_collator=DataCollatorWithPadding(tok),
        compute_metrics=metrics,
    )
    trainer.train()
    trainer.save_model(args.out)
    tok.save_pretrained(args.out)
    print(f"\nSaved fine-tuned model to {args.out}")
    print("To use it, set PRIMARY_MODEL in backend/config.py to that path.")


if __name__ == "__main__":
    main()
