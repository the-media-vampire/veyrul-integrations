#!/usr/bin/env python3
"""Reproducible synthetic FFmpeg regression. Writes only to a NEW output folder."""
import argparse
from array import array
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from beat_cut_plan import from_tempo, plan


def run(args, **kw):
    return subprocess.run(args, check=True, timeout=60, **kw)


def oracle(bpm, fps, bars):
    with localcontext() as ctx:
        ctx.prec = 50
        rate = Decimal(Fraction(fps).numerator) / Decimal(Fraction(fps).denominator)
        return [int((Decimal(i) * 240 * rate / Decimal(bpm)).to_integral_value(rounding=ROUND_HALF_UP))
                for i in range(bars + 1)]


def check_math():
    cases = [("117.45", "24", 64), ("120", "24", 32),
             ("120.25", "24000/1001", 64), ("137", "30000/1001", 128)]
    for bpm, fps, bars in cases:
        result = from_tempo(bpm, bars, fps)
        assert [b["output_frame"] for b in result["boundaries"]] == oracle(bpm, fps, bars)
        assert Fraction(result["max_abs_error_seconds"]) <= Fraction(1, 2) / Fraction(fps)
        assert sum(s["frames"] for s in result["segments"]) == result["total_frames"]
    measured = plan(["0.125", "0.646", "1.190", "1.697", "2.249"], "24")
    assert [b["output_frame"] for b in measured["boundaries"]] == [0, 13, 26, 38, 51]
    assert measured["audio_source_in_seconds"] == "1/8"
    assert plan(["0", "1/48"], "24")["total_frames"] == 1
    bad = [(["0", "0.001"], "24"), (["0", "0"], "24"),
           (["-1", "2"], "24"), (["0", "2"], "0"),
           ([0, 2.0], "24"), (["0", "nan"], "24")]
    for cuts, fps in bad:
        try:
            plan(cuts, fps)
        except (ValueError, ZeroDivisionError):
            pass
        else:
            raise AssertionError("invalid plan accepted")
    return {"tempo_cases": len(cases), "measured_irregular_grid": True,
            "tie_forward": True, "invalid_cases": len(bad)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    root = args.output_dir
    checks = check_math()
    bpm, fps, bars, sr = "117.45", "24", 64, 48000
    result = from_tempo(bpm, bars, fps)
    (root / "plan.json").write_text(json.dumps(result, indent=2) + "\n")
    expected = oracle(bpm, fps, bars)
    rounded_bar = oracle(bpm, fps, 1)[1]
    baseline = [i * rounded_bar for i in range(bars + 1)]
    # Independently place audible 1 ms pulses at ideal bar boundaries on a 48 kHz clock.
    with localcontext() as ctx:
        ctx.prec = 50
        clicks = [int((Decimal(i) * 240 * sr / Decimal(bpm)).to_integral_value(rounding=ROUND_HALF_UP))
                  for i in range(bars + 1)]
    samples = array("h", [0]) * (clicks[-1] + sr // 2)
    for index in clicks:
        samples[index:index + 48] = array("h", [6000]) * 48
    if sys.byteorder != "little":
        samples.byteswap()
    audio = root / "click-reference.flac"
    run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-f", "s16le", "-ar", str(sr),
         "-ac", "1", "-i", "pipe:0", "-c:a", "flac", str(audio)], input=samples.tobytes())
    del samples
    variants = []
    for name, frames in [("rounded-each-bar", baseline), ("absolute-boundaries", expected)]:
        media = root / (name + ".mkv")
        # Tiny original calibration colors; not downloaded or AI-generated footage.
        payload = b"".join(bytes([32 + 3 * i]) * (64 * 36 * 3 * (b - a))
                           for i, (a, b) in enumerate(zip(frames, frames[1:])))
        run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-f", "rawvideo",
             "-pixel_format", "rgb24", "-video_size", "64x36", "-framerate", fps,
             "-i", "pipe:0", "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
             "-c:v", "ffv1", "-pix_fmt", "bgr0", "-c:a", "copy", "-shortest", str(media)],
            input=payload)
        del payload
        decoded = run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(media),
                       "-map", "0:v:0", "-fps_mode", "passthrough", "-f", "rawvideo",
                       "-pix_fmt", "rgb24", "pipe:1"], stdout=subprocess.PIPE).stdout
        size = 64 * 36 * 3
        assert len(decoded) == frames[-1] * size
        transitions, previous = [0], decoded[0]
        for n in range(frames[-1]):
            pixel = decoded[n * size]
            assert decoded[n * size:(n + 1) * size] == bytes([pixel]) * size
            if pixel != previous:
                transitions.append(n)
                previous = pixel
        transitions.append(frames[-1])
        assert transitions == frames
        del decoded
        pcm = run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(media), "-map", "0:a:0",
                   "-f", "s16le", "-acodec", "pcm_s16le", "pipe:1"], stdout=subprocess.PIPE).stdout
        values = array("h"); values.frombytes(pcm)
        if sys.byteorder != "little":
            values.byteswap()
        peaks = [i for i, value in enumerate(values) if value and (i == 0 or values[i - 1] == 0)]
        expected_peaks = [i for i in clicks if i < len(values)]
        assert peaks == expected_peaks
        # End boundary need not have a pulse: it is the video end, not an internal cut.
        errors = [abs(Fraction(n, 24) - Fraction(clicks[i], sr))
                  for i, n in enumerate(transitions[:-1])]
        if name == "absolute-boundaries":
            assert max(errors) <= Fraction(1, 48) + Fraction(1, 2 * sr)
        variants.append({"variant": name, "decoded_frames": frames[-1],
                         "internal_cuts_checked": len(transitions) - 2,
                         "decoded_audio_pulses": len(peaks),
                         "maximum_internal_cut_error_seconds": float(max(errors)),
                         "final_boundary_error_frames": frames[-1] - expected[-1],
                         "sha256": hashlib.sha256(media.read_bytes()).hexdigest()})
        del pcm, values
    assert variants[0]["final_boundary_error_frames"] != 0
    report = {"schema": "beat-cut-evaluation/1", "fixture": "original synthetic 64x36 colors and 48kHz clicks",
              "bpm": bpm, "fps": fps, "bars": bars, "math_checks": checks, "variants": variants,
              "ffmpeg": subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[0],
              "limitations": ["CFR synthetic assembly only", "No ComfyUI/Colab generation",
                              "No beat detector or creative-quality evaluation", "Same-operator tests"]}
    (root / "EVALUATION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
