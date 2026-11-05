"""Original changed-input checks; no render or network call."""
import copy
import unittest
from edl_guard import sanitize_edl

class RangeChecks(unittest.TestCase):
    def test_valid_edits_preserve_metadata_and_input(self):
        edl={"title":"Original", "ranges":[{"video_id":"a","start":2,"end":5,"label":"one"},{"video_id":"a","start":0.5,"end":2.0}]}
        original=copy.deepcopy(edl)
        clean,rejected=sanitize_edl(edl)
        self.assertEqual(clean,edl)
        self.assertEqual(rejected,[])
        self.assertEqual(edl,original)
        self.assertIsNot(clean,edl)
        self.assertIsNot(clean['ranges'],edl['ranges'])

    def test_rejected_ranges_add_no_duration(self):
        invalid=[(4,3),(2,2),(float('nan'),3),(2,float('inf')),(False,True),('2','3')]
        edl={"ranges":[{"start":0,"end":1}]+[{"start":a,"end":b} for a,b in invalid]+[{"start":8,"end":10}]}
        clean,rejected=sanitize_edl(edl)
        self.assertEqual(clean['ranges'],[{"start":0,"end":1},{"start":8,"end":10}])
        self.assertEqual(sum(r['end']-r['start'] for r in clean['ranges']),3)
        self.assertEqual([r['index'] for r in rejected],list(range(1,7)))
        self.assertTrue(all(r['reason'] for r in rejected))

    def test_finite_changed_float_values(self):
        clean,rejected=sanitize_edl({"ranges":[{"start":1.25,"end":3.75},{"start":7.0,"end":7.125}]})
        self.assertFalse(rejected)
        self.assertEqual(sum(r['end']-r['start'] for r in clean['ranges']),2.625)

if __name__=='__main__':unittest.main()
