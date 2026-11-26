"""EcoGate exports. Imported by scripts/run_ecogate.py.

No other package exports a pre-generation energy gate.
"""

from ambiguity_layer.optimize.controller import baseline_answer_anyway_tokens, eco_process

__all__ = ["eco_process", "baseline_answer_anyway_tokens"]
