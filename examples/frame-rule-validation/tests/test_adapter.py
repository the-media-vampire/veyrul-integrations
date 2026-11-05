"""Tests for adapter.py on a new original synthetic scene checklist.
Scene (synthetic, no media): one courier at a rain-streaked shop door, door closed,
red umbrella. Observations are invented values, not transcribed from any still."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import adapter  # noqa: E402
from adapter import Rule, FrameObs, ValidationError, upstream  # noqa: E402

RULES = [
    Rule("S1", "exactly one person in first frame", "exact", 1),
    Rule("S2", "shop door is open", "boolean", False),   # negated prop: door must be closed
    Rule("S3", "umbrella colour", "contains", "red"),
]

VALID = [
    FrameObs("S1", 1, "clear"),
    FrameObs("S2", False, "clear"),
    FrameObs("S3", "dark red umbrella", "clear"),
]


class OrdinaryValid(unittest.TestCase):
    def test_all_match(self):
        out = adapter.strict_score_clip(RULES, VALID)
        self.assertEqual([r["verdict"] for r in out], ["MATCH"] * 3)

    def test_same_as_upstream_on_valid(self):
        self.assertEqual(adapter.strict_score_clip(RULES, VALID), upstream.score_clip(RULES, VALID))

    def test_mismatch_preserved(self):
        obs = [FrameObs("S1", 2, "clear"), FrameObs("S2", True, "clear"), FrameObs("S3", "blue", "clear")]
        out = adapter.strict_score_clip(RULES, obs)
        self.assertEqual([r["verdict"] for r in out], ["MISMATCH"] * 3)

    def test_partial_unclear_none_and_missing(self):
        obs = [FrameObs("S1", 1, "partial"), FrameObs("S2", None, "clear"), ]
        out = adapter.strict_score_clip(RULES, obs)
        self.assertEqual([r["verdict"] for r in out], ["AMBIGUOUS", "NOT_VERIFIED", "NOT_VERIFIED"])
        self.assertEqual(adapter.strict_check(RULES[2], FrameObs("S3", "red", "unclear")), "NOT_VERIFIED")


class Rejections(unittest.TestCase):
    def test_mismatched_id_check(self):
        with self.assertRaises(ValidationError):
            adapter.strict_check(RULES[0], FrameObs("ZZZ", 1, "clear"))

    def test_orphan_observation_score_clip(self):
        with self.assertRaises(ValidationError):
            adapter.strict_score_clip(RULES, VALID + [FrameObs("ZZZ", 1, "clear")])

    def test_duplicate_observations(self):
        with self.assertRaises(ValidationError):
            adapter.strict_score_clip(RULES, VALID + [FrameObs("S1", 2, "clear")])

    def test_duplicate_rule_ids(self):
        with self.assertRaises(ValidationError):
            adapter.strict_score_clip(RULES + [Rule("S1", "dup", "exact", 1)], VALID)

    def test_blank_state(self):
        for blank in ("", "   ", "\t"):
            with self.assertRaises(ValidationError):
                adapter.strict_check(RULES[1], FrameObs("S2", blank, "clear"))
            with self.assertRaises(ValidationError):
                adapter.strict_check(RULES[2], FrameObs("S3", blank, "clear"))

    def test_invalid_boolean_representation(self):
        for bad in ("false", "False", "no", "0", 0, 1, "true"):
            with self.assertRaises(ValidationError, msg=repr(bad)):
                adapter.strict_check(RULES[1], FrameObs("S2", bad, "clear"))

    def test_bool_for_exact_count(self):
        with self.assertRaises(ValidationError):
            adapter.strict_check(RULES[0], FrameObs("S1", True, "clear"))

    def test_invalid_labels(self):
        with self.assertRaises(ValidationError):
            adapter.strict_check(RULES[0], FrameObs("S1", 1, "PASS"))
        with self.assertRaises(ValidationError):
            adapter.strict_check(Rule("S9", "x", "PASS", 1), FrameObs("S9", 1, "clear"))
        with self.assertRaises(ValidationError):
            adapter.strict_check(Rule("S9", "x", "boolean", "false"), FrameObs("S9", False, "clear"))


if __name__ == "__main__":
    unittest.main()
