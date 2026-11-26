"""Pre-generation routing.

Called by ambiguity_layer/optimize/controller.py (decide) and
scripts/run_ecogate.py (decide). No existing file chooses to skip the LLM
before decoding an answer. Reads NLPAnalysis.proposed_spans and
config.ECO_TAU_HIGH / ECO_TAU_LOW. Returns one of nlp_clarify, llm_diagnose, answer.

User verbatim: "i need you to plan on building something novel combuoining this and also include power and token optimisation too built in that is novel i am not talking about something that is just looking novel for u but find out all the optimisation paper from top impact journals abd they will mention that they can do something in the future and all so do that impliment that talke a list of 20 papers from the top journals and find ou what will make my paper novel and build that"
"""

from __future__ import annotations

from ambiguity_layer import config
from ambiguity_layer.nlp.analyzer import NLPAnalysis

NLP_CLARIFY = "nlp_clarify"
LLM_DIAGNOSE = "llm_diagnose"
ANSWER = "answer"


def best_span_score(nlp: NLPAnalysis) -> float:
    if not nlp.proposed_spans:
        return 0.0
    return max(float(s.score) for s in nlp.proposed_spans)


def decide(nlp: NLPAnalysis) -> str:
    score = best_span_score(nlp)
    if score >= config.ECO_TAU_HIGH:
        return NLP_CLARIFY
    if score < config.ECO_TAU_LOW:
        return ANSWER
    return LLM_DIAGNOSE
