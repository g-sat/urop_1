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
