"""Labeled cases. scripts/eval_latent.py and tests/test_latent.py read CASES.

No existing file stores a reading, an immediate answer, and a follow-up answer
for latent ambiguity. Gold is compared only after classify() returns.

User instruction: "do this then i need you to evaluate this and check clearly with ecc after u impliment thjs"
"""

from __future__ import annotations

CASES: list[dict] = [
    {
        "id": "decision_bank",
        "gold": "decision",
        "prompt": "Meet me at the bank at 5.",
        "readings": ["river bank", "financial bank"],
        "immediate_answers": ["the riverside path", "the lobby of the First National branch"],
        "followup": "Which entrance?",
        "followup_answers": ["the footpath gate", "the main glass doors"],
    },
    {
        "id": "decision_draft",
        "gold": "decision",
        "prompt": "Circulate the draft to the cast.",
        "readings": ["Tuesday draft", "Friday draft"],
        "immediate_answers": ["send the Tuesday draft", "send the Friday draft"],
        "followup": "Who receives it?",
        "followup_answers": ["the cast", "the cast"],
    },
    {
        "id": "decision_payment",
        "gold": "decision",
        "prompt": "Was the order paid?",
        "readings": ["count both payments", "count only the successful payment"],
        "immediate_answers": ["no, one payment is still pending", "yes, the successful payment covers it"],
        "followup": "What is the status of the second payment?",
        "followup_answers": ["pending", "pending"],
    },
    {
        "id": "decision_location",
        "gold": "decision",
        "prompt": "Which location should they register in, Singapore or Delaware?",
        "readings": ["Singapore", "Delaware"],
        "immediate_answers": ["Singapore", "Delaware"],
        "followup": "Is a registration still required?",
        "followup_answers": ["yes", "yes"],
    },
    {
        "id": "latent_emissions",
        "gold": "latent",
        "prompt": "Emissions fell 10% and fares rose 10%. Did emissions fall?",
        "readings": ["pair the first number with emissions", "swap the two numbers"],
        "immediate_answers": ["yes", "yes"],
        "followup": "Did fares rise?",
        "followup_answers": ["yes", "no"],
    },
    {
        "id": "latent_sender",
        "gold": "latent",
        "prompt": "Alex told Jordan to send the report. Does a report need to be sent?",
        "readings": ["Alex is the sender", "Jordan is the sender"],
        "immediate_answers": ["yes", "yes"],
        "followup": "Who sends the report?",
        "followup_answers": ["Alex", "Jordan"],
    },
    {
        "id": "latent_percent_wording",
        "gold": "latent",
        "prompt": "Revenue grew 15 percent under the plan. Did revenue grow?",
        "readings": ["15 percent is revenue", "15 percent is profit"],
        "immediate_answers": ["yes, by 15%", "yes, by 15 percent"],
        "followup": "Did profit grow 15%?",
        "followup_answers": ["not stated", "yes"],
    },
    {
        "id": "latent_records",
        "gold": "latent",
        "prompt": "The records show high blood pressure and normal cholesterol. Is blood pressure high?",
        "readings": ["latest visit", "a previous visit with the same summary"],
        "immediate_answers": ["yes", "yes"],
        "followup": "Which visit are these records from?",
        "followup_answers": ["the latest visit", "a previous visit"],
    },
    {
        "id": "latent_refund",
        "gold": "latent",
        "prompt": "The customer wants a refund because voice commands failed. Is a refund being requested?",
        "readings": ["a software glitch caused the failure", "the user caused the failure"],
        "immediate_answers": ["yes", "yes"],
        "followup": "Should the refund be granted?",
        "followup_answers": ["yes, the system failed", "no, the user caused it"],
    },
    {
        "id": "none_explicit",
        "gold": "none",
        "prompt": "Book a table for two at 7pm on 12 March 2026 at 14 King Street.",
        "readings": ["that reservation"],
        "immediate_answers": ["booked"],
        "followup": "What time?",
        "followup_answers": ["7pm"],
    },
    {
        "id": "none_same_followup",
        "gold": "none",
        "prompt": "The cat sat on the mat. Where did the cat sit?",
        "readings": ["literal mat", "the same mat named again"],
        "immediate_answers": ["on the mat", "on the mat"],
        "followup": "Who sat?",
        "followup_answers": ["the cat", "the cat"],
    },
    {
        "id": "none_single_metric",
        "gold": "none",
        "prompt": "The Q3 2024 net profit margin was 12.4 percent. What was the margin?",
        "readings": ["net profit margin"],
        "immediate_answers": ["12.4 percent"],
        "followup": "Which quarter?",
        "followup_answers": ["Q3 2024"],
    },
]
