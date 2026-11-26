"""Tests for classify() in ambiguity_layer.latent.decide.

No existing test file covers latent versus decision ambiguity.
User instruction: "do this then i need you to evaluate this and check clearly with ecc after u impliment thjs"
"""

import unittest

from ambiguity_layer.latent.cases import CASES
from ambiguity_layer.latent.decide import classify, same_answer


class LatentAmbiguityTests(unittest.TestCase):
    def test_percent_wording_is_the_same_answer(self) -> None:
        self.assertTrue(same_answer("yes, by 15%", "yes, by 15 percent"))

    def test_every_labeled_case(self) -> None:
        for case in CASES:
            with self.subTest(case=case["id"]):
                result = classify(
                    case["readings"],
                    case["immediate_answers"],
                    case["followup_answers"],
                )
                self.assertEqual(result["label"], case["gold"])

    def test_latent_does_not_ask_now(self) -> None:
        for case in CASES:
            if case["gold"] != "latent":
                continue
            result = classify(
                case["readings"],
                case["immediate_answers"],
                case["followup_answers"],
            )
            self.assertEqual(result["action"], "answer_with_assumption")

    def test_decision_asks(self) -> None:
        for case in CASES:
            if case["gold"] != "decision":
                continue
            result = classify(
                case["readings"],
                case["immediate_answers"],
                case["followup_answers"],
            )
            self.assertEqual(result["action"], "ask")

    def test_misaligned_answers_raise(self) -> None:
        with self.assertRaises(ValueError):
            classify(["a", "b"], ["only one"], ["x", "y"])


if __name__ == "__main__":
    unittest.main()
