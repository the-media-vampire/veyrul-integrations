"""Meaningful boundary and input checks. Set VEYRUL_TIMING_TOOLKIT to the reviewed module."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from prepare import prepare

ROOT = Path(__file__).resolve().parent
TOOLKIT = Path(os.environ['VEYRUL_TIMING_TOOLKIT'])


class PreparationChecks(unittest.TestCase):
    def fixture(self, name='EDIT-01.json'):
        return json.loads((ROOT / name).read_text())

    def assert_schedule(self, data, expected, duration):
        result = prepare(data, TOOLKIT)
        self.assertEqual(result['durationInFrames'], duration)
        actual = [(w['text'], i['startFrame'], i['endFrame']) for w, i in zip(result['words'], result['frameIntervals'])]
        self.assertEqual(actual, expected)
        for frame in range(duration):
            matches = [i for i, (_, start, end) in enumerate(expected) if start <= frame < end]
            self.assertEqual(result['activeByFrame'][frame], matches[-1] if matches else None)
        self.assertEqual(result['unrepresentedIndices'], [])

    def test_first_edit_every_frame(self):
        self.assert_schedule(self.fixture(), [('Keep', 0, 18), ('useful', 18, 42), ('knowledge.', 42, 69),
            ('Make', 72, 84), ('every', 84, 96), ('edit', 96, 110), ('count.', 110, 128),
            ('Keep', 132, 150), ('useful', 150, 174)], 174)

    def test_changed_edit_every_frame(self):
        self.assert_schedule(self.fixture('EDIT-02.json'), [('Make', 0, 18), ('every', 18, 36), ('edit', 36, 57),
            ('count.', 57, 84), ('Keep', 90, 102), ('useful', 102, 118), ('knowledge.', 118, 136),
            ('every', 138, 156), ('edit', 156, 177)], 177)

    def test_does_not_mutate_inputs(self):
        data = self.fixture(); before = copy.deepcopy(data)
        prepare(data, TOOLKIT)
        self.assertEqual(data, before)

    def test_subframe_word_is_reported(self):
        data = self.fixture(); data['rows'] = [{'text': 'brief', 'start': '.01', 'end': '.02'}]
        data['cuts'] = [{'start_us': 0, 'end_us': 1000000, 'speed_num': 1, 'speed_den': 1}]
        result = prepare(data, TOOLKIT)
        self.assertEqual(result['unrepresentedIndices'], [0])
        self.assertEqual(result['activeByFrame'], [None] * 30)

    def test_overlap_arbitration_and_unicode(self):
        data = self.fixture(); data['rows'] = [{'text': '<b>café</b>', 'start': 0, 'end': 1},
            {'text': 'é', 'start': '.2', 'end': '.4'}, {'text': 'tie', 'start': '.2', 'end': '.4'}]
        data['cuts'] = [{'start_us': 0, 'end_us': 1000000, 'speed_num': 1, 'speed_den': 1}]
        result = prepare(data, TOOLKIT)
        self.assertEqual(result['words'][0]['text'], '<b>café</b>')
        self.assertEqual(result['activeByFrame'], [0] * 6 + [1] * 6 + [0] * 18)
        self.assertEqual(result['unrepresentedIndices'], [2])

    def test_24_fps_frame_aligned_edit(self):
        data = self.fixture(); data['fps'] = 24
        data['rows'] = [{'text': 'one', 'start': 0, 'end': '.5'}, {'text': 'two', 'start': '.5', 'end': 1}]
        data['cuts'] = [{'start_us': 0, 'end_us': 1000000, 'speed_num': 1, 'speed_den': 1}]
        self.assert_schedule(data, [('one', 0, 12), ('two', 12, 24)], 24)

    def test_empty_transcript_preserves_duration(self):
        data = self.fixture(); data['rows'] = []
        result = prepare(data, TOOLKIT)
        self.assertEqual(result['durationInFrames'], 174)
        self.assertEqual(set(result['activeByFrame']), {None})

    def test_input_rejections(self):
        for key, value in [('fps', True), ('fps', 29.97), ('fps', 61), ('rows', {}), ('cuts', []), ('unit', 'minutes')]:
            data = self.fixture(); data[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError): prepare(data, TOOLKIT)
        for value in [True, float('nan'), '-1', '1e999999999', '1e-999999999', 31, {}, '0' * 33]:
            data = self.fixture(); data['rows'][0]['start'] = value
            with self.subTest(timestamp=value), self.assertRaises(ValueError): prepare(data, TOOLKIT)

    def test_unaligned_edits_are_rejected(self):
        for change in [{'start_us': 1}, {'end_us': 2300001}, {'speed_num': 7}]:
            data = self.fixture(); data['cuts'][0].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'align'): prepare(data, TOOLKIT)

    def test_changed_toolkit_is_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / 'bad.py'; bad.write_text('raise RuntimeError("must not execute")\n')
            with self.assertRaisesRegex(ValueError, 'reviewed pin'): prepare(self.fixture(), bad)


if __name__ == '__main__':
    unittest.main()
