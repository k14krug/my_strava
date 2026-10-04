"""Bounded TCX/GPX source extraction, without signal or timing repair.

Only qualified known extension fields are mapped. Unknown extensions remain in
immutable originals. GPX's observed unqualified power and TrackPointExtension
hr dialect is explicitly supported as source evidence, with origin unknown.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zlib

from .errors import RideWorksError
from .fit import Session, Record, Lap, ParsedFit

MAPPING_VERSION = 'xml-activity-v1'
PARSER_VERSION = f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
TCX = 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
GPX = {'http://www.topografix.com/GPX/1/1', 'http://www.topografix.com/GPX/1/0', ''}
AE = 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'
TP = 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'


@dataclass(frozen=True)
class XMLExtraction:
    content_format: str
    parsed: ParsedFit
    context: dict


def _name(tag):
    if tag.startswith('{'):
        namespace, local = tag[1:].split('}', 1)
        return namespace, local
    return '', tag


def _tag(ns, local):
    return f'{{{ns}}}{local}' if ns else local


def _text(node, tag):
    values = [child.text.strip() for child in node.findall(tag) if child.text and child.text.strip()]
    if len(set(values)) > 1:
        raise RideWorksError('Conflicting XML source fields')
    return values[0] if values else None


def _number(value, *, integer=False):
    if value is None:
        return None
    try:
        result = float(value)
        if not math.isfinite(result) or result < 0 or (integer and not result.is_integer()):
            raise ValueError
        return int(result) if integer else result
    except ValueError as exc:
        raise RideWorksError('Invalid XML numeric source field') from exc


def _timestamp(value):
    if value is None or not value.strip():
        return None
    try:
        text = value.strip().replace('Z', '+00:00')
        try:
            stamp = datetime.fromisoformat(text)
        except ValueError:
            # Python 3.10 fromisoformat accepts only 3/6 fractional digits.
            # strptime %f accepts 1–6 digits exactly: .12 seconds remains .12,
            # with no rounding, timing repair or guessed offset.
            try:
                stamp = datetime.strptime(text, '%Y-%m-%dT%H:%M:%S.%f%z')
            except ValueError:
                stamp = datetime.strptime(text, '%Y-%m-%dT%H:%M:%S.%f')
        # A timestamp without offset remains offset-unknown; do not guess UTC.
        return stamp.astimezone(timezone.utc).isoformat() if stamp.tzinfo else stamp.isoformat()
    except ValueError as exc:
        raise RideWorksError('Invalid XML source timestamp') from exc


def _extension_number(node, tags):
    values = [_number(child.text, integer=True) for child in node.iter()
              if child.tag in tags and child.text and child.text.strip()]
    if len(set(values)) > 1:
        raise RideWorksError('Conflicting XML signal fields')
    return values[0] if values else None


def decode_xml(path: Path, packaging: str) -> XMLExtraction:
    opener = gzip.open if packaging == 'gzip' else open
    try:
        with opener(path, 'rb') as stream:
            payload = stream.read()
        # Known TCX artifacts have whitespace before their XML declaration.
        # Only the transient parser input is stripped; originals are unchanged.
        if b'<!DOCTYPE' in payload.upper() or b'<!ENTITY' in payload.upper():
            raise RideWorksError('XML DTD/entity declarations are unsupported')
        root = ET.fromstring(payload.lstrip())
    except (OSError, EOFError, zlib.error, ET.ParseError) as exc:
        raise RideWorksError('Invalid XML activity artifact') from exc
    namespace, local = _name(root.tag)
    if local == 'gpx' and namespace in GPX:
        return _gpx(root, namespace)
    if local == 'TrainingCenterDatabase' and namespace == TCX:
        return _tcx(root)
    raise RideWorksError('Unsupported XML activity format/namespace')


def _gpx(root, ns):
    tracks = root.findall(_tag(ns, 'trk'))
    if len(tracks) != 1:
        raise RideWorksError('Exactly one GPX track is supported')
    track = tracks[0]
    records, segments = [], []
    power_tags = {_tag(ns, 'power'), 'power'}
    hr_tags = {_tag(TP, 'hr'), _tag('TrackPointExtension', 'hr')}
    for segment in track.findall(_tag(ns, 'trkseg')):
        segments.append(len(records))
        for point in segment.findall(_tag(ns, 'trkpt')):
            i = len(records)
            records.append(Record(i, i, _timestamp(_text(point, _tag(ns, 'time'))),
                                  _extension_number(point, power_tags),
                                  _extension_number(point, hr_tags)))
    # Track type is source text, not an inferred sport classification. No
    # distance/time/power summary is manufactured from points or private tags.
    session = Session(None, None, _text(track, _tag(ns, 'type')), None,
                      *([None] * 9))
    return XMLExtraction('GPX', ParsedFit(session, records, [], []),
                         dict(segment_start_record_indexes=segments,
                              timestamp_policy='explicit offsets to UTC; absent offsets unknown',
                              summary_policy='unknown/private GPX summary extensions not normalized'))


def _tcx(root):
    activities = root.findall(f'{_tag(TCX, "Activities")}/{_tag(TCX, "Activity")}')
    if len(activities) != 1:
        raise RideWorksError('Exactly one TCX Activity is supported')
    activity = activities[0]
    records, laps, summaries, segments = [], [], [], []
    for lap_index, lap in enumerate(activity.findall(_tag(TCX, 'Lap'))):
        start = _timestamp(lap.get('StartTime'))
        # Keep TCX TotalTimeSeconds in its source field; do not equate it with
        # FIT elapsed/timer time, or aggregate laps into a fabricated summary.
        values = dict(start_time=start,
                      total_time_seconds=_number(_text(lap, _tag(TCX, 'TotalTimeSeconds'))),
                      distance_m=_number(_text(lap, _tag(TCX, 'DistanceMeters'))),
                      avg_heart_rate=_number(_text(lap, f'{_tag(TCX, "AverageHeartRateBpm")}/{_tag(TCX, "Value")}'), integer=True),
                      max_heart_rate=_number(_text(lap, f'{_tag(TCX, "MaximumHeartRateBpm")}/{_tag(TCX, "Value")}'), integer=True),
                      avg_power=_extension_number(lap.find(_tag(TCX, 'Extensions')), {_tag(AE, 'AvgWatts')}) if lap.find(_tag(TCX, 'Extensions')) is not None else None,
                      max_power=_extension_number(lap.find(_tag(TCX, 'Extensions')), {_tag(AE, 'MaxWatts')}) if lap.find(_tag(TCX, 'Extensions')) is not None else None)
        summaries.append(values)
        laps.append(Lap(lap_index, start, None, None, None))
        for track in lap.findall(_tag(TCX, 'Track')):
            segments.append(len(records))
            for point in track.findall(_tag(TCX, 'Trackpoint')):
                i = len(records)
                records.append(Record(i, i, _timestamp(_text(point, _tag(TCX, 'Time'))),
                                      _extension_number(point, {_tag(AE, 'Watts')}),
                                      _number(_text(point, f'{_tag(TCX, "HeartRateBpm")}/{_tag(TCX, "Value")}'), integer=True)))
    session = Session(_timestamp(_text(activity, _tag(TCX, 'Id'))), None,
                      activity.get('Sport'), None, *([None] * 9))
    return XMLExtraction('TCX', ParsedFit(session, records, laps, []),
                         dict(lap_summaries=summaries, segment_start_record_indexes=segments,
                              timestamp_policy='explicit offsets to UTC; absent offsets unknown'))
