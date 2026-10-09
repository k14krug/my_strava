"""Independent analytical oracles for the disposable P4-01 research calculations."""
import math
import unittest
from datetime import date
from tools.research_training_state import contiguous_power, normalized_power, power_stress, curves
from tools.compare_training_state import daily_context


class ResearchTrainingStateTests(unittest.TestCase):
    def test_constant_threshold_hour_is_100(self):
        self.assertEqual(normalized_power([250] * 3600), 250)
        self.assertEqual(power_stress([250] * 3600, 250), 100)
        self.assertEqual(power_stress([125] * 3600, 250), 25)
        self.assertEqual(power_stress([0] * 3600, 250), 0)

    def test_variable_power_against_direct_enumeration(self):
        values = [0] * 600 + [300] * 600 + [100] * 600 + [450] * 600
        # Direct enumeration, independent of production rolling-sum recurrence.
        expected = (sum((sum(values[i:i + 30]) / 30) ** 4 for i in range(len(values) - 29)) / (len(values) - 29)) ** .25
        self.assertAlmostEqual(normalized_power(values), expected, places=10)
        self.assertGreater(normalized_power(values), sum(values) / len(values))

    def test_no_ftp_is_missing_and_ftp_sensitivity_is_quadratic(self):
        values = [200] * 3600
        self.assertIsNone(power_stress(values, None))
        self.assertAlmostEqual(power_stress(values, 220) / power_stress(values, 200), 1 / 1.1 ** 2)
        for value in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                power_stress(values, value)

    def test_complete_envelope_does_not_repair_gaps_or_missing(self):
        times, power = list(range(60)), [200] * 60
        self.assertIsNone(contiguous_power(times, power))
        self.assertIsNone(contiguous_power(times, [0] * 60))
        for changed in (times[:20] + [19] + times[21:], times[:20] + [None] + times[21:], [2 * t for t in times]):
            self.assertEqual(contiguous_power(changed, power), 'non_contiguous_timing')
        for changed in (power[:20] + [None] + power[21:], power[:20] + [-1] + power[21:]):
            self.assertEqual(contiguous_power(times, changed), 'missing_or_invalid_power')

    def test_impulse_and_step_against_closed_form(self):
        impulse = curves([100] + [0] * 99, seed=0)
        step = curves([50] * 100, seed=0)
        for i in range(100):
            self.assertAlmostEqual(impulse[i]['ctl'], 100 / 42 * (41 / 42) ** i)
            self.assertAlmostEqual(impulse[i]['atl'], 100 / 7 * (6 / 7) ** i)
            self.assertAlmostEqual(step[i]['ctl'], 50 * (1 - (41 / 42) ** (i + 1)))
            self.assertAlmostEqual(step[i]['atl'], 50 * (1 - (6 / 7) ** (i + 1)))
        self.assertEqual(impulse[0]['tsb'], 0)
        self.assertAlmostEqual(impulse[1]['tsb'], 100 / 42 - 100 / 7)
        self.assertAlmostEqual(impulse[6]['mean7'], 100 / 7)
        self.assertEqual(impulse[7]['mean7'], 0)
        self.assertAlmostEqual(impulse[41]['mean42'], 100 / 42)
        self.assertEqual(impulse[42]['mean42'], 0)

    def test_unknown_days_never_become_rest_or_decay(self):
        data = curves([50] * 42 + [None] + [0] * 42, seed=0)
        self.assertIsNone(data[42]['ctl'])
        self.assertIsNone(data[-1]['ctl'])
        self.assertIsNone(data[43]['tsb'])
        self.assertIsNone(data[48]['mean7'])
        self.assertEqual(data[49]['mean7'], 0)
        self.assertIsNone(data[-2]['mean42'])
        self.assertEqual(data[-1]['mean42'], 0)
        self.assertIsNone(curves([100] * 100)[-1]['ctl'])

    def test_outlier_is_visible_and_no_negative_load(self):
        data = curves([0] * 42 + [1000], seed=0)
        self.assertEqual(data[-1]['mean7'], 1000 / 7)
        self.assertGreater(data[-1]['atl'], data[-1]['ctl'])
        with self.assertRaises(ValueError):
            curves([-1], seed=0)

    def test_recorded_duration_subtotal_exposes_missing_and_no_record_days(self):
        base = dict(kind='Ride', eligible=False, ftp=None, absolute_date=True, best20=None,
                    recorded_power_work_kj=None, stress=None)
        rows = [base | dict(day='2026-01-01', duration=3600),
                base | dict(day='2026-01-01', duration=None),
                base | dict(day='2026-01-03', duration=0)]
        days = daily_context(rows, date(2026, 1, 3))
        self.assertEqual(days[0]['known_elapsed_hours'], 1)
        self.assertEqual(days[0]['missing_duration'], 1)
        self.assertEqual(days[1]['recording_status'], 'no_recorded_cycling')
        self.assertEqual(days[2]['recording_status'], 'recorded_cycling')
        self.assertEqual(days[2]['known_hours7'], 1)
        self.assertEqual(days[2]['missing_duration7'], 1)
        self.assertEqual(days[2]['known_work_kj7'], 0)
        self.assertEqual(days[2]['work_unavailable7'], 3)
        self.assertFalse(days[2]['full_window7'])


if __name__ == '__main__':
    unittest.main()
