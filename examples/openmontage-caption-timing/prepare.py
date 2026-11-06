"""Map original word timestamps into edited-video seconds for OpenMontage.

Offline: no rendering, fetching, model calls or mutation of the source document.
"""
from pathlib import Path
import argparse
import importlib.util
import json


def prepare(document, timing):
    if not isinstance(document, dict) or set(document) != {'timebase', 'words', 'cuts'}:
        raise ValueError('requires exactly timebase, words and cuts')
    if document['timebase'] != 'source-seconds':
        raise ValueError('only original source-seconds accepted; do not retime output timestamps twice')
    if not isinstance(document['words'], list) or len(document['words']) > 500:
        raise ValueError('at most 500 source words per request')
    if not isinstance(document['cuts'], list) or len(document['cuts']) > 100:
        raise ValueError('at most 100 ordered cuts per request')
    mapped = timing.retime_words(timing.normalize_words(document['words']), document['cuts'])
    # Each occurrence remains separate, including a word retained in repeated cuts.
    words = [{'word': w['text'], 'start': w['start_us'] / 1_000_000,
              'end': w['end_us'] / 1_000_000} for w in mapped['words']]
    return {'timebase': 'edited-video-seconds', 'duration_seconds': mapped['duration_us'] / 1_000_000,
            'segments': [{'words': words}],
            'limits': ['Pass segments to remotion_caption_burn only with the matching edited video.',
                       'The native converter truncates seconds to integer milliseconds; submillisecond intervals may collapse.',
                       'No video edit, caption burn, ASR accuracy or visual-placement validation was run.']}


def load_timing():
    path = Path(__file__).resolve().parent.parent / 'edit-aware-word-timing' / 'media_timeline.py'
    spec = importlib.util.spec_from_file_location('veyrul_saved_timing', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    if args.input.stat().st_size > 1_048_576:
        parser.error('input exceeds 1 MiB')
    print(json.dumps(prepare(json.loads(args.input.read_text()), load_timing()), indent=2, allow_nan=False))
