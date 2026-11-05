"""Convert inspected retimed words to reviewable editor inputs; never call an editor.

MIT licensed. Input is media_timeline.py output (duration_us, words).
Clipped-word text is preserved: timing alone cannot prove the whole spoken word
survived. Inspect/listen at cut boundaries before applying these proposals.
"""
import argparse
import json
import sys


def validated(data):
    duration = data.get("duration_us")
    words = data.get("words")
    if type(duration) is not int or not 0 <= duration <= 86400_000000:
        raise ValueError("duration_us must be an integer within one day")
    if not isinstance(words, list) or len(words) > 10000:
        raise ValueError("words must be a bounded list")
    for word in words:
        if not isinstance(word, dict):
            raise ValueError("word must be an object")
        a, b, text = word.get("start_us"), word.get("end_us"), word.get("text")
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= duration:
            raise ValueError("word interval must be inside duration_us")
        if not isinstance(text, str) or not text.strip() or len(text) > 500:
            raise ValueError("word text is missing or too long")
        if any(c in text for c in ["\r", "\n", "\x00"]):
            raise ValueError("multiline/control text requires a separate caption policy")
    return words


def convert(data, target, project_id=None, track_id=None):
    words = validated(data)
    timed = [{"text": w["text"], "start": w["start_us"] / 1_000_000,
              "end": w["end_us"] / 1_000_000} for w in words]
    if target == "hyperframes":
        # Occurrence identity stays unique when an edit repeats source words.
        return [{"id": "edit-word-" + str(i), **w} for i, w in enumerate(timed)]
    if target == "cutline":
        if not project_id or not track_id:
            raise ValueError("Choose explicit project and new caption-track identifiers")
        return {"tool": "add_captions", "arguments": {
            "projectId": project_id, "trackId": track_id, "cues": timed,
            "replace": False, "fromTranscript": False,
        }}
    if target == "ffmpeg-skill":
        # SRT is millisecond precision. Reject overlaps and collapsed intervals
        # instead of silently choosing a display/layout policy.
        def ms(us):
            return (us + 500) // 1000
        def timestamp(n):
            return f"{n // 3600000:02}:{n // 60000 % 60:02}:{n // 1000 % 60:02},{n % 1000:03}"
        lines, prior_end = [], 0
        for i, w in enumerate(words):
            start, end = ms(w["start_us"]), ms(w["end_us"])
            if start < prior_end or end <= start:
                raise ValueError("SRT needs an explicit policy for overlapping or sub-millisecond words")
            if any(c in w["text"] for c in "<>{}"):
                raise ValueError("Markup-like text needs an explicit SRT escaping policy")
            lines.append(f"{i+1}\n{timestamp(start)} --> {timestamp(end)}\n{w['text']}\n")
            prior_end = end
        return "\n".join(lines)
    raise ValueError("Unknown target")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("retimed_json")
    p.add_argument("--target", required=True, choices=["hyperframes", "cutline", "ffmpeg-skill"])
    p.add_argument("--project-id")
    p.add_argument("--track-id")
    a = p.parse_args()
    try:
        with open(a.retimed_json, "rb") as stream:
            raw = stream.read(262145)
        if len(raw) > 262144:
            raise ValueError("Input exceeds 256 KiB")
        result = convert(json.loads(raw), a.target, a.project_id, a.track_id)
        print(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, AttributeError, TypeError) as error:
        p.error(str(error))


if __name__ == "__main__":
    main()
