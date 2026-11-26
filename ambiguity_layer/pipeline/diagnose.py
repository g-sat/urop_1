"""Ambiguity diagnosis: NLP priors + LLM confirmation."""

from __future__ import annotations

from typing import Any

from ambiguity_layer import config
from ambiguity_layer.llm import chat_json
from ambiguity_layer.nlp import NLPAnalysis, analyze

DIAGNOSTIC_SYSTEM = """You are an Ambiguity Diagnostics agent.
You receive (1) the user prompt and (2) deterministic NLP ambiguity priors
(NER, coreference risks, WSD/homonyms, dependency-scope cues, ranked span proposals).

Your job:
- Decide if a downstream LLM would need clarification before answering reliably.
- Use a proposed span only when it is the unclear part. A high score is not an order.
- Speaker words (I, we, our, you) are not ambiguity.
- missing_entity means a required thing, time, metric, or version is absent.
- semantic_overlap means the same words have two real readings.
- syntax_error means the sentence is broken. A grammatical sentence is not a syntax error.
- Do not default to semantic_overlap.
- Bias toward isAmbiguous=true when any critical detail is missing or multiply readable.
- Return STRICT JSON only:
{
  "isAmbiguous": boolean,
  "ambiguityType": "missing_entity" | "syntax_error" | "semantic_overlap",
  "problematicClause": "string",
  "reasoning": "string",
  "nlpSpanUsed": boolean,
  "nlpSpanKind": "string|null"
}
"""


def diagnose_ambiguity(user_input: str, nlp: NLPAnalysis | None = None) -> dict[str, Any]:
    text = (user_input or "").strip()
    if not text:
        raise ValueError("diagnose_ambiguity requires non-empty input.")

    nlp = nlp or analyze(text)
    span_block = "\n".join(
        f'{i}. kind={s.kind} type_prior={s.suggested_type} score={s.score:.2f} '
        f'text="{s.text}" detail={s.detail}'
        for i, s in enumerate(nlp.proposed_spans, 1)
    ) or "(no spans proposed)"

    messages = [
        {"role": "system", "content": DIAGNOSTIC_SYSTEM},
        {
            "role": "user",
            "content": (
                f"User prompt:\n\"\"\"{text}\"\"\"\n\n"
                f"{nlp.summary_for_llm}\n\n"
                f"Span candidates to choose from when possible:\n{span_block}\n\n"
                "Diagnose ambiguity now."
            ),
        },
    ]

    raw = chat_json(messages, temperature=0.0)
    result = _validate_diagnosis(raw, text, nlp)
    result["nlp"] = {
        "prior_type_scores": nlp.prior_type_scores,
        "proposed_spans": [s.__dict__ for s in nlp.proposed_spans],
        "entities": nlp.entities,
        "coref_cues": nlp.coref_cues,
        "wsd_cues": nlp.wsd_cues,
    }
    return result


def _validate_diagnosis(raw: dict[str, Any], text: str, nlp: NLPAnalysis) -> dict[str, Any]:
    is_ambiguous = bool(raw.get("isAmbiguous"))
    atype = str(raw.get("ambiguityType") or "").strip()
    if atype not in config.AMBIGUITY_TYPES:
        # fall back to strongest NLP prior
        atype = max(nlp.prior_type_scores, key=nlp.prior_type_scores.get) if nlp.prior_type_scores else "missing_entity"
        if atype not in config.AMBIGUITY_TYPES:
            atype = "missing_entity"

    clause = str(raw.get("problematicClause") or "").strip()
    if is_ambiguous and not clause and nlp.proposed_spans:
        clause = nlp.proposed_spans[0].text

    if is_ambiguous and clause and clause.lower() not in text.lower():
        # snap to best overlapping NLP span if LLM invented text
        for s in nlp.proposed_spans:
            if s.text.lower() in text.lower():
                clause = s.text
                raw["nlpSpanUsed"] = True
                raw["nlpSpanKind"] = s.kind
                break

    reasoning = str(raw.get("reasoning") or "").strip() or "No reasoning provided."

    return {
        "isAmbiguous": is_ambiguous,
        "ambiguityType": atype if is_ambiguous else None,
        "problematicClause": clause if is_ambiguous else "",
        "reasoning": reasoning,
        "nlpSpanUsed": bool(raw.get("nlpSpanUsed")),
        "nlpSpanKind": raw.get("nlpSpanKind"),
    }
