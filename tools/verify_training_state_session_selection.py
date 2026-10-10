#!/usr/bin/env python3
"""Verify installed session-power selection against sources and pinned upstream.

Private inputs/case evidence remain local; published outputs are aggregate only.
Uses actual current calculations/cache, never an uninstalled diagnostic curve.
"""
import argparse
from collections import Counter
from datetime import date,datetime,timedelta
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rideworks.store import Store
from rideworks.history import presentation
from rideworks.training_state import training_state,ride_results,calculate_ride
from tools.compare_training_state_elevate import read_reference
from tools.diagnose_training_state_power import response,table_digest
from tools.verify_training_state_production import preservation

REFERENCE_SHA='8fd699848e597a307b1d1adaffe19f5b99a149412d39bcd35a5e4e87806dd909'


def close(a,b):assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9)


def verify_session(store,ride,oracle):
    result=ride['session_power'];source=result.get('source')
    if result['stress'] is None:return 0
    if source['format']=='Strava API stream':
        observation=next(s for s in store.strava_stream_evidence(ride['activity_id']) if s['source_id']==source['stream_source_id'])
        times=observation['streams']['time']['data'];powers=observation['streams']['watts']['data']
        summary=store.get_source(source['summary_source_id'])['summary']['values'];events=[]
        assert summary['device_watts'] is True
        close(result['duration_seconds'],summary['moving_time']);close(result['elapsed_seconds'],summary['elapsed_time']);origin=0
    else:
        native=store.get_source(source['source_id']);summary=native['summary'];events=native['events']
        times=[datetime.fromisoformat(r['timestamp']).timestamp() if r['timestamp'] else None for r in native['records']]
        powers=[r['power'] for r in native['records']]
        close(result['duration_seconds'],summary['total_timer_time']);close(result['elapsed_seconds'],summary['total_elapsed_time'])
        origin=datetime.fromisoformat(summary['start_time']).timestamp()
    points=[(t,p) for t,p in zip(times,powers) if p is not None]
    intervals=[];active=None
    for event in events:
        if event['event']!='timer':continue
        t=datetime.fromisoformat(event['timestamp']).timestamp()
        if event['event_type']=='start':active=t
        else:assert active is not None;intervals.append((active,t));active=None
    assert active is None
    groups=[[(t,p) for t,p in points if a<=t and t+1<=b] for a,b in intervals] if intervals else [points]
    observed=[t for g in groups for t,p in g]
    # Independent direct integer-bin sliding counts, not production boundary events.
    timeline=intervals if result['timer_boundaries_verified'] else [(origin,origin+result['elapsed_seconds'])]
    bins=[]
    for a,b in timeline:
        assert a%1==0 and b%1==0
        evidence=set(t for t in observed if a<=t<b)
        bins.extend(int(t in evidence) for t in range(int(a),int(b)))
    width=min(300,len(bins));prefix=[0]
    for value in bins:prefix.append(prefix[-1]+value)
    minimum=min(prefix[i+width]-prefix[i] for i in range(len(bins)-width+1))
    screen=result['representativeness'];close(screen['observed_fraction'],sum(bins)/len(bins))
    close(screen['worst_window_observed_fraction'],minimum/width)
    assert sum(bins)/len(bins)>=.8-1e-12 and minimum/width>=.5-1e-12
    close(result['stress'],100*result['duration_seconds']/3600*(result['weighted_power']/ride['ftp']['value'])**2)
    assert result['samples_invented']==0 and not result['whole_session_verified']
    oracle.append(dict(ride=ride,groups=groups))
    return 1


def upstream_oracle(path,checks):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==REFERENCE_SHA
    source=path.read_text();start=source.index('    const poweredWeightedWatts = [];');end=source.index('\n  }',start)
    body=source[start:end]
    # Expose the actual function's batch count alongside its unchanged NP result.
    instrumented=body.replace('return Math.sqrt(Math.sqrt(_.mean(poweredWeightedWatts)));',
        'return {np:Math.sqrt(Math.sqrt(_.mean(poweredWeightedWatts))),count:poweredWeightedWatts.length};')
    assert instrumented!=body
    inputs=[dict(time=[t for t,p in g],watts=[p for t,p in g]) for c in checks for g in c['groups']]
    script="const _={mean:a=>a.length?a.reduce((x,y)=>x+y,0)/a.length:NaN};const ActivityComputer={WEIGHTED_WATTS_TIME_BUFFER:30};const f=new Function('powerArray','timeArray',"+json.dumps(instrumented)+");let s='';process.stdin.on('data',b=>s+=b);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(JSON.parse(s).map(x=>f(x.watts,x.time)))));"
    output=json.loads(subprocess.run(['node','-e',script],input=json.dumps(inputs),text=True,capture_output=True,check=True).stdout)
    offset=0
    for c in checks:
        results=output[offset:offset+len(c['groups'])];offset+=len(c['groups'])
        count=sum(x['count'] for x in results)
        expected=(math.fsum(x['np']**4*x['count'] for x in results if x['count'])/count)**.25
        close(expected,c['ride']['session_power']['weighted_power'])
        assert count==c['ride']['session_power']['buffer_count']
    assert offset==len(output)
    return dict(candidate_checks=len(checks),actual_upstream_buffer_checks=len(output),source_sha256=REFERENCE_SHA)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ('data-dir','baseline-dir','before','cases','blocked-cases','reference','reference-source','after-output','private-output','aggregate-output'):
        p.add_argument('--'+flag,type=Path,required=True)
    p.add_argument('--as-of',required=True);a=p.parse_args();now=datetime.fromisoformat(a.as_of)
    before=json.loads(a.before.read_text());old={r['activity_id']:r for r in before['rides']}
    completed,projections=read_reference(a.reference);reference={r['date']:r for r in completed}
    preserved=preservation(a.data_dir,a.baseline_dir);cases=json.loads(a.cases.read_text());oracle=[]
    with Store(a.data_dir) as store:
        signatures=dict(store.connection.execute('SELECT activity_id,input_signature FROM training_stress_cache'))
        with patch('rideworks.training_state.calculate_ride',wraps=calculate_ride) as calculate:
            data=training_state(store,'America/Los_Angeles',as_of=now);initial_recalculations=calculate.call_count
        rides,_=ride_results(store,'America/Los_Angeles',as_of=now)
        current={r['activity_id']:r for r in rides};assert current.keys()==old.keys()
        changed=[]
        for identity,r in current.items():
            prior=old[identity]
            for field in ('power','power_candidates','hr','hr_candidates','ftp','hr_settings'):assert r[field]==prior[field],field+' changed'
            if r['selected']!=prior['selected']:
                assert r['selected']['method']=='session_power' and prior['power']['status'] not in ('calculated','corrected_estimate')
                changed.append(r)
            if prior['power']['status'] in ('calculated','corrected_estimate'):assert r['selected']==prior['selected']
        final_signatures=dict(store.connection.execute('SELECT activity_id,input_signature FROM training_stress_cache'))
        digest=table_digest(store.connection)
        cached_versions=Counter(json.loads(r[0])['version'] for r in store.connection.execute('SELECT result_json FROM training_stress_cache'))
        assert cached_versions==Counter({data['version']:len(rides)})
        store.connection.execute('PRAGMA query_only=ON')
        fresh=0
        for snapshot in store.activity_history():
            identity=snapshot['activity']['activity_id']
            if identity not in current:continue
            r=current[identity]
            calculated=calculate_ride(store,snapshot,presentation(snapshot),r['ftp'],r['hr_settings'])
            assert calculated=={k:v for k,v in r.items() if k not in ('day','title','timezone_unknown')}
            fresh+=1
        assert fresh==len(rides) and digest==table_digest(store.connection)
        store.connection.execute('PRAGMA query_only=OFF')
        with patch('rideworks.training_state.calculate_ride',side_effect=AssertionError('cache must be reused')):
            assert data==training_state(store,'America/Los_Angeles',as_of=now)
        assert digest==table_digest(store.connection)
        examples=[]
        for case in cases:
            matches=[r for r in rides if r['day']==case['day'] and (not case.get('activity_id') or case['activity_id']==r['activity_id']) and (not case.get('title') or case['title']==r['title'])]
            assert len(matches)==1;r=matches[0]
            examples.append(dict(role=case['role'],before_ride=old[r['activity_id']],ride=r,
                before_behavior=response(before['data']['days'],r['day'],old[r['activity_id']],reference),
                behavior=response(data['days'],r['day'],r,reference)))
        checked={r['activity_id']:r for r in changed}
        checked.update({e['ride']['activity_id']:e['ride'] for e in examples})
        for r in checked.values():verify_session(store,r,oracle)
        assert digest==table_digest(store.connection)
    preserved_after=preservation(a.data_dir,a.baseline_dir);assert preserved==preserved_after
    with Store(a.data_dir) as reopened:
        with patch('rideworks.training_state.calculate_ride',side_effect=AssertionError('restart must reuse cache')):
            assert data==training_state(reopened,'America/Los_Angeles',as_of=now)
    pinned=upstream_oracle(a.reference_source,oracle)
    mandatory=next(e for e in examples if e['role']=='mandatory_short_interval_workout')
    assert mandatory['ride']['selected']['method']=='session_power'
    assert mandatory['ride']['session_power']['reason'] is None
    assert mandatory['behavior']['daily_changes']['fitness']>0 and mandatory['behavior']['daily_changes']['fatigue']>0
    assert mandatory['behavior']['next_calendar_day']['form']==mandatory['behavior']['selected_day']['fitness']-mandatory['behavior']['selected_day']['fatigue']
    outdoor=next(e for e in examples if e['role']=='retained_mandatory_outdoor_hr')
    assert outdoor['ride']['selected']==outdoor['before_ride']['selected'] and outdoor['ride']['selected']['method']=='hr'
    blocked=json.loads(a.blocked_cases.read_text())['blocked_best20_cases']
    windows={}
    for n in (7,42,90,365):
        cutoff=(date.fromisoformat(data['today'])-timedelta(days=n-1)).isoformat()
        b=[d for d in before['data']['days'] if d['day']>=cutoff];c=[d for d in data['days'] if d['day']>=cutoff]
        windows[str(n)]=dict(before_stress=math.fsum(d['stress'] for d in b),after_stress=math.fsum(d['stress'] for d in c),
            completed_reference_stress=math.fsum(float(reference[d['day']]['finalStressScore'] or 0) for d in c if d['day'] in reference),
            changed_rides=sum(r['day']>=cutoff for r in changed),selected_classes=dict(Counter(r['selected']['status'] for d in c for r in d['rides'])))
    directions={}
    for key,vendor_key in [('fitness','ctl'),('fatigue','atl')]:
        paired=[]
        for e in examples:
            behavior=e['behavior'];day=behavior['selected_day']['day'];prior=behavior['previous_calendar_day']['day']
            if day not in reference or prior not in reference:continue
            actual=behavior['daily_changes'][key];vendor=float(reference[day][vendor_key])-float(reference[prior][vendor_key])
            paired.append((actual>1e-9)-(actual<-1e-9)==(vendor>1e-9)-(vendor<-1e-9))
        directions[key]=dict(compared=len(paired),same_direction=sum(paired),different_direction=len(paired)-sum(paired))
    report=dict(version=data['version'],session_power_method=data['session_power_method'],session_power_policy=data['session_power_policy'],
        selection_policy=data['selection_policy'],before_coverage=before['data']['coverage'],after_coverage=data['coverage'],
        selection_changes=len(changed),selection_transitions=dict(Counter(old[r['activity_id']]['selected']['status']+' -> '+r['selected']['status'] for r in changed)),
        session_candidate_reasons=dict(Counter(r['session_power'].get('reason') or 'eligible' for r in rides)),
        all_recorded_power_and_work_preserved=True,all_hr_candidates_preserved=True,complete_corrected_selections_preserved=True,
        cache=dict(initial_recalculations=initial_recalculations,changed_signatures=sum(signatures.get(k)!=v for k,v in final_signatures.items()),
            current_cached_versions=dict(cached_versions),fresh_source_recalculations_identical=fresh,reused_identically=True,restart_reused_identically=True),
        independent_source_distribution_and_formula_checks=pinned['candidate_checks'],upstream_oracle=pinned,preservation=preserved,
        representative_cases=len(examples),mandatory_interval_selects_session_power=True,mandatory_outdoor_hr_preserved=True,
        representative_reference_directions=directions,
        diagnostic_only=False,windows=windows,projected_reference_days_excluded=len(projections),
        formerly_blocked_117=dict(rides=len(blocked),before_selected=dict(Counter(old[c['ride']['activity_id']]['selected']['status'] for c in blocked)),
            after_selected=dict(Counter(current[c['ride']['activity_id']]['selected']['status'] for c in blocked))),
        endpoint_after_minus_before={k:data['days'][-1][k]-before['data']['days'][-1][k] for k in ('fitness','fatigue','form')})
    private=dict(examples=examples,changed_rides=changed)
    for path,value in ((a.after_output,dict(data=data,rides=rides)),(a.private_output,private),(a.aggregate_output,report)):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__=='__main__':main()
