"""EcoGate controller.

Called by scripts/run_ecogate.py and ambiguity_layer/optimize/__init__.py.
No existing pipeline skips generation and the diagnostic LLM under an energy
budget. Reads the user string and NLP analysis. Writes a result dict with an
energy ledger. Does not modify the benchmark file.

User verbatim: "include power and token optimisation too built in" from future
work in top-venue optimisation papers, and build that system.
"""

from __future__ import annotations

import time
from typing import Any

from ambiguity_layer.llm.client import get_usage, reset_usage
from ambiguity_layer.nlp import analyze
from ambiguity_layer.optimize.energy import EnergyLedger
from ambiguity_layer.optimize.policy import ANSWER, NLP_CLARIFY, decide
from ambiguity_layer.optimize.templates import questions_from_nlp
from ambiguity_layer.pipeline.clarify import generate_clarification
from ambiguity_layer.pipeline.diagnose import diagnose_ambiguity
from ambiguity_layer.pipeline.process_query import _final_answer


def eco_process(user_input: str, *, generate_final: bool = False) -> dict[str, Any]:
    text = (user_input or "").strip()
    if not text:
        raise ValueError("eco_process requires non-empty user_input.")

    reset_usage()
    t0 = time.perf_counter()
    nlp = analyze(text)
    nlp_seconds = time.perf_counter() - t0
    action = decide(nlp)
    ledger = EnergyLedger(action=action, nlp_seconds=nlp_seconds)
    top = nlp.proposed_spans[0] if nlp.proposed_spans else None
    answer = None

    if action == NLP_CLARIFY:
        questions_out = questions_from_nlp(nlp)
        diagnosis = {
            "isAmbiguous": True,
            "ambiguityType": top.suggested_type if top else "semantic_overlap",
            "problematicClause": top.text if top else "",
            "reasoning": "Linguistic prior was high, so the diagnostic LLM was skipped.",
            "nlpSpanUsed": True,
            "nlpSpanKind": top.kind if top else None,
        }
        status = "needs_clarification"
        ledger.notes.append("zero LLM calls; template clarification")
    elif action == ANSWER:
        diagnosis = {
            "isAmbiguous": False,
            "ambiguityType": None,
            "problematicClause": "",
            "reasoning": "No strong linguistic ambiguity prior.",
            "nlpSpanUsed": False,
            "nlpSpanKind": None,
        }
        questions_out = []
        status = "ready"
        ledger.notes.append("skipped diagnostic LLM")
        if generate_final:
            answer = _final_answer(text, None)
            status = "answered"
    else:
        diagnosis = diagnose_ambiguity(text, nlp=nlp)
        if diagnosis["isAmbiguous"]:
            if top is not None:
                questions_out = questions_from_nlp(nlp)
                ledger.notes.append("diagnostic LLM only; template clarification")
            else:
                questions_out = generate_clarification(text, diagnosis)
                ledger.notes.append("diagnostic LLM and clarification LLM")
            status = "needs_clarification"
        else:
            questions_out = []
            status = "ready"
            if generate_final:
                answer = _final_answer(text, None)
                status = "answered"
            ledger.notes.append("diagnostic LLM; answer only if the prompt is clear")

    usage = get_usage()
    ledger.prompt_tokens = usage["prompt_tokens"]
    ledger.completion_tokens = usage["completion_tokens"]
    ledger.llm_calls = usage["calls"]

    out: dict[str, Any] = {
        "status": status,
        "action": action,
        "original_input": text,
        "diagnosis": diagnosis,
        "clarifying_questions": questions_out,
        "energy": ledger.to_dict(),
        "nlp_summary": nlp.summary_for_llm,
    }
    if answer is not None:
        out["answer"] = answer
    return out


def baseline_answer_anyway_tokens(user_input: str) -> dict[str, int]:
    """Length estimate of diagnose + clarify + answer, even if ambiguous.

    Used by scripts/run_ecogate.py. Does not call an API.
    """
    prompt_body = max(1, len((user_input or "").strip()) // 4)
    return {
        "prompt_tokens": (900 + prompt_body) + (400 + prompt_body) + (120 + prompt_body),
        "completion_tokens": 80 + 40 + 180,
        "llm_calls": 3,
    }
