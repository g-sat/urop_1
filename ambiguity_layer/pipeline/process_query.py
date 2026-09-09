"""End-to-end interception orchestration."""

from __future__ import annotations

from typing import Any

from ambiguity_layer.llm import chat_text
from ambiguity_layer.nlp import analyze
from ambiguity_layer.pipeline.clarify import generate_clarification
from ambiguity_layer.pipeline.diagnose import diagnose_ambiguity
from ambiguity_layer.pipeline.merge import merge_context


def process_query(
    user_input: str,
    *,
    generate_final: bool = False,
    final_system_prompt: str | None = None,
) -> dict[str, Any]:
    text = (user_input or "").strip()
    if not text:
        raise ValueError("process_query requires non-empty user_input.")

    nlp = analyze(text)
    diagnosis = diagnose_ambiguity(text, nlp=nlp)

    if diagnosis["isAmbiguous"]:
        questions = generate_clarification(text, diagnosis)
        return {
            "status": "needs_clarification",
            "original_input": text,
            "diagnosis": diagnosis,
            "clarifying_questions": questions,
            "nlp_summary": nlp.summary_for_llm,
        }

    out: dict[str, Any] = {
        "status": "ready",
        "original_input": text,
        "diagnosis": diagnosis,
        "merged_prompt": text,
        "nlp_summary": nlp.summary_for_llm,
    }
    if generate_final:
        out["status"] = "answered"
        out["answer"] = _final_answer(text, final_system_prompt)
    return out


def resolve_with_clarification(
    original_input: str,
    user_clarification: str,
    *,
    generate_final: bool = False,
    final_system_prompt: str | None = None,
) -> dict[str, Any]:
    merged = merge_context(original_input, user_clarification)
    out: dict[str, Any] = {
        "status": "ready",
        "original_input": original_input,
        "user_clarification": user_clarification,
        "merged_prompt": merged,
    }
    if generate_final:
        out["status"] = "answered"
        out["answer"] = _final_answer(merged, final_system_prompt)
    return out


def _final_answer(prompt: str, system_prompt: str | None) -> str:
    return chat_text(
        [
            {
                "role": "system",
                "content": system_prompt
                or "You are a helpful assistant. Answer clearly and accurately.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )
