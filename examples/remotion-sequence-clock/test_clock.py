import unittest
from clock import local_interval,visible

class ClockTests(unittest.TestCase):
    def test_original_rendered_boundaries(self):
        words=[(24,31),(31,37),(55,64),(67,76)]
        self.assertEqual([local_interval(s,e,24,48) for s,e in words],[(0,7),(7,13),(31,40),(43,48)])
        for f in range(96):
            for s,e in words:
                self.assertEqual(visible(local_interval(s,e,24,48),f-24),24<=f<72 and s<=f<e)
    def test_changed_offset_duration(self):
        for s,e in [(0,10),(8,15),(15,21),(23,25),(29,40)]:
            for f in range(45):self.assertEqual(visible(local_interval(s,e,12,12),f-12),12<=f<24 and s<=f<e)
    def test_outside(self):self.assertIsNone(local_interval(0,24,24,48));self.assertIsNone(local_interval(72,80,24,48))
    def test_left_clip(self):self.assertEqual(local_interval(20,30,24,48),(0,6))
    def test_right_clip(self):self.assertEqual(local_interval(67,76,24,48),(43,48))
    def test_whole_window(self):self.assertEqual(local_interval(0,100,24,48),(0,48))
    def test_end_exclusive(self):self.assertFalse(visible((0,7),7));self.assertTrue(visible((0,7),6))
    def test_nested_absolute_offset(self):self.assertEqual(local_interval(65,70,40+24,12),(1,6))
    def test_invalid_shape(self):
        for args in [(1,1,0,4),(2,1,0,4),(-1,3,0,4),(1,3,-1,4),(1,3,0,0),(1,3,0,-1),(1.5,3,0,4),(True,3,0,4)]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):local_interval(*args)
    def test_non_integer_frame(self):
        for f in [True,1.5,float('nan')]:
            with self.assertRaises(ValueError):visible((0,2),f)

if __name__=='__main__':unittest.main()
