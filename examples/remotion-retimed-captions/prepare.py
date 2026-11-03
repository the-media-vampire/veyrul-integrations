#!/usr/bin/env python3
"""Prepare bounded, frame-aligned Remotion input with reviewed saved timing code."""
import argparse
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

TOOLKIT_SHA256 = '1d9508741b4a64e002e883dfa309b53c400fbf155e938aa0db085e6e64f96f14'


def prepare(data, toolkit_path):
    if not isinstance(data, dict) or set(data) != {'label', 'fps', 'unit', 'rows', 'cuts'}:
        raise ValueError('expected label, fps, unit, rows and cuts')
    if not isinstance(data['label'], str) or not 1 <= len(data['label']) <= 80:
        raise ValueError('label must contain 1..80 characters')
    fps = data['fps']
    if type(fps) is not int or not 1 <= fps <= 60:
        raise ValueError('this example supports integer fps in 1..60')
    if data['unit'] not in ['seconds', 'milliseconds', 'microseconds']:
        raise ValueError('unsupported timestamp unit')
    rows, cuts = data['rows'], data['cuts']
    if not isinstance(rows, list) or len(rows) > 80 or not isinstance(cuts, list) or not 1 <= len(cuts) <= 12:
        raise ValueError('maximum 80 words and 1..12 cuts')
    maximum = {'seconds': 30, 'milliseconds': 30000, 'microseconds': 30000000}[data['unit']]
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'text', 'start', 'end'}:
            raise ValueError('word must have text, start and end')
        if not isinstance(row['text'], str) or len(row['text']) > 40:
            raise ValueError('example word limit is 40 characters; no automatic shortening')
        for key in ['start', 'end']:
            value = row[key]
            if type(value) not in [str, int, float] or len(str(value)) > 32:
                raise ValueError('bounded timestamp required')
            try:
                number = Decimal(str(value))
                if not number.is_finite() or not 0 <= number <= maximum:
                    raise ValueError('source timestamps must lie in first 30 seconds')
                if not -12 <= number.as_tuple().exponent <= 12:
                    raise ValueError('timestamp exponent is outside the bounded example range')
            except InvalidOperation as error:
                raise ValueError('invalid timestamp') from error
    offset = Fraction(0)
    segments = []
    for index, cut in enumerate(cuts):
        if not isinstance(cut, dict) or set(cut) != {'start_us', 'end_us', 'speed_num', 'speed_den'}:
            raise ValueError('invalid cut keys')
        if any(type(v) is not int for v in cut.values()):
            raise ValueError('cut values must be integers')
        if not 0 <= cut['start_us'] < cut['end_us'] <= 30000000:
            raise ValueError('source cut outside 0..30 seconds')
        if not 1 <= cut['speed_num'] <= 12 or not 1 <= cut['speed_den'] <= 12:
            raise ValueError('speed numerator and denominator must be 1..12')
        begin = Fraction(cut['start_us'] * fps, 1000000)
        end = Fraction(cut['end_us'] * fps, 1000000)
        length = (end - begin) * cut['speed_den'] / cut['speed_num']
        # Reject unsupported quantization instead of changing the edit silently.
        if any(x.denominator != 1 for x in [begin, end, offset, length]):
            raise ValueError('cut boundaries and output cut durations must align to the chosen frame grid')
        segments.append({'cut_index': index, 'from': int(offset), 'durationInFrames': int(length),
                         'trimBefore': int(begin), 'sourceFrames': int(end - begin),
                         'playbackRate': cut['speed_num'] / cut['speed_den']})
        offset += length
    if offset > 60 * fps:
        raise ValueError('output exceeds the 60-second example limit')
    source = Path(toolkit_path).read_bytes()
    if hashlib.sha256(source).hexdigest() != TOOLKIT_SHA256:
        raise ValueError('timing toolkit differs from the reviewed pin; review a changed module separately')
    spec = importlib.util.spec_from_file_location('veyrul_reviewed_timing', toolkit_path)
    toolkit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(toolkit)
    original = toolkit.normalize_words(rows, data['unit'])
    result = toolkit.retime_words(original, cuts)
    words = result['words']
    # The saved toolkit rounds to microseconds. That rounding can move a boundary
    # off an exact video frame (e.g. 11/3 seconds). Map the retained identities
    # directly from source microseconds and rational cuts before frame rounding.
    by_source = {word['source_index']: word for word in original}
    exact_starts = []
    frame_intervals = []
    ceil = lambda q: -(-q.numerator // q.denominator)
    for word in words:
        source_word = by_source[word['source_index']]
        cut = cuts[word['cut_index']]
        base = segments[word['cut_index']]['from']
        scale = Fraction(fps * cut['speed_den'], 1000000 * cut['speed_num'])
        start = base + (max(source_word['start_us'], cut['start_us']) - cut['start_us']) * scale
        end = base + (min(source_word['end_us'], cut['end_us']) - cut['start_us']) * scale
        exact_starts.append(start)
        frame_intervals.append({'startFrame': ceil(start), 'endFrame': ceil(end)})
    active = []
    for frame in range(int(offset)):
        candidates = [i for i, interval in enumerate(frame_intervals)
                      if interval['startFrame'] <= frame < interval['endFrame']]
        active.append(max(candidates, key=lambda i: (exact_starts[i], -i)) if candidates else None)
    represented = set(active) - {None}
    captions = [{'text': x['text'], 'startMs': x['start_us'] / 1000,
                 'endMs': x['end_us'] / 1000, 'timestampMs': None, 'confidence': None} for x in words]
    return {'label': data['label'], 'fps': fps, 'durationInFrames': int(offset),
            'duration_us': result['duration_us'], 'segments': segments, 'words': words,
            'sourceWords': original, 'captions': captions, 'activeByFrame': active,
            'frameIntervals': frame_intervals,
            'unrepresentedIndices': [i for i in range(len(words)) if i not in represented],
            'timingPolicy': 'Frame-start sampling from exact cut ratios before microsecond rounding; latest active start wins; ties keep the lower occurrence index. captions retains rounded-millisecond toolkit output; rendering uses frameIntervals.',
            'resource': {'record_id': 'art_01M6FTHTXK218N2MSF2FERAST5', 'revision': 1,
                         'toolkit_sha256': TOOLKIT_SHA256, 'evidence': 'controlled original code; unreviewed'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--toolkit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists; use a new path')
    if args.input.stat().st_size > 65536:
        parser.error('input exceeds 64 KiB')
    try:
        result = prepare(json.loads(args.input.read_text(encoding='utf-8')), args.toolkit)
        with args.output.open('x', encoding='utf-8') as out:
            json.dump(result, out, indent=2, ensure_ascii=False)
            out.write('\n')
        print(json.dumps({'output': str(args.output), 'frames': result['durationInFrames'],
                          'unrepresentedIndices': result['unrepresentedIndices']}))
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
