"""JSON adapter for the unchanged, pinned MIT media_timeline implementation."""

import argparse
import json
from pathlib import Path
import sys

RESOURCE_DIR = (
    Path(__file__).resolve().parent / "vendor" / "edit-aware-word-timing-3cc67c3"
)
sys.path.insert(0, str(RESOURCE_DIR))
from media_timeline import retime_words


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("words", type=Path)
    parser.add_argument("cuts", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    words = json.loads(args.words.read_text(encoding="utf-8"))
    cuts = json.loads(args.cuts.read_text(encoding="utf-8"))
    # The input already has integer microseconds and source identities.
    result = retime_words(words, cuts)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    # Never replace an input or a previous output.
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(payload)
    print(f"{args.output}: {len(result['words'])} occurrences; "
          f"duration_us={result['duration_us']}")


if __name__ == "__main__":
    main()
