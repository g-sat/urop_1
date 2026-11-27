"""Score ask-or-answer policies on the same 2,002 AmbigQA development questions.

Called by: .\\myVenv\\Scripts\\python.exe scripts\\score_ambigqa_baselines.py
make_ambigqa_score_figures.py scores string policies only. This file adds
MiniLM cosine clusters at 0.72 and the latent turn-2 count. No other file
does those two measurements.

Reads first-pass JSONL plus results/ambigqa_second_pass overrides.
Each item has readings, immediate_answers, followup_answers, and n.
Gold comes from ambigqa_type on the batch JSON.
Writes results/ambigqa_cursor/baseline_metrics.json.

User instruction: score every baseline as the same ask bit against
multipleQAs on the 2,002 development questions.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
COSINE_TAU = 0.72


def load_decide():
    spec = importlib.util.spec_from_file_location(
        "latent_decide",
        ROOT / "ambiguity_layer" / "latent" / "decide.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def second_pass() -> dict[str, dict]:
    found: dict[str, dict] = {}
    folder = ROOT / "results" / "ambigqa_second_pass"
    for path in sorted(folder.glob("pass_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                found[str(item["id"])] = item
    return found


def prf(gold: list[bool], pred: list[bool]) -> dict[str, float]:
    tp = sum(g and p for g, p in zip(gold, pred))
    fp = sum((not g) and p for g, p in zip(gold, pred))
    fn = sum(g and (not p) for g, p in zip(gold, pred))
    tn = sum((not g) and (not p) for g, p in zip(gold, pred))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    n = tp + fp + fn + tn
    return {
        "accuracy": round((tp + tn) / n, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def clusters(vectors: np.ndarray, tau: float) -> int:
    groups: list[list[int]] = []
    for index in range(len(vectors)):
        placed = False
        for group in groups:
            sims = vectors[index] @ vectors[group].T
            if float(np.max(sims)) >= tau:
                group.append(index)
                placed = True
                break
        if not placed:
            groups.append([index])
    return len(groups)


def load_items(decide) -> list[dict]:
    revised = second_pass()
    items = []
    batches = ROOT / "data" / "ambigqa_batches"
    labeled = ROOT / "results" / "ambigqa_cursor"
    for src in sorted(batches.glob("batch_*.json")):
        kinds = {
            str(row["id"]): row["ambigqa_type"]
            for row in json.loads(src.read_text(encoding="utf-8"))
        }
        out = labeled / (src.stem + ".jsonl")
        for line in out.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            item = revised.get(str(item["id"]), item)
            label = decide.classify(
                item["readings"],
                item["immediate_answers"],
                item["followup_answers"],
            )["label"]
            items.append(
                {
                    "id": str(item["id"]),
                    "gold": kinds[str(item["id"])] == "multipleQAs",
                    "label": label,
                    "n": int(item["n"]),
                    "answers": item["immediate_answers"],
                    "follow": item["followup_answers"],
                }
            )
    return items


def embed_ask(items: list[dict]) -> list[bool]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    flat = [answer if answer else " " for item in items for answer in item["answers"]]
    vectors = model.encode(
        flat,
        normalize_embeddings=True,
        batch_size=64,
        show_progress_bar=False,
    )
    vectors = np.asarray(vectors)
    asks = []
    cursor = 0
    for item in items:
        width = len(item["answers"])
        block = vectors[cursor : cursor + width]
        cursor += width
        asks.append(clusters(block, COSINE_TAU) >= 2)
    return asks


def main() -> None:
    decide = load_decide()
    items = load_items(decide)
    gold = [item["gold"] for item in items]
    rule = [item["label"] == "decision" for item in items]
    flag = [item["label"] in {"decision", "latent"} for item in items]
    many = [item["n"] >= 2 for item in items]
    always_ask = [True] * len(items)
    always_answer = [False] * len(items)
    print("embedding", len(items))
    embed = embed_ask(items)
    systems = {
        "ask_if_answers_differ": rule,
        "ask_if_decision_or_latent": flag,
        "ask_if_k_ge_2": many,
        "always_ask": always_ask,
        "always_answer": always_answer,
        "minilm_cosine_0.72": embed,
    }
    table = {}
    for name, pred in systems.items():
        row = prf(gold, pred)
        row["disagreements_with_rule"] = sum(a != b for a, b in zip(rule, pred))
        table[name] = row
        print(name, row)
    latent = [item for item in items if item["label"] == "latent"]
    turn2_fail_if_other = 0
    for item in latent:
        first = item["follow"][0]
        if any(not decide.same_answer(first, other) for other in item["follow"][1:]):
            turn2_fail_if_other += 1
    table["latent_turn2"] = {
        "n": len(latent),
        "other_reading_followup_differs": turn2_fail_if_other,
    }
    print("turn2", table["latent_turn2"])
    out = ROOT / "results" / "ambigqa_cursor" / "baseline_metrics.json"
    out.write_text(json.dumps(table, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
