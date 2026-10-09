#!/usr/bin/env python3
"""Independent recomputation of published P4-01 error/coverage summaries."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.verify_sauce_gaps import close


def verify(root,report):
    summary=json.loads(report.read_text());cases=json.loads((root/'cases-private.json').read_text())
    results={r['key']:r for r in map(json.loads,(root/'sauce-private.jsonl').open())}
    checks=0
    for group in summary['comparisons']:
        rows=[c for c in cases if c['scope']==group['scope'] and c['gap_class']==group['gap_class'] and c['gap_length']==group['gap_length']]
        for name,stats in group['methods'].items():
            deltas=[];percents=[]
            for c in rows:
                value=c['observed']['stress'] if name=='observed600' else c['reference'] if name=='strict' and c['strict_available'] else None if name=='strict' else results[c['key']][name]['stress']
                if value is None:continue
                d=Decimal(str(value))-Decimal(str(c['reference']));deltas.append(d)
                if c['reference']>0:percents.append(d/Decimal(str(c['reference']))*100)
            assert stats['cases']==len(rows) and stats['available']==len(deltas) and stats['unavailable']==len(rows)-len(deltas)
            for label,values in [('signed_points',deltas),('absolute_points',list(map(abs,deltas))),('signed_percent',percents),('absolute_percent',list(map(abs,percents)))]:
                actual=stats[label];assert actual['n']==len(values)
                close(actual['median'],statistics.median(values) if values else None)
                close(actual['min'],min(values) if values else None);close(actual['max'],max(values) if values else None)
                if values:
                    ordered=sorted(values);position=Decimal(len(values)-1)*Decimal('.95');i=int(position)
                    p95=ordered[i]+(ordered[min(i+1,len(values)-1)]-ordered[i])*(position-i)
                else:p95=None
                close(actual['p95'],p95);checks+=1
    controlled=[c for c in cases if c['scope']!='actual_unknown' and c['gap_class']!='none']
    actual=[c for c in cases if c['gap_class']=='actual_interrupted']
    for policy in summary['policies']:
        limit=policy['max_missing_seconds']
        admitted=[c for c in controlled if c['gap_class'] not in ('boundary_loss','proven_pause') and c['gap_length']<=limit and len(c['removed_indices'])*100<=c['original_seconds']]
        actual_admitted=[c for c in actual if c['max_missing_gap']<=limit and c['missing_interior_seconds']*100<=c['span'] and not c['known_pause_count'] and not c['excluded_native_rows']]
        assert policy['controlled']['available']==len(admitted)
        assert policy['actual_interrupted_admitted']==len(actual_admitted)
    for n,window in summary['recent'].items():
        from datetime import date,timedelta
        start=str(date(2026,10,8)-timedelta(days=int(n)-1))
        group=[c for c in cases if c['scope']=='actual_unknown' and start<=c['day']<='2026-10-08']
        assert window['contributors']==len(group)
        close(window['sauce_experiment_subtotal'],sum(Decimal(str(results[c['key']]['sauce']['stress'])) for c in group))
        close(window['observed600_subtotal'],sum(Decimal(str(c['observed']['stress'])) for c in group))
        assert sum(window['candidate_classes'].values())==len(group)
    return dict(published_distribution_checks=checks,policy_grids_verified=4,recent_windows_verified=2)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=verify(a.input_dir,a.report);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
