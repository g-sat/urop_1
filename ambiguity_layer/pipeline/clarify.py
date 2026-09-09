"""Generate 1–2 clause-targeted clarifying questions."""

from __future__ import annotations

from typing import Any

from ambiguity_layer.llm import chat_json

SYSTEM = """You generate minimal clarifying questions for an ambiguity interception system.
Rules:
- Produce strictly 1 or 2 questions.
- Target ONLY the problematic clause / NLP evidence provided.
- Do not answer the original prompt.
- Return STRICT JSON: {"questions": ["...", "..."]}
"""


def generate_clarification(
    original_input: str,
    diagnosis: dict[str, Any],
) -> list[str]:
    if not diagnosis.get("isAmbiguous"):
        raise ValueError("generate_clarification called on non-ambiguous diagnosis.")

    nlp = diagnosis.get("nlp") or {}
    messages = [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": (
                f"Original prompt:\n\"\"\"{original_input}\"\"\"\n\n"
                f"ambiguityType: {diagnosis.get('ambiguityType')}\n"
                f"problematicClause: {diagnosis.get('problematicClause')}\n"
                f"reasoning: {diagnosis.get('reasoning')}\n"
                f"nlpSpanKind: {diagnosis.get('nlpSpanKind')}\n"
                f"coref_cues: {nlp.get('coref_cues')}\n"
                f"wsd_cues: {nlp.get('wsd_cues')}\n\n"
                "Generate 1 or 2 minimal clarifying questions."
            ),
        },
    ]
    raw = chat_json(messages, temperature=0.3)
    questions = raw.get("questions")
    if not isinstance(questions, list):
        raise ValueError("Clarification JSON missing questions array.")
    cleaned = [str(q).strip() for q in questions if str(q).strip()]
    if not 1 <= len(cleaned) <= 2:
        raise ValueError(f"Expected 1–2 questions, got {len(cleaned)}.")
    return cleaned
