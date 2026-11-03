"""Executed bounded synthetic checks; all oracles use the standard library."""

import copy
from decimal import Decimal, Inexact, Rounded, localcontext
from fractions import Fraction
import itertools
import json
import math
from pathlib import Path
import random
import unittest

from media_timeline import normalize_words, retime_words, build_events


def raw(start=0, end=1, text='word'):
    return dict(text=text, start=start, end=end)


def word(start=0, end=1, source=0, text='word'):
    return dict(text=text, source_index=source, start_us=start, end_us=end)


def event_word(start=0, end=1, source=0, cut=0, text='word'):
    return dict(word(start, end, source, text), cut_index=cut)


def cut(start=0, end=1, num=1, den=1):
    return dict(start_us=start, end_us=end, speed_num=num, speed_den=den)


def nearest(numerator, denominator):
    quotient, remainder = divmod(numerator, denominator)
    return quotient + (2 * remainder >= denominator)


def oracle_retime(words, cuts):
    """LCM integer timeline, independent of production Fraction accumulation."""
    grid = 1
    for c in cuts:
        grid = grid * c['speed_num'] // math.gcd(grid, c['speed_num'])
    carry = 0
    result = []
    for ci, c in enumerate(cuts):
        step = grid // c['speed_num'] * c['speed_den']
        for w in words:
            left, right = max(w['start_us'], c['start_us']), min(w['end_us'], c['end_us'])
            if left < right:
                start = nearest(carry + (left - c['start_us']) * step, grid)
                end = nearest(carry + (right - c['start_us']) * step, grid)
                if start < end:
                    result.append(event_word(start, end, w['source_index'], ci, w['text']))
        carry += (c['end_us'] - c['start_us']) * step
    result.sort(key=lambda w: (w['start_us'], w['end_us'], w['cut_index'], w['source_index']))
    return dict(words=result, duration_us=nearest(carry, grid))


def oracle_events(words, duration):
    """Assign priority masks in sorted priority order, then run-length encode."""
    samples = list(range(5000, duration, 10000))
    count = (duration + 9999) // 10000
    if len(samples) < count:
        samples.append(duration - 1)
    choices = [None] * count
    for i in sorted(range(len(words)), key=lambda i: (-words[i]['start_us'], i)):
        w = words[i]
        for k, sample in enumerate(samples):
            if choices[k] is None and w['start_us'] <= sample < w['end_us']:
                choices[k] = i
    events, position = [], 0
    for active, run in itertools.groupby(choices):
        length = sum(1 for _ in run)
        events.append(dict(start_cs=position, end_cs=position + length, active_index=active))
        position += length
    return dict(events=events, unrepresented_indices=[i for i in range(len(words)) if i not in choices])


class NormalizationTests(unittest.TestCase):
    def test_units_and_half_up(self):
        for unit, value in [('seconds', '0.0000025'), ('milliseconds', '.0025'), ('microseconds', '2.5')]:
            self.assertEqual(normalize_words([raw(value, 10)], unit)[0]['start_us'], 3)
        self.assertEqual(normalize_words([raw(1, 2)])[0]['end_us'], 2000000)

    def test_valid_grammar(self):
        for token in ['+0', '-0', '-0.0', '1.', '.1', '+.1', '001.20', '1.e-3', '1E+1', ' \t\n\r\v\f.5 ']:
            expected = Fraction(token.strip()) * 1000000
            self.assertEqual(normalize_words([raw(token, 29)])[0]['start_us'], nearest(expected.numerator, expected.denominator))

    def test_invalid_numbers_at_each_boundary(self):
        bad = [True, False, None, [], {}, (), Decimal('.5'), Fraction(1, 2), 1j,
               float('nan'), float('inf'), float('-inf'), -1, '-1e-20', '', '.', '+',
               '1e', '1e+', '1_0', '1/2', '0x10', '1 0', '1\t0', '١', '１２',
               '1e٢', '\u00a01', '1\u2003', 'NaN', 'Infinity', '1\x00']
        for value in bad:
            for field in ('start', 'end'):
                row = raw(0, 29)
                row[field] = value
                with self.subTest(value=repr(value), field=field), self.assertRaises(ValueError):
                    normalize_words([row])

    def test_structure_and_units(self):
        for rows in (None, {}, (), '', True, iter([])):
            with self.assertRaises(ValueError):
                normalize_words(rows)
        for unit in ('s', '', None, True, [], {}):
            with self.assertRaises(ValueError):
                normalize_words([], unit)
        for row in (None, [], {}, {**raw(), 'extra': 1}, {'text': 'x', 'start': 0}):
            with self.assertRaises(ValueError):
                normalize_words([row])

    def test_invalid_text_all_controls(self):
        for text in [None, 1, True, [], {}, '', ' ', '\u2003'] + ['a' + chr(i) + 'b' for i in list(range(32)) + [127]]:
            with self.subTest(text=repr(text)), self.assertRaises(ValueError):
                normalize_words([raw(text=text)])

    def test_unicode_duplicates_sort_identity(self):
        texts = ['🙂', ' 世界 ', '{literal}\\x', 'e\u0301', 'é', '\u200b']
        rows = [raw(2, 3, t) for t in texts] + [raw(0, 4, 'first'), raw(2, 3, texts[0])]
        result = normalize_words(rows)
        self.assertEqual([w['source_index'] for w in result], [6, 0, 1, 2, 3, 4, 5, 7])
        self.assertEqual([w['text'] for w in result[1:]], texts + [texts[0]])

    def test_converted_sort_and_collapsed_intervals(self):
        rows = [raw('.4', '1.4', 'a'), raw('.1', '1.2', 'b')]
        self.assertEqual([w['text'] for w in normalize_words(rows, 'microseconds')], ['a', 'b'])
        for start, end in [('.1', '.4'), (1, 1), (2, 1)]:
            with self.assertRaises(ValueError):
                normalize_words([raw(start, end)], 'microseconds')
        self.assertEqual(normalize_words([raw('.49', '.5')], 'microseconds')[0]['end_us'], 1)

    def test_float_rounding_regression(self):
        self.assertEqual(normalize_words([raw(0.0001245, 1)])[0]['start_us'], 125)
        self.assertEqual(normalize_words([raw(0.0000025, 1)])[0]['start_us'], 3)

    def test_decimal_context_independence(self):
        with localcontext() as ctx:
            ctx.prec = 2
            ctx.traps[Inexact] = ctx.traps[Rounded] = True
            got = normalize_words([raw('1.234567499999999999999', '2.0000005')])
        self.assertEqual((got[0]['start_us'], got[0]['end_us']), (1234567, 2000001))

    def test_seeded_decimal_and_float_oracle(self):
        rng = random.Random(20261102)
        for _ in range(600):
            token = str(rng.randrange(0, 20000000)) + 'e-7'
            for value in (token, float(token)):
                exact = Fraction(str(value)) * 1000000
                self.assertEqual(normalize_words([raw(value, 29)])[0]['start_us'], nearest(exact.numerator, exact.denominator))


class RetimeTests(unittest.TestCase):
    def test_empty_inputs_and_full_duration(self):
        self.assertEqual(retime_words([], []), dict(words=[], duration_us=0))
        self.assertEqual(retime_words([word()], []), dict(words=[], duration_us=0))
        self.assertEqual(retime_words([], [cut(0, 5, 2)]), dict(words=[], duration_us=3))

    def test_absolute_rounding_carry(self):
        got = retime_words([word(0, 5)], [cut(0, 5, 2)] * 3)
        self.assertEqual(got['duration_us'], 8)
        self.assertEqual([(w['start_us'], w['end_us']) for w in got['words']], [(0, 3), (3, 5), (5, 8)])

    def test_collapsed_occurrence_phase(self):
        got = retime_words([word()], [cut(0, 1, 3)] * 12)
        self.assertEqual(got['duration_us'], 4)
        self.assertEqual([w['cut_index'] for w in got['words']], [1, 4, 7, 10])
        self.assertEqual(build_events(got['words'], 4)['unrepresented_indices'], [0, 1, 2])

    def test_exact_offset_with_local_boundary(self):
        got = retime_words([word(10, 11)], [cut(0, 1, 3), cut(10, 12, 3)])
        self.assertEqual(got['words'], [event_word(0, 1, 0, 1)])
        got2 = retime_words([word(10, 11)], [cut(0, 2, 3), cut(10, 12, 3)])
        self.assertEqual(got2['words'], [])

    def test_half_open_clipping_and_repeated_source(self):
        words = [word(0, 4), word(4, 8, 1), word(8, 10, 2)]
        self.assertEqual(retime_words(words, [cut(4, 8)])['words'], [event_word(0, 4, 1)])
        self.assertEqual(retime_words([word(4, 8)], [cut(0, 6), cut(5, 10)])['words'],
                         [event_word(4, 6, 0, 0), event_word(6, 9, 0, 1)])

    def test_stable_equal_keys_and_any_order(self):
        words = [word(10, 20, 4, 'z'), word(0, 5, 3), word(10, 20, 4, 'a')]
        got = retime_words(words, [cut(0, 30)])['words']
        self.assertEqual([w['text'] for w in got], ['word', 'z', 'a'])

    def test_all_speed_pairs(self):
        for num in range(1, 13):
            for den in range(1, 13):
                words = [word(1, 23), word(0, 2, 1)]
                cuts = [cut(0, 13, num, den), cut(10, 27, den, num)]
                self.assertEqual(retime_words(words, cuts), oracle_retime(words, cuts))

    def test_seeded_retime_and_shuffled_highlights(self):
        rng = random.Random(88143)
        for _ in range(500):
            words = []
            for i in range(rng.randrange(0, 15)):
                left = rng.randrange(0, 100000)
                words.append(word(left, left + rng.randrange(1, 30000), i % 4, '🙂 ' + str(i)))
            rng.shuffle(words)
            cuts = []
            for _ in range(rng.randrange(0, 8)):
                left = rng.randrange(0, 100000)
                cuts.append(cut(left, left + rng.randrange(1, 30000), rng.randrange(1, 13), rng.randrange(1, 13)))
            result = retime_words(words, cuts)
            self.assertEqual(result, oracle_retime(words, cuts))
            rng.shuffle(result['words'])
            self.assertEqual(build_events(result['words'], result['duration_us']), oracle_events(result['words'], result['duration_us']))

    def test_word_validation_even_without_cuts(self):
        for field in ('source_index', 'start_us', 'end_us'):
            for value in (True, False, -1, 1.5, '1', None, []):
                bad = word()
                bad[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    retime_words([bad], [])
        for bad in (None, {}, [], {**word(), 'extra': 1}, word(2, 1), word(1, 1), word(text='x\n')):
            with self.assertRaises(ValueError):
                retime_words([bad], [])

    def test_cut_validation_even_without_words(self):
        for field in ('start_us', 'end_us', 'speed_num', 'speed_den'):
            for value in (True, False, -1, 1.5, '1', None, []):
                bad = cut()
                bad[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    retime_words([], [bad])
        for bad in (None, {}, [], {**cut(), 'extra': 1}, cut(1, 1), cut(2, 1), cut(num=0), cut(den=0)):
            with self.assertRaises(ValueError):
                retime_words([], [bad])
        for bad in (None, {}, (), '', True):
            with self.assertRaises(ValueError):
                retime_words(bad, [])
            with self.assertRaises(ValueError):
                retime_words([], bad)


class HighlightTests(unittest.TestCase):
    def test_empty_zero_and_pauses(self):
        self.assertEqual(build_events([], 0), dict(events=[], unrepresented_indices=[]))
        self.assertEqual(build_events([], 10001)['events'], [dict(start_cs=0, end_cs=2, active_index=None)])
        words = [event_word(10000, 20000)]
        self.assertEqual(build_events(words, 30000), oracle_events(words, 30000))

    def test_original_position_ties_and_resume(self):
        words = [event_word(20000, 40000, 99), event_word(0, 20000, 8)]
        self.assertEqual([e['active_index'] for e in build_events(words, 40000)['events']], [1, 0])
        words = [event_word(0, 10000, 99), event_word(0, 30000, 0)]
        self.assertEqual([e['active_index'] for e in build_events(words, 30000)['events']], [0, 1])

    def test_short_and_long_unrepresented(self):
        words = [event_word(0, 30000), event_word(4000, 30000), event_word(1000, 2000)]
        self.assertEqual(build_events(words, 30000)['unrepresented_indices'], [0, 2])

    def test_exact_half_open_sample(self):
        words = [event_word(0, 5000), event_word(5000, 5001)]
        self.assertEqual(build_events(words, 10000)['events'][0]['active_index'], 1)
        self.assertEqual(build_events(words, 10000)['unrepresented_indices'], [0])

    def test_final_clamp_duration_sensitive(self):
        words = [event_word(10000, 10001)]
        self.assertEqual(build_events(words, 10001)['unrepresented_indices'], [])
        self.assertEqual(build_events(words, 10002)['unrepresented_indices'], [0])
        self.assertEqual(build_events([event_word(0, 1)], 1)['events'][0]['active_index'], 0)

    def test_event_validation(self):
        for duration in (True, False, -1, 1.0, '1', None, []):
            with self.assertRaises(ValueError):
                build_events([], duration)
        for field in ('source_index', 'cut_index', 'start_us', 'end_us'):
            for value in (True, False, -1, 1.5, '1', None, []):
                bad = event_word()
                bad[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    build_events([bad], 1)
        for bad in (None, {}, [], {**event_word(), 'extra': 1}, event_word(0, 2), event_word(1, 1), event_word(text='x\x7f')):
            with self.assertRaises(ValueError):
                build_events([bad], 1)
        with self.assertRaises(ValueError):
            build_events([event_word()], 0)
        for words in (None, {}, (), True):
            with self.assertRaises(ValueError):
                build_events(words, 1)

    def test_exhaustive_sample_boundaries(self):
        points = [0, 1, 4999, 5000, 5001, 9999, 10000, 10001, 14999, 15000, 15001, 20000]
        intervals = list(itertools.combinations(points, 2))
        for a, b in itertools.product(intervals, repeat=2):
            words = [event_word(*a), event_word(*b)]
            self.assertEqual(build_events(words, 20000), oracle_events(words, 20000))

    def test_seeded_event_oracle(self):
        rng = random.Random(143333)
        for _ in range(700):
            duration = rng.randrange(1, 120000)
            words = []
            for i in range(rng.randrange(0, 20)):
                left = rng.randrange(duration)
                words.append(event_word(left, rng.randrange(left + 1, duration + 1), i % 3, i % 4))
            self.assertEqual(build_events(words, duration), oracle_events(words, duration))


class ApplyTests(unittest.TestCase):
    def load_pipeline(self, name):
        fixture = json.loads(Path(__file__).with_name(name).read_text())
        normalized = normalize_words(fixture['rows'], fixture['unit'])
        retimed = retime_words(normalized, fixture['cuts'])
        highlights = build_events(retimed['words'], retimed['duration_us'])
        return fixture, normalized, retimed, highlights

    def test_changed_edit_against_separate_oracles(self):
        fixture, n, r, h = self.load_pipeline('CHANGED-EDIT.json')
        self.assertEqual(r, oracle_retime(n, fixture['cuts']))
        self.assertEqual(h, oracle_events(r['words'], r['duration_us']))
        self.assertEqual((len(n), len(r['words']), r['duration_us'], len(h['events'])), (7, 13, 143333, 9))
        self.assertEqual(h['unrepresented_indices'], [3, 4, 8, 10])

    def test_saved_output_roundtrip_schema_and_coverage(self):
        saved = json.loads(Path(__file__).with_name('OUTPUT.json').read_text())
        fixture, n, r, h = self.load_pipeline('CHANGED-EDIT.json')
        self.assertEqual(set(saved), {'normalized', 'retimed', 'highlights'})
        self.assertEqual(saved, dict(normalized=n, retimed=r, highlights=h))
        self.assertEqual(saved['retimed'], oracle_retime(n, fixture['cuts']))
        self.assertEqual(saved['highlights'], oracle_events(r['words'], r['duration_us']))
        previous_end, previous_active = 0, object()
        for e in saved['highlights']['events']:
            self.assertEqual(set(e), {'start_cs', 'end_cs', 'active_index'})
            self.assertEqual(e['start_cs'], previous_end)
            self.assertLess(e['start_cs'], e['end_cs'])
            self.assertNotEqual(e['active_index'], previous_active)
            previous_end, previous_active = e['end_cs'], e['active_index']
        self.assertEqual(previous_end, (r['duration_us']+9999)//10000)

    def test_saved_audit_loss_classification(self):
        audit = json.loads(Path(__file__).with_name('TIMING_AUDIT.json').read_text())
        self.assertEqual(audit['nonempty_source_intersections'], 13)
        self.assertEqual(audit['rounded_collapsed_occurrences'], [])
        self.assertEqual([(o['input_index'], o['status']) for o in audit['occurrences'] if o['status'] != 'represented'],
                         [(3, 'overlap_arbitration'), (4, 'no_sample_in_interval'),
                          (8, 'no_sample_in_interval'), (10, 'overlap_arbitration')])
        self.assertEqual([c['end_exact_us'] for c in audit['cut_boundaries']],
                         ['80000/3', '170000/3', '250000/3', '430000/3'])
        self.assertEqual(audit['ticks'][-1]['sample_us'], 143332)
        self.assertEqual(audit['grid_overhang_us'], 6667)

    def test_changed_edit_occurrence_trace(self):
        fixture, n, r, h = self.load_pipeline('CHANGED-EDIT.json')
        self.assertEqual([w['source_index'] for w in n], [1, 5, 3, 2, 6, 0, 4])
        self.assertEqual([(w['source_index'], w['cut_index']) for w in r['words']],
                         [(0, 0), (4, 0), (1, 1), (5, 1), (3, 1), (2, 1), (6, 1),
                          (0, 2), (4, 2), (1, 3), (5, 3), (2, 3), (6, 3)])
        for w in r['words']:
            self.assertEqual(w['text'], fixture['rows'][w['source_index']]['text'])
        self.assertEqual((r['words'][4]['start_us'], r['words'][4]['end_us']), (27167, 27169))

    def test_changed_edit_same_tail_different_sampling_phase(self):
        _, _, r, h = self.load_pipeline('CHANGED-EDIT.json')
        choices = [e['active_index'] for e in h['events']]
        self.assertIn(1, choices)
        self.assertNotIn(8, choices)
        self.assertEqual((r['words'][1]['start_us'], r['words'][1]['end_us']), (20000, 26667))
        self.assertEqual((r['words'][8]['start_us'], r['words'][8]['end_us']), (76667, 83333))

    def test_changed_edit_clipping_creates_tie_and_resume(self):
        _, _, r, h = self.load_pipeline('CHANGED-EDIT.json')
        self.assertEqual([w['start_us'] for w in r['words'][9:12]], [83333] * 3)
        self.assertEqual([(e['start_cs'], e['end_cs'], e['active_index']) for e in h['events'][-3:]],
                         [(8, 9, 9), (9, 13, 11), (13, 15, 12)])
        self.assertEqual(h['events'][-1]['end_cs'] * 10000 - r['duration_us'], 6667)

    def test_example_fixture(self):
        fixture, n, r, h = self.load_pipeline('EXAMPLE.json')
        self.assertEqual(r, oracle_retime(n, fixture['cuts']))
        self.assertEqual(h, oracle_events(r['words'], r['duration_us']))
        self.assertEqual((r['duration_us'], len(r['words']), len(h['events'])), (639167, 6, 7))
        self.assertEqual(h['unrepresented_indices'], [4])

    def test_stage_rounding_cannot_be_fused(self):
        n = normalize_words([raw('9999.5', '10000.5')], 'microseconds')
        r = retime_words(n, [cut(0, 20000, 2)])
        self.assertEqual((r['words'][0]['start_us'], r['words'][0]['end_us']), (5000, 5001))
        self.assertEqual(build_events(r['words'], r['duration_us'])['unrepresented_indices'], [])

    def test_nonmutation_success_failure_and_fresh_results(self):
        fixture = json.loads(Path(__file__).with_name('CHANGED-EDIT.json').read_text())
        original = copy.deepcopy(fixture)
        n = normalize_words(fixture['rows'], fixture['unit'])
        n_before = copy.deepcopy(n)
        r = retime_words(n, fixture['cuts'])
        r_before = copy.deepcopy(r)
        build_events(r['words'], r['duration_us'])
        self.assertEqual(fixture, original)
        self.assertEqual(n, n_before)
        self.assertEqual(r, r_before)
        r['words'][0]['text'] = 'changed'
        self.assertEqual(n, n_before)
        for function, args in [(normalize_words, ([raw(), raw(text='\n')],)),
                               (retime_words, ([word()], [cut(), cut(num=0)])),
                               (build_events, ([event_word(), event_word(0, 2)], 1))]:
            before = copy.deepcopy(args)
            with self.assertRaises(ValueError):
                function(*args)
            self.assertEqual(args, before)

    def test_study_bound_occurrences_and_duration(self):
        words = [word(0, 4999999, i) for i in range(80)]
        r = retime_words(words, [cut(0, 4999999)] * 12)
        self.assertEqual((len(r['words']), r['duration_us']), (960, 59999988))
        h = build_events(r['words'], r['duration_us'])
        self.assertEqual(len(h['unrepresented_indices']), 948)
        self.assertEqual(h['events'][-1]['end_cs'], 6000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
