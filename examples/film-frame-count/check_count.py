"""Execute only the reviewed FILM generator control flow with scalar test doubles.

No neural model, image decoder, encoder, network, or third-party imports run.
The extracted functions retain their upstream statements and Apache-2.0 origin.
"""
import argparse
import ast
import hashlib
import json
from fractions import Fraction
from pathlib import Path

PINNED_COMMIT = "69f8708f08e62c2edf46a27616a4bfcf083e2076"
PINNED_SHA256 = "aba55119d8c4af3f86b7482df5d5161dd46fff05791a902faec1a3edc7c63592"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", type=Path, help="Unmodified eval/util.py from the pinned FILM commit")
args = parser.parse_args()
source = args.source
with source.open("rb") as handle:
    raw = handle.read(1_048_577)
if len(raw) > 1_048_576 or hashlib.sha256(raw).hexdigest() != PINNED_SHA256:
    parser.error("source bytes do not match the reviewed FILM commit; nothing executed")
names = {'_recursive_generator', 'interpolate_recursively_from_memory',
         'interpolate_recursively_from_files'}
nodes = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name in names]
assert len(nodes) == 3

class Frame:
    def __init__(self, value): self.value = Fraction(value)
    def __getitem__(self, _): return self

class NP:
    newaxis = None
    float32 = float
    @staticmethod
    def full(**_): return None

class Progress:
    def __init__(self, **_): pass
    def update(self, _): pass

def midpoint(a, b, _): return [Frame((a.value + b.value) / 2)]

env = {'np': NP, 'tqdm': Progress, 'read_image': lambda x: Frame(int(x))}
module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *nodes], type_ignores=[])
exec(compile(ast.fix_missing_locations(module), str(source), 'exec'), env)
rows = []
for count in [1, 2, 3, 5, 25, 273]:
    for depth in [0, 1, 2, 3]:
        memory_originals = [Frame(i) for i in range(count)]
        file_originals = [Frame(i) for i in range(count)]
        env['read_image'] = lambda name: file_originals[int(name)]
        a = list(env['interpolate_recursively_from_memory'](memory_originals, depth, midpoint))
        b = list(env['interpolate_recursively_from_files']([str(i) for i in range(count)], depth, midpoint))
        expected = (count - 1) * 2 ** depth + 1
        assert len(a) == len(b) == expected
        assert [f.value for f in a] == [f.value for f in b]
        assert a[0].value == 0 and a[-1].value == count - 1
        assert all(y.value > x.value for x, y in zip(a, a[1:]))
        for output, originals in [(a, memory_originals), (b, file_originals)]:
            original_ids = {id(frame) for frame in originals}
            observed_originals = [id(frame) for frame in output if id(frame) in original_ids]
            assert observed_originals == [id(frame) for frame in originals], 'original identity, multiplicity or order changed'
            assert [frame.value for frame in output if frame.value.denominator == 1] == list(range(count))
        rows.append({'input_frames': count, 'depth': depth, 'actual': len(a),
                     'readme_formula': (2 ** depth + 1) * (count - 1), 'expected': expected,
                     'each_original_once_in_order_both_paths': True})
result = {'upstream_commit': '69f8708f08e62c2edf46a27616a4bfcf083e2076',
          'source_sha256': hashlib.sha256(raw).hexdigest(),
          'scope': 'Unmodified generator statements extracted from reviewed source; scalar midpoint/image-reader test doubles only.',
          'checks': len(rows), 'both_file_and_memory_paths': True, 'passed': True,
          'model_or_media_execution': False, 'rows': rows}
print(json.dumps(result, indent=2))
