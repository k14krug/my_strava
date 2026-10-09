#!/usr/bin/env python3
"""Independent numerical oracle for pinned Sauce experiment inputs/outputs.

Uses integer prefix sums + Decimal fourth powers/roots, not upstream or research
rolling implementations. All paths/rows are PRIVATE. Source preservation is also
checked with the existing full-store verifier.
"""
import argparse
from collections import Counter
from decimal import Decimal
import json
import math
from pathlib import Path
import statistics


def close(a,b):
    if a is None or b is None:assert a is b,(a,b)
    else:assert abs(float(a)-float(b)) <= max(1e-7,abs(float(b))*1e-10),(a,b)


def oracle(request,options):
    s=request['streams'];times=s['time'];power=s['watts'];n=len(times)
    assert len(power)==n and all(type(x) is int and x>=0 for x in power)
    assert all(b>a for a,b in zip(times,times[1:]))
    gaps=[b-a for a,b in zip(times,times[1:])]
    mode=Counter(gaps).most_common(1)[0][0] or 1
    maxgap=math.floor(max(mode,statistics.median(gaps))+.5)*4
    active=[False]
    hasdist=bool(s.get('distance') and s['distance'][-1])
    for i,delta in enumerate(gaps,1):
        distance=(s['distance'][i] or 0)-(s['distance'][i-1] or 0) if hasdist else 0
        enabled=bool(power[i] or (not hasdist and s['moving'][i]) or s.get('cadence',[0]*n)[i] or hasdist and distance/delta>=.447)
        enabled=enabled and delta<options.get('maxImmobileGap',75)
        if options.get('timerAware') and any(times[i-1]<b and times[i]>=a for a,b in request.get('pauseSpans',[])):enabled=False
        active.append(enabled)
    expanded=[];et=[];kind=[]
    def add(t,v,k):et.append(t);expanded.append(v);kind.append(k)
    for i,(t,p) in enumerate(zip(times,power)):
        if i:
            delta=t-times[i-1]
            if not active[i]:
                if delta>3600:
                    edge=1800-mode
                    x=mode
                    while x<edge:add(times[i-1]+x,0,'zero');x+=mode
                    add(times[i-1]+edge,0,'break')
                    x=delta-edge
                    while x<delta:add(times[i-1]+x,0,'zero');x+=mode
                else:
                    x=mode
                    while x<delta:add(times[i-1]+x,0,'zero');x+=mode
            else:
                x=mode
                while x<delta:add(times[i-1]+x,p,'pad');x+=mode
        add(t,p,'observed')
    seconds=sum(delta for delta,enabled in zip(gaps,active[1:]) if enabled)
    duration=sum(et[i]-et[i-1] for i in range(1,len(et)) if kind[i] in ('observed','pad'))
    work=sum(expanded[i]*(et[i]-et[i-1]) for i in range(1,len(et)) if kind[i] in ('observed','pad'))
    size=math.floor(30/mode+.5)
    np=None
    if len(expanded)*mode>=300 and size>=2:
        prefix=[0]
        for v in expanded:prefix.append(prefix[-1]+v)
        totals=[prefix[i+1]-prefix[i+1-size] for i in range(size-1,len(expanded))]
        count=sum(v!=0 or kind[i] not in ('zero','break') for i,v in enumerate(totals,size-1))
        fourth=Decimal(sum(v**4 for v in totals))/Decimal(size**4)
        np=(fourth/count).sqrt().sqrt() if fourth>1 else Decimal(0) if count else None
    avg=work/duration if duration else None
    used=np or avg
    stress=Decimal(str(used))*Decimal(str(used))/Decimal(request['ftp'])**2*Decimal(str(seconds))/36 if used is not None else None
    counts=Counter(kind)
    return dict(stress=stress,np=np,average=avg,active_seconds=seconds,corrected_active_seconds=duration,work_kj=work/1000,
        idealGap=mode,maxGap=maxgap,counts=dict(observed=counts['observed'],valuePad=counts['pad'],zeroPad=counts['zero'],breakPad=counts['break']))


def observed_oracle(streams,ftp,minimum=600):
    times=streams['time'];values=streams['watts'];starts=[0]+[i for i in range(1,len(times)) if times[i]!=times[i-1]+1]+[len(times)]
    stress=Decimal(0);seconds=0;count=0
    for a,b in zip(starts,starts[1:]):
        if b-a<minimum:continue
        p=values[a:b];sums=[sum(p[i:i+30]) for i in range(len(p)-29)]
        np=(Decimal(sum(x**4 for x in sums))/Decimal(30**4*len(sums))).sqrt().sqrt()
        stress+=Decimal(b-a)/36*(np/ftp)**2;seconds+=b-a;count+=1
    return (stress if count else None),seconds


def verify(directory):
    cases={r['key']:r for r in json.loads((directory/'cases-private.json').read_text())}
    cache=json.loads((directory/'sensors-private.json').read_text())
    refs=cache['reference_ids'];base={}
    # Reconstruct original reference arrays directly from immutable cached input,
    # and verify every injection is a deletion or declared pause time shift only.
    for i,(identity,scope) in enumerate(refs):
        item=cache['items'][identity];s=item['streams'];indices=list(range(len(s['time'])))
        if scope=='strict_timer':
            a,b=item['timer_intervals'][0];indices=[j for j in indices if a<=s['time'][j]<b]
        base[i]={k:[v[j] for j in indices] for k,v in s.items()}
        offset=base[i]['time'][0];base[i]['time']=[t-offset for t in base[i]['time']]
    count=variants=0
    with (directory/'requests-private.jsonl').open() as inputs,(directory/'sauce-private.jsonl').open() as outputs:
        for line,resultline in zip(inputs,outputs,strict=True):
            request=json.loads(line);result=json.loads(resultline);c=cases[request['key']]
            assert result['key']==request['key']
            s=request['streams'];ftp=Decimal(request['ftp'])
            expected,seconds=observed_oracle(s,ftp)
            close(c['observed']['stress'],expected);assert c['observed']['seconds']==seconds
            if request['key'].startswith('ref_'):
                index=int(request['key'].split('_')[1]);original=base[index]
                mask=set(c['removed_indices']);keep=[i for i in range(len(original['time'])) if i not in mask]
                expected_streams={k:[v[j] for j in keep] for k,v in original.items()}
                if c['gap_class']=='proven_pause':
                    midpoint=len(original['time'])//2
                    expected_streams['time']=[t+(c['gap_length'] if j>=midpoint else 0) for j,t in enumerate(original['time'])]
                    ref,_=observed_oracle(expected_streams,ftp)
                else:ref,_=observed_oracle(original,ftp)
                assert s==expected_streams
                close(c['reference'],ref)
            else:
                assert s==cache['items'][c['activity_id']]['streams']
                close(c['observed']['stress'],c['old_segment_stress'])
            for name,options in request['variants'].items():
                expected=oracle(request,options);actual=result[name]
                for key in expected:
                    if key=='counts':assert actual[key]==expected[key],(request['key'],actual[key],expected[key])
                    else:close(actual[key],expected[key])
                variants+=1
            count+=1
            if count%250==0:print(f'Independent numerical check {count}/{len(cases)}',flush=True)
    assert count==len(cases)
    return dict(cases=count,upstream_variant_checks=variants,reference_rides=len(refs),
        injected_values_changed=0,originals_edited=0,method='independent Python integer-window/Decimal oracle',
        all_inputs_and_deletions_verified=True,all_observed_segment_results_verified=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-dir',type=Path,required=True);a=p.parse_args()
    result=verify(a.input_dir);(a.input_dir/'numerical-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
