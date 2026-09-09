"""Active Ambiguity Interception Layer — NLP priors + LLM diagnosis."""

from ambiguity_layer.pipeline.process_query import (
    process_query,
    resolve_with_clarification,
)

__all__ = ["process_query", "resolve_with_clarification"]
