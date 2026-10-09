#!/usr/bin/env python3
"""P4-01 aggregate publisher: no source identities, dated rides or sensor streams."""
import argparse
from collections import Counter,defaultdict
from datetime import date,timedelta
import json
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.research_sauce_gaps import PIN,VERSION,prepare_reference
from tools.research_training_state import normalized_power


def percentile(values,q):
    if not values:return None
    a=sorted(values);pos=(len(a)-1)*q;lo=int(pos);hi=math.ceil(pos)
    return a[lo]+(a[hi]-a[lo])*(pos-lo)


def distribution(values):
    return dict(n=len(values),min=min(values) if values else None,median=percentile(values,.5),
        p95=percentile(values,.95),max=max(values) if values else None)


def errors(group,result,method):
    points=[];percent=[]
    for c in group:
        value=(c['observed']['stress'] if method=='observed600' else c['reference'] if c['strict_available'] else None) if method in ('observed600','strict') else result[c['key']][method]['stress']
        if value is None:continue
        delta=value-c['reference'];points.append(delta)
        if c['reference']>0:percent.append(delta/c['reference']*100)
    return dict(cases=len(group),available=len(points),unavailable=len(group)-len(points),
        signed_points=distribution(points),absolute_points=distribution([abs(v) for v in points]),
        signed_percent=distribution(percent),absolute_percent=distribution([abs(v) for v in percent]))


def admissible(c,limit):
    if c['scope']=='actual_unknown':
        return (c['max_missing_gap']<=limit and c['missing_interior_seconds']/c['span']<=.01
                and c['known_pause_count']==0 and c['excluded_native_rows']==0)
    return (c['gap_class'] not in ('boundary_loss','proven_pause') and c['gap_length']<=limit
            and len(c['removed_indices'])/c['original_seconds']<=.01)


def summarize(root,ftp_results):
    cases=json.loads((root/'cases-private.json').read_text())
    cache=json.loads((root/'sensors-private.json').read_text())
    result={r['key']:r for r in map(json.loads,(root/'sauce-private.jsonl').open())}
    numerical=json.loads((root/'numerical-verification.json').read_text())
    controlled=[c for c in cases if c['scope']!='actual_unknown']
    actual=[c for c in cases if c['scope']=='actual_unknown']
    by=defaultdict(list)
    for c in controlled:by[(c['scope'],c['gap_class'],c['gap_length'])].append(c)
    comparisons=[dict(scope=scope,gap_class=kind,gap_length=length,
        methods={m:errors(group,result,m) for m in ('strict','observed600','sauce','timer_aware','cutoff30','cutoff120')})
        for (scope,kind,length),group in sorted(by.items())]
    refstats={}
    for scope in ('strict_timer','complete_envelope'):
        refs=[cache['items'][i] for i,s in cache['reference_ids'] if s==scope]
        streams=[prepare_reference(x,scope) for x in refs]
        refstats[scope]=dict(rides=len(refs),seconds=distribution([len(s['time']) for s in streams]),
            intensity_np_over_ftp=distribution([normalized_power(s['watts'])/x['ftp'] for x,s in zip(refs,streams)]),
            variability_np_over_mean=distribution([normalized_power(s['watts'])/(sum(s['watts'])/len(s['watts'])) for s in streams]),
            observed_zero_fraction=distribution([s['watts'].count(0)/len(s['watts']) for s in streams]),
            years=dict(Counter(x['day'][:4] for x in refs)),
            file_manufacturers=dict(Counter(x['devices'][0].get('manufacturer','unknown') if x['devices'] else 'unknown' for x in refs)),
            rides_with_wahoo_power_device=sum(any(d.get('manufacturer')=='wahoo_fitness' and d.get('device_type')==17 for d in x['devices']) for x in refs),
            source_classes=dict(Counter(x['source_kind'] for x in refs)))
    policies=[]
    interrupted=[c for c in actual if c['gap_class']=='actual_interrupted']
    for limit in (1,5,15,30):
        admitted=[c for c in controlled if c['gap_class']!='none' and admissible(c,limit)]
        policies.append(dict(max_missing_seconds=limit,max_missing_fraction=.01,
            controlled=errors(admitted,result,'sauce'),controlled_omitted=len(controlled)-48-len(admitted),
            actual_interrupted_admitted=sum(admissible(c,limit) for c in interrupted),actual_interrupted_denominator=len(interrupted)))
    actual_groups=[]
    for reason,group in [(k,[c for c in actual if c['whole_reason']==k]) for k in (None,'non_contiguous_timing','missing_or_invalid_power')]:
        differences=[result[c['key']]['sauce']['stress']-c['observed']['stress'] for c in group]
        ratios=[100*(result[c['key']]['sauce']['stress']/c['observed']['stress']-1) for c in group if c['observed']['stress']]
        actual_groups.append(dict(reason=reason or 'complete_envelope',rides=len(group),
            source_classes=dict(Counter(c['source_kind'] for c in group)),
            disagreement_points=distribution(differences),disagreement_percent=distribution(ratios),
            value_pads=sum(result[c['key']]['sauce']['counts']['valuePad'] for c in group),
            zero_pads=sum(result[c['key']]['sauce']['counts']['zeroPad'] for c in group),
            break_markers=sum(result[c['key']]['sauce']['counts']['breakPad'] for c in group),
            known_pause_rides=sum(c['known_pause_count']>0 for c in group),
            gaps=distribution([c['max_missing_gap'] for c in group])))
    original=json.loads((ftp_results/'activities-private.json').read_text());asof=date(2026,10,8);recent={}
    for n in (7,42):
        start=str(asof-timedelta(days=n-1));group=[c for c in actual if start<=c['day']<=str(asof)]
        cycling=[r for r in original if r['kind'] in ('Ride','Virtual Ride') and r['day'] and start<=r['day']<=str(asof)]
        recent[str(n)]=dict(cycling=len(cycling),contributors=len(group),unavailable=len(cycling)-len(group),
            outdoor_excluded=sum(r['kind']=='Ride' for r in cycling),
            observed600_subtotal=sum(c['observed']['stress'] for c in group),
            sauce_experiment_subtotal=sum(result[c['key']]['sauce']['stress'] for c in group),
            no_record_days=n-len({r['day'] for r in cycling}),
            candidate_classes=dict(complete_envelope=sum(c['whole_reason'] is None for c in group),
                small_gap_interval_estimate=sum(c['whole_reason'] is not None and admissible(c,5) for c in group),
                other_partial=sum(c['whole_reason'] is not None and not admissible(c,5) for c in group)),
            cutoffs={str(k):dict(admitted=sum(admissible(c,k) for c in group),
                estimated_interval_subtotal=sum(result[c['key']]['sauce']['stress'] for c in group if admissible(c,k))) for k in (1,5,15,30)})
    # Stratify targeted high/low losses without presenting one favorite case.
    placements=[]
    for scope in ('strict_timer','complete_envelope'):
        for placement in ('random','highest_power','lowest_power'):
            group=[c for c in controlled if c['scope']==scope and c['gap_class']=='unexplained_loss' and c['placement']==placement]
            placements.append(dict(scope=scope,placement=placement,methods={m:errors(group,result,m) for m in ('observed600','sauce')}))
    return dict(version=VERSION,pin=PIN,source_sha256=next(iter(result.values()))['sha256'],
        references=refstats,controlled_cases=len(controlled),actual_cases=len(actual),comparisons=comparisons,
        placements=placements,policies=policies,actual_disagreement=actual_groups,recent=recent,
        numerical_verification=numerical),cases,result


def plots(summary,cases,result,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(13,10),constrained_layout=True)
    for ax,scope,title in zip(axes[0],('strict_timer','complete_envelope'),('24 strict timer references','24 supplemental recorded envelopes')):
        groups=[x for x in summary['comparisons'] if x['scope']==scope and x['gap_class']=='unexplained_loss']
        groups.sort(key=lambda x:x['gap_length']);x=list(range(len(groups)))
        for method,color,label in [('observed600','#a45d30','Observed ≥600 s'),('sauce','#235b82','Pinned Sauce candidate')]:
            ax.plot(x,[g['methods'][method]['absolute_percent']['median'] for g in groups],color=color,label=label+' median')
            ax.plot(x,[g['methods'][method]['absolute_percent']['p95'] for g in groups],color=color,linestyle='--',label=label+' p95')
        ax.set_xticks(x,[str(g['gap_length']) for g in groups]);ax.set_xlabel('Deleted seconds (3 placements per reference)')
        ax.set_ylabel('Absolute error vs reference (%)');ax.set_title(title,loc='left')
    group=[c for c in cases if c['gap_class']=='actual_interrupted'];ax=axes[1,0]
    ax.scatter([c['observed']['stress'] for c in group],[result[c['key']]['sauce']['stress'] for c in group],s=12,alpha=.65,color='#235b82')
    limit=max(max(c['observed']['stress'],result[c['key']]['sauce']['stress']) for c in group)
    ax.plot([0,limit],[0,limit],linestyle=':',color='#777');ax.set_xlabel('Observed segment subtotal (points)');ax.set_ylabel('Sauce estimate (points)')
    ax.set_title('281 actual interruptions: disagreement, NOT accuracy',loc='left',fontsize=10)
    ax=axes[1,1];policies=summary['policies']
    ax.bar([str(p['max_missing_seconds']) for p in policies],[p['actual_interrupted_admitted'] for p in policies],color='#235b82')
    ax.set_xlabel('Candidate maximum missing gap (s); total loss ≤1%');ax.set_ylabel('Admitted / 281 actual interrupted rides')
    ax.set_title('Recorded-interval estimates; boundaries still unproven',loc='left',fontsize=10)
    for ax in axes.flat:ax.spines[['top','right']].set_visible(False)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=2,fontsize=9)
    fig.suptitle('P4-01 controlled gap experiment — numerical recovery, not physiological validation')
    fig.savefig(out/'sauce-gap-comparison.png',dpi=150);plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-dir',type=Path,required=True)
    p.add_argument('--ftp-results',type=Path,required=True);p.add_argument('--report-dir',type=Path,required=True);p.add_argument('--plots',action='store_true');a=p.parse_args()
    summary,cases,result=summarize(a.input_dir,a.ftp_results)
    (a.report_dir/'sauce-comparison.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    lines=['# P4-01 controlled loss summary','',
        'Exact pinned Sauce functions on documented adapted inputs. These are numerical',
        'errors against complete-recording references, not physiological accuracy. Each',
        'loss length uses 3 placements × 24 rides per scope. Counts are available / cases.',
        'Full results, signed/absolute point errors and placement strata: [JSON](sauce-comparison.json).','',
        '| Reference scope | Lost s | Segment coverage | Segment median absolute % | Segment worst absolute % | Sauce coverage | Sauce median absolute % | Sauce worst absolute % |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for scope in ('strict_timer','complete_envelope'):
        for item in sorted((v for v in summary['comparisons'] if v['scope']==scope and v['gap_class']=='unexplained_loss'),key=lambda v:v['gap_length']):
            o=item['methods']['observed600'];s=item['methods']['sauce']
            lines.append(f"| {scope} | {item['gap_length']} | {o['available']}/{o['cases']} | {o['absolute_percent']['median']:.3f} | {o['absolute_percent']['max']:.3f} | {s['available']}/{s['cases']} | {s['absolute_percent']['median']:.3f} | {s['absolute_percent']['max']:.3f} |")
    lines+=['','A numerically available estimate is not evidence that missing watts were recovered.',
        'The 600-second method intentionally reports a partial subtotal. Comparing it with',
        'the full reference quantifies omitted contribution, not a claim its partial label is wrong.','']
    (a.report_dir/'sauce-errors.md').write_text('\n'.join(lines))
    if a.plots:plots(summary,cases,result,a.report_dir)
    print(json.dumps(dict(controlled=summary['controlled_cases'],actual=summary['actual_cases'],policies=summary['policies'],recent=summary['recent']),indent=2))


if __name__=='__main__':main()
