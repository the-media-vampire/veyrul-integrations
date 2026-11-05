import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("adapt_timing", Path(__file__).with_name("adapt_timing.py"))
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
FIXTURE = {"duration_us": 900000, "words": [
    {"text": "Cross", "start_us": 0, "end_us": 100000},
    {"text": "the", "start_us": 266667, "end_us": 400000},
    {"text": "Cross", "start_us": 450000, "end_us": 850000},
]}


class AdapterChecks(unittest.TestCase):
    def test_hyperframes_preserves_repeated_occurrences(self):
        result = adapter.convert(FIXTURE, "hyperframes")
        self.assertEqual([w["id"] for w in result], ["edit-word-0", "edit-word-1", "edit-word-2"])
        self.assertEqual([w["start"] for w in result], [0, .266667, .45])
        self.assertEqual(result[2]["text"], "Cross")

    def test_cutline_is_an_explicit_non_replacing_proposal(self):
        result = adapter.convert(FIXTURE, "cutline", "fixture-project", "new-caption-track")
        self.assertEqual(result["tool"], "add_captions")
        a = result["arguments"]
        self.assertFalse(a["replace"])
        self.assertFalse(a["fromTranscript"])
        self.assertEqual(a["cues"][1], {"text": "the", "start": .266667, "end": .4})
        with self.assertRaises(ValueError):
            adapter.convert(FIXTURE, "cutline")

    def test_srt_is_millisecond_precision(self):
        result = adapter.convert(FIXTURE, "ffmpeg-skill")
        self.assertEqual(result, "1\n00:00:00,000 --> 00:00:00,100\nCross\n\n2\n00:00:00,267 --> 00:00:00,400\nthe\n\n3\n00:00:00,450 --> 00:00:00,850\nCross\n")

    def test_invalid_or_ambiguous_inputs_are_not_silently_repaired(self):
        for mutation in [{"start_us": -1}, {"end_us": 0}, {"end_us": 900001}, {"text": "line\nbreak"}]:
            bad = json.loads(json.dumps(FIXTURE));bad["words"][0].update(mutation)
            with self.assertRaises(ValueError):
                adapter.convert(bad, "hyperframes")
        for end, text in [(300, "too short"), (100000, "<b>markup</b>")]:
            with self.assertRaises(ValueError):
                adapter.convert({"duration_us": 1000000, "words": [{"text": text, "start_us": 0, "end_us": end}]}, "ffmpeg-skill")
        overlap = json.loads(json.dumps(FIXTURE));overlap["words"][1]["start_us"] = 50000
        with self.assertRaises(ValueError):
            adapter.convert(overlap, "ffmpeg-skill")


if __name__ == "__main__":
    unittest.main()
