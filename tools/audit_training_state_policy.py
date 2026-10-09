#!/usr/bin/env python3
"""P4-01 §16 aggregate audit of the Owner-selected screen; no load implementation.

Recompute gaps from private source arrays, cross-check the historical experiment,
and publish only aggregate coverage. Never assign corrected whole-session labels.
"""
import argparse
from collections import Counter
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path


def audit(root, ftp_root):
    cache = json.loads((root / 'sensors-private.json').read_text())
    source = ftp_root / 'activities-private.json'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == cache['sourcehash']
    rows = {r['activity_id']: r for r in json.loads(source.read_text())}
    cases = [c for c in json.loads((root / 'cases-private.json').read_text())
             if c['scope'] == 'actual_unknown']
    checked = []
    for c in cases:
        x = cache['items'][c['activity_id']]
        t, p = x['streams']['time'], x['streams']['watts']
        assert len(t) == len(p) and len(t) > 1
        assert all(math.isfinite(v) and v >= 0 for v in p)
        deltas = [b-a for a, b in zip(t, t[1:])]
        assert all(d > 0 and float(d).is_integer() for d in deltas)
        assert Counter(deltas).most_common(1)[0][0] == 1
        span = t[-1]-t[0]+1
        loss = sum(d-1 for d in deltas)
        maximum = max(d-1 for d in deltas)
        assert (span, loss, maximum) == (c['span'], c['missing_interior_seconds'], c['max_missing_gap'])
        assert x['source_kind'] == c['source_kind'] == rows[c['activity_id']]['power_source']
        assert x['excluded_native_rows'] == c['excluded_native_rows']
        assert len(x['pauseSpans']) == c['known_pause_count']
        base_ok = loss*100 <= span and not x['excluded_native_rows'] and not x['pauseSpans']
        screens = {n: base_ok and maximum <= n for n in (5, 15, 30)}
        fit = x['source_kind'] == 'FIT'
        selected = fit and screens[15] and c['whole_reason'] is not None
        # This is corroborating metadata only, not a corrected timer calculation.
        timer = rows[c['activity_id']]['timer']
        assert timer['boundary_verified'] == x['timer_boundary_verified']
        assert timer['delta'] == x['timer_delta']
        corroborated = bool(timer['boundary_verified'] and timer['delta'] == 0
                            and len(x['timer_intervals']) == 1
                            and t[0] == x['timer_intervals'][0][0]
                            and t[-1]+1 >= x['timer_intervals'][0][1])
        checked.append(dict(case=c, screens=screens, selected=selected,
                            corroborated=corroborated, missing=loss))
    interrupted = [x for x in checked if x['case']['gap_class'] == 'actual_interrupted']
    comparison = {}
    for n in (5, 15, 30):
        group = [x for x in interrupted if x['screens'][n]]
        comparison[str(n)] = dict(all_sources=len(group),
            source_classes=dict(Counter(x['case']['source_kind'] for x in group)),
            boundary_and_timer_screen=sum(x['corroborated'] for x in group))
    selected = [x for x in interrupted if x['selected']]
    recent = {}
    for n in (7, 42):
        start = str(date(2026, 10, 8)-timedelta(days=n-1))
        group = [x for x in checked if start <= x['case']['day'] <= '2026-10-08']
        cycling = [r for r in rows.values() if r['kind'] in ('Ride', 'Virtual Ride')
                   and r['day'] and start <= r['day'] <= '2026-10-08']
        classes = Counter('calculated_recorded_envelope' if x['case']['whole_reason'] is None
                          else 'fit_estimate_screen' if x['selected'] else 'partial_observed'
                          for x in group)
        recent[str(n)] = dict(recorded_cycling=len(cycling),contributors=len(group),
            classes=dict(classes),omitted_rides=len(cycling)-len(group),
            no_record_days=n-len({r['day'] for r in cycling}),
            known_interior_missing_seconds=sum(x['missing'] for x in group),
            fit_estimate_screen_missing_seconds=sum(x['missing'] for x in group if x['selected']),
            observed_seconds_omitted_by_historical_600s_comparator=sum(x['case']['observed']['omitted_short_seconds'] for x in group),
            omitted_whole_ride_or_boundary_time='unknown; not zero')
    return dict(method='p4-01-owner-policy-audit-v1',jit='36c72d0',
        actual_cases_checked=len(checked),interrupted_denominator=len(interrupted),
        comparison=comparison,selected_fit_intervals=len(selected),
        selected_boundary_and_timer_screen=sum(x['corroborated'] for x in selected),
        corrected_whole_session_calculations_verified=0,
        policy=dict(max_missing_seconds=15,max_missing_fraction=.01,source='FIT',
                    pause_rule='split validated timer intervals; reset NP; no pause filling',
                    api='observed-only; no gap correction'),
        recent=recent,scope='Coverage reconciliation only; historical Sauce outputs unchanged; no production calculation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,required=True)
    parser.add_argument('--ftp-results',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = audit(args.input_dir,args.ftp_results)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2))
