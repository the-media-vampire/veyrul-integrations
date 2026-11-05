import unittest
from check_tokens import check


class HandoffTests(unittest.TestCase):
    def test_current_shapes_and_overshoot_are_valid(self):
        out = check({"space": {"$type": "dimension", "$value": {"value": 0.5, "unit": "rem"}},
                     "time": {"$type": "duration", "$value": {"value": 150, "unit": "ms"}},
                     "ease": {"$type": "cubicBezier", "$value": [0.34, 1.56, 0.64, 1]}})
        self.assertEqual(out["status"], "subset_passed")
        self.assertEqual(out["checked"], 3)
        self.assertFalse(out["full_conformance"])

    def test_css_strings_are_not_current_typed_token_values(self):
        for kind, value in [("dimension", "8px"), ("duration", "150ms"), ("cubicBezier", "ease"),
                            ("cubicBezier", "cubic-bezier(.34, 1.56, .64, 1)")]:
            with self.subTest(kind=kind, value=value):
                self.assertEqual(check({"x": {"$type": kind, "$value": value}})["status"], "subset_failed")

    def test_inherited_type_and_chained_alias(self):
        out = check({"$type": "duration", "a": {"$value": {"value": 0, "unit": "s"}},
                     "b": {"$value": "{a}"}, "c": {"$value": "{b}"}})
        self.assertEqual(out["checked"], 3)
        self.assertEqual(out["issues"], [])

    def test_alias_failures_are_not_silently_resolved(self):
        for value, expected in [("{x}", "reference_cycle"), ("{missing}", "reference_missing")]:
            self.assertEqual(check({"x": {"$type": "duration", "$value": value}})["issues"][0]["code"], expected)
        result = check({"x": {"$type": "duration", "$value": "{y}"}, "y": {"$type": "number", "$value": 4}})
        self.assertEqual(result["issues"][0]["code"], "reference_type_mismatch")

    def test_bad_units_boolean_and_nonfinite_values_fail(self):
        for value in [{"value": 1, "unit": "seconds"}, {"value": True, "unit": "s"}, {"value": float('nan'), "unit": "s"}, {"value": 10**400, "unit": "s"}]:
            self.assertEqual(check({"x": {"$type": "duration", "$value": value}})["status"], "subset_failed")
        for value in [[-1, 0, 1, 1], [0, 0, 2, 1], [0, 0, 1], [False, 0, 1, 1]]:
            self.assertEqual(check({"x": {"$type": "cubicBezier", "$value": value}})["status"], "subset_failed")

    def test_other_types_are_explicitly_unchecked(self):
        out = check({"x": {"$type": "color", "$value": "#123456"}})
        self.assertEqual(out["status"], "no_supported_tokens")
        self.assertEqual(out["unchecked_types"], ["color"])

    def test_input_and_depth_bound(self):
        with self.assertRaises(ValueError):
            check([])
        document = {}
        cursor = document
        for _ in range(34):
            cursor["next"] = {}
            cursor = cursor["next"]
        with self.assertRaisesRegex(ValueError, "document_bound"):
            check(document)

    def test_malformed_type_and_long_alias_chain_are_bounded(self):
        with self.assertRaisesRegex(ValueError, "type_must_be_string"):
            check({"x": {"$type": [], "$value": 1}})
        document = {str(i): {"$type": "duration", "$value": "{" + str(i + 1) + "}"} for i in range(40)}
        document["40"] = {"$type": "duration", "$value": {"value": 1, "unit": "s"}}
        self.assertEqual(check(document)["issues"][0]["code"], "reference_bound")


if __name__ == "__main__":
    unittest.main()
