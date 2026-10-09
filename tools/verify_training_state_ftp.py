#!/usr/bin/env python3
"""Independent direct-SQL / integer-window / Decimal P4-01 continuation oracle.

Does not import the FTP lookup, segmentation, NP, timer or daily research methods.
Run on PRIVATE outputs; optional --live-dir verifies all table fingerprints.
"""
import argparse
from collections import Counter
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
import hashlib
from itertools import groupby
import json
from pathlib import Path
import sqlite3
import sys
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.verify_rideworks_dashboard import source_rows
from tools.verify_training_state import fingerprint

KEYS = ('segment_work_kj','matched_work_kj','stress600','stress30','floor_stress','full_timer_stress')


def close(a,b,tolerance='1e-7'):
    if a is None or b is None:
        assert a is b, (a,b)
    else:
        assert abs(Decimal(str(a))-Decimal(str(b)))<Decimal(tolerance),(a,b)


def stamp(value):
    if not value:return None
    d=datetime.fromisoformat(value)
    return d.timestamp() if d.tzinfo else None


def partition(times, powers, intervals=None):
    counts=Counter(times)
    known=[t for t in times if t is not None]
    if any(b<a for a,b in zip(known,known[1:])):return []
    selected=[]
    for i,(t,p) in enumerate(zip(times,powers)):
        if t is None or counts[t]!=1 or type(p) is not int or p<0:continue
        region=0 if intervals is None else next((j for j,(a,b) in enumerate(intervals) if a<=t<t+1<=b),None)
        if region is not None:selected.append((i,t,region))
    # Both native row sequence and time must advance together. Filtering a bad
    # sample cannot reconnect the surrounding good values into a new NP window.
    return [[r[1][0] for r in group] for _,group in groupby(enumerate(selected),
        key=lambda r:(r[1][0]-r[0],r[1][1]-r[0],r[1][2]))]


def stats(parts,powers,ftp,minimum):
    detail=[]
    for part in parts:
        if len(part)<minimum:continue
        values=[powers[i] for i in part]
        fourth=Decimal(sum(sum(values[j:j+30])**4 for j in range(len(values)-29))) / Decimal(30**4*(len(values)-29))
        np=fourth.sqrt().sqrt()
        stress=Decimal(len(values))/36*(np/ftp)**2 if ftp else None
        detail.append(dict(first_index=part[0],last_index=part[-1],seconds=len(part),np=np,
            work_kj=Decimal(sum(values))/1000,stress=stress))
    seconds=sum(x['seconds'] for x in detail)
    windows=sum(x['seconds']-29 for x in detail)
    pooled=(sum((x['np']**4*(x['seconds']-29) for x in detail),Decimal(0))/windows).sqrt().sqrt() if windows else None
    return dict(seconds=seconds,pooled_np=pooled,pooled_stress=Decimal(seconds)/36*(pooled/ftp)**2 if pooled is not None and ftp else None,work_kj=sum((x['work_kj'] for x in detail),Decimal(0)),
        stress=sum((x['stress'] for x in detail),Decimal(0)) if detail and ftp else None,details=detail)


def verify(args):
    db=sqlite3.connect((args.data_dir.resolve()/'rideworks.sqlite3').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    before=hashlib.sha256((args.data_dir/'rideworks.sqlite3').read_bytes()).hexdigest()
    rows=json.loads((args.input_dir/'activities-private.json').read_text())
    days=json.loads((args.input_dir/'daily-private.json').read_text())
    summary=json.loads((args.input_dir/'summary.json').read_text())
    with args.ftp.open() as source:
        history=list(csv.DictReader(source))
    assert len(history)==66
    for i,h in enumerate(history):
        assert int(h['ftp_watts'])>0
        assert h['effective_until_date_exclusive']==(history[i+1]['effective_from_date'] if i<65 else '')
        if i:assert history[i-1]['effective_from_date']<h['effective_from_date']
    assert summary['ftp']['sha256']==hashlib.sha256(args.ftp.read_bytes()).hexdigest()
    independent={r['activity_id']:r for r in source_rows(db)}
    saved={i:json.loads(p) for i,p in db.execute("SELECT activity_id,result_json FROM performance_history WHERE policy='virtual-power-evidence-v2'")}
    checked=Counter();segment_count=0
    for r in rows:
        src=independent[r['activity_id']];dt=src['stamp']
        day=str(dt.astimezone(ZoneInfo('America/Los_Angeles')).date() if dt.tzinfo else dt.date()) if dt else None
        assert r['day']==day and r['kind']==src['kind']
        found=[h for h in history if day and h['effective_from_date']<=day and (not h['effective_until_date_exclusive'] or day<h['effective_until_date_exclusive'])]
        assert len(found)<=1
        h=found[0] if found else None
        assert r['dated_ftp']==(dict(start=h['effective_from_date'],end=h['effective_until_date_exclusive'] or None,watts=int(h['ftp_watts'])) if h else None)
        uncertain=False
        if dt and not dt.tzinfo:
            for delta in (-1,1):
                other=str(date.fromisoformat(day)+timedelta(days=delta))
                adjacent=[x for x in history if x['effective_from_date']<=other and (not x['effective_until_date_exclusive'] or other<x['effective_until_date_exclusive'])]
                uncertain |= adjacent!=found
        assert uncertain==r['ftp_date_uncertain']
        ftp=Decimal(h['ftp_watts']) if h and not uncertain else None
        p=saved[r['activity_id']];assert p['eligible']==r['eligible']
        if not p['eligible']:
            assert all(r[k] is None for k in KEYS)
            continue
        assert r['kind']=='Virtual Ride'
        if p.get('extraction_id'):
            data=list(db.execute('SELECT timestamp,power FROM records WHERE extraction_id=? ORDER BY record_index',(p['extraction_id'],)))
            times=[stamp(x[0]) for x in data];powers=[x[1] for x in data]
            events=[dict(e) for e in db.execute("SELECT * FROM events WHERE extraction_id=? AND event='timer' ORDER BY source_order",(p['extraction_id'],))]
            session=dict(db.execute('SELECT * FROM sessions WHERE extraction_id=?',(p['extraction_id'],)).fetchone())
        else:
            data=json.loads(db.execute('SELECT evidence_json FROM strava_stream_sources WHERE source_id=?',(p['api_evidence']['stream_source_id'],)).fetchone()[0])
            times=data['time']['data'];powers=data['watts']['data'];events=[];session={}
        parts=partition(times,powers)
        close(r['segment_work_kj'],Decimal(sum(powers[i] for part in parts for i in part))/1000 if parts else None)
        assert r['observed_seconds']==sum(map(len,parts))
        stats_by_min={}
        for minimum in (30,600):
            expected=stats(parts,powers,ftp,minimum);stats_by_min[minimum]=expected;actual=r[f'segment{minimum}']
            assert actual['seconds']==expected['seconds'] and len(actual['details'])==len(expected['details'])
            for a,b in zip(actual['details'],expected['details']):
                for key in b:close(a[key],b[key])
                segment_count+=1
            close(actual['stress'],expected['stress']);close(r[f'stress{minimum}'],expected['stress'])
            close(actual['work_kj'],expected['work_kj'])
            close(actual['pooled_np'],expected['pooled_np']);close(actual['pooled_stress'],expected['pooled_stress'])
        close(r['matched_work_kj'],stats_by_min[600]['work_kj'] if stats_by_min[600]['stress'] is not None else None)
        complete=len(parts)==1 and len(parts[0])==len(powers) and len(powers)>=30
        close(r['floor_stress'],stats_by_min[30]['stress'] if complete else None)
        # This retained corpus has strictly alternating start/stop pairs. Fail on
        # new event shapes rather than silently adopting research parser behavior.
        intervals=[]; invalid_pair=False
        assert len(events)%2==0
        for a,b in zip(events[::2],events[1::2]):
            assert a['event_type']=='start' and b['event_type'] in ('stop','stop_all')
            intervals.append((stamp(a['timestamp']),stamp(b['timestamp'])))
            invalid_pair |= intervals[-1][1]<=intervals[-1][0]
        assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:]))
        if invalid_pair:
            assert r['timer']['error']=='unpaired_or_unsupported_timer_event'
            intervals=[]
        assert r['timer']['intervals']==([list(x) for x in intervals] if intervals else None)
        tparts=partition(times,powers,intervals)
        expected=stats(tparts,powers,ftp,600)
        for field in ('stress','seconds','work_kj','pooled_np','pooled_stress'):
            close(r['timer']['metrics'][field],expected[field])
        active=sum(b-a for a,b in intervals) if intervals else None
        cover=sum(map(len,tparts));assert r['timer']['covered_active_seconds']==cover
        boundary=bool(intervals and stamp(session['start_time'])==intervals[0][0]
            and stamp(session['timestamp']) is not None and intervals[-1][1]<=stamp(session['timestamp'])
            and session['total_elapsed_time'] is not None and intervals[-1][1]<=intervals[0][0]+session['total_elapsed_time'])
        assert boundary==r['timer']['boundary_verified']
        for tolerance,key in [(0,'full_timer_stress'),(1,'full_timer_tolerance1_stress')]:
            qualify=bool(boundary and active==cover==expected['seconds'] and session.get('total_timer_time') is not None and abs(active-session['total_timer_time'])<=tolerance)
            close(r[key],expected['stress'] if qualify else None)
        checked['eligible']+=1
        checked['dated_stress']+=r['stress600'] is not None
        checked['exact_timer_stress']+=r['full_timer_stress'] is not None
    # Every daily value is rebuilt from private per-activity contributions; every
    # rolling value uses direct date predicates (not research slice boundaries).
    for i,d in enumerate(days):
        group=[r for r in rows if r['day']==d['day'] and r['kind'] in ('Ride','Virtual Ride')]
        assert d['rides']==len(group) and d['no_record']==(not group)
        for key in KEYS:
            values=[Decimal(str(r[key])) for r in group if r[key] is not None]
            close(d[key],sum(values) if values else None)
            assert d[key+'_contributors']==len(values) and d[key+'_missing']==len(group)-len(values)
        for n in (7,42):
            start=str(date.fromisoformat(d['day'])-timedelta(days=n-1))
            window=[r for r in rows if r['day'] and start<=r['day']<=d['day'] and r['kind'] in ('Ride','Virtual Ride')]
            assert d[f'window{n}']['rides']==len(window)
            for key in KEYS:
                values=[Decimal(str(r[key])) for r in window if r[key] is not None]
                actual=d[f'window{n}'][key]
                close(actual['subtotal'],sum(values) if values else None,'1e-6')
                assert actual['contributors']==len(values) and actual['missing']==len(window)-len(values)
                checked['rolling_comparisons']+=1
        assert d['industry_unknown_seed']['ctl'] is None and d['industry_unknown_seed']['atl'] is None and d['industry_unknown_seed']['tsb'] is None
    def check_coverage(actual, candidates):
        cycling=[r for r in candidates if r['kind'] in ('Ride','Virtual Ride')]
        groups=dict(cycling=cycling,virtual=[r for r in cycling if r['kind']=='Virtual Ride'],
            outdoor=[r for r in cycling if r['kind']=='Ride'],eligible=[r for r in cycling if r['eligible']],
            complete_envelope=[r for r in cycling if r['eligible'] and r['whole_power_reason'] is None],
            incomplete_envelope=[r for r in cycling if r['eligible'] and r['whole_power_reason'] is not None])
        for name, group in groups.items():
            got=actual[name]
            assert got['denominator']==len(group)
            assert got['dated_ftp']==sum(r['dated_ftp'] is not None for r in group)
            assert got['no_dated_ftp']==sum(r['dated_ftp'] is None for r in group)
            assert got['uncertain_ftp_date']==sum(r['ftp_date_uncertain'] for r in group)
            for key in KEYS:assert got[key]==sum(r[key] is not None for r in group)
            assert got['full_timer_tolerance1']==sum(r['full_timer_tolerance1_stress'] is not None for r in group)
    check_coverage(summary['coverage'],rows)
    for year, coverage in summary['by_year'].items():check_coverage(coverage,[r for r in rows if r['year']==year])
    for n in (7,42):
        start=str(date.fromisoformat(summary['as_of'])-timedelta(days=n-1))
        check_coverage(summary['latest'][str(n)]['coverage'],[r for r in rows if r['day'] and start<=r['day']<=summary['as_of']])
        assert summary['latest'][str(n)]['window']==days[-1][f'window{n}']
    periods=json.loads((args.input_dir/'periods.json').read_text())
    for public, period in zip(summary['periods'],periods):
        assert public['window']==period['window']==period['series'][-1]['window42']
        assert public['label']==period['label']
    artifact_count=0
    for table in ('sources','export_snapshots'):
        for row in db.execute(f'SELECT * FROM {table}'):
            path=(args.data_dir/row['stored_path']).resolve()
            assert args.data_dir.resolve() in path.parents
            raw=path.read_bytes();assert len(raw)==row['byte_size'] and hashlib.sha256(raw).hexdigest()==row['sha256'];artifact_count+=1
    preserved=None
    if args.live_dir:
        live=sqlite3.connect((args.live_dir.resolve()/'rideworks.sqlite3').as_uri()+'?mode=ro',uri=True)
        preserved=fingerprint(db)==fingerprint(live);assert preserved;live.close()
    assert hashlib.sha256((args.data_dir/'rideworks.sqlite3').read_bytes()).hexdigest()==before
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not list(db.execute('PRAGMA foreign_key_check'))
    db.close()
    return dict(activities_verified=len(rows),ftp_intervals_verified=len(history),**checked,
        segment_metric_checks=segment_count,daily_rows_verified=len(days),verified_original_artifacts=artifact_count,
        live_tables_unchanged=preserved,snapshot_unchanged=True,integrity='ok',foreign_key_violations=0)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--input-dir',type=Path,required=True)
    p.add_argument('--ftp',type=Path,required=True);p.add_argument('--live-dir',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=verify(a);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
