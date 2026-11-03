#!/usr/bin/env python3
"""Check the saved timing tool on a reordered/repeated post-generation edit."""
import importlib.util
import json
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    source = here.parent / "edit-aware-word-timing" / "media_timeline.py"
    spec = importlib.util.spec_from_file_location("saved_media_timeline", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("The sibling edit-aware-word-timing example is required")
    library = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(library)
    job = json.loads((here / "EDIT.json").read_text(encoding="utf-8"))
    result = library.retime_words(library.normalize_words(job["rows"], job["unit"]), job["cuts"])
    expected = [
        ("Blue", 200000, 500000), ("hour", 600000, 900000),
        ("Morning", 1200000, 1600000), ("light", 1700000, 2000000),
        ("Blue", 2100000, 2250000), ("hour", 2300000, 2450000)
    ]
    actual = [(word["text"], word["start_us"], word["end_us"]) for word in result["words"]]
    if actual != expected or result["duration_us"] != 2500000:
        raise RuntimeError("Edit timing did not match the manually derived expectation")
    highlights = library.build_events(result["words"], result["duration_us"])
    print(json.dumps({"status": "passed", "duration_us": result["duration_us"],
                      "retimed_words": result["words"], "highlights": highlights,
                      "checks": "Six exact word intervals, reordered/repeated source ranges, 2x final cut, 2.5 s duration",
                      "not_checked": "ComfyUI generation, media rendering, font fit, speech transcription"}, indent=2))


if __name__ == "__main__":
    main()
