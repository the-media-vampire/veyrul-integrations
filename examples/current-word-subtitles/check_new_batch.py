#!/usr/bin/env python3
"""Check the saved widescreen ASS artifact without rendering or external media."""
import hashlib
import json
from pathlib import Path
import platform

from subtitle_workflow import build_events, generate_ass
from test_workflow import WHITE, YELLOW, WorkflowTests, read_dialogues, visible_characters


def main():
    root = Path(__file__).resolve().parent
    spec = json.loads((root / "new-batch.json").read_text(encoding="utf-8"))
    raw = (root / "new-batch.ass").read_bytes()
    ass = raw.decode("utf-8")
    assert (spec["width"], spec["height"], spec["duration_ms"]) == (1920, 1080, 6200)
    assert ass == generate_ass(spec), "saved ASS differs from generated contract"
    WorkflowTests().assert_contract(spec)
    for line in ("PlayResX: 1920", "PlayResY: 1080", "LayoutResX: 1920", "LayoutResY: 1080"):
        assert line in ass.splitlines()
    events = build_events(spec)
    dialogues = read_dialogues(ass)
    assert len(dialogues) == 14
    assert sum(e["active_index"] is None for e in events) == 7
    sentence = "A quiet pause, then a clear finish."
    pause_index = next(i for i, w in enumerate(spec["words"]) if w["text"] == "pause,")
    then_index = pause_index + 1
    assert spec["words"][then_index]["text"] == "then"
    gap_start = spec["words"][pause_index]["end_ms"]
    gap_end = spec["words"][then_index]["start_ms"]
    assert (gap_start, gap_end) == (2200, 4000)
    gaps = [(s, e, p) for s, e, p in dialogues if s < gap_end and e > gap_start]
    assert len(gaps) == 1 and gaps[0][:2] == (gap_start, gap_end)
    text, colors = visible_characters(gaps[0][2])
    assert text == sentence and colors == [WHITE] * len(sentence)
    samples = []
    for ms, expected in ((2199, "pause,"), (2200, ""), (3100, ""),
                         (3999, ""), (4000, "then"), (4299, "then"), (4300, "a")):
        matches = [(s, e, p) for s, e, p in dialogues if s <= ms < e]
        assert len(matches) == 1
        text, colors = visible_characters(matches[0][2])
        assert text == sentence
        highlighted = "".join(c for c, color in zip(text, colors) if color == YELLOW)
        assert highlighted == expected, (ms, highlighted, expected)
        samples.append({"time_ms": ms, "highlighted": highlighted or None})
    report = {
        "status": "passed", "python": platform.python_version(),
        "evaluation": "founder-controlled synthetic evaluation; no independent reproduction or visual production acceptance",
        "resolution": [1920, 1080], "duration_ms": 6200,
        "dialogue_events": 14, "word_events": 7, "pause_events": 7,
        "sentence": sentence, "silence_ms": [gap_start, gap_end],
        "silence_duration_ms": gap_end - gap_start,
        "silence_state": "full sentence white; no active word", "boundary_samples": samples,
        "ass_bytes": len(raw), "ass_sha256": hashlib.sha256(raw).hexdigest(),
        "checks": ["saved artifact equals generator output", "complete timeline partition",
                   "per-character static colors on every interval", "widescreen headers",
                   "entire long pause white", "exclusive ends and adjacent word transition"],
        "limitations": ["No rendering", "Font availability, glyphs, wrapping, fit and color pipeline unverified",
                        "Boundary samples are timestamp queries, not video frames"],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
