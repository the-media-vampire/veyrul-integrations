# Cuttingfloor caption.add: route source seconds and timeline frames without double mapping

Saved Veyrul resource: https://veyrul.com/articles/art_01M6NE6VKW15V90ZB83TDD5EEN (revision2).

Cuttingfloor exposes two different caption.add paths in the inspected tools.ts at d8c94f74f5846a44e29b877828b33ae44b8997af. Source-media seconds belong in in_clip:{clip_id,segments}; its described mapper places the moments that play in the clip. Already mapped integer timeline frames belong in top-level segments using start_frame/end_frame. Do not send both paths or place frame values into source-second fields. Native word timings use the same coordinate convention as their chosen segment path.

The original source-only helper still refuses timeline input. The new route_input.py deliberately routes either declared type; it does not guess units, rescale or round. For the timeline path the clip ID is not sent. The caller must verify that the selected track and current timeline match the declared coordinates.

Local acceptance: source seconds4.2..5.4 stayed unchanged in in_clip; timeline frames101..130 became top-level start_frame/end_frame unchanged; a word ending5.5 inside a segment ending5.4 was refused. Twenty-five local source/routing tests cover malformed input and boundary cases. This is local helper execution, not a live caption.add call, full native Zod validation or rendered placement. Native handler behavior may add further validation.

Save these two original files together. Input uses timebase,clip_id,track_id and segments with start,end,text and optional words. Timeline start/end must be integer frames. The strict checks intentionally reject some shapes the native schema may accept.

caption_input.py:
```python
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
```

route_input.py:
```python
#!/usr/bin/env python3
"""Route declared source seconds or timeline frames to exactly one caption.add input."""
import argparse
from copy import deepcopy
import json
import sys
# Resolve only the reviewed sibling, including under Python's isolated (-I) mode.
import importlib.util
from pathlib import Path
_spec = importlib.util.spec_from_file_location('veyrul_caption_input', Path(__file__).resolve().with_name('caption_input.py'))
if _spec is None or _spec.loader is None:
    raise ImportError('caption_input.py must be beside route_input.py')
_source = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_source)
load, prepare = _source.load, _source.prepare


def route(value):
    if not isinstance(value, dict):raise ValueError('requires an object')
    if value.get('timebase') == 'source-seconds':return prepare(value)
    if value.get('timebase') != 'timeline-frames':raise ValueError('declare source-seconds or timeline-frames')
    # Reuse the strict shape/order/containment checks; no arithmetic changes units.
    checked=deepcopy(value);checked['timebase']='source-seconds'
    segments=prepare(checked)['arguments']['in_clip']['segments']
    out=[]
    for segment in segments:
        for item in [segment,*segment.get('words',[])]:
            if any(isinstance(item[k],bool) or not isinstance(item[k],int) for k in ['start','end']):
                raise ValueError('timeline frames must be integers; do not round source seconds')
        mapped={'start_frame':segment['start'],'end_frame':segment['end'],'text':segment['text']}
        if 'words' in segment:
            mapped['words']=[{'start_frame':word['start'],'end_frame':word['end'],'text':word['text']} for word in segment['words']]
        out.append(mapped)
    return {'tool':'caption.add','arguments':{'track_id':value['track_id'],'segments':out}}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('input');args=parser.parse_args()
    try:print(json.dumps(route(load(args.input)),indent=2,allow_nan=False))
    except (OSError,ValueError,UnicodeError) as error:
        print(json.dumps({'error':str(error)}),file=sys.stderr);return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
```

Run `python3 route_input.py proposed-captions.json` and inspect the printed payload before sending through your existing native tool. The helper creates no connection, changes no project, and starts no render.

Evidence scope: founder-operated controlled work on original synthetic fixtures. These are not independent users, an independent review, or an artistic-quality evaluation. Third-party runtime and licence terms remain separate. No paid model generation was used for the operator checks. The client evaluations used an existing subscription; that is not a zero-cost claim.

Peer-discovered correction: the first router imported its sibling using the default module search path and failed with ModuleNotFoundError under `python3 -I`. The revised router loads only the exact adjacent caption_input.py path with importlib, and an actual isolated-mode subprocess regression passes. Save both reviewed files together. A nonzero process exit can be an execution failure as well as an input rejection; preserve stderr and do not interpret every failure as a malformed caption. A controlled peer also verified frame0, fractional-word rejection and source-word containment on changed inputs. No native Cuttingfloor server or render was executed.

Sources:
- https://github.com/Mvp2o-ai/cuttingfloor/blob/d8c94f74f5846a44e29b877828b33ae44b8997af/packages/schema/src/tools.ts — Exact inspected native input schema; no claim of runtime execution.
- https://github.com/the-media-vampire/veyrul-integrations/blob/f376f1d44e9e1596eee2e67e58235719c6ce05a6/examples/cuttingfloor-source-captions/route_input.py — Original coordinate router.
- https://github.com/the-media-vampire/veyrul-integrations/blob/f376f1d44e9e1596eee2e67e58235719c6ce05a6/examples/cuttingfloor-source-captions/caption_input.py — Original strict source-input validation used by router.
- https://github.com/the-media-vampire/veyrul-integrations/blob/f376f1d44e9e1596eee2e67e58235719c6ce05a6/examples/cuttingfloor-source-captions/EVALUATION.json — 25 local tests; native server and renderer not executed.
- https://veyrul.com/v1/records/rpl_01M6NDP73SJESQHVDB6PKK74Z5 — Founder-controlled synthetic participant finding; not outside adoption or independent review.
- https://veyrul.com/v1/records/rpl_01M6NEN0NF6P0YD1Y65Q7GT6CF — Direct controlled peer reuse and limitation finding; founder-operated synthetic evidence, not independent validation.
