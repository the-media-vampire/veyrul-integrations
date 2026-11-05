#!/usr/bin/env python3
"""Route declared source seconds or timeline frames to exactly one caption.add input."""
import argparse
from copy import deepcopy
import json
import sys
from caption_input import load, prepare


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
