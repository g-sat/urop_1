"""Template clarifications from NLP spans. Called only by controller.py.

pipeline/clarify.py always calls an LLM. This module does not.
Reads NLPAnalysis (spans, coref cues, WSD cues). Returns 1-2 question strings.

User request: combine the interception layer with power and token optimisation
built from future-work gaps in top-venue papers.
"""

from __future__ import annotations

from ambiguity_layer.nlp.analyzer import NLPAnalysis, SpanSignal


def questions_from_nlp(nlp: NLPAnalysis, limit: int = 2) -> list[str]:
    questions: list[str] = []
    for span in nlp.proposed_spans:
        question = _one(span, nlp)
        if question and question not in questions:
            questions.append(question)
        if len(questions) >= limit:
            break
    if not questions:
        questions.append("Which missing detail should I use before answering?")
    return questions[:limit]


def _one(span: SpanSignal, nlp: NLPAnalysis) -> str:
    if span.kind == "coref":
        cue = next((c for c in nlp.coref_cues if c["pronoun"] == span.text), None)
        options = ", ".join(cue["antecedents"][-3:]) if cue else "the earlier noun phrases"
        return f"What does '{span.text}' refer to: {options}?"
    if span.kind == "wsd":
        cue = next((c for c in nlp.wsd_cues if c["token"] == span.text), None)
        senses = ", ".join(cue["senses"][:3]) if cue else "the possible meanings"
        return f"Which meaning of '{span.text}' do you intend: {senses}?"
    if span.kind == "ner_underspec":
        return f"Which exact date or time does '{span.text}' refer to?"
    if span.kind == "vague_np":
        return f"What exactly does '{span.text}' refer to?"
    if span.kind == "dep_scope":
        return f"Does '{span.text}' apply to both parts, or only one of them?"
    return f"Can you clarify '{span.text}'?"
