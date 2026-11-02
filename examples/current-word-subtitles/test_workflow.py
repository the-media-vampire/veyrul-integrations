#!/usr/bin/env python3
"""Executable offline contract tests; no renderer, network or media required."""

import copy
import json
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
import unittest

from subtitle_workflow import build_events, generate_ass


ROOT = Path(__file__).resolve().parent
WHITE, YELLOW = "FFFFFF", "00FFFF"


def example():
    return {
        "duration_ms": 4000, "width": 1080, "height": 1920,
        "words": [
            {"text": "Hello,", "start_ms": 300, "end_ms": 800},
            {"text": "world!", "start_ms": 1200, "end_ms": 1800},
        ],
    }


def parse_time(value):
    match = re.fullmatch(r"(\d+):(\d{2}):(\d{2})\.(\d{2})", value)
    if not match:
        raise AssertionError("invalid ASS timestamp: " + value)
    h, m, s, cs = map(int, match.groups())
    if m >= 60 or s >= 60:
        raise AssertionError("unnormalized ASS timestamp")
    return ((h * 60 + m) * 60 + s) * 1000 + cs * 10


def read_dialogues(ass):
    result = []
    for line in ass.splitlines():
        if line.startswith("Dialogue: "):
            fields = line[len("Dialogue: "):].split(",", 9)
            if len(fields) != 10:
                raise AssertionError("Dialogue must have ten fields")
            result.append((parse_time(fields[1]), parse_time(fields[2]), fields[9]))
    return result


def visible_characters(payload):
    """Small independent interpreter of only the allowed static color syntax."""
    color = None
    chars, colors = [], []
    cursor = 0
    while cursor < len(payload):
        if payload[cursor] == "{":
            match = re.match(r"\{\\1c&H([0-9A-F]{6})&\}", payload[cursor:])
            if match is None:
                raise AssertionError("unexpected override: " + payload[cursor:])
            color = match.group(1)
            cursor += len(match.group(0))
        else:
            if payload[cursor] in "\\}":
                raise AssertionError("unexpected ASS control character")
            chars.append(payload[cursor])
            colors.append(color)
            cursor += 1
    return "".join(chars), colors


class WorkflowTests(unittest.TestCase):
    def assert_contract(self, spec):
        original = copy.deepcopy(spec)
        events = build_events(spec)
        dialogues = read_dialogues(generate_ass(spec))
        self.assertEqual(spec, original)
        self.assertEqual(len(events), len(dialogues))
        sentence = " ".join(word["text"] for word in spec["words"])
        cursor = 0
        for event, (start, end, payload) in zip(events, dialogues):
            self.assertEqual(set(event), {"start_ms", "end_ms", "active_index", "text"})
            self.assertEqual(event["start_ms"], cursor)
            self.assertGreater(event["end_ms"], cursor)
            self.assertEqual((start, end), (event["start_ms"], event["end_ms"]))
            expected_active = next((i for i, word in enumerate(spec["words"])
                                    if word["start_ms"] <= start < word["end_ms"]), None)
            self.assertEqual(event["active_index"], expected_active)
            # No event may cross a change in the expected active word.
            for word in spec["words"]:
                for boundary in (word["start_ms"], word["end_ms"]):
                    self.assertFalse(start < boundary < end)
            self.assertEqual(event["text"], sentence)
            text, colors = visible_characters(payload)
            self.assertEqual(text, sentence)
            expected_colors = []
            for i, word in enumerate(spec["words"]):
                if i:
                    expected_colors.append(WHITE)
                expected_colors.extend([YELLOW if i == expected_active else WHITE]
                                       * len(word["text"]))
            self.assertEqual(colors, expected_colors)
            cursor = end
        self.assertEqual(cursor, spec["duration_ms"])
        self.assertEqual(spec, original)

    def assert_invalid(self, spec, message):
        original = copy.deepcopy(spec)
        for function in (build_events, generate_ass):
            with self.subTest(function=function.__name__):
                with self.assertRaisesRegex(ValueError, message):
                    function(spec)
                self.assertEqual(spec, original)

    def test_requested_example(self):
        spec = example()
        self.assertEqual(build_events(spec), [
            dict(start_ms=0, end_ms=300, active_index=None, text="Hello, world!"),
            dict(start_ms=300, end_ms=800, active_index=0, text="Hello, world!"),
            dict(start_ms=800, end_ms=1200, active_index=None, text="Hello, world!"),
            dict(start_ms=1200, end_ms=1800, active_index=1, text="Hello, world!"),
            dict(start_ms=1800, end_ms=4000, active_index=None, text="Hello, world!"),
        ])
        self.assert_contract(spec)

    def test_adjacent_words_cover_duration(self):
        spec = example()
        spec["words"][0].update(start_ms=0, end_ms=1200)
        spec["words"][1].update(end_ms=4000)
        self.assertEqual([e["active_index"] for e in build_events(spec)], [0, 1])
        self.assert_contract(spec)

    def test_single_centisecond(self):
        self.assert_contract(dict(duration_ms=10, width=1, height=1,
                                  words=[dict(text="Yes!", start_ms=0, end_ms=10)]))

    def test_unicode_punctuation_and_commas(self):
        spec = example()
        spec["words"][0]["text"] = "¿Héllo,世界?"
        spec["words"][1]["text"] = "cafe\u0301—🙂!"
        self.assert_contract(spec)
        generate_ass(spec).encode("utf-8")

    def test_identical_words_are_indexed_separately(self):
        spec = example()
        spec["words"][1]["text"] = spec["words"][0]["text"]
        self.assert_contract(spec)

    def test_minute_hour_and_centisecond_boundaries(self):
        spec = dict(duration_ms=3600010, width=1920, height=1080, words=[
            dict(text="minute", start_ms=59990, end_ms=60010),
            dict(text="hour", start_ms=3599990, end_ms=3600010),
        ])
        self.assert_contract(spec)
        output = generate_ass(spec)
        for timestamp in ("0:00:59.99", "0:01:00.01", "0:59:59.99", "1:00:00.01"):
            self.assertIn(timestamp, output)

    def test_ass_sections_style_and_resolution(self):
        output = generate_ass(example())
        lines = output.splitlines()
        self.assertEqual([line for line in lines if line.startswith("[")],
                         ["[Script Info]", "[V4+ Styles]", "[Events]"])
        for line in ("ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920",
                     "LayoutResX: 1080", "LayoutResY: 1920"):
            self.assertIn(line, lines)
        style_format = lines[lines.index("[V4+ Styles]") + 1][8:].split(", ")
        style = next(line[7:].split(",") for line in lines if line.startswith("Style: "))
        self.assertEqual(len(style_format), 23)
        self.assertEqual(len(style), 23)
        self.assertEqual(style[1], "DejaVu Sans")
        self.assertEqual(style[3], "&H00FFFFFF")
        self.assertEqual(style[-1], "1")
        self.assertEqual(lines[lines.index("[Events]") + 1],
                         "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")
        self.assertNotRegex(output, r"\\(?:[kK]|t\(|fad)")
        self.assertTrue(output.endswith("\n"))

    def test_deterministic_and_independent_results(self):
        spec = example()
        self.assertEqual(generate_ass(spec), generate_ass(spec))
        events = build_events(spec)
        events[0]["text"] = "changed"
        self.assertEqual(build_events(spec)[0]["text"], "Hello, world!")

    def test_seeded_timelines(self):
        rng = random.Random(173)
        for case in range(80):
            cursor, words = 0, []
            for index in range(rng.randint(1, 12)):
                start = cursor + rng.randint(0, 5) * 10
                cursor = start + rng.randint(1, 8) * 10
                words.append(dict(text="w{}!".format(index), start_ms=start, end_ms=cursor))
            spec = dict(duration_ms=cursor + rng.randint(0, 8) * 10,
                        width=1080, height=1920, words=words)
            with self.subTest(case=case):
                self.assert_contract(spec)

    def test_missing_fields(self):
        for key in ("duration_ms", "width", "height", "words"):
            spec = example()
            del spec[key]
            self.assert_invalid(spec, "missing required field")
        for key in ("text", "start_ms", "end_ms"):
            spec = example()
            del spec["words"][0][key]
            self.assert_invalid(spec, "missing required field")

    def test_shapes_and_empty_words(self):
        for value in (None, [], "spec", 3):
            self.assert_invalid(value, "spec must be an object")
        for value in ([], None, {}, "hello"):
            spec = example()
            spec["words"] = value
            self.assert_invalid(spec, "non-empty list")
        spec = example()
        spec["words"] = ["hello"]
        self.assert_invalid(spec, "must be an object")

    def test_invalid_text(self):
        for value in ("", "  \t", None, 42):
            spec = example()
            spec["words"][0]["text"] = value
            self.assert_invalid(spec, "non-empty string")
        for char in ("\\", "{", "}", "\r", "\n"):
            spec = example()
            spec["words"][0]["text"] = "x" + char + "y"
            self.assert_invalid(spec, "backslash, braces, CR or LF")
        for value, message in (("x\x00y", "NUL"), ("\ud800", "Unicode")):
            spec = example()
            spec["words"][0]["text"] = value
            self.assert_invalid(spec, message)

    def test_noninteger_times(self):
        for key in ("duration_ms", "start_ms", "end_ms"):
            for value in (True, False, 300.0, "300", None):
                spec = example()
                target = spec if key == "duration_ms" else spec["words"][0]
                target[key] = value
                self.assert_invalid(spec, "must be an integer")

    def test_noncentisecond_times(self):
        for key, value in (("duration_ms", 4001), ("start_ms", 301), ("end_ms", 801)):
            spec = example()
            target = spec if key == "duration_ms" else spec["words"][0]
            target[key] = value
            self.assert_invalid(spec, "multiple of 10")

    def test_nonpositive_duration_and_dimensions(self):
        for key in ("duration_ms", "width", "height"):
            for value in (0, -10):
                spec = example()
                spec[key] = value
                self.assert_invalid(spec, key + " must be positive")
        for key in ("width", "height"):
            for value in (True, 100.0, "100", None):
                spec = example()
                spec[key] = value
                self.assert_invalid(spec, key + " must be an integer")

    def test_out_of_bounds_and_empty_or_reversed_intervals(self):
        for start, end in ((-10, 800), (300, 4010), (300, 300), (800, 300), (4010, 4020)):
            spec = example()
            spec["words"][0].update(start_ms=start, end_ms=end)
            self.assert_invalid(spec, "0 <= start_ms < end_ms <= duration_ms")

    def test_overlapping_nested_and_unsorted_intervals(self):
        for start, end in ((790, 1800), (300, 800), (400, 500)):
            spec = example()
            spec["words"][1].update(start_ms=start, end_ms=end)
            self.assert_invalid(spec, "sorted and non-overlapping")
        spec = example()
        spec["words"].reverse()
        self.assert_invalid(spec, "sorted and non-overlapping")

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "subtitle_workflow.py"),
                               *map(str, args)], cwd=ROOT, capture_output=True,
                              encoding="utf-8", timeout=10)

    def test_cli_utf8_output_and_input_preservation(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            source, output = Path(directory) / "input.json", Path(directory) / "out.ass"
            spec = example()
            spec["words"][0]["text"] = "世界🙂,"
            content = json.dumps(spec, ensure_ascii=False)
            source.write_text(content, encoding="utf-8")
            result = self.run_cli(source, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), generate_ass(spec))
            self.assertEqual(source.read_text(encoding="utf-8"), content)

    def test_cli_rejects_bad_input_without_clobbering_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            source, output = Path(directory) / "input.json", Path(directory) / "out.ass"
            for content in ("{", '{"words": []}', '{"duration_ms": true}'):
                source.write_text(content, encoding="utf-8")
                output.write_text("keep", encoding="utf-8")
                result = self.run_cli(source, output)
                self.assertEqual(result.returncode, 2)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(output.read_text(), "keep")

    def test_cli_io_errors_arguments_and_same_path(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            source = Path(directory) / "input.json"
            source.write_text(json.dumps(example()), encoding="utf-8")
            for args in ((), (source, source), (source, directory),
                         (Path(directory) / "missing.json", Path(directory) / "out.ass")):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
