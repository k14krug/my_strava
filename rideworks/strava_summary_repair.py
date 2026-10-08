"""Owner-invoked P3-01 repair of at most eight established GPX/export rides.

No discovery, listing, streams, fuzzy matching or sync-checkpoint advancement.
Only allowlisted summary values survive the per-response transaction.
"""
import re
import sqlite3

from .history import presentation
from .performance import converge_performance
from .strava import AuthenticationError, SCOPE, TokenFile, refreshed_connection
from .strava_api import SyncError, activity_type, apply_observations, normalize


def validate_targets(store, targets):
    if not isinstance(targets,dict) or not 1<=len(targets)<=8:
        raise SyncError('Summary repair requires one to eight explicit established targets')
    if any(not isinstance(k,str) or not re.fullmatch(r'[1-9][0-9]{0,19}',k)
           or not isinstance(v,str) for k,v in targets.items()) or len(set(targets.values()))!=len(targets):
        raise SyncError('Invalid or duplicate summary repair target')
    for external, identity in targets.items():
        associated={r[0] for r in store.connection.execute('''
            SELECT activity_id FROM strava_export_sources WHERE external_id=?
            UNION SELECT activity_id FROM strava_api_activities WHERE external_id=?
            UNION SELECT activity_id FROM strava_api_sources WHERE external_id=?''',(external,external,external))}
        if associated!={identity}:
            raise SyncError('Summary repair target lacks an unambiguous established identity')
        snapshots=store.activity_history(identity)
        row=presentation(snapshots[0])
        kinds={e['source']['kind'] for e in row['sources']}
        if row['activity_type']!='Ride' or not {'strava_export','file_gpx'}<=kinds:
            raise SyncError('Summary repair is limited to established GPX/export Ride Activities')


def enrich_summaries(store, client, targets, *, now=None):
    """Sequential bounded repair; a failure keeps earlier committed summaries."""
    validate_targets(store,targets)  # Entire manifest checked before any HTTP request.
    report=dict(status='completed',scope=SCOPE,targets=len(targets),activity_requests=0,
                summaries_retained=0,usable_distances=0,new_observations=0,unchanged_observations=0)
    tokens=TokenFile(store.data_dir)
    requests_before=client.summary_requests
    with tokens.lock():
        try:
            current=tokens.read()
            checkpoint=store.connection.execute('SELECT athlete_id FROM strava_sync_state WHERE singleton=1').fetchone()
            if checkpoint and checkpoint[0]!=str(current['athlete_id']):
                raise SyncError('Connected Strava athlete differs from the stored checkpoint')
            current=refreshed_connection(tokens,client,now=now)
            for external in targets:
                payload=client.activity_summary(current['access_token'],external)
                if isinstance(payload,dict) and 'athlete' in payload:
                    if not isinstance(payload['athlete'],dict) or payload['athlete'].get('id')!=current['athlete_id']:
                        raise SyncError('Strava activity belongs to an unexpected athlete')
                values=normalize(payload)
                if str(values['id'])!=external or activity_type(values)!='Ride':
                    raise SyncError('Targeted response identity or classification differs from the authorized Ride')
                applied=apply_observations(store,[values],current['athlete_id'],None,established_targets=targets)
                report['summaries_retained']+=1
                for field in ('new_observations','unchanged_observations'):
                    report[field]+=applied[field]
                if values.get('distance') is None:
                    raise SyncError('Targeted summary has no usable distance; repair stopped')
                report['usable_distances']+=1
        except AuthenticationError as error:
            tokens.clear()
            report.update(status='stopped',error=str(error))
        except SyncError as error:
            report.update(status='stopped',error=str(error))
        except (OSError,sqlite3.Error):
            report.update(status='stopped',error='Local summary repair failed')
        # Earlier observations remain durable even on a later HTTP/persistence failure.
        report.update(converge_performance(store),rate_limits=dict(client.rate),
                      activity_requests=client.summary_requests-requests_before)
    return report
