"""Check the two frozen numerical outputs; this does not render media."""
from pathlib import Path
import json
root=Path(__file__).resolve().parent
expected=json.loads((root/'expected.json').read_text())
for label in ['initial','return']:
    out=json.loads((root/f'captions-{label}.json').read_text())
    actual={'duration_us':out['duration_us'],'words':[{k:w[k] for k in ['text','start_us','end_us']} for w in out['words']]}
    assert actual==expected[label], label+'_mismatch'
    print(label+': '+str(len(actual['words']))+' intervals and duration match')
