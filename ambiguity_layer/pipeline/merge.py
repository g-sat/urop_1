"""Merge original prompt with user clarification."""

from __future__ import annotations

from ambiguity_layer.llm import chat_text

SYSTEM = """Merge an ambiguous user prompt with their clarification into one clear,
self-contained prompt for a downstream model. Do not answer the prompt.
Output plain text only — the rewritten prompt."""


def merge_context(original_input: str, user_clarification: str) -> str:
    original = (original_input or "").strip()
    clarification = (user_clarification or "").strip()
    if not original or not clarification:
        raise ValueError("merge_context requires original_input and user_clarification.")

    return chat_text(
        [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Original prompt:\n\"\"\"{original}\"\"\"\n\n"
                    f"User clarification:\n\"\"\"{clarification}\"\"\"\n\n"
                    "Produce the merged unambiguous prompt."
                ),
            },
        ],
        temperature=0.2,
    )
