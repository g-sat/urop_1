# Active Ambiguity Interception Layer

Python-only research stack: **NLP ambiguity priors + LLM diagnosis/clarification**.

## Layout

```
ambiguity_layer/
  nlp/           # POS, NER, deps, coref cues, WSD, span proposals
  pipeline/      # diagnose → clarify → merge → process_query
  eval/          # SBERT + NLI clarification/clause scoring
  analysis/      # clustering, confusion matrix, error attribution
  llm/           # OpenAI-compatible client (LLM7)
scripts/
  setup_nlp.py
  demo.py
  create_dataset.py
  run_benchmark.py
  run_analysis.py
docs/METRICS.md
```

## Setup

```powershell
.\myVenv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/setup_nlp.py
```

Configure `.env` (see `.env.example`).

## Run

```powershell
python scripts/demo.py
python scripts/run_benchmark.py --limit 5
python scripts/run_benchmark.py --out results/benchmark_nlp.json
python scripts/run_analysis.py --results results/benchmark_nlp.json
python scripts/create_dataset.py -n 20
```

## Method (short)

1. **NLP analysis** extracts entities, coref risks, homonyms, dependency-scope cues, and ranked problematic spans.  
2. **LLM diagnosis** consumes those priors and confirms `isAmbiguous` / type / clause (preferring NLP spans).  
3. **Clarification** asks 1–2 questions targeting the clause; execution halts.  
4. **Evaluation** uses sentence embeddings (+ optional NLI), not word overlap.
