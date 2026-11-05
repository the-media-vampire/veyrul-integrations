#!/usr/bin/env python3
"""Measure a PCM16 WAV's loop boundary. No edits, models, network or audibility verdict."""
import argparse
from array import array
import json
import math
from pathlib import Path
import sys
import wave

MAX_BYTES = 128 * 1024 * 1024


def measure(path, max_bytes=MAX_BYTES):
    path = Path(path)
    if max_bytes <= 0 or path.stat().st_size > max_bytes:
        raise ValueError('input exceeds the byte limit')
    with wave.open(str(path), 'rb') as wav:
        channels, width, rate, frames = (
            wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes())
        if wav.getcomptype() != 'NONE' or width != 2:
            raise ValueError('requires uncompressed signed 16-bit PCM WAV')
        if not 1 <= channels <= 32 or rate <= 0 or frames < 2:
            raise ValueError('requires 1–32 channels, positive sample rate and at least two frames')
        if frames * channels * width > max_bytes:
            raise ValueError('declared audio exceeds the byte limit')
        first, last = [None] * channels, [None] * channels
        sums, squares = [0] * channels, [0] * channels
        peaks, delta_peaks, delta_squares = [0] * channels, [0] * channels, [0] * channels
        count = 0
        while count < frames:
            requested = min(8192, frames - count)
            raw = wav.readframes(requested)
            if len(raw) != requested * channels * width:
                raise ValueError('truncated PCM payload')
            samples = array('h')
            samples.frombytes(raw)
            if sys.byteorder != 'little':
                samples.byteswap()
            for i, sample in enumerate(samples):
                c = i % channels
                if first[c] is None:
                    first[c] = sample
                if last[c] is not None:
                    delta = sample - last[c]
                    delta_peaks[c] = max(delta_peaks[c], abs(delta))
                    delta_squares[c] += delta * delta
                last[c] = sample
                sums[c] += sample
                squares[c] += sample * sample
                peaks[c] = max(peaks[c], abs(sample))
            count += requested
    results = []
    for c in range(channels):
        seam = abs(first[c] - last[c])
        results.append({
            'channel': c + 1,
            'first_sample': first[c], 'last_sample': last[c],
            'boundary_jump_fs': seam / 32768,
            'max_adjacent_jump_fs': delta_peaks[c] / 32768,
            'adjacent_jump_rms_fs': math.sqrt(delta_squares[c] / (frames - 1)) / 32768,
            'boundary_to_max_adjacent_ratio': seam / delta_peaks[c] if delta_peaks[c] else None,
            'dc_offset_fs': sums[c] / frames / 32768,
            'rms_fs': math.sqrt(squares[c] / frames) / 32768,
            'peak_fs': peaks[c] / 32768,
        })
    return {
        'schema': 'veyrul-audio-loop-measurement/1',
        'sample_rate_hz': rate, 'frames': frames, 'channels': channels,
        'duration_seconds': frames / rate, 'per_channel': results,
        'method': 'Compare the last-to-first sample step with steps inside each channel.',
        'audibility_assessed': False, 'loudness_lufs_measured': False,
        'limitations': [
            'A normal continuous waveform can have a nonzero last-to-first sample step.',
            'A small boundary jump does not establish rhythmic, phase or perceptual continuity.',
            'Inspect repeated playback, channel behavior and the intended loop length.',
            'LUFS, true peak and encoded delivery checks require separate measurements.',
        ],
        'files_modified': 0, 'network_requests': 0, 'model_calls': 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wav', type=Path)
    args = parser.parse_args()
    try:
        result = measure(args.wav)
    except (OSError, ValueError, wave.Error, EOFError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
