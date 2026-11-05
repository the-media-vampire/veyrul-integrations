#!/usr/bin/env python3
"""Validate explicitly source-timed words and print a Cuttingfloor caption.add payload."""
import argparse
import json
import math
from pathlib import Path
import sys

MAX_BYTES = 2 * 1024 * 1024


def keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ValueError('unexpected or missing fields')


def text(value, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError('text is empty or too long')
    return value


def interval(value):
    for field in ('start', 'end'):
        n = value[field]
        if isinstance(n, bool) or not isinstance(n, (int, float)):
            raise ValueError('times must be finite nonnegative source seconds')
        try:
            finite = math.isfinite(n)
        except OverflowError:
            finite = False
        if not finite or n < 0:
            raise ValueError('times must be finite nonnegative source seconds')
    if value['end'] <= value['start']:
        raise ValueError('end must follow start')


def prepare(value):
    keys(value, ('timebase', 'clip_id', 'track_id', 'segments'))
    if value['timebase'] != 'source-seconds':
        raise ValueError('requires original source-seconds; never supply mapped timeline times')
    clip_id, track_id = text(value['clip_id'], 256), text(value['track_id'], 256)
    segments = value['segments']
    if not isinstance(segments, list) or not 1 <= len(segments) <= 5000:
        raise ValueError('requires 1–5000 segments for one clip')
    cleaned = []
    previous_end = 0
    for segment in segments:
        keys(segment, ('start', 'end', 'text'), ('words',))
        interval(segment)
        if segment['start'] < previous_end:
            raise ValueError('segments overlap or are out of source-time order')
        previous_end = segment['end']
        item = {k: segment[k] for k in ('start', 'end')}
        item['text'] = text(segment['text'], 2000)
        if 'words' in segment:
            words = segment['words']
            if not isinstance(words, list) or not 1 <= len(words) <= 500:
                raise ValueError('requires 1–500 words when words are supplied')
            word_end = segment['start']
            item['words'] = []
            for word in words:
                keys(word, ('start', 'end', 'text'))
                interval(word)
                if word['start'] < word_end or word['end'] > segment['end']:
                    raise ValueError('word overlaps, is out of order or is outside its segment')
                word_end = word['end']
                item['words'].append({'start': word['start'], 'end': word['end'], 'text': text(word['text'], 200)})
        cleaned.append(item)
    return {'tool': 'caption.add', 'arguments': {
        'track_id': track_id, 'in_clip': {'clip_id': clip_id, 'segments': cleaned}}}


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


def load(path):
    with Path(path).open('rb') as f:
        raw = f.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('input exceeds 2 MiB')
    return json.loads(raw, object_pairs_hook=unique_fields,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON number')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        result = prepare(load(args.input))
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
