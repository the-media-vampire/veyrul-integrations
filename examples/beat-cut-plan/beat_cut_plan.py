#!/usr/bin/env python3
"""Plan CFR cut boundaries from measured song times or a constant-tempo fallback.

Python 3.10+, standard library only. Does not fetch, install, render or overwrite.
Times are decimal strings or fractions; the first cut is the audio source in-point.
"""
import argparse
from fractions import Fraction
import json
import sys


def rational(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("Use decimal strings or fractions, not JSON floats")
    if len(str(value)) > 64:
        raise ValueError("Numeric value is too long")
    return Fraction(value)


def nearest_frame(value):
    """Nonnegative rational, nearest integer; exact half frames round forward."""
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def plan(cut_seconds, fps):
    rate = rational(fps)
    if not 0 < rate <= 1000:
        raise ValueError("fps must be positive and at most 1000")
    if not isinstance(cut_seconds, list) or not 2 <= len(cut_seconds) <= 4097:
        raise ValueError("Provide 2 through 4097 absolute source cut times")
    times = [rational(t) for t in cut_seconds]
    if times[0] < 0 or times[-1] > 86400:
        raise ValueError("Source times must be within 0 through 86400 seconds")
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("Source cut times must strictly increase")
    origin = times[0]
    frames = [nearest_frame((t - origin) * rate) for t in times]
    if any(b <= a for a, b in zip(frames, frames[1:])):
        raise ValueError("Two cuts collapse onto the same frame; revise the cut plan")
    boundaries = [
        {"source_seconds": str(t), "output_frame": n,
         "output_seconds": str(Fraction(n) / rate),
         "error_seconds": str(Fraction(n) / rate - (t - origin))}
        for t, n in zip(times, frames)
    ]
    segments = [
        {"segment": i + 1, "start_frame": a, "end_frame": b, "frames": b - a}
        for i, (a, b) in enumerate(zip(frames, frames[1:]))
    ]
    return {"schema": "beat-cut-plan/1", "fps": str(rate),
            "audio_source_in_seconds": str(origin),
            "rounding": "nearest absolute output boundary; ties forward",
            "boundaries": boundaries, "segments": segments,
            "total_frames": frames[-1], "duration_seconds": str(Fraction(frames[-1]) / rate),
            "max_abs_error_seconds": str(max(abs(Fraction(b["error_seconds"])) for b in boundaries)),
            "scope": "CFR planning only; no beat detection, rendering or creative-quality judgment"}


def from_tempo(bpm, bars, fps, beats_per_bar=4, song_in="0"):
    tempo, offset = rational(bpm), rational(song_in)
    if not 0 < tempo <= 1000 or not 1 <= bars <= 4096 or not 1 <= beats_per_bar <= 32:
        raise ValueError("bpm, bars or beats-per-bar outside supported bounds")
    bar = Fraction(60 * beats_per_bar) / tempo
    return plan([str(offset + i * bar) for i in range(bars + 1)], fps)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--bpm", help="constant-tempo fallback; verify against actual audio")
    source.add_argument("--cut-times", help="JSON list of absolute measured cut times as strings")
    parser.add_argument("--fps", required=True, help="exact rate, e.g. 24 or 24000/1001")
    parser.add_argument("--bars", type=int)
    parser.add_argument("--beats-per-bar", type=int, default=4)
    parser.add_argument("--song-in", default="0", help="audio in-point, constant-tempo mode only")
    args = parser.parse_args()
    try:
        if args.bpm:
            if args.bars is None:
                raise ValueError("--bpm requires --bars")
            result = from_tempo(args.bpm, args.bars, args.fps, args.beats_per_bar, args.song_in)
        else:
            if args.bars is not None or args.song_in != "0" or args.beats_per_bar != 4:
                raise ValueError("Tempo options cannot be combined with --cut-times")
            with open(args.cut_times, "rb") as stream:
                data = stream.read(262145)
            if len(data) > 262144:
                raise ValueError("Cut-time file exceeds 256 KiB")
            result = plan(json.loads(data), args.fps)
        json.dump(result, sys.stdout, indent=2)
        print()
    except (ValueError, ZeroDivisionError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
