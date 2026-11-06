#!/usr/bin/env python3
"""Local Rhubarb runner and rational-frame export. Python standard library only.

Input: <=120 s mono PCM16 WAV at 16 kHz. Never uploads audio or installs tools.
Frame n samples the cue at n/fps; adjacent ranges use [start_frame, end_frame).
"""
import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
import subprocess
import time
import wave

SHAPES = set('ABCDEFGHX')


def number(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError('cue times must be JSON numbers')
    if not math.isfinite(value):
        raise ValueError('cue times must be finite')
    return Fraction(str(value))


def validate(data, audio_duration=None, shapes=SHAPES):
    duration = number(data['metadata']['duration'])
    if not 0 < duration <= 120:
        raise ValueError('duration must be between 0 and 120 seconds')
    if audio_duration is not None and not 0 <= audio_duration-duration < Fraction(11, 1000):
        raise ValueError('cue duration does not match the audio; expected centisecond truncation')
    cues = data['mouthCues']
    if not isinstance(cues, list) or not cues or len(cues) > 24000:
        raise ValueError('missing or oversized mouthCues')
    end = Fraction(0)
    for cue in cues:
        start, stop = number(cue['start']), number(cue['end'])
        if start != end or stop <= start or stop > duration:
            raise ValueError('cues must cover the duration without gaps, overlaps or empty intervals')
        if cue['value'] not in shapes:
            raise ValueError('unexpected mouth shape')
        end = stop
    if end != duration:
        raise ValueError('last cue must end at metadata.duration')
    return duration


def frame_ranges(data, fps):
    duration = validate(data)
    fps = Fraction(fps)
    if not 1 <= fps <= 120:
        raise ValueError('fps must be between 1 and 120')
    ranges, skipped = [], 0
    for cue in data['mouthCues']:
        start = math.ceil(number(cue['start']) * fps)
        end = math.ceil(number(cue['end']) * fps)
        if start == end:
            skipped += 1
            continue
        ranges.append({'start_frame': start, 'end_frame': end, 'value': cue['value']})
    return {'fps': str(fps), 'frame_count': math.ceil(duration * fps),
            'sampling': 'frame n samples time n/fps; end_frame is exclusive',
            'subframe_cues_without_sample': skipped, 'ranges': ranges}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rhubarb', type=Path, required=True, help='trusted existing executable')
    parser.add_argument('--audio', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='new directory; existing paths refused')
    parser.add_argument('--recognizer', choices=['pocketSphinx', 'phonetic'], required=True)
    parser.add_argument('--extended-shapes', default='GHX')
    parser.add_argument('--dialog', type=Path)
    parser.add_argument('--fps', default='24', help='integer or fraction, e.g. 30000/1001')
    args = parser.parse_args()
    fps = Fraction(args.fps)
    if not 1 <= fps <= 120:
        parser.error('fps must be between 1 and 120')
    if set(args.extended_shapes) - set('GHX') or len(set(args.extended_shapes)) != len(args.extended_shapes):
        parser.error('extended shapes must be a unique subset of GHX (or empty)')
    audio, binary = args.audio.resolve(strict=True), args.rhubarb.resolve(strict=True)
    if not audio.is_file() or audio.stat().st_size > 4*1024*1024:
        parser.error('input must be a WAV file no larger than 4 MiB')
    with wave.open(str(audio), 'rb') as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 16000, 'NONE'):
            parser.error('convert audio to mono PCM16 WAV at 16 kHz first')
        duration = Fraction(wav.getnframes(), wav.getframerate())
        if not Fraction(1, 100) <= duration <= 120:
            parser.error('audio must be between 0.01 and 120 seconds')
    command = [str(binary), '-r', args.recognizer, '-f', 'json', '--machineReadable',
               '--threads', '2', '--extendedShapes', args.extended_shapes]
    if args.dialog:
        dialog = args.dialog.resolve(strict=True)
        if not dialog.is_file() or dialog.stat().st_size > 65536:
            parser.error('dialog must be a text file <=64 KiB')
        dialog.read_text(encoding='utf-8')
        command += ['--dialogFile', str(dialog)]
    command += [str(audio)]
    # mkdir is exclusive; do not overwrite an earlier result or the user's audio.
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, timeout=120, check=False)
    except subprocess.TimeoutExpired as error:
        (args.out/'status.jsonl').write_bytes(error.stderr or b'')
        (args.out/'raw-cues.json').write_bytes(error.stdout or b'')
        raise SystemExit('Rhubarb timed out; partial output preserved, no success receipt.')
    (args.out/'status.jsonl').write_bytes(result.stderr)
    (args.out/'raw-cues.json').write_bytes(result.stdout)
    if result.returncode:
        raise SystemExit('Rhubarb failed; preserved status.jsonl. No success receipt written.')
    data = json.loads(result.stdout)
    validate(data, duration, set('ABCDEF'+args.extended_shapes))
    # Keep the exact output private; sanitized JSON and receipt contain no input pathname.
    safe = {'metadata': {'duration': data['metadata']['duration']}, 'mouthCues': data['mouthCues']}
    frames = frame_ranges(safe, fps)
    for name, value in [('cues.json', safe), ('frames.json', frames)]:
        (args.out/name).write_text(json.dumps(value, indent=2)+'\n')
    receipt = {'audio_sha256': hashlib.sha256(audio.read_bytes()).hexdigest(),
               'rhubarb_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
               'recognizer': args.recognizer, 'extended_shapes': args.extended_shapes,
               'cue_count': len(data['mouthCues']), 'duration_seconds': float(duration),
               'elapsed_seconds': round(time.monotonic()-started, 3),
               'fps': str(fps), 'frame_count': frames['frame_count'],
               'execution': 'local CLI and structural timing validation only',
               'limitations': ['no perceptual lip-sync score', 'no character artwork or editor integration tested',
                               'audio and private paths must not be shared automatically']}
    (args.out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
