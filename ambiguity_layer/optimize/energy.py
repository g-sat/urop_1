"""Token and energy ledger for one intercepted query.

Called from ambiguity_layer/optimize/controller.py and scripts/run_ecogate.py.
No other module accounts joules. Reads config energy factors. Writes a dict
via to_dict(); does not touch the dataset file.

User request: combine the interception layer with power and token optimisation
built from future-work gaps in top-venue papers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ambiguity_layer import config


@dataclass
class EnergyLedger:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    llm_calls: int = 0
    nlp_seconds: float = 0.0
    action: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def joules(self) -> float:
        llm = (
            self.prompt_tokens * config.INPUT_JOULES_PER_TOKEN
            + self.completion_tokens * config.OUTPUT_JOULES_PER_TOKEN
        )
        cpu = self.nlp_seconds * config.CPU_WATTS
        return llm + cpu

    def grams_co2(self) -> float:
        return self.joules() / 3.6e6 * config.GRID_GCO2_PER_KWH

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "llm_calls": self.llm_calls,
            "nlp_seconds": round(self.nlp_seconds, 4),
            "joules": round(self.joules(), 4),
            "grams_co2": round(self.grams_co2(), 6),
            "notes": self.notes,
        }
