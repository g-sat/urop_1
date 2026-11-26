# What makes this paper different

This note is linked from README.md. It does not replace docs/METRICS.md.
METRICS.md scores detection and clarification. This file states the new claim:
token and energy control before generation.

User instruction: plan and build something novel that combines the ambiguity
layer with power and token optimisation, taken from future-work statements in
top-venue papers, using a list of 20 papers.

The contribution is **EcoGate**: a pre-generation controller that spends
linguistic computation first, skips the LLM when that evidence is already
strong, and refuses to decode an answer while the prompt is still ambiguous.

## Twenty papers and the opening they leave

| # | Paper | Venue | What they leave open |
|---|--------|--------|----------------------|
| 1 | FrugalGPT (Chen, Zaharia, Zou) | TMLR 2024 | They name environmental impact and uncertainty as future objectives. The cascade still generates an answer before it can stop. |
| 2 | RouteLLM (Ong et al.) | ICLR 2025 | Routes by model strength, not by refusing an ambiguous query. |
| 3 | LLMLingua (Jiang et al.) | EMNLP 2023 | Compresses the prompt, then still answers it. |
| 4 | CALM (Schuster et al.) | NeurIPS 2022 | Early exit is per token during decoding. The request is still answered. |
| 5 | Speculative decoding (Leviathan, Kalman, Matias) | ICML 2023 | Faster decoding of the same answer. |
| 6 | LayerSkip (Elhoushi et al.) | ACL 2024 | Self-speculative early exit. Does not decide whether decode should start. |
| 7 | PagedAttention / vLLM (Kwon et al.) | SOSP 2023 | KV-cache memory. The query is assumed to be worth generating. |
| 8 | PowerInfer (Song et al.) | SOSP 2024 | Power of the forward pass, not power avoided by not calling the model. |
| 9 | BLOOM carbon footprint (Luccioni, Viguier, Ligozat) | JMLR 2023 | Better reporting of inference emissions. No policy that withholds generation. |
| 10 | SpecEE | ISCA 2025 | Early-exit power inside the forward pass. A skipped request is outside the design. |
| 11 | Efficient LLM serving survey | ACM Computing Surveys | Future work stays on faster decoding. |
| 12 | Language model cascades, token-level uncertainty | arXiv 2404.10136 | Deferral starts after generation evidence exists. |
| 13 | AmbigQA (Min et al.) | EMNLP 2020 | Answering every interpretation multiplies output tokens. |
| 14 | Semantic uncertainty (Kuhn et al.) | ICLR 2023 | Uncertainty is bought by extra sampled answers. |
| 15 | SelfCheckGPT (Manakul et al.) | EMNLP 2023 | More answers, then a consistency check. |
| 16 | Clarify When Necessary | NAACL Findings 2025 | A score for when to ask. Not tied to joules, and not a zero-token first stage. |
| 17 | From Answers to Interpretations | EMNLP Findings 2026 | They estimate ambiguity without answers. Their future work is to use that estimate to choose an action. EcoGate is that action. |
| 18 | Steerable clarification policies | arXiv 2512.04068 | A learned cost per word. No zero-token linguistic stage and no watt model. |
| 19 | RegretBench | arXiv 2607.21143 | Future work is policy optimisation under interaction cost, not accelerator energy. |
| 20 | Diagnostic clarifying questions | EMNLP 2026 | Question quality, not the energy of refusing a premature answer. |

## The claim

Cost and power papers assume an answer should be produced, then make it cheaper.
Ambiguity papers either pay for many answers or stop at a score.

EcoGate does three things those systems do not do together:

1. A linguistic first stage at zero LLM tokens. If the top span score is at least `ECO_TAU_HIGH` (default 0.80), the system asks a template question and never calls the model.
2. No decode while the prompt is ambiguous. Output tokens dominate energy because decode is memory-bandwidth bound. EcoGate does not spend them on a guessed answer.
3. A reported energy ledger in `ambiguity_layer/optimize/energy.py`. It is a comparison model, not a wall-meter claim.

Uncertain prompts still get one diagnostic LLM call. Clear prompts skip diagnosis.

## How to run

```powershell
python scripts/run_ecogate.py
python scripts/run_ecogate.py --live
```

The default run is offline. `--live` calls the API only on the uncertain band.
