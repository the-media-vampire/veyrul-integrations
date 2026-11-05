import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from caption_input import prepare, load


def sample():
    return {'timebase': 'source-seconds', 'clip_id': 'example-clip', 'track_id': 'example-caption-track',
            'segments': [{'start': 10, 'end': 11, 'text': 'Stay here', 'words': [
                {'start': 10, 'end': 10.4, 'text': 'Stay'}, {'start': 10.6, 'end': 11, 'text': 'here'}]}]}


class CaptionInput(unittest.TestCase):
    def test_source_times_survive_without_retiming(self):
        data = sample(); original = copy.deepcopy(data)
        result = prepare(data)
        self.assertEqual(result['arguments']['in_clip']['segments'], data['segments'])
        self.assertEqual(result['tool'], 'caption.add')
        self.assertNotIn('segments', result['arguments'])
        self.assertEqual(data, original)

    def test_refuses_timeline_seconds_frames_and_missing_timebase(self):
        for base in ('timeline-seconds', 'source-frames', 'timeline-frames', None):
            d = sample(); d['timebase'] = base
            with self.subTest(base=base), self.assertRaises(ValueError): prepare(d)
        d = sample(); del d['timebase']
        with self.assertRaises(ValueError): prepare(d)

    def test_refuses_premapped_top_level_segments_and_extra_fields(self):
        d = sample(); d['offset_frames'] = 5
        with self.assertRaises(ValueError): prepare(d)
        d = sample(); d['segments'][0]['start_frame'] = 300
        with self.assertRaises(ValueError): prepare(d)

    def test_nonfinite_bool_negative_or_reversed_time(self):
        for n in (True, float('nan'), float('inf'), 10**400, -1, 12, '10'):
            d = sample(); d['segments'][0]['start'] = n
            with self.subTest(n=n), self.assertRaises(ValueError): prepare(d)

    def test_segment_and_word_bounds(self):
        for field, n in (('start', 9.9), ('end', 11.1), ('end', 10)):
            d = sample(); d['segments'][0]['words'][0][field] = n
            with self.subTest(field=field, n=n), self.assertRaises(ValueError): prepare(d)

    def test_overlapping_words_and_segments_rejected(self):
        d = sample(); d['segments'][0]['words'][1]['start'] = 10.3
        with self.assertRaises(ValueError): prepare(d)
        d = sample(); d['segments'].append(copy.deepcopy(d['segments'][0]))
        with self.assertRaises(ValueError): prepare(d)

    def test_pause_between_words_preserved(self):
        words = prepare(sample())['arguments']['in_clip']['segments'][0]['words']
        self.assertAlmostEqual(words[1]['start'] - words[0]['end'], .2)

    def test_segment_without_words_supported(self):
        d = sample(); del d['segments'][0]['words']
        self.assertNotIn('words', prepare(d)['arguments']['in_clip']['segments'][0])

    def test_empty_inputs_and_long_text_rejected(self):
        changes = [('clip_id', ''), ('segments', []), ('track_id', ' ')]
        for key, value in changes:
            d = sample(); d[key] = value
            with self.assertRaises(ValueError): prepare(d)
        d = sample(); d['segments'][0]['words'][0]['text'] = 'x' * 201
        with self.assertRaises(ValueError): prepare(d)

    def test_word_and_segment_count_caps(self):
        d = sample(); d['segments'] *= 5001
        with self.assertRaises(ValueError): prepare(d)
        d = sample(); d['segments'][0]['words'] *= 251
        with self.assertRaises(ValueError): prepare(d)

    def test_parser_rejects_duplicate_and_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'in.json'
            for raw in ('{"timebase": "source-seconds", "timebase": "timeline-seconds"}', '{"start": NaN}'):
                p.write_text(raw)
                with self.assertRaises(ValueError): load(p)

    def test_cli_preserves_input_and_prints_payload(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'in.json'; raw = json.dumps(sample()); p.write_text(raw)
            result = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('caption_input.py')), str(p)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), prepare(sample()))
            self.assertEqual(p.read_text(), raw)
            self.assertEqual(len(list(Path(td).iterdir())), 1)


if __name__ == '__main__':
    unittest.main()
