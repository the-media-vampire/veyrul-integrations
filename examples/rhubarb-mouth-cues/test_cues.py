import copy
from fractions import Fraction
import math
import unittest
from cues import validate, frame_ranges


class TimingTest(unittest.TestCase):
    def setUp(self):
        self.data = {'metadata': {'duration': 1}, 'mouthCues': [
            {'start': 0, 'end': 0.04, 'value': 'A'},
            {'start': 0.04, 'end': 0.05, 'value': 'B'},
            {'start': 0.05, 'end': 0.4, 'value': 'C'},
            {'start': 0.4, 'end': 1, 'value': 'X'}]}

    def test_frame_export_matches_direct_audio_clock_sampling(self):
        for rate in ['24', '25', '30', '60', '24000/1001', '30000/1001']:
            with self.subTest(rate=rate):
                fps = Fraction(rate)
                result = frame_ranges(self.data, rate)
                actual = {}
                for span in result['ranges']:
                    for n in range(span['start_frame'], span['end_frame']):
                        self.assertNotIn(n, actual)
                        actual[n] = span['value']
                self.assertEqual(len(actual), math.ceil(fps))
                for n in range(math.ceil(fps)):
                    time = Fraction(n)/fps
                    expected = next(c['value'] for c in self.data['mouthCues']
                                    if Fraction(str(c['start'])) <= time < Fraction(str(c['end'])))
                    self.assertEqual(actual[n], expected)

    def test_exact_boundary_uses_new_shape(self):
        result = frame_ranges(self.data, '25')
        self.assertEqual(result['ranges'][1], {'start_frame': 1, 'end_frame': 2, 'value': 'B'})

    def test_subframe_cue_is_reported(self):
        self.data['mouthCues'][0]['end'] = 0.01
        self.data['mouthCues'][1]['start'] = 0.01
        self.data['mouthCues'][1]['end'] = 0.02
        self.data['mouthCues'][2]['start'] = 0.02
        self.assertEqual(frame_ranges(self.data, '24')['subframe_cues_without_sample'], 1)

    def test_rejects_gap_overlap_empty_and_unknown_shape(self):
        for key, val in [('start', 0.03), ('start', 0.045), ('end', 0.04), ('value', 'Z'), ('start', True), ('end', float('nan'))]:
            with self.subTest(key=key, value=val):
                bad = copy.deepcopy(self.data)
                bad['mouthCues'][1][key] = val
                with self.assertRaises(ValueError): validate(bad)

    def test_rejects_wrong_audio_or_clip_length(self):
        with self.assertRaises(ValueError): validate(self.data, Fraction(2))
        with self.assertRaises(ValueError): validate(self.data, Fraction(9,10))
        validate(self.data, Fraction(1009,1000))

    def test_basic_shape_set_rejects_extended_cues(self):
        with self.assertRaises(ValueError): validate(self.data, shapes=set('ABCDEF'))

    def test_rejects_invalid_frame_rates(self):
        for fps in ['0', '-1', '121']:
            with self.assertRaises(ValueError): frame_ranges(self.data, fps)


if __name__ == '__main__': unittest.main()
