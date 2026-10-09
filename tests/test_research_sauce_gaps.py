"""Synthetic experiment and independent oracle checks; no personal ride fixtures."""
from decimal import Decimal
import unittest
from tools.research_sauce_gaps import gap_cases,observed,subset
from tools.verify_sauce_gaps import oracle,observed_oracle


class SauceGapResearchTests(unittest.TestCase):
    def streams(self,n=1800):
        return dict(time=list(range(n)),watts=[200]*n,moving=[True]*n)

    def test_injections_are_deterministic_and_leave_source_unchanged(self):
        s=self.streams();before={k:v[:] for k,v in s.items()}
        first=list(gap_cases(s,123));second=list(gap_cases(s,123))
        self.assertEqual(first,second);self.assertEqual(s,before)
        for name,mask,meta in first:
            self.assertEqual(len(mask),len(set(mask)))
            self.assertTrue(all(0<=i<1800 for i in mask))
            cut=subset(s,[i for i in range(1800) if i not in set(mask)])
            self.assertEqual(len(cut['time']),1800-len(mask))

    def test_complete_constant_reference_and_sauce_endpoint_convention(self):
        s=self.streams();reference,seconds=observed_oracle(s,Decimal(200))
        self.assertEqual(reference,50);self.assertEqual(seconds,1800)
        exact=oracle(dict(streams=s,ftp=200),{})
        self.assertEqual(exact['np'],200);self.assertEqual(exact['active_seconds'],1799)
        self.assertAlmostEqual(float(exact['stress']),1799/36)

    def test_small_gap_estimation_versus_observed_only(self):
        s=self.streams();cut=subset(s,[i for i in range(1800) if i!=900])
        exact=oracle(dict(streams=cut,ftp=200),{})
        self.assertEqual(exact['counts']['valuePad'],1)
        self.assertAlmostEqual(float(exact['stress']),1799/36)
        partial=observed(cut,200)
        self.assertEqual(partial['seconds'],1799)
        self.assertAlmostEqual(partial['stress'],1799/36)

    def test_upstream_75_second_gap_boundary_is_not_accuracy_threshold(self):
        s=self.streams()
        for missing,pad,zero in [(73,73,0),(74,0,74)]:
            cut=subset(s,[i for i in range(1800) if not 700<=i<700+missing])
            result=oracle(dict(streams=cut,ftp=200),{})
            self.assertEqual(result['counts']['valuePad'],pad)
            self.assertEqual(result['counts']['zeroPad'],zero)

    def test_proven_pause_variant_excludes_padding_as_measured(self):
        s=self.streams();s['time']=[t+(60 if t>=900 else 0) for t in s['time']]
        request=dict(streams=s,ftp=200,pauseSpans=[[900,960]])
        heuristic=oracle(request,{})
        informed=oracle(request,dict(timerAware=True))
        self.assertEqual(heuristic['counts']['valuePad'],60)
        self.assertEqual(informed['counts']['zeroPad'],60)
        self.assertLess(informed['active_seconds'],heuristic['active_seconds'])

    def test_recorded_zero_survives_and_no_600_second_segment_is_unknown(self):
        s=self.streams();s['watts']=[0]*1800
        self.assertEqual(oracle(dict(streams=s,ftp=200),{})['stress'],0)
        self.assertEqual(observed(s,200)['stress'],0)
        self.assertIsNone(observed(self.streams(599),200)['stress'])

    def test_hard_interval_loss_cannot_be_recovered_from_identical_observations(self):
        low=self.streams();high=self.streams();high['watts'][800:805]=[1000]*5
        keep=[i for i in range(1800) if not 800<=i<805]
        self.assertEqual(subset(low,keep),subset(high,keep))
        high_reference=observed_oracle(high,Decimal(200))[0]
        self.assertGreater(high_reference,observed_oracle(low,Decimal(200))[0])
        estimate=oracle(dict(streams=subset(high,keep),ftp=200),{})['stress']
        self.assertAlmostEqual(float((estimate/high_reference-1)*100),-5.112649333939334)


if __name__=='__main__':unittest.main()
