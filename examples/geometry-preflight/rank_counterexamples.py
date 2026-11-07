"""Three counterexamples to a distinct-height gate. Arithmetic only; no Blender."""
import json
from quilt_check import height_uv


def describe(values):
    levels = len(set(round(z, 6) for z in values))
    return {'samples': len(values), 'distinct_rounded_levels': levels,
            'ratio': levels / len(values), 'height_range': max(values)-min(values),
            'rejected_by_5_percent_gate': levels / len(values) < 0.05}


def run():
    periodic = describe([height_uv(i/8, j/8) for i in range(1,40) for j in range(1,40)])
    ramp = describe([0.18 + 0.01*i/40 for i in range(1,40) for j in range(1,40)])
    constant = describe([0.18] * 10)
    assert periodic['rejected_by_5_percent_gate'] and abs(periodic['height_range']-0.012)<1e-12
    assert ramp['rejected_by_5_percent_gate'] and ramp['height_range'] > 0
    assert not constant['rejected_by_5_percent_gate'] and constant['height_range'] == 0
    return {'periodic_false_rejection': periodic, 'ramp_false_uniform_inference': ramp,
            'small_constant_false_acceptance': constant,
            'decision': 'Reject this threshold as a general construction gate.',
            'scope': 'Python arithmetic only; no mesh, topology, render or visual result.'}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
