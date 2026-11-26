# Results report

Figures are computed from the JSON files in `results/`. No new model calls were made for this report.

## Interception quality

The three columns are not the same metric. Word overlap punishes paraphrases. The intent judge asks whether the question seeks the same information, and it relabeled 29 gold types. SBERT/NLI is the embedding score from the Python NLP run.

| Scorer | n | Errors | Detection | Type | Clause | Clarification |
|---|---:|---:|---:|---:|---:|---:|
| Word overlap | 56 | 0 | 0.946 | 0.357 | 0.643 | 0.316 avg score |
| Intent judge | 49 | 7 | 0.959 | 0.959 | 0.694 | 0.653 match rate |
| SBERT / NLI | 56 | 0 | 1.000 | 0.357 | 1.000 | 0.321 match rate |

![Quality under three scorers](../results/figures/quality_scorers.png)

The file label `ambiguity_type` is not an independent annotation. `scripts/create_dataset.py` requests the type by cycling missing entity, syntax error, and semantic overlap. The sentences labeled syntax error are grammatical. A confusion matrix against that field is not a result a journal can use, so it is not the figure below.

What can be reported is the decision the gate is for: ask before answering when the prompt is under-specified, and answer when the prompt already names the time, place, and quantity. The ambiguous set is the 56 generated prompts. The clear set is five controls written with an explicit date, place, or quantity.

The gate asks on 54 of 56 generated prompts and answers on 4 of 5 clear controls.

![Ask versus answer](../results/figures/ask_controls.png)

The old type figure compared predictions with the cycled file label, so every row piled into semantic overlap. The figure below ignores that field. The row is the type supported by the clarification question. The column is the type read from the prompt alone. The column is the type read from the prompt alone. Semantic overlap means the prompt has two readings: a pointer such as this issue or large that could apply to either of two metrics, both X and Y set against only one of them, conflicting beliefs, or the word or. A detail that is only unnamed is a missing entity.

```
[[34, 0, 0], [0, 1, 0], [3, 0, 18]]
```

![Type agreement](../results/figures/type_counts_corrected.png)

## Tokens

The previous token figure compared a flat overhead guess with zeros. That was not a measurement. The figure below counts words in the prompt itself and words in the clarifying question the gate emits. Both series are text, so neither is a row of zeros standing in for a model bill.

Mean prompt length is 46.8 words. Mean question length is 24.0 words. A question is emitted for 54 of 56 prompts.

![Word tokens per prompt](../results/figures/tokens_per_prompt.png)

The routing figure counts how many prompts stay on the local parser. It is a decision count, not a token measurement and not a metered energy trace.

| Route | Prompts |
|---|---:|
| NLP only | 51 |
| One diagnostic call | 5 |
| Answer directly | 0 |

![EcoGate routing](../results/figures/ecogate_routing.png)

## Source files

- `results/benchmark_full.json`
- `results/benchmark_full_intent.json`
- `results/benchmark_nlp.json`
- `results/ecogate.json`
