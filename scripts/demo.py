"""Interactive demo of the NLP + LLM interception layer."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ambiguity_layer.pipeline import process_query, resolve_with_clarification


def main() -> None:
    print("=== Active Ambiguity Interception Layer (NLP + LLM) ===\n")
    user_input = input("Your prompt: ").strip()
    print("\nRunning NLP analysis + diagnosis...\n")
    result = process_query(user_input, generate_final=True)

    print(result.get("nlp_summary", ""))
    print()

    if result["status"] == "needs_clarification":
        d = result["diagnosis"]
        print("Ambiguity detected.")
        print(f"  Type:   {d.get('ambiguityType')}")
        print(f"  Clause: {d.get('problematicClause')}")
        print(f"  NLP span used: {d.get('nlpSpanUsed')} ({d.get('nlpSpanKind')})")
        print(f"  Reason: {d.get('reasoning')}\n")
        print("Clarifying questions:")
        for i, q in enumerate(result["clarifying_questions"], 1):
            print(f"  {i}. {q}")
        clarification = input("\nYour clarification: ").strip()
        resolved = resolve_with_clarification(
            result["original_input"], clarification, generate_final=True
        )
        print("\nMerged prompt:")
        print(f"  {resolved['merged_prompt']}\n")
        print("Final answer:")
        print(resolved["answer"])
    else:
        print("No ambiguity — final answer:")
        print(result.get("answer"))


if __name__ == "__main__":
    main()
