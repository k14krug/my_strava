"""Candidate methodology checks, explicitly outside production selection."""
from datetime import datetime,timezone
from unittest import TestCase
from tools.evaluate_training_state_session_power import estimate,reference_np,synthetic_cases


class SessionPowerEvaluationTests(TestCase):
    def test_constant_reference_and_session_formula_no_generated_samples(self):
        result=estimate(list(range(3600)),[200]*3600,duration=3600,elapsed_duration=3600,ftp=200)
        self.assertEqual(reference_np(list(range(3600)),[200]*3600),200)
        self.assertEqual(result['stress'],100);self.assertEqual(result['samples_invented'],0)
        self.assertFalse(result['whole_session_verified']);self.assertEqual(result['status'],'diagnostic_estimate')

    def test_batch_time_emission_is_not_rolling_np_or_interpolation(self):
        t=list(range(1200));p=[100+(i*13)%251 for i in t]
        gap_times=t[:615]+[x+133 for x in t[615:]]
        a=reference_np(t,p);b=reference_np(gap_times,p)
        self.assertNotEqual(a,b)
        r=estimate(gap_times,p,duration=1200,elapsed_duration=1333,ftp=200)
        self.assertEqual(r['samples_invented'],0);self.assertTrue(r['limitations'])

    def test_missing_invalid_and_conflicting_durations_excluded(self):
        kwargs=dict(duration=1200,elapsed_duration=1200,ftp=200)
        for times,powers,changes in [(list(range(1200)),[None]*1200,{}),
            ([0,1,1],[200]*3,{}),(list(range(1200)),[200]*1200,dict(duration=1202)),
            (list(range(1200)),[200]*1200,dict(ftp=None))]:
            self.assertIsNone(estimate(times,powers,**(kwargs|changes))['stress'])
        powers=[200]*1200;powers[600]=None
        result=estimate(list(range(1200)),powers,**kwargs)
        self.assertEqual(result['missing_watt_samples_excluded'],1)
        self.assertAlmostEqual(result['stress'],100/3)
        self.assertEqual(result['samples_invented'],0)

    def test_sparse_cannot_claim_representative_seconds_from_high_fraction(self):
        rows={r['case']:r for r in synthetic_cases()}
        self.assertIsNone(rows['uniform_sparse']['estimate']['stress'])
        self.assertIsNone(rows['clustered_sparse']['estimate']['stress'])
        self.assertEqual(rows['missing_hard']['observed_fraction'],rows['missing_recovery']['observed_fraction'])
        self.assertNotEqual(rows['missing_hard']['relative_error_against_complete'],rows['missing_recovery']['relative_error_against_complete'])
        self.assertTrue(rows['high_density_missing_hard']['known_missing_hard_interval'])
        self.assertIn('proposed_selection_exception',rows['high_density_missing_hard'])

    def test_verified_pause_excluded_and_timer_conflict_rejected(self):
        r=next(r for r in synthetic_cases() if r['case']=='verified_pause_with_nonzero_samples')['estimate']
        self.assertEqual(r['known_pause_samples_excluded'],60);self.assertEqual(r['timer_intervals'],2)
        self.assertNotEqual(r['literal_reference_stress'],r['stress'])
        stamp=lambda t:datetime.fromtimestamp(t,timezone.utc).isoformat()
        events=[dict(event='timer',event_type='start',timestamp=stamp(0))]
        r=estimate(list(range(1200)),[200]*1200,duration=1200,elapsed_duration=1200,ftp=200,events=events)
        self.assertEqual(r['reason'],'contradictory_or_unresolved_timer')
