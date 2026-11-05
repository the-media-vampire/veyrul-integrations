"""Input-validation adapter for video-use helpers/render.py build_master_srt.

The candidate (the-media-vampire/video-use@080dda49) validates word intervals
but not EDL ranges. It accumulates seg_offset += end - start for every range,
so a reversed range moves later cues backwards, and a NaN/inf range poisons
every later offset. This adapter filters ranges before the unchanged function
runs. The same sanitized EDL must also drive segment extraction/concat;
otherwise captions and video desynchronize.
"""
from __future__ import annotations

import math


def _finite_number(v) -> bool:
    return type(v) in (int, float) and math.isfinite(v)


def sanitize_edl(edl: dict) -> tuple[dict, list[dict]]:
    """Return (edl copy with only valid ranges, rejected ranges with reasons).

    A range is valid when start/end are finite real numbers (bool and numeric
    strings rejected) and end > start. Rejected ranges contribute no duration.
    """
    kept, rejected = [], []
    for i, r in enumerate(edl.get("ranges", [])):
        s, e = r.get("start"), r.get("end")
        if not (_finite_number(s) and _finite_number(e)):
            reason = "nonfinite_or_nonnumeric"
        elif e < s:
            reason = "reversed"
        elif e == s:
            reason = "empty"
        else:
            kept.append(r)
            continue
        rejected.append({"index": i, "start": repr(s), "end": repr(e), "reason": reason})
    clean = dict(edl)
    clean["ranges"] = kept
    return clean, rejected


def build_master_srt_validated(render, edl: dict, edit_dir, out_path) -> list[dict]:
    """Call render.build_master_srt unchanged on the sanitized EDL."""
    clean, rejected = sanitize_edl(edl)
    render.build_master_srt(clean, edit_dir, out_path)
    return rejected
