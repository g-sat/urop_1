# Evaluation Metrics (Python NLP + LLM stack)

Scoring uses **semantic similarity**, not exact word overlap.

## Pipeline metrics (`scripts/run_benchmark.py`)

| Metric | Meaning |
|--------|---------|
| `detection_rate` | Fraction where interception fired (`isAmbiguous=true`) |
| `type_accuracy` | Predicted `ambiguityType` equals gold label |
| `clause_hit_rate` | SBERT similarity between predicted & gold clause ≥ 0.45 |
| `clarification_match_rate` | SBERT (+ optional NLI) says system question asks for same info as gold |
| `avg_clause_score` | Mean SBERT clause similarity |
| `avg_clarification_score` | Mean SBERT / SBERT+NLI clarification score |
| `nlp_span_usage_rate` | Fraction where diagnosis used an NLP-proposed span |

## Clarification scoring

1. **SBERT** (`all-MiniLM-L6-v2`): max cosine(predicted question, gold question); match if ≥ 0.55  
2. **Optional NLI** (`nli-deberta-v3-small`): entailment-style equivalence  
3. Combined when NLI enabled: average scores; match if either flags match and mean ≥ 0.45  

No Jaccard / token-overlap success criterion.

## Analysis metrics (`scripts/run_analysis.py`)

| Output | Meaning |
|--------|---------|
| Prompt clusters | K-Means over SBERT embeddings of `long_prompt` |
| Confusion matrix | Gold vs predicted ambiguity types |
| Miss attribution | Which NLP phenomenon (`coref`, `wsd`, `ner_underspec`, …) tops the span list on failures |

## NLP priors used in diagnosis

| Signal | Role |
|--------|------|
| Tokenization / POS / deps | Structure + scope cues |
| NER | Entities present vs missing |
| Coref heuristics | Pronouns/demonstratives with multiple antecedents |
| Homonym lexicon (WSD) | `bank`, `crane`, … → `semantic_overlap` |
| Underspecified time | `Monday` without absolute date → `missing_entity` |
| Ranked span proposals | LLM chooses `problematicClause` among NLP candidates |
