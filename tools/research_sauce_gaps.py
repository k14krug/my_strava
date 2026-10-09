#!/usr/bin/env python3
"""P4-01 §15: bounded PRIVATE controlled-gap and actual-recording experiment.

Runs unmodified pinned Sauce math through a local Node adapter. Never writes the
store, edits originals, fetches Strava data, or promotes estimates to measurements.
"""
import argparse
from collections import Counter
from datetime import date, timedelta
import hashlib
import io
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import fitdecode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.research_training_state import readonly_store, verified_bytes, dump, normalized_power
from tools.research_training_state_ftp import source_data, segments, metrics

VERSION='p4-01-sauce-gap-experiment-v1'
PIN='4b6d4f42bf56d064507d694abd56e5f989530e03'
GAPS=(1,5,15,30,60,73,74,75,300,600)


def references(rows):
    strict=sorted((r for r in rows if r['full_timer_stress'] is not None),key=lambda r:r['activity_id'])
    candidates=[r for r in rows if r['floor_stress'] is not None and r['full_timer_stress'] is None]
    selected={}
    # Deliberate coverage of duration, relative intensity and variable power;
    # this is a descriptive stress test, not a random population sample.
    for key in [lambda r:r['observed_seconds'],lambda r:r['segment600']['pooled_np']/r['dated_ftp']['watts'],
                lambda r:r['segment600']['pooled_np']/(r['segment_work_kj']*1000/r['observed_seconds'])]:
        ordered=sorted(candidates,key=lambda r:(key(r),r['activity_id']))
        for i in range(8):
            row=ordered[round(i*(len(ordered)-1)/7)];selected[row['activity_id']]=row
    for row in sorted(candidates,key=lambda r:r['activity_id']):
        if len(selected)>=24:break
        selected.setdefault(row['activity_id'],row)
    return [(r,'strict_timer') for r in strict]+[(r,'complete_envelope') for r in sorted(selected.values(),key=lambda r:r['activity_id'])]


def extract(store,row,saved):
    times,powers,session,events,moving=source_data(store,saved)
    sensors={}; devices=[]
    if saved.get('extraction_id'):
        source=dict(store.connection.execute('SELECT * FROM sources WHERE source_id=?',(row['power_source_id'],)).fetchone())
        payload=verified_bytes(store.data_dir,source);raw=[]
        with fitdecode.FitReader(io.BytesIO(payload),check_crc=fitdecode.CrcCheck.RAISE) as reader:
            for frame in reader:
                if not isinstance(frame,fitdecode.FitDataMessage):continue
                fields={f.name:f.value for f in frame.fields}
                if frame.name=='record':raw.append(fields)
                if frame.name in ('file_id','device_info'):
                    devices.append({k:fields[k] for k in ('manufacturer','product','product_name','device_type','source_type') if k in fields and fields[k] is not None})
        assert len(raw)==len(times)
        assert [v.get('power') for v in raw]==powers
        for name in ('cadence','distance'):
            sensors[name]=[v.get(name) for v in raw]
        # FIT has no Strava moving stream. Derived speed flag is explicit; when
        # trainer distance is present the exact Sauce function ignores this flag.
        moving=[(v.get('enhanced_speed',v.get('speed')) or 0) >= .447 for v in raw]
        moving_origin='derived FIT speed >=0.447 m/s; missing speed false'
    else:
        data=json.loads(store.connection.execute('SELECT evidence_json FROM strava_stream_sources WHERE source_id=?',(row['power_source_id'],)).fetchone()[0])
        for name in ('cadence','distance'):
            if name in data:sensors[name]=data[name]['data']
        moving_origin='retained API moving' if moving is not None else 'moving unavailable; false adapter'
        if moving is None:moving=[False]*len(times)
    counts=Counter(times); valid=[i for i,(t,p) in enumerate(zip(times,powers)) if t is not None and counts[t]==1 and type(p) in (int,float) and math.isfinite(p) and p>=0]
    if any(times[b]<=times[a] for a,b in zip(valid,valid[1:])):raise ValueError('Backwards native source: report, do not sort')
    base=times[0]
    streams=dict(time=[times[i]-base for i in valid],watts=[powers[i] for i in valid],moving=[moving[i] for i in valid])
    streams.update({k:[values[i] for i in valid] for k,values in sensors.items()})
    intervals=[(a-base,b-base) for a,b in row['timer']['intervals']] if row['timer']['intervals'] else []
    pause_spans=[(a[1],b[0]) for a,b in zip(intervals,intervals[1:])]
    return dict(activity_id=row['activity_id'],streams=streams,ftp=row['dated_ftp']['watts'],
        ftp_interval=row['dated_ftp'],devices=devices,moving_origin=moving_origin,
        excluded_native_rows=len(times)-len(valid),timer_intervals=intervals,pauseSpans=pause_spans,
        timer_delta=row['timer']['delta'],timer_boundary_verified=row['timer']['boundary_verified'],
        day=row['day'],source_kind=row['power_source'],old_segment_stress=row['stress600'],
        strict_stress=row['full_timer_stress'],whole_reason=row['whole_power_reason'])


def subset(streams,indices):
    return {k:[v[i] for i in indices] for k,v in streams.items()}


def observed(streams,ftp):
    parts,error=segments(streams['time'],streams['watts'])
    if error:raise ValueError(error)
    value=metrics(parts,streams['watts'],ftp,600)
    return dict(stress=value['stress'],seconds=value['seconds'],work_kj=value['work_kj'],
        segments=value['segments'],omitted_short_seconds=len(streams['watts'])-value['seconds'])


def gap_cases(streams,seed):
    n=len(streams['time']);powers=streams['watts'];rng=random.Random(seed)
    yield 'pristine', [], dict(gap_class='none',gap_length=0,placement='none',seed=seed)
    for length in GAPS:
        prefix=[0]
        for p in powers:prefix.append(prefix[-1]+p)
        lo,hi=30,n-length-30
        if hi<lo:continue
        starts=dict(random=rng.randint(lo,hi),highest_power=max(range(lo,hi+1),key=lambda i:prefix[i+length]-prefix[i]),
                    lowest_power=min(range(lo,hi+1),key=lambda i:prefix[i+length]-prefix[i]))
        for placement,start in starts.items():
            indices=list(range(start,start+length))
            near=powers[start:start+length]
            yield f'loss_{length}_{placement}',indices,dict(gap_class='unexplained_loss',gap_length=length,
                placement=placement,seed=seed,removed_mean_power=sum(near)/length,removed_all_zero=all(p==0 for p in near))
    indices=sorted({i for j in range(1,13) for i in range(n*j//13,min(n*j//13+5,n-1))})
    yield 'bursty_12x5',indices,dict(gap_class='bursty',gap_length=5,placement='12 equally spaced bursts',seed=seed)
    for where,indices in [('start',list(range(30))),('end',list(range(n-30,n)))]:
        yield 'boundary_'+where,indices,dict(gap_class='boundary_loss',gap_length=30,placement=where,seed=seed)
    zero=[i for i,p in enumerate(powers[1:-1],1) if p==0]
    if zero:
        chosen=zero[len(zero)//2]
        yield 'observed_zero_loss',[chosen],dict(gap_class='observed_zero_loss',gap_length=1,placement='middle observed zero',seed=seed,removed_all_zero=True)


def prepare_reference(item,scope):
    streams=item['streams']
    if scope=='strict_timer':
        intervals=item['timer_intervals']
        assert len(intervals)==1
        indices=[i for i,t in enumerate(streams['time']) if intervals[0][0]<=t and t+1<=intervals[0][1]]
        streams=subset(streams,indices)
    offset=streams['time'][0]
    streams=dict(streams,time=[t-offset for t in streams['time']])
    assert streams['time']==list(range(len(streams['time'])))
    return streams


def make_experiment(cache,out):
    metadata=[];counts=Counter()
    variants=dict(sauce={},timer_aware=dict(timerAware=True),cutoff30=dict(maxImmobileGap=30),cutoff120=dict(maxImmobileGap=120))
    with (out/'requests-private.jsonl').open('w') as requests:
        def emit(key,streams,item,record,pause_spans=None):
            request=dict(key=key,streams=streams,ftp=item['ftp'],pauseSpans=pause_spans or [],variants=variants)
            requests.write(json.dumps(request,separators=(',',':'))+'\n')
            record.update(key=key,activity_id=item['activity_id'],ftp=item['ftp'],source_kind=item['source_kind'],
                scope=record.get('scope','actual_unknown'),observed=observed(streams,item['ftp']),
                samples=len(streams['time']),span=streams['time'][-1]-streams['time'][0]+1)
            metadata.append(record)
        for index,(identity,scope) in enumerate(cache['reference_ids']):
            item=cache['items'][identity];streams=prepare_reference(item,scope);n=len(streams['time'])
            np=normalized_power(streams['watts']);reference=n/36*(np/item['ftp'])**2
            for case,mask,meta in gap_cases(streams,4011500+index):
                lost=set(mask);cut=subset(streams,[i for i in range(n) if i not in lost])
                emit(f'ref_{index}_{case}',cut,item,dict(meta,scope=scope,reference=reference,original_seconds=n,
                    removed_indices=mask,strict_available=scope=='strict_timer' and not mask,
                    boundary_loss=case.startswith('boundary_')))
            # Pauses add wall time without deleting any signal; the timer-aware
            # reference resets NP at the known stop/restart, as the existing rule.
            midpoint=n//2
            for pause in (5,60,300):
                paused=dict(streams,time=[t+(pause if i>=midpoint else 0) for i,t in enumerate(streams['time'])])
                target=observed(paused,item['ftp'])['stress']
                emit(f'ref_{index}_pause_{pause}',paused,item,dict(scope=scope,gap_class='proven_pause',gap_length=pause,
                    placement='midpoint; no power loss',seed=4011500+index,reference=target,original_seconds=n,
                    removed_indices=[],strict_available=scope=='strict_timer',boundary_loss=False),[(midpoint,midpoint+pause)])
        for identity in cache['actual_ids']:
            item=cache['items'][identity]
            times=item['streams']['time'];gaps=[b-a-1 for a,b in zip(times,times[1:]) if b-a>1]
            emit('actual_'+identity,item['streams'],item,dict(day=item['day'],gap_class='actual_interrupted' if item['whole_reason'] else 'actual_complete_envelope',
                whole_reason=item['whole_reason'],strict_available=item['strict_stress'] is not None,reference=None,
                max_missing_gap=max(gaps,default=0),missing_interior_seconds=sum(gaps),
                known_pause_count=len(item['pauseSpans']),excluded_native_rows=item['excluded_native_rows'],
                old_segment_stress=item['old_segment_stress']),item['pauseSpans'])
    dump(out/'cases-private.json',metadata)
    return metadata


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--ftp-results',type=Path,required=True)
    p.add_argument('--upstream',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--reuse-sensors',action='store_true');a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
    rows=json.loads((a.ftp_results/'activities-private.json').read_text())
    dbhash=hashlib.sha256((a.data_dir/'rideworks.sqlite3').read_bytes()).hexdigest()
    sourcehash=hashlib.sha256((a.ftp_results/'activities-private.json').read_bytes()).hexdigest()
    cache_path=a.output_dir/'sensors-private.json'
    if a.reuse_sensors:
        cache=json.loads(cache_path.read_text())
        assert cache['dbhash']==dbhash and cache['sourcehash']==sourcehash and cache['version']==VERSION
    else:
        refs=references(rows);asof=date(2026,10,8)
        actual=[r for r in rows if r['stress600'] is not None and (r['whole_power_reason'] is not None or date.fromisoformat(r['day'])>=asof-timedelta(days=41))]
        selected={r['activity_id']:r for r in actual+ [r for r,_ in refs]}
        store=readonly_store(a.data_dir)
        try:
            saved={i:json.loads(j) for i,j in store.connection.execute("SELECT activity_id,result_json FROM performance_history WHERE policy='virtual-power-evidence-v2'")}
            items={}
            for i,(identity,row) in enumerate(sorted(selected.items())):
                items[identity]=extract(store,row,saved[identity])
                if (i+1)%25==0:print(f'Parsed sensor context {i+1}/{len(selected)}',flush=True)
        finally:store.close()
        cache=dict(version=VERSION,dbhash=dbhash,sourcehash=sourcehash,items=items,
            reference_ids=[(r['activity_id'],scope) for r,scope in refs],actual_ids=[r['activity_id'] for r in actual])
        dump(cache_path,cache)
    make_experiment(cache,a.output_dir)
    subprocess.run(['node','tools/run_sauce_research.mjs',str(a.upstream),str(a.output_dir/'requests-private.jsonl'),str(a.output_dir/'sauce-private.jsonl')],check=True)
    assert hashlib.sha256((a.data_dir/'rideworks.sqlite3').read_bytes()).hexdigest()==dbhash
    print('Experiment complete; PRIVATE results require independent verification and aggregate publication.')


if __name__=='__main__':main()
