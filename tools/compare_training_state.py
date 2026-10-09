#!/usr/bin/env python3
"""P4-01: synthetic same-input model comparisons + anonymized real context periods.

Requires the completed private census. Makes no athlete FTP/HR inference.
Optional plotting uses a disposable matplotlib installation, not a product dependency.
"""
import argparse
from collections import Counter, defaultdict
from datetime import date, timedelta
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.research_training_state import curves, dump, power_stress


def synthetic_comparisons():
    patterns = {
        'steady': [50] * 126,
        'same_weekly_total_concentrated': [0, 0, 0, 0, 0, 175, 175] * 18,
        'build_then_rest': [25] * 42 + [75] * 42 + [0] * 42,
        'one_unknown_day': [50] * 63 + [None] + [50] * 62,
    }
    traces = {key: curves(loads, seed=0) for key, loads in patterns.items()}
    values = [200] * 3600
    stress = {str(ftp): power_stress(values, ftp) for ftp in (180, 200, 220)}
    summary = dict(origin='synthetic_not_rider_estimates', seed='explicit_zero_before_day_1',
        method='TSS-style input; 1/tau industry EWMA; complete 7/42-day means',
        ftp_sensitivity_same_200w_hour=stress,
        patterns={k: {str(i + 1): rows[i] for i in (41, 62, 63, 69, 83, 90, 104, 105, 125)} for k, rows in traces.items()})
    return traces, summary


def daily_context(rows, as_of):
    cycling = [r for r in rows if r['kind'] in ('Ride', 'Virtual Ride') and r['day'] and date.fromisoformat(r['day']) <= as_of]
    by_day = defaultdict(list)
    for row in cycling:
        by_day[date.fromisoformat(row['day'])].append(row)
    start = min(by_day)
    daily = []
    for offset in range((as_of - start).days + 1):
        day = start + timedelta(days=offset); group = by_day[day]
        known = [r for r in group if r['duration'] is not None]
        power_work = [r for r in group if r['recorded_power_work_kj'] is not None]
        daily.append(dict(day=day.isoformat(), rides=len(group),
            known_elapsed_hours=math.fsum(r['duration'] for r in known) / 3600,
            recorded_power_work_kj=math.fsum(r['recorded_power_work_kj'] for r in power_work),
            work_contributors=len(power_work), work_unavailable=len(group) - len(power_work),
            missing_duration=len(group) - len(known),
            excluded_power=sum(not r['eligible'] for r in group),
            missing_ftp=sum(r['eligible'] and r['ftp'] is None for r in group),
            daily_stress=sum(r['stress'] for r in group) if group and all(r['stress'] is not None for r in group) else None,
            unknown_timezone=sum(not r['absolute_date'] for r in group),
            best20=max((r['best20'] for r in group if r['eligible']), default=None),
            recording_status='no_recorded_cycling' if not group else 'recorded_cycling'))
    # These are observed-history volume subtotals, never complete physiological load.
    for index, item in enumerate(daily):
        for n in (7, 42):
            window = daily[max(0, index + 1 - n):index + 1]
            item[f'known_hours{n}'] = math.fsum(d['known_elapsed_hours'] for d in window)
            item[f'known_work_kj{n}'] = math.fsum(d['recorded_power_work_kj'] for d in window)
            item[f'work_unavailable{n}'] = sum(d['work_unavailable'] for d in window)
            item[f'missing_duration{n}'] = sum(d['missing_duration'] for d in window)
            item[f'rides{n}'] = sum(d['rides'] for d in window)
            item[f'no_record_days{n}'] = sum(d['rides'] == 0 for d in window)
            item[f'full_window{n}'] = len(window) == n
    return daily


def compare_periods(daily):
    # Predetermined descriptive selectors; no performance parameter fitting.
    peak = max(range(len(daily)), key=lambda i: daily[i]['best20'] or -1)
    volume = max(range(41, len(daily)), key=lambda i: daily[i]['known_hours42'])
    ends = [('A — latest 42 days', len(daily) - 1),
            ('B — around highest observed best-20', min(peak + 7, len(daily) - 1)),
            ('C — highest known 42-day elapsed duration', volume)]
    periods = []
    for label, end in ends:
        group = daily[max(0, end - 41):end + 1]
        best = [r['best20'] for r in group if r['best20'] is not None]
        period = dict(label=label, selection='descriptive; not an independent validation sample',
            days=len(group), rides=sum(r['rides'] for r in group),
            known_elapsed_hours=sum(r['known_elapsed_hours'] for r in group),
            recorded_power_work_kj=sum(r['recorded_power_work_kj'] for r in group),
            work_contributors=sum(r['work_contributors'] for r in group),
            work_unavailable=sum(r['work_unavailable'] for r in group),
            rides_missing_duration=sum(r['missing_duration'] for r in group),
            recorded_rides_without_eligible_power=sum(r['excluded_power'] for r in group),
            eligible_rides_missing_ftp=sum(r['missing_ftp'] for r in group),
            days_without_recorded_cycling=sum(not r['rides'] for r in group),
            best20_days=len(best), best20_min=min(best) if best else None,
            best20_max=max(best) if best else None,
            week_subtotals_hours=[math.fsum(r['known_elapsed_hours'] for r in group[i:i+7]) for i in range(0, len(group), 7)],
            # No real dates, source IDs or titles in this anonymized series.
            series=[{k: v for k, v in r.items() if k != 'day'} | {'relative_day': i + 1} for i, r in enumerate(group)])
        periods.append(period)
    return periods


def plots(traces, periods, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(4, 1, figsize=(11, 11), sharex=True, constrained_layout=True)
    labels = [('ctl', '42-day EWMA'), ('atl', '7-day EWMA'), ('mean42', '42-day rolling mean'), ('mean7', '7-day rolling mean')]
    for ax, (name, rows) in zip(axes, traces.items()):
        x = list(range(1, len(rows) + 1))
        ax.bar(x, [r['load'] if r['load'] is not None else math.nan for r in rows], color='#ddd', label='Synthetic input')
        for key, label in labels:
            ax.plot(x, [r[key] if r[key] is not None else math.nan for r in rows], label=label, linewidth=1.6, linestyle='--' if 'mean' in key else '-')
        for i, r in enumerate(rows, 1):
            if r['load'] is None:
                ax.axvline(i, color='#a83232', linestyle=':', label='Unknown input; not rest')
        ax.set_title(name.replace('_', ' '), loc='left'); ax.set_ylabel('Input units/day')
    axes[0].legend(ncol=3, fontsize=8); axes[-1].set_xlabel('Synthetic day (explicit zero initial state)')
    fig.suptitle('Same daily input, different summaries — synthetic examples only')
    fig.savefig(output / 'synthetic-model-comparison.png', dpi=150); plt.close(fig)
    fig, axes = plt.subplots(3, 2, figsize=(12, 10), constrained_layout=True)
    for pair, period in zip(axes, periods):
        series = period['series']; x = [r['relative_day'] for r in series]
        left, right = pair
        left.bar(x, [r['known_elapsed_hours'] for r in series], color='#6a8495', label='Known elapsed hours')
        left.plot(x, [r['known_hours7'] / 7 for r in series], color='#163b55', label='7-day subtotal / 7')
        left.plot(x, [r['known_hours42'] / 42 for r in series], color='#ad7422', label='42-day subtotal / 42')
        missing = [r for r in series if r['missing_duration']]
        left.scatter([r['relative_day'] for r in missing], [0] * len(missing), marker='x', color='#a83232', label='Ride duration missing')
        left.set_title(period['label'], loc='left', fontsize=10); left.set_ylabel('Elapsed hours (not intensity)')
        points = [r for r in series if r['best20'] is not None]
        right.scatter([r['relative_day'] for r in points], [r['best20'] for r in points], color='#163b55', s=18)
        right.set_ylabel('Eligible best-20 (W)'); right.set_title('Separate Performance outcome; no fitted model', fontsize=10)
        for ax in pair:
            ax.set_xlim(.5, 42.5); ax.set_xlabel('Relative day (identities and dates omitted)')
    axes[0, 0].legend(fontsize=7)
    fig.suptitle('Recorded-history context — missing load is not zero; no recorded ride is not proven rest', fontsize=11)
    fig.savefig(output / 'anonymized-context-periods.png', dpi=150); plt.close(fig)
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), constrained_layout=True)
    for ax, period in zip(axes, periods):
        series = period['series']; x = [r['relative_day'] for r in series]
        ax.bar(x, [r['recorded_power_work_kj'] for r in series], color='#cad4db', label='Recorded eligible work subtotal')
        ax.plot(x, [r['known_work_kj7'] / 7 for r in series], label='7-day subtotal / 7', color='#163b55')
        ax.plot(x, [r['known_work_kj42'] / 42 for r in series], label='42-day subtotal / 42', color='#ad7422')
        missing = [r for r in series if r['work_unavailable']]
        ax.scatter([r['relative_day'] for r in missing], [0] * len(missing), color='#a83232', marker='x', label='Recorded ride has unavailable/excluded work')
        ax.set_title(period['label'], loc='left'); ax.set_ylabel('kJ (not stress points)'); ax.set_xlabel('Relative day')
    axes[0].legend(fontsize=8)
    fig.suptitle('Eligible recorded power work — partial subtotals, not whole-history training load')
    fig.savefig(output / 'anonymized-work-periods.png', dpi=150); plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--as-of', type=date.fromisoformat, required=True)
    parser.add_argument('--plots', action='store_true')
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = json.loads((args.input_dir / 'activities.json').read_text())
    raw = json.loads((args.input_dir / 'raw-inventory.json').read_text())
    # This task's observed state must be explicitly reviewed before assigning FTP.
    # This script does not accept a convenient current FTP or infer one from power.
    # Source-session candidates are already explicitly resolved by the census.
    # None is carried across a date or borrowed from a different sport.
    daily = daily_context(rows, args.as_of)
    traces, synthetic = synthetic_comparisons(); periods = compare_periods(daily)
    dump(args.output_dir / 'daily-private.json', daily)
    dump(args.output_dir / 'synthetic.json', synthetic)
    dump(args.output_dir / 'periods.json', periods)
    summary = dict(calendar_days=len(daily), recorded_cycling_days=sum(r['rides'] > 0 for r in daily),
        days_without_recorded_cycling=sum(r['rides'] == 0 for r in daily),
        cycling_days_missing_ftp=sum(r['missing_ftp'] > 0 for r in daily),
        cycling_days_with_excluded_power=sum(r['excluded_power'] > 0 for r in daily),
        source_session_threshold_stress_candidates=sum(r['stress'] is not None for r in rows),
        owner_verified_historical_ftp_intervals=0, actual_hr_reference_normalized_activity_loads=0,
        isolated_candidates=[dict(year=r['year'], ftp=r['ftp'], normalized_power=r['normalized_power'],
            stress=r['stress'], sample_seconds=r['power_samples'], scope=r['ftp_scope'],
            status=r['stress_status']) for r in rows if r['stress'] is not None],
        actual_ctl_atl_tsb='unavailable: historical load inputs and initial state not established',
        latest42={k:v for k,v in periods[0].items() if k != 'series'})
    dump(args.output_dir / 'comparison.json', summary)
    if args.plots:
        plots(traces, periods, args.output_dir)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
