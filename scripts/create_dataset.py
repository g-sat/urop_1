"""Generate a diverse ambiguity benchmark dataset via an LLM."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
from pathlib import Path

from openai import OpenAI

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "ambiguity_benchmark.jsonl"

AMBIGUITY_TYPES = (
    "missing_entity",
    "syntax_error",
    "semantic_overlap",
)

DOMAINS = (
    "healthcare appointment",
    "software bug report",
    "travel booking",
    "legal contract",
    "university coursework",
    "restaurant reservation",
    "e-commerce return",
    "HR performance review",
    "scientific experiment",
    "personal finance",
    "sports schedule",
    "real estate listing",
    "customer support chat",
    "cooking recipe",
    "music festival",
    "cybersecurity incident",
    "film production",
    "climate policy",
    "startup fundraising",
    "veterinary clinic",
)

SCENARIO_SEEDS = (
    "pronoun with two possible antecedents",
    "homonym (bank, crane, bat, spring, etc.)",
    "underspecified time or timezone",
    "unclear which document/version is meant",
    "conflicting constraints in one request",
    "missing location that changes the answer",
    "ambiguous 'they' / 'it' referent",
    "scope of 'all' / 'only' / 'except'",
    "unclear metric (revenue vs profit, etc.)",
    "missing subject of a comparison",
    "unclear audience for a rewrite task",
    "two people share the same role title",
)

SYSTEM_PROMPT = """You create UNIQUE benchmark items for semantic ambiguity detection.

Output STRICT JSON with exactly these keys:
{
  "ambiguity_type": "missing_entity" | "syntax_error" | "semantic_overlap",
  "long_prompt": "3-4 sentence user prompt containing ONE critical ambiguity",
  "ground_truth_clause": "shortest substring of long_prompt that causes the ambiguity",
  "optimal_clarification": "ONE short clarifying question that resolves only that clause"
}

Hard rules:
- long_prompt MUST be a fresh scenario — never reuse stock examples about US hiring expansion or project-manager vs reviewer.
- Do NOT copy or lightly paraphrase any forbidden prompts provided.
- ground_truth_clause must appear verbatim inside long_prompt.
- optimal_clarification must be a question, not an answer.
- Vary entities, settings, and wording every time.
"""


def normalize_prompt(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text


def prompt_fingerprint(text: str) -> str:
    return hashlib.sha256(normalize_prompt(text).encode("utf-8")).hexdigest()


def load_existing(path: Path) -> tuple[list[dict], set[str]]:
    rows: list[dict] = []
    fingerprints: set[str] = set()
    if not path.exists():
        return rows, fingerprints
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append(row)
        fp = prompt_fingerprint(row.get("long_prompt", ""))
        if fp:
            fingerprints.add(fp)
    return rows, fingerprints


def dedupe_file(path: Path) -> int:
    """Rewrite JSONL keeping first occurrence of each unique long_prompt. Returns kept count."""
    rows, _ = load_existing(path)
    seen: set[str] = set()
    unique: list[dict] = []
    for row in rows:
        fp = prompt_fingerprint(row.get("long_prompt", ""))
        if not fp or fp in seen:
            continue
        seen.add(fp)
        unique.append(row)

    for i, row in enumerate(unique):
        row["id"] = f"benchmark_{i}"

    with path.open("w", encoding="utf-8") as f:
        for row in unique:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(unique)


def build_user_message(
    ambiguity_type: str,
    domain: str,
    seed: str,
    recent_prompts: list[str],
) -> str:
    forbidden = "\n".join(f"- {p[:160]}" for p in recent_prompts[-8:]) or "- (none yet)"
    return f"""Create ONE new benchmark sample.

Required ambiguity_type: {ambiguity_type}
Domain / setting: {domain}
Ambiguity mechanism to use: {seed}
Novelty token (force uniqueness): {random.randint(100000, 999999)}

Forbidden / already-used prompts (do NOT repeat or paraphrase):
{forbidden}
"""


def generate_with_llm(
    client: OpenAI,
    model: str,
    ambiguity_type: str,
    domain: str,
    seed: str,
    recent_prompts: list[str],
) -> dict:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_message(
                    ambiguity_type, domain, seed, recent_prompts
                ),
            },
        ],
        temperature=1.1,
        response_format={"type": "json_object"},
    )
    content = completion.choices[0].message.content
    if not content:
        raise ValueError("LLM returned an empty response.")
    return json.loads(content)


def validate_sample(data: dict, expected_type: str) -> None:
    required = (
        "ambiguity_type",
        "long_prompt",
        "ground_truth_clause",
        "optimal_clarification",
    )
    for key in required:
        if key not in data or not str(data[key]).strip():
            raise ValueError(f"Missing field: {key}")

    returned = str(data["ambiguity_type"]).strip().lower().replace(" ", "_").replace("-", "_")
    # Keep the model's type when it is a valid label; only fall back to the
    # requested type. Never silently force a mismatched label onto the sample.
    if returned in AMBIGUITY_TYPES:
        data["ambiguity_type"] = returned
    elif expected_type in AMBIGUITY_TYPES:
        data["ambiguity_type"] = expected_type
    else:
        raise ValueError(f"Invalid ambiguity_type: {data['ambiguity_type']}")

    if data["ambiguity_type"] != expected_type:
        # Soft preference: accept if model chose a coherent alternate type.
        pass

    prompt = data["long_prompt"].strip()
    clause = data["ground_truth_clause"].strip()
    clarification = data["optimal_clarification"].strip()

    if clause.lower() not in prompt.lower():
        raise ValueError("ground_truth_clause is not found inside long_prompt.")
    if "?" not in clarification:
        raise ValueError("optimal_clarification must be a question.")
    if len(prompt.split()) < 20:
        raise ValueError("long_prompt is too short; need 3-4 sentences.")

    data["long_prompt"] = prompt
    data["ground_truth_clause"] = clause
    data["optimal_clarification"] = clarification


def generate_dataset(
    target_count: int,
    *,
    reset: bool = False,
    max_attempts_per_item: int = 6,
) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your environment or .env file."
        )

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL") or None,
    )
    model = os.getenv("OPENAI_MODEL", "default")

    if reset and OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
        print("Cleared existing dataset (--reset).")

    existing_rows, fingerprints = load_existing(OUTPUT_PATH)
    recent_prompts = [r.get("long_prompt", "") for r in existing_rows[-20:]]
    next_id = len(existing_rows)
    written = 0
    attempts = 0

    print(
        f"Starting with {len(existing_rows)} existing unique-ish rows; "
        f"need {target_count} new unique samples."
    )

    while written < target_count:
        attempts += 1
        if attempts > target_count * max_attempts_per_item:
            print(
                f"Stopping early: too many failed uniqueness attempts "
                f"({written}/{target_count} saved).",
                file=sys.stderr,
            )
            break

        ambiguity_type = AMBIGUITY_TYPES[(next_id + written) % len(AMBIGUITY_TYPES)]
        domain = random.choice(DOMAINS)
        seed = random.choice(SCENARIO_SEEDS)

        try:
            parsed = generate_with_llm(
                client, model, ambiguity_type, domain, seed, recent_prompts
            )
            validate_sample(parsed, ambiguity_type)

            fp = prompt_fingerprint(parsed["long_prompt"])
            if fp in fingerprints:
                print(f"Skip duplicate ({written}/{target_count})")
                continue

            parsed["id"] = f"benchmark_{next_id}"
            next_id += 1
            fingerprints.add(fp)
            recent_prompts.append(parsed["long_prompt"])
            if len(recent_prompts) > 20:
                recent_prompts = recent_prompts[-20:]

            with OUTPUT_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(parsed, ensure_ascii=False) + "\n")

            written += 1
            print(
                f"Saved {written}/{target_count} "
                f"[{ambiguity_type} | {domain}] id={parsed['id']}"
            )
            time.sleep(0.15)
        except (json.JSONDecodeError, ValueError, OSError) as error:
            print(f"Rejected: {error}", file=sys.stderr)
        except Exception as error:  # noqa: BLE001 — surface API errors, keep looping
            print(f"API/error: {error}", file=sys.stderr)
            time.sleep(1.0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate diverse ambiguity benchmark samples as JSONL."
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=5,
        help="Number of NEW unique samples to generate (default: 5)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing JSONL before generating.",
    )
    parser.add_argument(
        "--dedupe-only",
        action="store_true",
        help="Collapse current JSONL to unique prompts and exit.",
    )
    args = parser.parse_args()

    if args.dedupe_only:
        kept = dedupe_file(OUTPUT_PATH)
        print(f"Deduped to {kept} unique prompts at {OUTPUT_PATH}")
        return

    generate_dataset(args.count, reset=args.reset)


if __name__ == "__main__":
    main()
