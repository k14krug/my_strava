#!/usr/bin/env python3
"""Inspect only STRAVA-001's diagnostic FIT/TCX/GPX candidates.

Install the pinned research dependency with tools/requirements-strava-002.txt.
No activity streams, coordinates, source paths, or free-text CSV values are emitted.
"""

import argparse
import gzip
import hashlib
import json
import math
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

import inspect_strava_export as prior

SCHEMA_VERSION = 1
TOOL_VERSION = "1.0"
PUBLIC_XML_HOSTS = ("www.topografix.com", "www.garmin.com", "www.w3.org", "www.cluetrust.com")
SIGNALS = ("time", "gps", "altitude", "distance", "speed", "heart_rate", "cadence", "power", "temperature")
NUMERIC_SIGNALS = set(SIGNALS) - {"time", "gps"}


def safe_name(value):
    value = str(value or "")
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,79}", value):
        return value
    return "name-sha256:" + hashlib.sha256(value.encode("utf-8", "surrogatepass")).hexdigest()[:16]


def safe_label(value):
    return prior.safe_label(value)


def safe_namespace(uri):
    if any(uri.startswith("http://" + host + "/") or uri.startswith("https://" + host + "/")
           for host in PUBLIC_XML_HOSTS):
        return uri
    return "namespace-sha256:" + hashlib.sha256(uri.encode("utf-8")).hexdigest()[:16]


def local_name(tag):
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def numeric(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def rounded(value):
    return round(value, 3) if value is not None else None


def numeric_stats(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return None
    return {"count": len(values), "minimum": rounded(values[0]),
            "median": rounded(statistics.median(values)), "maximum": rounded(values[-1])}


def parse_time(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def timing_summary(timestamps, point_count):
    """Use source order; large gap means >max(30 s, 5x median positive delta)."""
    times = [stamp for stamp in timestamps if stamp is not None]
    deltas = []
    duplicate = 0
    backward = 0
    for previous, current in zip(times, times[1:]):
        try:
            seconds = (current - previous).total_seconds()
        except TypeError:
            backward += 1
            continue
        if seconds > 0:
            deltas.append(seconds)
        elif seconds == 0:
            duplicate += 1
        else:
            backward += 1
    positive = sorted(deltas)
    median = statistics.median(positive) if positive else None
    threshold = max(30.0, 5.0 * median) if median is not None else None
    common = None
    if positive:
        counts = Counter(positive)
        common = min(value for value, count in counts.items() if count == max(counts.values()))
    return {"point_count": point_count, "timestamped_points": len(times),
            "missing_or_invalid_timestamps": point_count - len(times),
            "first_timestamp": times[0].isoformat() if times else None,
            "last_timestamp": times[-1].isoformat() if times else None,
            "positive_delta_seconds": {"count": len(positive),
                                       "minimum": rounded(positive[0]) if positive else None,
                                       "median": rounded(median),
                                       "p90_nearest_rank": rounded(positive[math.ceil(.9 * len(positive)) - 1]) if positive else None,
                                       "maximum": rounded(positive[-1]) if positive else None,
                                       "common": rounded(common)},
            "duplicate_timestamps": duplicate, "backward_or_incompatible_timestamps": backward,
            "large_gap_threshold_seconds": rounded(threshold),
            "large_gap_count": sum(value > threshold for value in positive) if threshold is not None else 0,
            "large_gap_rule": "positive delta > max(30 seconds, 5 x median positive delta)"}


def signal_summary(point_count, values):
    result = {}
    for name in SIGNALS:
        items = values.get(name, [])
        result[name] = {"points_with_value": len(items), "point_count": point_count,
                        "coverage_fraction": rounded(len(items) / point_count) if point_count else None}
        if name in NUMERIC_SIGNALS:
            result[name]["values"] = numeric_stats(items)
    return result


def load_csv(source):
    csv_path = prior.locate_csv(source)
    original, columns, fields, rows, malformed = prior.read_csv(csv_path)
    if malformed:
        raise ValueError(f"activities.csv has {malformed} malformed-width rows")
    return original, columns, fields, rows


def row_value(row, fields, key, *, last=False):
    names = fields.get(key, [])
    sequence = reversed(names) if last else names
    for name in sequence:
        value = row[name].strip()
        if value:
            return value
    return None


def csv_summary(row, fields):
    """Keep only numeric/date/type and structural flags; never emit free text."""
    return {"activity_id": prior.safe_id(row_value(row, fields, "activity_id")),
            "date": prior.parse_date(row_value(row, fields, "date")),
            "activity_type": safe_label(row_value(row, fields, "activity_type")) if row_value(row, fields, "activity_type") else None,
            "elapsed_time_present": bool(row_value(row, fields, "elapsed_time")),
            "moving_time_present": bool(row_value(row, fields, "moving_time")),
            "distance_present": bool(row_value(row, fields, "distance")),
            "elevation_present": bool(row_value(row, fields, "elevation")),
            "heart_rate_present": bool(row_value(row, fields, "heart_rate")),
            "cadence_present": bool(row_value(row, fields, "cadence")),
            "power_present": bool(row_value(row, fields, "power")),
            "commute_flag": prior.classify_flag(row_value(row, fields, "commute"))
                            if fields.get("commute") else None,
            "from_upload_field_present": bool(row.get("From Upload", "").strip()),
            "gear_field_present": bool(row.get("Activity Gear", "").strip() or row.get("Bike", "").strip())}


def no_file_rows(rows, fields):
    if not fields.get("filename"):
        raise ValueError("activities.csv has no recognized Filename column")
    result = [csv_summary(row, fields) for row in rows
              if not row_value(row, fields, "filename")]
    return sorted(result, key=lambda row: (row["date"] or "", row["activity_id"] or ""))


def resolve_candidates(source, inventory, rows, fields):
    candidates = inventory.get("candidate_files")
    if not isinstance(candidates, list):
        raise ValueError("inventory.json has no candidate_files list")
    filename_key = fields.get("filename", [None])[0]
    id_key = fields.get("activity_id", [None])[0]
    if not filename_key or not id_key:
        raise ValueError("activities.csv needs Filename and Activity ID for candidate resolution")
    by_filename = defaultdict(list)
    for row in rows:
        by_filename[row[filename_key]].append(row)
    resolved, errors = [], []
    seen = set()
    for candidate in candidates:
        reference = candidate.get("file")
        activity_id = candidate.get("activity_id")
        if not isinstance(reference, str) or not re.fullmatch(r"activities/[0-9][0-9_-]*\.(?:fit|tcx|gpx)(?:\.gz)?", reference, re.I):
            errors.append({"activity_id": activity_id, "reason": "candidate path is not a safe, resolvable activity path"})
            continue
        relative = PurePosixPath(reference)
        if reference in seen:
            errors.append({"activity_id": activity_id, "reason": "duplicate candidate path"})
            continue
        seen.add(reference)
        path = source.joinpath(*relative.parts)
        if not path.is_file() or path.is_symlink() or source not in path.resolve().parents:
            errors.append({"activity_id": activity_id, "reason": "candidate file missing or unsafe"})
            continue
        matches = by_filename[reference]
        if len(matches) != 1 or matches[0][id_key].strip() != activity_id:
            errors.append({"activity_id": activity_id, "reason": "CSV filename/activity-ID association is not unique and exact"})
            continue
        resolved.append((candidate, path, matches[0]))
    return resolved, errors


def safe_unit(value):
    if value is None:
        return None
    value = str(value)
    return value if re.fullmatch(r"[A-Za-z0-9%°/_-]{1,24}", value) else "[withheld]"


def frame_values(frame):
    """Prefer a non-null decoded value when fitdecode expands a field twice."""
    values = {}
    for field in frame.fields:
        name = str(field.name)
        if field.value is not None and name not in values:
            values[name] = field.value
    return values


def first_value(values, *names):
    return next((values[name] for name in names if values.get(name) is not None), None)


def add_point_signal(values, name, value):
    if value is not None:
        values[name].append(value)


def fit_record_signals(decoded, values, timestamps):
    stamp = parse_time(decoded.get("timestamp"))
    timestamps.append(stamp)
    add_point_signal(values, "time", 1 if stamp else None)
    if decoded.get("position_lat") is not None and decoded.get("position_long") is not None:
        add_point_signal(values, "gps", 1)
    for signal, names in {
        "altitude": ("enhanced_altitude", "altitude"),
        "distance": ("distance",), "speed": ("enhanced_speed", "speed"),
        "heart_rate": ("heart_rate",), "cadence": ("cadence",),
        "power": ("power",), "temperature": ("temperature",),
    }.items():
        add_point_signal(values, signal, numeric(first_value(decoded, *names)))


def fit_message_summary(frames):
    """Summarize already decoded frames; enables tests without synthetic FIT bytes."""
    counts = Counter()
    fields = defaultdict(dict)
    values = defaultdict(list)
    timestamps = []
    sessions, laps, devices, field_descriptions = [], [], [], []
    event_types = Counter()
    summary_power_fields = 0
    definition_frames = 0
    for frame in frames:
        if getattr(frame, "frame_type", None) == "definition":
            definition_frames += 1
            continue
        if getattr(frame, "frame_type", None) != "data":
            continue
        message = safe_name(frame.name)
        counts[message] += 1
        seen_defined, seen_nonnull = set(), set()
        for field in frame.fields:
            name = safe_name(field.name_or_num if hasattr(field, "name_or_num") else field.name)
            number = getattr(field, "def_num", None)
            is_dev = bool(getattr(getattr(field, "field_def", None), "is_dev", False))
            key = (name, number, is_dev)
            if key not in fields[message]:
                fields[message][key] = {"name": name, "field_number": number,
                                        "developer_field": is_dev, "units": safe_unit(getattr(field, "units", None)),
                                        "messages_defining_field": 0, "messages_with_value": 0}
            if key not in seen_defined:
                fields[message][key]["messages_defining_field"] += 1
                seen_defined.add(key)
            if field.value is not None and key not in seen_nonnull:
                fields[message][key]["messages_with_value"] += 1
                seen_nonnull.add(key)
        decoded = frame_values(frame)
        if message == "record":
            fit_record_signals(decoded, values, timestamps)
        elif message == "session":
            sessions.append(decoded)
        elif message == "lap":
            laps.append(decoded)
        elif message in ("file_id", "device_info"):
            devices.append({"message": message,
                            "manufacturer": safe_label(str(decoded.get("manufacturer"))) if decoded.get("manufacturer") is not None else None,
                            "product_code": decoded.get("product") if isinstance(decoded.get("product"), int) else None,
                            "device_type": safe_label(decoded.get("device_type")) if isinstance(decoded.get("device_type"), str) else None,
                            "device_type_code": decoded.get("device_type") if isinstance(decoded.get("device_type"), int) else None,
                            "serial_number_present": decoded.get("serial_number") is not None})
        elif message == "event":
            event = safe_label(decoded.get("event")) if decoded.get("event") is not None else "[unknown]"
            kind = safe_label(decoded.get("event_type")) if decoded.get("event_type") is not None else "[unknown]"
            event_types[event + ":" + kind] += 1
        elif message == "field_description":
            field_descriptions.append({"field_name": safe_name(decoded.get("field_name")),
                                       "units": safe_unit(decoded.get("units")),
                                       "field_definition_number": decoded.get("field_definition_number")
                                       if isinstance(decoded.get("field_definition_number"), int) else None})
        if message in ("session", "lap"):
            summary_power_fields += sum(decoded.get(name) is not None for name in ("avg_power", "max_power", "normalized_power"))
    source_summary = {}
    if len(sessions) == 1:
        session = sessions[0]
        for label, names in {
            "elapsed_seconds": ("total_elapsed_time",),
            "timer_seconds": ("total_timer_time",),
            "distance_m": ("total_distance",),
            "elevation_gain_m": ("total_ascent",),
            "avg_heart_rate_bpm": ("avg_heart_rate",),
            "avg_cadence_rpm": ("avg_cadence",),
            "avg_power_watts": ("avg_power",),
            "max_power_watts": ("max_power",),
            "avg_temperature_c": ("avg_temperature",),
        }.items():
            number = numeric(first_value(session, *names))
            if number is not None:
                source_summary[label] = {"value": rounded(number), "basis": "FIT session " + names[0]}
    sport = safe_label(str(sessions[0].get("sport"))) if len(sessions) == 1 and sessions[0].get("sport") is not None else None
    sub_sport = safe_label(str(sessions[0].get("sub_sport"))) if len(sessions) == 1 and sessions[0].get("sub_sport") is not None else None
    message_fields = {}
    for message in sorted(fields):
        message_fields[message] = sorted(fields[message].values(),
                                         key=lambda item: (item["name"], item["field_number"] if item["field_number"] is not None else -1,
                                                           item["developer_field"]))
    return {"format_family": "FIT", "message_counts": dict(sorted(counts.items())),
            "definition_frame_count": definition_frames, "message_fields": message_fields,
            "point_count": counts["record"], "signals": signal_summary(counts["record"], values),
            "timing": timing_summary(timestamps, counts["record"]),
            "summary": source_summary, "session_count": counts["session"], "lap_count": counts["lap"],
            "event_type_counts": dict(sorted(event_types.items())),
            "device_clues": sorted(devices, key=lambda item: (item["message"], item["manufacturer"] or "", item["product_code"] or -1)),
            "developer_field_descriptions": sorted(field_descriptions, key=lambda item: item["field_name"]),
            "activity_sport": sport, "activity_sub_sport": sub_sport,
            "summary_power_field_count": summary_power_fields,
            "record_power_count": len(values["power"])}


def inspect_fit(path):
    try:
        import fitdecode
    except ImportError as exc:
        raise ValueError("fitdecode 0.11.0 is required; install tools/requirements-strava-002.txt in an isolated environment") from exc
    if fitdecode.__version__ != "0.11.0":
        raise ValueError(f"fitdecode 0.11.0 is required; found {fitdecode.__version__}")
    try:
        opener = gzip.open if path.name.lower().endswith(".gz") else open
        with opener(path, "rb") as stream:
            with fitdecode.FitReader(stream, check_crc=fitdecode.CrcCheck.RAISE,
                                     error_handling=fitdecode.ErrorHandling.RAISE) as reader:
                def frames():
                    for frame in reader:
                        if frame.frame_type == fitdecode.FIT_FRAME_DATA:
                            yield SimpleNamespace(frame_type="data", name=frame.name, fields=frame.fields)
                        elif frame.frame_type == fitdecode.FIT_FRAME_DEFINITION:
                            yield SimpleNamespace(frame_type="definition")
                return fit_message_summary(frames())
    except (OSError, EOFError, fitdecode.FitParseError) as exc:
        raise ValueError(f"strict FIT parsing failed: {type(exc).__name__}: {exc}") from exc


def xml_tag_name(tag, aliases):
    if tag.startswith("{"):
        uri, name = tag[1:].split("}", 1)
        return aliases[uri] + ":" + safe_name(name)
    return safe_name(tag)


def children_named(node, name):
    return [child for child in node if local_name(child.tag).lower() == name.lower()]


def descendants_named(node, name):
    return [child for child in node.iter() if child is not node and local_name(child.tag).lower() == name.lower()]


def child_text(node, name):
    children = children_named(node, name)
    return "".join(children[0].itertext()).strip() if children else None


def descendant_number(node, *names):
    for name in names:
        children = descendants_named(node, name)
        if children:
            value = numeric("".join(children[0].itertext()).strip())
            if value is not None:
                return value
    return None


def safe_vendor(value):
    if not value:
        return None
    label = str(value).strip()
    known = ("Garmin", "Strava", "Wahoo", "Zwift", "Polar", "Suunto", "TrainingPeaks", "Tacx")
    return label if label in known else "[withheld]"


def xml_point_signals(point, family, values, timestamps):
    if family == "GPX":
        stamp_text = child_text(point, "time")
        gps = numeric(point.attrib.get("lat")) is not None and numeric(point.attrib.get("lon")) is not None
    else:
        stamp_text = child_text(point, "Time")
        gps = descendant_number(point, "LatitudeDegrees") is not None and descendant_number(point, "LongitudeDegrees") is not None
    stamp = parse_time(stamp_text)
    timestamps.append(stamp)
    add_point_signal(values, "time", 1 if stamp else None)
    add_point_signal(values, "gps", 1 if gps else None)
    for signal, names in {
        "altitude": ("ele", "AltitudeMeters"),
        "distance": ("DistanceMeters", "distance"),
        "speed": ("Speed", "speed"),
        "heart_rate": ("HeartRateBpm", "hr", "heartrate"),
        "cadence": ("Cadence", "cad", "RunCadence"),
        "power": ("Watts", "power", "watts"),
        "temperature": ("atemp", "Temperature", "temp"),
    }.items():
        add_point_signal(values, signal, descendant_number(point, *names))


def inspect_xml(path, family):
    try:
        opener = gzip.open if path.name.lower().endswith(".gz") else open
        with opener(path, "rb") as stream:
            raw = stream.read()
        normalized = raw.lstrip(b" \t\r\n")
        leading_whitespace = len(raw) - len(normalized)
        root = ET.fromstring(normalized)
    except (OSError, EOFError, ET.ParseError) as exc:
        raise ValueError(f"{family} XML parsing failed: {type(exc).__name__}: {exc}") from exc
    uris = sorted({node.tag[1:].split("}", 1)[0] for node in root.iter() if node.tag.startswith("{")})
    aliases = {uri: "ns" + str(index + 1) for index, uri in enumerate(uris)}
    namespace_labels = {aliases[uri]: safe_namespace(uri) for uri in uris}
    node_counts = Counter(xml_tag_name(node.tag, aliases) for node in root.iter())
    points = [node for node in root.iter() if local_name(node.tag) == ("trkpt" if family == "GPX" else "Trackpoint")]
    point_fields = Counter()
    extension_tags = set()
    values = defaultdict(list)
    timestamps = []
    for point in points:
        fields = {xml_tag_name(node.tag, aliases) for node in point.iter() if node is not point}
        point_fields.update(fields)
        xml_point_signals(point, family, values, timestamps)
    for extension in (node for node in root.iter() if local_name(node.tag).lower() == "extensions"):
        extension_tags.update(xml_tag_name(node.tag, aliases) for node in extension.iter() if node is not extension)
    summary = {}
    summary_power_fields = 0
    sport = None
    if family == "TCX":
        activities = [node for node in root.iter() if local_name(node.tag) == "Activity"]
        if activities:
            sport = safe_label(activities[0].attrib.get("Sport")) if activities[0].attrib.get("Sport") else None
        laps = [node for node in root.iter() if local_name(node.tag) == "Lap"]
        elapsed = [numeric(child_text(lap, "TotalTimeSeconds")) for lap in laps]
        distances = [numeric(child_text(lap, "DistanceMeters")) for lap in laps]
        if laps and all(value is not None for value in elapsed):
            summary["elapsed_seconds"] = {"value": rounded(sum(elapsed)), "basis": "TCX sum of lap TotalTimeSeconds"}
        if laps and all(value is not None for value in distances):
            summary["distance_m"] = {"value": rounded(sum(distances)), "basis": "TCX sum of lap DistanceMeters"}
        if len(laps) == 1:
            for label, names, unit in (
                ("avg_heart_rate_bpm", ("AverageHeartRateBpm",), "TCX lap AverageHeartRateBpm"),
                ("avg_cadence_rpm", ("Cadence",), "TCX lap Cadence"),
                ("avg_power_watts", ("AvgWatts",), "TCX lap extension AvgWatts"),
                ("max_power_watts", ("MaxWatts",), "TCX lap extension MaxWatts"),
            ):
                number = descendant_number(laps[0], *names)
                if number is not None:
                    summary[label] = {"value": rounded(number), "basis": unit}
        for lap in laps:
            summary_power_fields += sum(descendant_number(lap, name) is not None for name in ("AvgWatts", "MaxWatts"))
        creators = [node for node in root.iter() if local_name(node.tag) == "Creator"]
        device_clues = {"creator_element_present": bool(creators),
                        "creator_label": safe_vendor(child_text(creators[0], "Name")) if creators else None}
    else:
        tracks = [node for node in root.iter() if local_name(node.tag) == "trk"]
        segments = [node for node in root.iter() if local_name(node.tag) == "trkseg"]
        laps = []
        device_clues = {"creator_attribute_present": "creator" in root.attrib,
                        "creator_label": safe_vendor(root.attrib.get("creator"))}
    return {"format_family": family, "xml_namespaces": namespace_labels,
            "xml_node_counts": dict(sorted(node_counts.items())),
            "point_field_coverage": dict(sorted(point_fields.items())),
            "extension_tag_names": sorted(extension_tags),
            "leading_xml_whitespace_bytes_removed": leading_whitespace,
            "point_count": len(points), "signals": signal_summary(len(points), values),
            "timing": timing_summary(timestamps, len(points)),
            "summary": summary, "lap_count": len(laps),
            "track_count": len(tracks) if family == "GPX" else len(activities),
            "segment_count": len(segments) if family == "GPX" else None,
            "activity_sport": sport, "device_clues": device_clues,
            "summary_power_field_count": summary_power_fields,
            "record_power_count": len(values["power"])}


def csv_number(row, columns, original_columns, names, *, last=False):
    matches = [(column, numeric(row[column])) for column, original in zip(columns, original_columns)
               if prior.normalized_header(original) in names and row[column].strip()]
    if not matches:
        return None, None
    column, value = matches[-1] if last else matches[0]
    return value, column


def compare_numeric(csv_value, file_value, *, absolute, relative, note, direct=True):
    result = {"csv_value": rounded(csv_value), "source_value": rounded(file_value), "note": note}
    if csv_value is None and file_value is None:
        result["status"] = "unavailable"
    elif csv_value is None:
        result["status"] = "file_only"
    elif file_value is None:
        result["status"] = "csv_only"
    elif not direct:
        result["status"] = "not_directly_comparable"
    else:
        tolerance = max(absolute, relative * max(abs(csv_value), abs(file_value)))
        result["absolute_difference"] = rounded(abs(csv_value - file_value))
        result["tolerance"] = {"absolute_floor": absolute, "relative_fraction": relative}
        result["status"] = ("both_present_apparently_consistent" if abs(csv_value - file_value) <= tolerance
                            else "both_present_materially_different")
    return result


def compare_presence(csv_present, file_present, *, comparable=False, note=""):
    if not csv_present and not file_present:
        status = "unavailable"
    elif csv_present and not file_present:
        status = "csv_only"
    elif file_present and not csv_present:
        status = "file_only"
    elif comparable:
        status = "both_present_apparently_consistent"
    else:
        status = "not_directly_comparable"
    return {"status": status, "csv_present": bool(csv_present),
            "source_present": bool(file_present), "note": note}


def comparisons(row, original_columns, columns, fields, source):
    summary = source["summary"]
    def source_number(key):
        return summary.get(key, {}).get("value")
    result = {}
    csv_elapsed, _ = csv_number(row, columns, original_columns, {"elapsed time"}, last=True)
    result["elapsed_seconds"] = compare_numeric(
        csv_elapsed, source_number("elapsed_seconds"), absolute=5, relative=.01,
        note="CSV Elapsed Time is numeric but unit is not labeled; seconds are inferred from its scale and source overlap."
             " FIT session elapsed and TCX lap elapsed can use different boundaries.")
    csv_moving, _ = csv_number(row, columns, original_columns, {"moving time"})
    result["moving_vs_timer_seconds"] = compare_numeric(
        csv_moving, source_number("timer_seconds"), absolute=0, relative=0, direct=False,
        note="Strava moving time and FIT timer time need not share a definition.")
    distances = [(column, numeric(row[column])) for column, original in zip(columns, original_columns)
                 if prior.normalized_header(original) == "distance" and row[column].strip()]
    csv_distance = distances[-1][1] if distances else None
    scale_supported = (len(distances) >= 2 and distances[0][1] not in (None, 0)
                       and csv_distance is not None and 900 <= csv_distance / distances[0][1] <= 1100)
    result["distance_m"] = compare_numeric(
        csv_distance, source_number("distance_m"), absolute=100, relative=.01, direct=scale_supported,
        note="The last duplicate CSV Distance is treated as metre-like only where it is about 1000x the first;"
             " this is a row-level inference, not a documented export contract.")
    for key, csv_names, source_key, absolute, relative, note in (
        ("elevation_gain_m", {"elevation gain", "total elevation gain"}, "elevation_gain_m", 10, .05,
         "CSV elevation may be corrected differently from source ascent."),
        ("average_heart_rate_bpm", {"average heart rate", "average heartrate"}, "avg_heart_rate_bpm", 2, .02,
         "CSV and source averages may use different samples or moving-time rules."),
        ("average_cadence_rpm", {"average cadence"}, "avg_cadence_rpm", 2, .03,
         "CSV and source cadence averages may exclude different samples."),
        ("average_power_watts", {"average watts", "average power"}, "avg_power_watts", 5, .05,
         "A numeric power match does not establish measured-power provenance."),
    ):
        csv_value, _ = csv_number(row, columns, original_columns, csv_names)
        result[key] = compare_numeric(csv_value, source_number(source_key),
                                      absolute=absolute, relative=relative, note=note)
    csv_weather, _ = csv_number(row, columns, original_columns, {"weather temperature"})
    result["weather_vs_source_temperature_c"] = compare_numeric(
        csv_weather, source_number("avg_temperature_c"), absolute=0, relative=0, direct=False,
        note="CSV weather temperature is not a source sensor temperature.")
    csv_type = row_value(row, fields, "activity_type")
    file_type = source.get("activity_sport")
    result["activity_type"] = compare_presence(
        csv_type, file_type, comparable=bool(csv_type and file_type and csv_type.lower() == file_type.lower()),
        note="Source sport and Strava Activity Type may use different vocabularies or classification rules.")
    result["date_time"] = compare_presence(
        row_value(row, fields, "date"), source["timing"]["first_timestamp"],
        note="CSV Activity Date lacks an explicit timezone; source stream timestamps are not directly aligned.")
    clues = source.get("device_clues")
    device_present = (bool(clues) if isinstance(clues, list)
                      else any(value for key, value in (clues or {}).items() if key.endswith("present") or key == "creator_label"))
    result["device_metadata"] = compare_presence(
        False, device_present, note="CSV gear/bike fields are not device or sensor identifiers.")
    result["filename"] = {"status": "both_present_apparently_consistent", "csv_present": True,
                          "source_present": True, "note": "Exact relative Filename association, not stream identity proof."}
    return result


def power_evidence(row, fields, source):
    csv_columns = [column for column in fields.get("power", []) if row[column].strip()]
    return {"record_level_source_power": {"present": source["record_power_count"] > 0,
                                           "points_with_value": source["record_power_count"]},
            "source_summary_power": {"present": source["summary_power_field_count"] > 0,
                                     "field_count": source["summary_power_field_count"]},
            "csv_power_metadata": {"present": bool(csv_columns), "columns_with_values": csv_columns},
            "provenance_classification": "unknown",
            "provenance_note": "Power values or streams alone do not identify measured, calculated, or estimated origin."}


def inspect_export(source, inventory_path):
    source = Path(source).expanduser().resolve()
    if not source.is_dir():
        raise ValueError("source must be an existing extracted-export directory")
    inventory = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    original, columns, fields, rows = load_csv(source)
    resolved, resolution_errors = resolve_candidates(source, inventory, rows, fields)
    missing_rows = no_file_rows(rows, fields)
    report = {"schema_version": SCHEMA_VERSION, "tool_version": TOOL_VERSION,
              "source": "local extracted Strava export (path withheld)",
              "candidate_source": "STRAVA-001 inventory.json",
              "candidate_count": len(inventory["candidate_files"]),
              "resolved_candidate_count": len(resolved),
              "resolution_errors": resolution_errors,
              "fit_parser": {"name": "fitdecode", "version": "0.11.0", "crc_check": "raise",
                             "error_handling": "raise"},
              "xml_parser": "Python standard-library ElementTree",
              "candidate_samples": [], "no_file_rows": missing_rows,
              "no_file_row_count": len(missing_rows), "warnings": []}
    if resolution_errors:
        report["status"] = "resolution_failed"
        return report
    for candidate, path, row in resolved:
        file_format = candidate["format"]
        try:
            if file_format in (".fit", ".fit.gz"):
                source_evidence = inspect_fit(path)
            elif file_format in (".tcx", ".tcx.gz"):
                source_evidence = inspect_xml(path, "TCX")
            elif file_format in (".gpx", ".gpx.gz"):
                source_evidence = inspect_xml(path, "GPX")
            else:
                raise ValueError("unsupported candidate format")
        except ValueError as exc:
            report["resolution_errors"].append({"activity_id": candidate["activity_id"],
                                                "reason": f"candidate parsing failed: {exc}"})
            report["status"] = "candidate_parse_failed"
            return report
        report["candidate_samples"].append({"activity_id": candidate["activity_id"],
                                            "file": candidate["file"], "format": file_format,
                                            "selection_reasons": candidate["reasons"],
                                            "csv": csv_summary(row, fields),
                                            "source_evidence": source_evidence,
                                            "csv_source_comparison": comparisons(row, original, columns, fields,
                                                                                 source_evidence),
                                            "power_evidence": power_evidence(row, fields, source_evidence)})
        if source_evidence.get("leading_xml_whitespace_bytes_removed"):
            report["warnings"].append(
                f"Activity {candidate['activity_id']}: ignored {source_evidence['leading_xml_whitespace_bytes_removed']} leading XML whitespace bytes before parsing; source file unchanged.")
    report["candidate_samples"].sort(key=lambda sample: (sample["activity_id"], sample["file"]))
    report["status"] = "complete"
    return report


def aggregate(report):
    formats = defaultdict(lambda: {"samples": 0, "points": 0, "lap_count": 0,
                                   "session_count": 0, "device_clue_candidates": 0,
                                   "signal_candidates": Counter(), "message_names": set(),
                                   "developer_field_names": set(),
                                   "extension_tags": set(), "namespace_labels": set()})
    comparisons_by_status = Counter()
    differing = []
    power = Counter()
    for sample in report["candidate_samples"]:
        source = sample["source_evidence"]
        fmt = source["format_family"]
        group = formats[fmt]
        group["samples"] += 1
        group["points"] += source["point_count"]
        group["lap_count"] += source["lap_count"]
        group["session_count"] += source.get("session_count", 0)
        clues = source.get("device_clues")
        if clues and (isinstance(clues, list) or any(value for value in clues.values())):
            group["device_clue_candidates"] += 1
        group["developer_field_names"].update(item["field_name"] for item in source.get("developer_field_descriptions", []))
        for signal, values in source["signals"].items():
            if values["points_with_value"]:
                group["signal_candidates"][signal] += 1
        group["message_names"].update(source.get("message_counts", {}))
        group["extension_tags"].update(source.get("extension_tag_names", []))
        group["namespace_labels"].update(source.get("xml_namespaces", {}).values())
        for field, comparison in sample["csv_source_comparison"].items():
            comparisons_by_status[comparison["status"]] += 1
            if comparison["status"] == "both_present_materially_different":
                differing.append({"activity_id": sample["activity_id"], "field": field,
                                  "csv_value": comparison.get("csv_value"),
                                  "source_value": comparison.get("source_value")})
        evidence = sample["power_evidence"]
        power["record_source"] += evidence["record_level_source_power"]["present"]
        power["summary_source"] += evidence["source_summary_power"]["present"]
        power["csv_metadata"] += evidence["csv_power_metadata"]["present"]
    return {"formats": {fmt: {"samples": group["samples"], "points": group["points"],
                               "signal_candidates": dict(sorted(group["signal_candidates"].items())),
                               "lap_count": group["lap_count"], "session_count": group["session_count"],
                               "device_clue_candidates": group["device_clue_candidates"],
                               "message_names": sorted(group["message_names"]),
                               "developer_field_names": sorted(group["developer_field_names"]),
                               "extension_tags": sorted(group["extension_tags"]),
                               "namespace_labels": sorted(group["namespace_labels"])}
                        for fmt, group in sorted(formats.items())},
            "comparison_status_counts": dict(sorted(comparisons_by_status.items())),
            "material_numeric_differences": sorted(differing, key=lambda item: (item["activity_id"], item["field"])),
            "power_candidate_counts": dict(sorted(power.items())),
            "no_file_by_year": dict(sorted(Counter(row["date"][:4] for row in report["no_file_rows"] if row["date"]).items())),
            "no_file_by_activity_type": dict(sorted(Counter(row["activity_type"] or "unknown" for row in report["no_file_rows"]).items()))}


def markdown(report):
    lines = ["# STRAVA-002 sample inspection", "",
             "Diagnostic evidence from STRAVA-001 candidates. No raw streams, coordinates, activity names, or absolute source paths are included.", "",
             "## Candidate resolution", "",
             f"- Inventory candidates: {report['candidate_count']}",
             f"- Resolved and parsed: {len(report['candidate_samples'])}",
             f"- Status: {report['status']}"]
    for error in report["resolution_errors"]:
        lines.append(f"- Activity {error['activity_id'] or 'unknown'}: {error['reason']}")
    if report["status"] != "complete":
        return "\n".join(lines + ["", "Inspection stopped before a complete report.", ""])
    summary = report["aggregate"]
    lines += ["", "## Format and signal evidence", "",
              "| Format | Samples | Points | Candidate files with signals |",
              "| --- | ---: | ---: | --- |"]
    for fmt, group in summary["formats"].items():
        signal_text = ", ".join(f"{name} {count}" for name, count in group["signal_candidates"].items())
        lines.append(f"| {fmt} | {group['samples']} | {group['points']} | {signal_text or 'none'} |")
    fit_group = summary["formats"].get("FIT", {})
    lines += ["", "FIT message names seen: " + ", ".join(fit_group.get("message_names", [])) + ".",
              f"FIT sessions/laps: {fit_group.get('session_count', 0)}/{fit_group.get('lap_count', 0)}; "
              f"files with device clues: {fit_group.get('device_clue_candidates', 0)}.",
              "FIT developer field descriptions: " + (", ".join(fit_group.get("developer_field_names", [])) or "none") + ".", ""]
    relevant_extensions = {"hr", "cad", "atemp", "power", "watts", "avgwatts", "maxwatts", "speed",
                           "trackpointextension", "tpx", "lx"}
    for fmt in ("TCX", "GPX"):
        group = summary["formats"].get(fmt)
        if group:
            relevant = [tag for tag in group["extension_tags"]
                        if tag.rsplit(":", 1)[-1].lower() in relevant_extensions]
            lines.append(f"- {fmt}: {group['lap_count']} laps; {len(group['extension_tags'])} extension tag names "
                         f"({', '.join(relevant) or 'no common signal tags'}); full names in JSON.")
            lines.append(f"- {fmt} XML namespaces encountered: {len(group['namespace_labels'])}; labels in JSON.")
    lines += ["", "## Candidate-level evidence", "",
              "Signal abbreviations: G GPS, H heart rate, C cadence, P power, T temperature. Counts are points with a value.", "",
              "| Activity ID | Format | Points | G/H/C/P/T | Median delta (s) | Large gaps | Power source / CSV |",
              "| --- | --- | ---: | --- | ---: | ---: | --- |"]
    for sample in report["candidate_samples"]:
        source = sample["source_evidence"]
        signals = source["signals"]
        selected = "/".join(str(signals[name]["points_with_value"])
                            for name in ("gps", "heart_rate", "cadence", "power", "temperature"))
        power = sample["power_evidence"]
        powers = (f"record {int(power['record_level_source_power']['present'])}, "
                  f"summary {int(power['source_summary_power']['present'])}, "
                  f"CSV {int(power['csv_power_metadata']['present'])}")
        delta = source["timing"]["positive_delta_seconds"]["median"]
        lines.append(f"| {sample['activity_id']} | {sample['format']} | {source['point_count']} | {selected} | "
                     f"{delta if delta is not None else 'n/a'} | {source['timing']['large_gap_count']} | {powers} |")
    lines += ["", "The full per-message field counts, XML tag/extension names, signal coverage, timing distributions,"
              " and source summary values are in `sample_inspection.json`.", "",
              "## CSV versus file", "",
              "Comparison status counts (across candidate-field pairs):"]
    for status, count in summary["comparison_status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines += ["", "Numeric comparisons use max(absolute floor, relative fraction): elapsed 5 s/1%, "
              "distance 100 m/1%, elevation 10 m/5%, heart rate 2 bpm/2%, cadence 2 rpm/3%, power 5 W/5%."
              " CSV elapsed seconds and the last duplicate Distance as metre-like are explicit inferences from observed numeric scales;"
              " apparent agreement does not prove equivalent definitions.", ""]
    if summary["material_numeric_differences"]:
        lines.append(f"- {len(summary['material_numeric_differences'])} candidate-field comparisons exceed those tolerances; numeric differences do not establish why values differ:")
        for item in summary["material_numeric_differences"]:
            lines.append(f"  - Activity {item['activity_id']} {item['field']}: CSV {item['csv_value']}, source {item['source_value']}.")
    else:
        lines.append("- No directly compared candidate-field values exceeded the stated tolerances.")
    lines += ["", "## Power provenance", "",
              f"- Candidate files with record-level source power: {summary['power_candidate_counts'].get('record_source', 0)}",
              f"- Candidate files with source summary power: {summary['power_candidate_counts'].get('summary_source', 0)}",
              f"- Candidate rows with Strava CSV power metadata: {summary['power_candidate_counts'].get('csv_metadata', 0)}",
              "- Provenance classification remains `unknown` for every candidate: these values do not identify a measured, calculated, or estimated origin.", "",
              "## CSV rows without a filename", "",
              f"{report['no_file_row_count']} rows; years: {summary['no_file_by_year']}; types: {summary['no_file_by_activity_type']}.", "",
              "| Activity ID | Date | Type | Elapsed / distance / HR / cadence / power present |",
              "| --- | --- | --- | --- |"]
    for row in report["no_file_rows"]:
        flags = "/".join("Y" if row[key] else "N" for key in
                         ("elapsed_time_present", "distance_present", "heart_rate_present",
                          "cadence_present", "power_present"))
        lines.append(f"| {row['activity_id'] or 'unknown'} | {row['date'] or 'unknown'} | {row['activity_type'] or 'unknown'} | {flags} |")
    upload_count = sum(row["from_upload_field_present"] for row in report["no_file_rows"])
    gear_count = sum(row["gear_field_present"] for row in report["no_file_rows"])
    lines += ["", f"Structural flags among those rows: From Upload field populated in {upload_count}; gear field populated in {gear_count}.",
              "The missing filename is observed; the cause is not established.", "",
              "## Limits and next questions", "",
              "- This is a deliberately diverse sample of 23 files, not a whole-history prevalence estimate.",
              "- FIT was decoded with `fitdecode==0.11.0` using strict CRC/error handling; TCX/GPX used ElementTree.",
              "- GPS coordinates, raw points, serial numbers, route names, and CSV free text were excluded.",
              "- CSV Activity Date lacks a timezone; source timestamps and CSV dates were not aligned as instants.",
              "- CSV weather temperature is not directly comparable with a source temperature sensor.",
              "- Source power fields do not by themselves establish power provenance.",
              "- Position fields do not prove physical GPS capture, especially in virtual rides."]
    for warning in report["warnings"]:
        lines.append("- " + warning)
    lines += ["- Which file-only signals and developer fields merit a targeted next experiment?",
              "- What evidence explains the CSV rows without activity-file references?", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="root of an already extracted Strava export")
    parser.add_argument("inventory", help="STRAVA-001 inventory.json")
    parser.add_argument("--output-dir", default="reports/STRAVA-002",
                        help="output directory (default: reports/STRAVA-002)")
    args = parser.parse_args(argv)
    try:
        report = inspect_export(args.source, args.inventory)
        if report["status"] == "complete":
            report["aggregate"] = aggregate(report)
        output = Path(args.output_dir).expanduser().resolve()
        source = Path(args.source).expanduser().resolve()
        if output == source or source in output.parents:
            raise ValueError("output directory must be outside the extracted export")
        output.mkdir(parents=True, exist_ok=True)
        (output / "sample_inspection.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        (output / "sample_inspection.md").write_text(markdown(report), encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"sample inspection error: {exc}\n")
    print(f"Wrote {output / 'sample_inspection.json'} and {output / 'sample_inspection.md'}")
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    sys.exit(main())
