#!/usr/bin/env python3
"""Apply the inspected timing library to a local JSON edit specification."""
import argparse
import json
from pathlib import Path
from media_timeline import normalize_words,retime_words,build_events

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    args=parser.parse_args()
    data=json.loads(args.input.read_text(encoding='utf-8'))
    normalized=normalize_words(data['rows'],data['unit'])
    retimed=retime_words(normalized,data['cuts'])
    highlights=build_events(retimed['words'],retimed['duration_us'])
    print(json.dumps({'normalized':normalized,'retimed':retimed,'highlights':highlights},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
