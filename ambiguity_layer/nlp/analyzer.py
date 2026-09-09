"""spaCy-backed linguistic analysis: POS, NER, deps, coref cues, WSD priors."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Any

import spacy
from spacy.tokens import Doc, Token

from ambiguity_layer import config
from ambiguity_layer.nlp.lexicon import (
    AMBIGUOUS_DEMONSTRATIVES,
    HOMONYMS,
    UNDERSPECIFIED_TIME,
)


@dataclass
class SpanSignal:
    text: str
    start: int
    end: int
    kind: str  # coref | ner_underspec | wsd | dep_scope | vague_np
    score: float
    detail: str
    suggested_type: str  # missing_entity | semantic_overlap | syntax_error


@dataclass
class NLPAnalysis:
    text: str
    tokens: list[dict[str, Any]] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    coref_cues: list[dict[str, Any]] = field(default_factory=list)
    wsd_cues: list[dict[str, Any]] = field(default_factory=list)
    proposed_spans: list[SpanSignal] = field(default_factory=list)
    prior_type_scores: dict[str, float] = field(default_factory=dict)
    summary_for_llm: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@lru_cache(maxsize=1)
def load_nlp():
    try:
        return spacy.load(config.SPACY_MODEL)
    except OSError as exc:
        raise RuntimeError(
            f"spaCy model '{config.SPACY_MODEL}' not installed. "
            f"Run: python -m spacy download {config.SPACY_MODEL}"
        ) from exc


def analyze(text: str) -> NLPAnalysis:
    """Full input analysis used as ambiguity priors for the diagnostic LLM."""
    nlp = load_nlp()
    doc = nlp(text.strip())
    analysis = NLPAnalysis(text=doc.text)

    analysis.tokens = [
        {
            "text": t.text,
            "lemma": t.lemma_.lower(),
            "pos": t.pos_,
            "tag": t.tag_,
            "dep": t.dep_,
            "head": t.head.text,
            "i": t.i,
            "idx": t.idx,
        }
        for t in doc
        if not t.is_space
    ]

    analysis.entities = [
        {
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
        }
        for ent in doc.ents
    ]

    analysis.dependencies = [
        {
            "gov": t.head.text,
            "dep": t.dep_,
            "dep_text": t.text,
            "span": doc[min(t.i, t.head.i) : max(t.i, t.head.i) + 1].text,
        }
        for t in doc
        if t.dep_ in {"prep", "pobj", "relcl", "acl", "amod", "nmod", "dobj", "nsubj"}
        and not t.is_space
    ]

    analysis.coref_cues = _coref_ambiguity(doc)
    analysis.wsd_cues = _wsd_cues(doc)
    analysis.proposed_spans = _propose_spans(doc, analysis)
    analysis.prior_type_scores = _prior_type_scores(analysis)
    analysis.summary_for_llm = _format_summary(analysis)
    return analysis


def _noun_chunks_before(doc: Doc, token: Token) -> list[str]:
    chunks = []
    for chunk in doc.noun_chunks:
        if chunk.end <= token.i:
            chunks.append(chunk.text)
    return chunks


def _coref_ambiguity(doc: Doc) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    for t in doc:
        low = t.text.lower()
        if low not in AMBIGUOUS_DEMONSTRATIVES and t.pos_ != "PRON":
            continue
        if t.pos_ not in {"PRON", "DET"} and low not in AMBIGUOUS_DEMONSTRATIVES:
            continue
        antecedents = _noun_chunks_before(doc, t)
        # Multiple plausible antecedents → coreference ambiguity
        if len(antecedents) >= 2:
            cues.append(
                {
                    "pronoun": t.text,
                    "start": t.idx,
                    "end": t.idx + len(t.text),
                    "antecedents": antecedents[-4:],
                    "detail": f"'{t.text}' has {len(antecedents)} prior noun-phrase antecedents",
                }
            )
    return cues


def _wsd_cues(doc: Doc) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    seen: set[str] = set()
    for t in doc:
        lemma = t.lemma_.lower()
        if lemma in HOMONYMS and lemma not in seen:
            seen.add(lemma)
            senses = HOMONYMS[lemma]
            cues.append(
                {
                    "token": t.text,
                    "lemma": lemma,
                    "start": t.idx,
                    "end": t.idx + len(t.text),
                    "senses": senses,
                    "detail": f"Homonym '{lemma}' admits senses: {', '.join(senses)}",
                }
            )
    return cues


def _underspecified_time_spans(doc: Doc) -> list[SpanSignal]:
    spans: list[SpanSignal] = []
    has_absolute_date = any(e.label_ in {"DATE"} and any(ch.isdigit() for ch in e.text) for e in doc.ents)
    for t in doc:
        if t.lemma_.lower() in UNDERSPECIFIED_TIME or t.text.lower() in UNDERSPECIFIED_TIME:
            if has_absolute_date:
                continue
            spans.append(
                SpanSignal(
                    text=t.text,
                    start=t.idx,
                    end=t.idx + len(t.text),
                    kind="ner_underspec",
                    score=0.82,
                    detail=f"Temporal expression '{t.text}' lacks absolute date/timezone anchor",
                    suggested_type="missing_entity",
                )
            )
    return spans


def _vague_nominal_spans(doc: Doc) -> list[SpanSignal]:
    vague = {"metric", "metrics", "issue", "record", "records", "result", "results", "thing", "stuff", "item"}
    spans: list[SpanSignal] = []
    for chunk in doc.noun_chunks:
        head = chunk.root.lemma_.lower()
        if head in vague:
            # Prefer longer phrase containing the vague head
            spans.append(
                SpanSignal(
                    text=chunk.text,
                    start=chunk.start_char,
                    end=chunk.end_char,
                    kind="vague_np",
                    score=0.7,
                    detail=f"Vague nominal '{chunk.text}' may be underspecified",
                    suggested_type="missing_entity",
                )
            )
    return spans


def _dep_scope_spans(doc: Doc) -> list[SpanSignal]:
    """Coordination / attachment that often creates scope ambiguity."""
    spans: list[SpanSignal] = []
    for t in doc:
        if t.dep_ == "cc" and t.head.pos_ in {"NOUN", "PROPN", "VERB", "ADJ"}:
            left = t.head
            rights = [c for c in t.head.children if c.dep_ == "conj"]
            if rights:
                start = min(left.idx, t.idx, *(r.idx for r in rights))
                end = max(
                    left.idx + len(left),
                    t.idx + len(t),
                    *(r.idx + len(r) for r in rights),
                )
                phrase = doc.text[start:end]
                spans.append(
                    SpanSignal(
                        text=phrase,
                        start=start,
                        end=end,
                        kind="dep_scope",
                        score=0.65,
                        detail=f"Coordination scope around '{phrase}' may admit multiple readings",
                        suggested_type="semantic_overlap",
                    )
                )
    return spans


def _propose_spans(doc: Doc, analysis: NLPAnalysis) -> list[SpanSignal]:
    spans: list[SpanSignal] = []

    for cue in analysis.coref_cues:
        spans.append(
            SpanSignal(
                text=cue["pronoun"],
                start=cue["start"],
                end=cue["end"],
                kind="coref",
                score=min(0.95, 0.55 + 0.1 * len(cue["antecedents"])),
                detail=cue["detail"] + f"; candidates={cue['antecedents']}",
                suggested_type="semantic_overlap",
            )
        )

    for cue in analysis.wsd_cues:
        spans.append(
            SpanSignal(
                text=cue["token"],
                start=cue["start"],
                end=cue["end"],
                kind="wsd",
                score=0.88,
                detail=cue["detail"],
                suggested_type="semantic_overlap",
            )
        )

    spans.extend(_underspecified_time_spans(doc))
    spans.extend(_vague_nominal_spans(doc))
    spans.extend(_dep_scope_spans(doc))

    # Missing DATE entity when temporal language is present but no DATE NER
    temporal_words = any(t.lemma_.lower() in UNDERSPECIFIED_TIME for t in doc)
    if temporal_words and not any(e["label"] == "DATE" for e in analysis.entities):
        pass  # already covered by underspecified time spans

    # Deduplicate by (start,end,kind), keep highest score
    best: dict[tuple[int, int, str], SpanSignal] = {}
    for s in spans:
        key = (s.start, s.end, s.kind)
        if key not in best or s.score > best[key].score:
            best[key] = s

    ranked = sorted(best.values(), key=lambda x: (-x.score, x.start))
    return ranked[:8]


def _prior_type_scores(analysis: NLPAnalysis) -> dict[str, float]:
    scores = {"missing_entity": 0.0, "syntax_error": 0.0, "semantic_overlap": 0.0}
    for s in analysis.proposed_spans:
        scores[s.suggested_type] = max(scores[s.suggested_type], float(s.score))

    # Very short / fragmentary text → syntax prior
    if len(analysis.text.split()) < 6 or analysis.text.strip().endswith((",", "and", "or", "the")):
        scores["syntax_error"] = max(scores["syntax_error"], 0.6)

    return scores


def _format_summary(analysis: NLPAnalysis) -> str:
    lines = ["NLP ambiguity priors (deterministic linguistic analysis):"]

    if analysis.entities:
        ents = ", ".join(f"{e['text']}[{e['label']}]" for e in analysis.entities[:12])
        lines.append(f"- NER entities present: {ents}")
    else:
        lines.append("- NER entities present: (none)")

    if analysis.coref_cues:
        for c in analysis.coref_cues[:4]:
            lines.append(f"- Coref risk: {c['detail']}")
    else:
        lines.append("- Coref risk: none flagged")

    if analysis.wsd_cues:
        for w in analysis.wsd_cues[:4]:
            lines.append(f"- WSD/homonym: {w['detail']}")
    else:
        lines.append("- WSD/homonym: none flagged")

    lines.append("- Proposed problematic spans (ranked):")
    if not analysis.proposed_spans:
        lines.append("  (none — prompt may still be ambiguous for missing task/entity reasons)")
    for i, s in enumerate(analysis.proposed_spans, 1):
        lines.append(
            f"  {i}. [{s.kind} | prior={s.suggested_type} | score={s.score:.2f}] "
            f'"{s.text}" - {s.detail}'
        )

    lines.append(
        "- Type prior strengths: "
        + ", ".join(
            f"{k}={v:.2f}" for k, v in analysis.prior_type_scores.items()
        )
    )
    return "\n".join(lines)
