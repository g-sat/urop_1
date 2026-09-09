"""Homonym / multi-sense lexicon for WSD ambiguity priors."""

from __future__ import annotations

# lemma -> distinct everyday senses (semantic_overlap cues)
HOMONYMS: dict[str, list[str]] = {
    "bank": ["financial institution", "river edge", "rely upon"],
    "crane": ["bird", "lifting machine", "stretch neck"],
    "bat": ["flying mammal", "sports club", "blink"],
    "spring": ["season", "water source", "coil", "jump"],
    "bark": ["tree covering", "dog sound"],
    "seal": ["marine animal", "close tightly", "official stamp"],
    "match": ["contest", "pair together", "firestarter"],
    "mole": ["animal", "skin mark", "spy", "unit"],
    "plant": ["vegetation", "factory", "place secretly"],
    "right": ["correct", "direction", "entitlement"],
    "left": ["direction", "remaining", "departed"],
    "light": ["illumination", "not heavy", "ignite"],
    "park": ["recreation area", "leave vehicle"],
    "pitch": ["throw", "tone", "sales talk", "sports field"],
    "current": ["present time", "electric flow", "water flow"],
    "date": ["calendar day", "romantic outing", "fruit"],
    "jam": ["preserve", "congestion", "improvise music"],
    "nail": ["fastener", "fingernail", "succeed"],
    "rock": ["stone", "music genre", "sway"],
    "fall": ["autumn", "drop", "waterfall"],
    "issue": ["problem", "edition", "emit"],
    "case": ["instance", "container", "legal matter"],
    "term": ["word", "period", "condition"],
    "interest": ["curiosity", "finance charge", "stake"],
    "charge": ["accuse", "fee", "electrical energy", "rush"],
    "board": ["plank", "committee", "get on vehicle"],
    "draft": ["preliminary text", "air current", "conscript", "beer"],
    "file": ["document", "tool", "line of people"],
    "plain": ["simple", "flat land"],
    "pound": ["weight", "currency", "strike"],
}

# weekday / relative time without absolute anchor → missing_entity cue
UNDERSPECIFIED_TIME = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "tomorrow",
    "yesterday",
    "tonight",
    "later",
    "soon",
    "recently",
    "earlier",
}

AMBIGUOUS_DEMONSTRATIVES = {"this", "that", "these", "those", "it", "they", "them", "its", "their"}
