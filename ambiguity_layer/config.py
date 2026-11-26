"""Project configuration loaded from environment / .env."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.llm7.io/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "default")

SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
NLI_MODEL = os.getenv("NLI_MODEL", "cross-encoder/nli-deberta-v3-small")

DATASET_PATH = ROOT / "ambiguity_benchmark.jsonl"
RESULTS_DIR = ROOT / "results"
ANALYSIS_DIR = ROOT / "analysis_outputs"

AMBIGUITY_TYPES = ("missing_entity", "syntax_error", "semantic_overlap")

# How many times to wait out provider 429s before failing a call
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))

# EcoGate thresholds. Read by ambiguity_layer/optimize/policy.py.
ECO_TAU_HIGH = float(os.getenv("ECO_TAU_HIGH", "0.80"))
ECO_TAU_LOW = float(os.getenv("ECO_TAU_LOW", "0.35"))

# Relative energy model. Read by ambiguity_layer/optimize/energy.py.
# Output tokens dominate because decode is memory-bandwidth bound.
INPUT_JOULES_PER_TOKEN = float(os.getenv("INPUT_JOULES_PER_TOKEN", "0.2"))
OUTPUT_JOULES_PER_TOKEN = float(os.getenv("OUTPUT_JOULES_PER_TOKEN", "8.0"))
CPU_WATTS = float(os.getenv("CPU_WATTS", "15"))
GRID_GCO2_PER_KWH = float(os.getenv("GRID_GCO2_PER_KWH", "400"))
