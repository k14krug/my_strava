#!/usr/bin/env python3
"""Publish only whitelisted P4-01 aggregate evidence; private rows never copied."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir',type=Path,required=True)
    p.add_argument('--report-dir',type=Path,required=True)
    p.add_argument('--test-count',type=int,required=True,help='Count from completed full-suite log')
    a=p.parse_args()
    rows=json.loads((a.input_dir/'activities-private.json').read_text())
    summary=json.loads((a.input_dir/'summary.json').read_text())
    independent=json.loads((a.input_dir/'independent-verification.json').read_text())
    eligible=[r for r in rows if r['eligible']];dated=[r for r in eligible if r['stress600'] is not None]
    # Explicit output keys exclude activity IDs, dates, source IDs, FTP values,
    # private paths and per-segment source pointers in the detailed input.
    diagnostic=dict(eligible=len(eligible),
        timer_event_pair_counts=dict(Counter(len(r['timer']['intervals'] or []) for r in eligible)),
        timer_errors=dict(Counter(r['timer']['error'] or 'none' for r in eligible)),
        gap_seconds=sum(r['gap_seconds'] for r in eligible),
        invalid_power_samples=sum(r['invalid_power_samples'] for r in eligible),
        duplicate_timestamp_samples=sum(r['duplicate_timestamp_samples'] for r in eligible),
        missing_timestamp_samples=sum(r['missing_timestamp_samples'] for r in eligible),
        gapped_sample_count_equals_timer=sum(r['whole_power_reason']=='non_contiguous_timing' and r['summary_matches_samples'] for r in eligible),
        dated_observed_seconds=sum(r['observed_seconds'] for r in dated),
        dated_omitted_short_seconds600=sum(r['omitted_short_seconds600'] for r in dated),
        stress30=sum(r['stress30'] for r in dated),stress600=sum(r['stress600'] for r in dated),
        minimum_segment_sensitivity_affected_rides=sum(r['stress30']!=r['stress600'] for r in dated),
        pooled_to_segment_stress_ratio_range=[f(r['segment600']['pooled_stress']/r['stress600'] for r in dated if r['stress600']) for f in (min,max)],
        timezone_unknown_cycling=sum(r['kind'] in ('Ride','Virtual Ride') and not r['absolute_date'] for r in rows),
        timezone_unknown_eligible=sum(not r['absolute_date'] for r in eligible),
        cycling_on_ftp_change_date=sum(r['kind'] in ('Ride','Virtual Ride') and r['dated_ftp'] is not None and r['dated_ftp']['start']==r['day'] for r in rows),
        eligible_on_ftp_change_date=sum(r['dated_ftp'] is not None and r['dated_ftp']['start']==r['day'] for r in eligible))
    # Only structural FTP metadata and aggregates are in summary.json. Reassert
    # that its shape is the known publisher contract before copying it.
    expected={'version','as_of','ftp','coverage','by_year','latest','calendar_days','no_record_days','actual_ctl_atl_tsb','periods'}
    if set(summary)!=expected:raise ValueError('Review changed summary publication shape')
    if set(summary['ftp'])!={'rows','sha256','source','first','last','structurally_valid'}:raise ValueError('Unexpected FTP details')
    path=a.report_dir/'acceptance.json';old=json.loads(path.read_text())
    initial=old.get('initial_research',old)
    result=dict(task='P4-01',status='ready_for_owner_review_not_accepted',
        controlling_main='91842f7',jit='645cb48',phase4_contract='a74c97c',
        initial_research=initial,
        initial_scope='Retained evidence before Owner-supplied dated FTP; original findings preserved, recommendation superseded',
        continuation=dict(**summary,diagnostics=diagnostic,independent=independent,
            verification=dict(full_suite=a.test_count,focused_research_tests=18,owner_accepted=False,analyst_accepted=False),
            production_changes=False,external_activity_api_requests=0))
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    shutil.copyfile(a.input_dir/'anonymized-ftp-model-comparison.png',a.report_dir/'anonymized-ftp-model-comparison.png')
    lines=['# P4-01 revised FTP coverage','',
        'Dated FTP and partial recorded contributions; no full-history load claim. All counts',
        'use unchanged Performance-v2 selection. Reproduce with the continuation tools.',
        'See [DESIGN-003](../../docs/design/DESIGN-003-training-state-model.md) for timing rules.',
        '', '| Year | Cycling | Dated FTP | Eligible power | Eligible × FTP | Complete envelope × FTP | Incomplete envelope × FTP | Exact full-timer stress |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for year,group in summary['by_year'].items():
        lines.append(f"| {year} | {group['cycling']['denominator']} | {group['cycling']['dated_ftp']} | {group['eligible']['denominator']} | {group['eligible']['dated_ftp']} | {group['complete_envelope']['dated_ftp']} | {group['incomplete_envelope']['dated_ftp']} | {group['cycling']['full_timer_stress']} |")
    lines+=['','Each cell is a count, not a percentage. Year/type details and recent 7-/42-day',
        'denominators are in [acceptance.json](acceptance.json), `continuation.coverage`,',
        '`continuation.by_year` and `continuation.latest`. The original retained-source',
        'census is preserved under `initial_research` and [coverage.md](coverage.md).','']
    (a.report_dir/'ftp-coverage.md').write_text('\n'.join(lines))


if __name__=='__main__':main()
