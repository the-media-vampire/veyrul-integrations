import copy
import unittest
import json, subprocess, sys, tempfile
from pathlib import Path
from route_input import route


def sample(timebase='source-seconds'):
    return {'timebase':timebase,'clip_id':'take2','track_id':'captions','segments':[{'start':10,'end':30,'text':'Two words','words':[{'start':10,'end':20,'text':'Two'},{'start':20,'end':30,'text':'words'}]}]}

class RoutingTests(unittest.TestCase):
    def test_source_preserves_coordinates(self):
        value=sample();value['segments'][0]['start']=9.5;before=copy.deepcopy(value);p=route(value)
        self.assertEqual(p['arguments']['in_clip']['segments'],value['segments']);self.assertEqual(value,before);self.assertNotIn('segments',p['arguments'])
    def test_timeline_once(self):
        p=route(sample('timeline-frames'))['arguments'];self.assertNotIn('in_clip',p);self.assertNotIn('clip_id',p)
        self.assertEqual(p['segments'][0]['start_frame'],10);self.assertEqual(p['segments'][0]['words'][1]['end_frame'],30)
    def test_no_rounding(self):
        v=sample('timeline-frames');v['segments'][0]['words'][0]['start']=10.5
        with self.assertRaisesRegex(ValueError,'integers'):route(v)
    def test_bool_refused(self):
        v=sample('timeline-frames');v['segments'][0]['start']=False
        with self.assertRaises(ValueError):route(v)
    def test_outside_word(self):
        for tb in ['source-seconds','timeline-frames']:
            with self.subTest(tb=tb):
                v=sample(tb);v['segments'][0]['words'][1]['end']=31
                with self.assertRaises(ValueError):route(v)
    def test_unknown_timebase(self):
        with self.assertRaisesRegex(ValueError,'declare'):route(sample('milliseconds'))
    def test_no_inference(self):
        v=sample();v.pop('timebase')
        with self.assertRaises(ValueError):route(v)
    def test_extraneous_mapping(self):
        v=sample('timeline-frames');v['in_clip']={}
        with self.assertRaises(ValueError):route(v)
    def test_overlap(self):
        v=sample('timeline-frames');v['segments'][0]['words'][1]['start']=19
        with self.assertRaises(ValueError):route(v)
    def test_infinite(self):
        v=sample('source-seconds');v['segments'][0]['end']=float('inf')
        with self.assertRaises(ValueError):route(v)
    def test_zero_duration(self):
        v=sample('timeline-frames');v['segments'][0]['words'][1]['end']=20
        with self.assertRaises(ValueError):route(v)
    def test_isolated_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            f=Path(folder)/'input.json';f.write_text(json.dumps(sample('timeline-frames')))
            run=subprocess.run([sys.executable,'-I',str(Path(__file__).with_name('route_input.py')),str(f)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(json.loads(run.stdout)['arguments']['segments'][0]['start_frame'],10)
    def test_empty(self):
        v=sample();v['segments']=[]
        with self.assertRaises(ValueError):route(v)

if __name__=='__main__':unittest.main()
