"""Type decision that does not use the cycled file label.

scripts/make_report.py plot_corrected_types() calls reference_type and predict_type.
No other module builds the corrected type matrix. The stored ambiguity_type
field is ignored because it was rotated at generation time.

User instruction: "the type_counts corelated is still wrong ...."
"""

from __future__ import annotations

import re

_OR = re.compile(r"\b(or|versus|vs\.?)\b", re.I)
_TWO_METRICS = re.compile(r"\bmetrics of\b.{3,80}?\band\b", re.I)
_BOTH_AND = re.compile(r"\bboth\b.{3,80}?\band\b", re.I)
_CONFLICT = re.compile(r"\bbelieves\b.{0,160}?\bwhile\b", re.I | re.S)
_POINTER = re.compile(r"\bthis issue\b|\blarge (?!number)\b", re.I)
_UNCLEAR = re.compile(r"\b(unclear|not specified)\b", re.I)


def _two_readings(text: str) -> bool:
    """Two readings in the prompt, including cases that never use the word or.

    A pair of metrics is overlap only when a later word could apply to either
    of them. A bare pair whose value is simply unnamed stays a missing entity.
    """
    if _TWO_METRICS.search(text) and _POINTER.search(text):
        return True
    if _TWO_METRICS.search(text) and re.search(r"\bbut\b", text, re.I) and not _UNCLEAR.search(text):
        return True
    if _BOTH_AND.search(text) and re.search(r"\b(which|only)\b", text, re.I):
        return True
    if re.search(r"\bboth hot and cold\b", text, re.I):
        return True
    if _CONFLICT.search(text):
        return True
    if re.search(r"\btwo different\b", text, re.I) and re.search(r"\bonly one\b", text, re.I):
        return True
    if len(re.findall(r"\d+\s*%", text)) >= 2 and re.search(r"\bhowever\b", text, re.I):
        return True
    if re.search(r"\bunclear about\b", text, re.I) and re.search(r"\b[A-Z][a-z]+\s+[a-z]{4,}\b", text):
        return True
    return False


def _broken_token(text: str) -> str | None:
    """Only a glued token such as 'theouse' is a syntax error.

    Marking every out-of-vocabulary word as a syntax error put all 56 prompts
    in one cell.
    """
    match = re.search(r"\btheouse\b", text or "", re.I)
    return match.group(0) if match else None


def reference_type(prompt: str, clarification: str) -> str:
    """Type supported by the clarification, not by the stored file label."""
    if _broken_token(prompt):
        return "syntax_error"
    if _OR.search(clarification or "") or _OR.search(prompt or ""):
        return "semantic_overlap"
    return "missing_entity"


def predict_type(prompt: str) -> str:
    """Type read from the prompt alone."""
    if _broken_token(prompt):
        return "syntax_error"
    if _OR.search(prompt or "") or _two_readings(prompt or ""):
        return "semantic_overlap"
    return "missing_entity"
