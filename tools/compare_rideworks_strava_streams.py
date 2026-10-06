#!/usr/bin/env python3
"""Bounded STRAVA-004 Stage A comparison; no product stream writes or raw public data."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rideworks.config import strava_credentials
from rideworks.performance import performance_history
from rideworks.store import Store
from rideworks.strava import ApiClient, AuthenticationError, STREAM_KEYS, TokenFile, refreshed_connection
from rideworks.strava_api import SyncError
from rideworks.strava_streams import MAPPING, parse_streams


def instant(text):
    return datetime.fromisoformat(text.replace('Z','+00:00')).astimezone(timezone.utc)


def timing(values):
    deltas=Counter(b-a for a,b in zip(values,values[1:]))
    return dict(count=len(values),first=values[0] if values else None,last=values[-1] if values else None,
                duplicates=sum(n for d,n in deltas.items() if d==0),backwards=sum(n for d,n in deltas.items() if d<0),
                gap_count=sum(n for d,n in deltas.items() if d>1),
                delta_distribution={str(d):n for d,n in sorted(deltas.items())})


def independent_best(offsets,powers):
    """Segment valid exact-one-second runs; independently enumerate prefix-sum windows."""
    if len(offsets)!=len(powers):
        return None
    runs=[];run=[]
    for index,(offset,power) in enumerate(zip(offsets,powers)):
        if power is None or (run and offset-offsets[run[-1]]!=1):
            if run:runs.append(run)
            run=[]
        if power is not None:run.append(index)
    if run:runs.append(run)
    best=None;eligible=0
    for run in runs:
        prefix=[0]
        for index in run:prefix.append(prefix[-1]+powers[index])
        for position in range(len(run)-1199):
            total=prefix[position+1200]-prefix[position];eligible+=1
            if best is None or total>best['sum_watts']:
                index=run[position]
                mean=Decimal(total)/Decimal(1200)
                best=dict(sum_watts=total,average_watts=float(mean),
                          rounded_watts=int(mean.quantize(Decimal('1'),rounding=ROUND_HALF_UP)),
                          start_elapsed=offsets[index],end_exclusive_elapsed=offsets[index]+1200,
                          start_index=index,sample_count=1200)
    if best is not None:best['eligible_window_count']=eligible
    return best


def signal_comparison(api_times,api_values,fit_times,fit_values):
    """Unique exact absolute timestamps only; no nearest-neighbor or fitted shift."""
    api_counts=Counter(api_times);fit_counts=Counter(fit_times)
    fit={stamp:value for stamp,value in zip(fit_times,fit_values) if stamp is not None and fit_counts[stamp]==1}
    unique=[(index,stamp,value) for index,(stamp,value) in enumerate(zip(api_times,api_values))
            if api_counts[stamp]==1 and stamp in fit]
    pairs=[(index,stamp,fit[stamp],value) for index,stamp,value in unique]
    both=[p for p in pairs if p[2] is not None and p[3] is not None]
    exact=sum(f==a for _,_,f,a in both)
    differences=[abs(f-a) for _,_,f,a in both]
    mismatches=[dict(api_sample_index=i,elapsed_from_api_first=(stamp-api_times[0]).total_seconds(),
                     fit_value=f,api_value=a,difference=a-f)
                for i,stamp,f,a in both if f!=a][:5]
    return dict(api_samples=len(api_values),fit_samples=len(fit_values),timestamp_pairs=len(pairs),
                pairing_coverage=len(pairs)/len(api_values) if api_values else None,
                both_present=len(both),exact_matches=exact,exact_match_rate=exact/len(both) if both else None,
                max_absolute_difference=max(differences) if differences else None,
                mean_absolute_difference=sum(differences)/len(differences) if differences else None,
                api_missing=sum(v is None for v in api_values),fit_missing=sum(v is None for v in fit_values),
                paired_api_missing=sum(a is None for _,_,f,a in pairs),
                paired_fit_missing=sum(f is None for _,_,f,a in pairs),
                api_zero=sum(v==0 for v in api_values),fit_zero=sum(v==0 for v in fit_values),
                paired_both_zero=sum(f==0 and a==0 for _,_,f,a in pairs),
                missing_pattern_differences=sum((f is None)!=(a is None) for _,_,f,a in pairs),
                first_mismatches=mismatches)


def compare(streams,evidence,api_start):
    records=evidence['records'];fit_start=instant(evidence['summary']['start_time'])
    fit_times=[instant(r['timestamp']) if r['timestamp'] else None for r in records]
    offsets=streams.get('time',{}).get('data',[])
    api_times=[api_start+timedelta(seconds=value) for value in offsets]
    metadata={k:{field:v[field] for field in ('resolution','series_type','original_size')}|dict(returned_length=len(v['data'])) for k,v in streams.items()}
    result=dict(returned_types=list(streams),missing_types=[k for k in STREAM_KEYS if k not in streams],
                metadata=metadata,api_time=timing(offsets),fit_record_count=len(records),
                fit_time=timing([(t-fit_start).total_seconds() for t in fit_times if t is not None]),
                fit_missing_timestamps=sum(t is None for t in fit_times),
                api_start_minus_fit_session_start_seconds=(api_start-fit_start).total_seconds(),
                alignment='Exact absolute instant: API summary start_date + returned offset versus FIT record timestamp. Duplicate instants excluded; no fitted shift.',
                signals={})
    for key,field in (('watts','power'),('heartrate','heart_rate')):
        if key not in streams:
            result['signals'][key]=dict(status='api_stream_missing');continue
        if len(streams[key]['data'])!=len(offsets):
            result['signals'][key]=dict(status='length_mismatch_not_paired');continue
        result['signals'][key]=dict(status='compared',**signal_comparison(api_times,streams[key]['data'],fit_times,[r[field] for r in records]))
    result['signals']['cadence']=dict(status='not_comparable_fit_extraction_has_no_sample_cadence',
                                     api_samples=len(streams.get('cadence',{}).get('data',[])))
    if 'watts' in streams:
        best=independent_best(offsets,streams['watts']['data'])
    else:best=None
    fit_offsets=[(t-fit_start).total_seconds() if t is not None else None for t in fit_times]
    # Missing FIT timestamps split valid runs; retain record order and do not invent offsets.
    fit_best=independent_best(fit_offsets,[r['power'] if t is not None else None for r,t in zip(records,fit_times)])
    result['experimental_best20']=dict(api=best,fit=fit_best,
        raw_difference_watts=best['average_watts']-fit_best['average_watts'] if best and fit_best else None,
        window_alignment_equal=(api_start+timedelta(seconds=best['start_elapsed'])==fit_start+timedelta(seconds=fit_best['start_elapsed'])) if best and fit_best else None,
        trusted_performance_enrollment=False)
    problems=[]
    if not offsets or result['api_time']['duplicates'] or result['api_time']['backwards']:problems.append('time_unavailable_or_nonmonotonic')
    for key in ('watts','heartrate'):
        signal=result['signals'][key]
        if signal['status']!='compared':problems.append(key+'_not_comparable')
        elif signal['pairing_coverage']!=1 or signal['exact_match_rate']!=1 or signal['missing_pattern_differences']:problems.append(key+'_coverage_or_values_not_exact_requires_interpretation')
    if any(v['original_size']!=len(v['data']) or v['resolution']!='high' for v in streams.values()):problems.append('sampling_metadata_requires_interpretation')
    result['evidence_review_reasons']=problems
    return result


def fingerprint(connection):
    result={}
    for table, in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        digest=sha256()
        for row in connection.execute('SELECT * FROM '+table+' ORDER BY rowid'):
            digest.update(json.dumps(tuple(row),ensure_ascii=True).encode()+b'\n')
        result[table]=digest.hexdigest()
    return result


def write_private(path,value):
    descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,'w') as stream:json.dump(value,stream,allow_nan=False)


def run(data_dir,cache_dir,*,fetch=False):
    if fetch:
        cache_dir.mkdir(parents=True,exist_ok=False)
        os.chmod(cache_dir,0o700)
    client=ApiClient(strava_credentials()) if fetch else None
    reports=[];excluded=[];requests=0
    with Store(data_dir) as store:
        before=fingerprint(store.connection)
        originals={p.name:(p.stat().st_size,p.stat().st_mtime_ns) for p in store.originals.iterdir()}
        history_before=performance_history(store)
        rows=store.connection.execute('''SELECT a.activity_id,a.external_id,s.evidence_json FROM strava_api_activities a
            JOIN strava_export_sources e ON e.external_id=a.external_id
            JOIN strava_api_sources s ON s.source_id=a.current_source_id ORDER BY a.external_id''').fetchall()
        if len(rows)!=4:raise SyncError('Expected four established overlap candidates; stop for evidence review')
        tokens=TokenFile(store.data_dir)
        with tokens.lock():
            try:
                current=refreshed_connection(tokens,client) if fetch else None
                for ordinal,row in enumerate(rows,1):
                    label='overlap-'+str(ordinal)
                    snapshot=store.get_activity(row['activity_id'])
                    files=[e for e in snapshot['sources'] if e['source']['kind']=='file_fit' and e['source']['content_format']=='FIT']
                    if len(files)!=1 or not files[0]['extraction'].get('extraction_id'):
                        excluded.append(dict(label=label,reason='not_exactly_one_supported_fit_source'));continue
                    path=cache_dir/(label+'.json')
                    if fetch:
                        raw=client.streams(current['access_token'],row['external_id']);requests+=1
                        streams=parse_streams(raw)
                        write_private(path,dict(activity_id=row['activity_id'],external_id=row['external_id'],
                            retrieved_at=datetime.now(timezone.utc).isoformat(),mapping_version=MAPPING,
                            requested=list(STREAM_KEYS),streams=streams))
                    else:
                        saved=json.loads(path.read_text())
                        if saved['external_id']!=row['external_id'] or saved['activity_id']!=row['activity_id']:
                            raise SyncError('Cached overlap does not match the established source identity')
                        streams=parse_streams(saved['streams'])
                    result=compare(streams,files[0],instant(json.loads(row['evidence_json'])['start_date']))
                    reports.append(dict(label=label,**result))
            except AuthenticationError:
                tokens.clear();raise
        assert before==fingerprint(store.connection),'Stage A changed accepted database evidence'
        assert originals=={p.name:(p.stat().st_size,p.stat().st_mtime_ns) for p in store.originals.iterdir()}
        assert store.connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not store.connection.execute('PRAGMA foreign_key_check').fetchall()
        history_after=performance_history(store)
        assert history_before==history_after
    needs_review=bool(excluded) or any(r['evidence_review_reasons'] for r in reports)
    return dict(stage='A',status='evidence_review_required' if needs_review else 'exact_power_hr_evidence_supports_graph_review',
                requested_keys=list(STREAM_KEYS),scope='activity:read_all',overlap_candidates=4,compared=len(reports),
                excluded=excluded,overlaps=reports,stream_requests_this_run=requests,
                rate_limits=client.rate if fetch else {},database_unchanged=True,originals_unchanged=True,
                performance_eligible=len(history_after['points']),performance_pending=history_after['pending'],
                integrity=True,foreign_keys=True,product_stream_writes=0,api_only_catchup_requests=0,
                trusted_performance_policy_changed=False,phase_3_started=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--cache-dir',type=Path,required=True)
    parser.add_argument('--fetch',action='store_true',help='Explicitly fetch four overlap streams; otherwise compare existing local cache only')
    args=parser.parse_args()
    try:result=run(args.data_dir,args.cache_dir,fetch=args.fetch)
    except (SyncError,OSError):
        print('Stage A could not complete; private responses remain local. No product stream evidence was written.',file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result,indent=2))
