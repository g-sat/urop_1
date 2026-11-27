"""AmbigQA study: learned detector plus end-to-end latent labels.

Run: python scripts/run_ambigqa_study.py
     python scripts/run_ambigqa_study.py --live --limit 300

Reads data/ambigqa_train_light.json and data/ambigqa_dev_light.json.
Writes results/ambigqa_study.json and results/ambigqa_latent.jsonl.
No other script trains this detector or generates readings on AmbigQA.
Does not create human annotations or a user study.

User instruction: do the missing journal items now, including real prompts,
model-generated readings, label rates, a learned detector, and an
end-to-end path.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ambiguity_layer.latent.decide import classify
from ambiguity_layer.llm.client import chat_json, get_usage, reset_usage

DATA = ROOT / "data"
OUT = ROOT / "results" / "ambigqa_study.json"
LIVE = ROOT / "results" / "ambigqa_latent.jsonl"


def load(name: str) -> list[dict]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def is_multi(row: dict) -> int:
    return int(row["annotations"][0]["type"] == "multipleQAs")


def train_detector() -> dict:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score

    from ambiguity_layer.eval.embeddings import embed

    train = load("ambigqa_train_light.json")
    dev = load("ambigqa_dev_light.json")
    random.seed(0)
    train = random.sample(train, 2000)
    y_train = [is_multi(row) for row in train]
    y_dev = [is_multi(row) for row in dev]
    x_train = embed([row["question"] for row in train])
    x_dev = embed([row["question"] for row in dev])
    model = LogisticRegression(max_iter=200)
    model.fit(x_train, y_train)
    pred = model.predict(x_dev)
    majority = max(set(y_dev), key=y_dev.count)
    majority_pred = [majority] * len(y_dev)
    return {
        "train_n": len(train),
        "dev_n": len(dev),
        "dev_ambiguous_rate": round(sum(y_dev) / len(y_dev), 3),
        "detector_accuracy": round(float(accuracy_score(y_dev, pred)), 3),
        "detector_f1": round(float(f1_score(y_dev, pred)), 3),
        "majority_accuracy": round(float(accuracy_score(y_dev, majority_pred)), 3),
    }


def sample_questions(limit: int) -> list[dict]:
    dev = load("ambigqa_dev_light.json")
    multi = [row for row in dev if is_multi(row)]
    single = [row for row in dev if not is_multi(row)]
    random.seed(1)
    half = limit // 2
    picked = random.sample(multi, min(half, len(multi))) + random.sample(
        single, min(limit - half, len(single))
    )
    random.shuffle(picked)
    return picked[:limit]


def done_ids() -> set[str]:
    if not LIVE.exists():
        return set()
    ids = set()
    for line in LIVE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.add(json.loads(line)["id"])
    return ids


PROMPT = """You label ambiguity for one question. Return JSON only:
{
  "readings": ["reading 1", "reading 2", "reading 3"],
  "immediate_answers": ["answer 1", "answer 2", "answer 3"],
  "followup": "one next question",
  "followup_answers": ["follow-up 1", "follow-up 2", "follow-up 3"]
}
Use 3 readings when more than one reading exists.
If there is one reading, return one reading and one answer in each list.
Keep answers short."""


def one_item(row: dict) -> dict:
    reset_usage()
    raw = chat_json(
        [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": row["question"]},
        ],
        temperature=0.2,
    )
    readings = [str(x) for x in raw.get("readings") or [] if str(x).strip()]
    immediate = [str(x) for x in raw.get("immediate_answers") or []]
    follow = [str(x) for x in raw.get("followup_answers") or []]
    n = min(len(readings), len(immediate), len(follow))
    if n == 0:
        raise ValueError("model returned no aligned readings")
    decision = classify(readings[:n], immediate[:n], follow[:n])
    usage = get_usage()
    return {
        "id": row["id"],
        "question": row["question"],
        "ambigqa_type": row["annotations"][0]["type"],
        "n_readings": n,
        "label": decision["label"],
        "action": decision["action"],
        "prompt_tokens": usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
    }


def summarize_live(rows: list[dict]) -> dict:
    from collections import Counter

    labels = Counter(row["label"] for row in rows)
    n = len(rows) or 1
    multi = [row for row in rows if row["ambigqa_type"] == "multipleQAs"]
    single = [row for row in rows if row["ambigqa_type"] == "singleAnswer"]

    def rate(group: list[dict], label: str) -> float:
        if not group:
            return 0.0
        return round(sum(row["label"] == label for row in group) / len(group), 3)

    return {
        "n": len(rows),
        "label_counts": dict(labels),
        "decision_rate": round(labels.get("decision", 0) / n, 3),
        "latent_rate": round(labels.get("latent", 0) / n, 3),
        "none_rate": round(labels.get("none", 0) / n, 3),
        "multipleQAs_n": len(multi),
        "singleAnswer_n": len(single),
        "latent_rate_on_multipleQAs": rate(multi, "latent"),
        "latent_rate_on_singleAnswer": rate(single, "latent"),
        "decision_rate_on_multipleQAs": rate(multi, "decision"),
        "none_rate_on_singleAnswer": rate(single, "none"),
        "readings_3_to_5": sum(3 <= row["n_readings"] <= 5 for row in rows),
        "total_tokens": sum(row["prompt_tokens"] + row["completion_tokens"] for row in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--all", action="store_true", help="Every AmbigQA dev question")
    parser.add_argument("--skip-detector", action="store_true")
    args = parser.parse_args()
    if args.skip_detector:
        report = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"detector": None, "live": None}
    else:
        report = {"detector": train_detector(), "live": None}
        print(json.dumps(report["detector"], indent=2))
    if args.live:
        seen = done_ids()
        source = load("ambigqa_dev_light.json") if args.all else sample_questions(args.limit)
        total = len(source)
        picked = [row for row in source if row["id"] not in seen]
        LIVE.parent.mkdir(parents=True, exist_ok=True)
        with LIVE.open("a", encoding="utf-8") as handle:
            for i, row in enumerate(picked, start=1):
                print(f"[{len(seen)+i}/{total}] {row['id']}", flush=True)
                try:
                    item = one_item(row)
                except Exception as exc:  # noqa: BLE001
                    print(f"  skip {exc}", flush=True)
                    continue
                handle.write(json.dumps(item) + "\n")
                handle.flush()
                print(f"  {item['label']} readings={item['n_readings']}", flush=True)
        rows = [
            json.loads(line)
            for line in LIVE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        report["live"] = summarize_live(rows)
        print(json.dumps(report["live"], indent=2))
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
