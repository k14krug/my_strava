#!/usr/bin/env python3
"""Census an extracted Strava export without retaining or reporting activity streams.

Requires the scoped STRAVA-002 fitdecode dependency. Source files are read only.
"""

import argparse
import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import inspect_activity_samples as samples
import inspect_strava_export as prior

SCHEMA_VERSION = 1
TOOL_VERSION = "1.0"
SOURCE_SIGNALS = samples.SIGNALS
SAFE_REFERENCE = re.compile(r"activities/[0-9][0-9_-]*\.(?:fit|tcx|gpx)(?:\.gz)?", re.I)
CYCLING = ("Ride", "Virtual Ride")


def label(row, fields, key):
    return samples.row_value(row, fields, key)


def cohort(activity_type):
    return activity_type if activity_type in CYCLING else "Other"


def source_flags(evidence):
    return {name: evidence["signals"][name]["points_with_value"] > 0 for name in SOURCE_SIGNALS}


def combination_flags(flags, record_power, csv_power):
    """Evidence combinations; Activity Type is a label, not physical modality."""
    return {
        "source_record_power": record_power,
        "no_source_record_power": not record_power,
        "heart_rate_without_source_record_power": flags["heart_rate"] and not record_power,
        "position_altitude_without_source_record_power": flags["gps"] and flags["altitude"] and not record_power,
        "position_altitude_heart_rate_without_source_record_power": flags["gps"] and flags["altitude"] and flags["heart_rate"] and not record_power,
        "cadence_without_source_record_power": flags["cadence"] and not record_power,
        "csv_power_without_source_record_power": csv_power and not record_power,
    }


def power_key(record, summary, csv):
    return f"record={int(record)},summary={int(summary)},csv={int(csv)}"


def build_rows(source):
    """Validate the exact CSV population before parsing any activity file."""
    _original, _columns, fields, rows = samples.load_csv(source)
    if not fields.get("filename") or not fields.get("activity_id") or not fields.get("date"):
        raise ValueError("CSV needs Filename, Activity ID, and Activity Date columns")
    refs = Counter(label(row, fields, "filename") for row in rows if label(row, fields, "filename"))
    ids = Counter(label(row, fields, "activity_id") for row in rows)
    if any(count != 1 for count in refs.values()) or any(count != 1 for count in ids.values()):
        raise ValueError("CSV has duplicate filename references or activity IDs")
    prepared = []
    for row in rows:
        activity_id = prior.safe_id(label(row, fields, "activity_id"))
        if not activity_id:
            raise ValueError("CSV contains an unsafe or missing activity ID")
        date = prior.parse_date(label(row, fields, "date"))
        if label(row, fields, "date") and not date:
            raise ValueError("CSV contains an unparseable activity date")
        reference = label(row, fields, "filename")
        if reference and not SAFE_REFERENCE.fullmatch(reference):
            raise ValueError(f"unsafe or unsupported activity reference for activity {activity_id}")
        activity_type = prior.safe_label(label(row, fields, "activity_type")) if label(row, fields, "activity_type") else "[missing]"
        prepared.append({"id": activity_id, "date": date, "year": date[:4] if date else "[unknown]",
                         "type": activity_type, "cohort": cohort(activity_type), "reference": reference,
                         "format": prior.extension(reference) if reference else "[no file]",
                         "csv_power": any(row[column].strip() for column in fields["power"]),
                         "status": "no_file" if not reference else "pending"})
    return sorted(prepared, key=lambda item: (item["year"], item["id"])), fields


def verify_population(prepared, inventory_path):
    if inventory_path is None:
        return
    inventory = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    expected = inventory["associations"]
    actual = (len(prepared), sum(bool(row["reference"]) for row in prepared),
              sum(not row["reference"] for row in prepared))
    baseline = (inventory["csv"]["row_count"], expected["exact_matched_activity_file_rows"],
                expected["rows_without_reference"])
    if actual != baseline:
        raise ValueError(f"source population {actual} differs from STRAVA-001 {baseline}; stop before census")


def safe_path(source, reference):
    relative = PurePosixPath(reference)
    path = source.joinpath(*relative.parts)
    if path.is_symlink() or not path.is_file() or source not in path.resolve().parents:
        return None
    return path


def xml_prevalence_name(name, namespaces):
    prefix, separator, local = name.partition(":")
    if separator and prefix in namespaces:
        return namespaces[prefix] + ":" + local
    return name


def structural(evidence):
    if evidence["format_family"] == "FIT":
        messages = evidence["message_counts"]
        return {"fit_messages": sorted(messages),
                "fit_record_fields": sorted(field["name"] for field in evidence["message_fields"].get("record", [])
                                            if field["messages_with_value"]),
                "fit_developer_fields": sorted(set(field["field_name"] for field in evidence["developer_field_descriptions"])),
                "fit_device_clue": bool(evidence["device_clues"])}
    namespaces = evidence["xml_namespaces"]
    return {"xml_namespaces": sorted(set(namespaces.values())),
            "xml_extension_tags": sorted(set(xml_prevalence_name(name, namespaces)
                                              for name in evidence["extension_tag_names"])),
            "xml_point_fields": sorted(set(xml_prevalence_name(name, namespaces)
                                           for name in evidence["point_field_coverage"])),
            "xml_device_clue": any(value for value in evidence["device_clues"].values())}


def gpx_summary_power_tag_count(path):
    """Count numeric GPX summary-shaped power tags outside track points.

    This supplements STRAVA-002's point-focused GPX summary, without treating a
    vendor extension as proof of measured power or common summary semantics.
    """
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rb") as stream:
        root = ET.fromstring(stream.read().lstrip(b" \t\r\n"))
    count = 0
    def visit(node, inside_point=False):
        nonlocal count
        inside_point = inside_point or samples.local_name(node.tag).lower() == "trkpt"
        if not inside_point and samples.local_name(node.tag).lower() in ("avgpower", "maxpower", "avgwatts", "maxwatts"):
            if samples.numeric("".join(node.itertext()).strip()) is not None:
                count += 1
        for child in node:
            visit(child, inside_point)
    visit(root)
    return count


def inspect_one(source, row):
    path = safe_path(source, row["reference"])
    if path is None:
        row["status"] = "missing_or_unsafe_file"
        return
    try:
        family = row["format"]
        if family in (".fit", ".fit.gz"):
            evidence = samples.inspect_fit(path)
        elif family in (".tcx", ".tcx.gz"):
            evidence = samples.inspect_xml(path, "TCX")
        elif family in (".gpx", ".gpx.gz"):
            evidence = samples.inspect_xml(path, "GPX")
        else:
            raise ValueError("unsupported format")
        gpx_summary_tags = gpx_summary_power_tag_count(path) if family in (".gpx", ".gpx.gz") else 0
    except Exception as exc:
        # Parser exception text can contain source paths or data. Report its class only.
        row["status"] = "parse_failed"
        message = str(exc)
        if message.startswith("strict FIT parsing failed"):
            category = "strict_fit_parse_failure"
        elif message.startswith("GPX XML parsing failed") or message.startswith("TCX XML parsing failed") or isinstance(exc, ET.ParseError):
            category = "xml_parse_failure"
        else:
            category = "unexpected_" + type(exc).__name__
        row["failure_category"] = category
        return
    row["status"] = "parsed"
    row["signals"] = source_flags(evidence)
    row["signal_points"] = {name: evidence["signals"][name]["points_with_value"] for name in SOURCE_SIGNALS}
    row["point_count"] = evidence["point_count"]
    row["record_power"] = evidence["record_power_count"] > 0
    row["summary_power"] = evidence["summary_power_field_count"] > 0 or gpx_summary_tags > 0
    row["gpx_summary_power_tags"] = gpx_summary_tags
    row["timing"] = evidence["timing"]
    row["structure"] = structural(evidence)
    row["xml_whitespace"] = evidence.get("leading_xml_whitespace_bytes_removed", 0)


def ratio(count, denominator):
    return round(100 * count / denominator, 1) if denominator else None


def tally(rows):
    parsed = [row for row in rows if row["status"] == "parsed"]
    with_file = [row for row in rows if row["reference"]]
    format_counts = Counter(row["format"] for row in with_file)
    coverage = {name: {"files": sum(row["signals"][name] for row in parsed),
                       "denominator_parsed_files": len(parsed),
                       "percent_of_parsed_files": ratio(sum(row["signals"][name] for row in parsed), len(parsed)),
                       "points_with_value": sum(row["signal_points"][name] for row in parsed)}
                for name in SOURCE_SIGNALS}
    timing = {"denominator_parsed_files": len(parsed),
              "files_with_points": sum(row["point_count"] > 0 for row in parsed),
              "files_with_missing_or_invalid_timestamps": sum(row["timing"]["missing_or_invalid_timestamps"] > 0 for row in parsed),
              "files_with_duplicate_timestamps": sum(row["timing"]["duplicate_timestamps"] > 0 for row in parsed),
              "files_with_backward_or_incompatible_timestamps": sum(row["timing"]["backward_or_incompatible_timestamps"] > 0 for row in parsed),
              "files_with_large_gaps": sum(row["timing"]["large_gap_count"] > 0 for row in parsed),
              "total_missing_or_invalid_timestamps": sum(row["timing"]["missing_or_invalid_timestamps"] for row in parsed),
              "total_duplicate_timestamps": sum(row["timing"]["duplicate_timestamps"] for row in parsed),
              "total_backward_or_incompatible_timestamps": sum(row["timing"]["backward_or_incompatible_timestamps"] for row in parsed),
              "total_large_gaps": sum(row["timing"]["large_gap_count"] for row in parsed)}
    for key in ("common", "median"):
        values = [row["timing"]["positive_delta_seconds"][key] for row in parsed
                  if row["timing"]["positive_delta_seconds"][key] is not None]
        # Distribution is over per-file intervals; no pooled-stream inference.
        timing[key + "_interval_file_distribution_seconds"] = samples.numeric_stats(values)
        timing[key + "_interval_file_counts_seconds"] = dict(sorted(Counter(str(value) for value in values).items(),
                                                                     key=lambda item: float(item[0])))
    matrix = Counter(power_key(row["record_power"], row["summary_power"], row["csv_power"]) for row in parsed)
    for row in rows:
        if row["status"] != "parsed":
            matrix[power_key(False, False, row["csv_power"])] += 1
    return {"population": {"csv_rows": len(rows), "source_file_backed_rows": len(with_file),
                            "no_file_rows": len(rows) - len(with_file), "attempted_source_files": len(with_file),
                            "parsed_source_files": len(parsed),
                            "failed_source_files": len(with_file) - len(parsed),
                            "status_counts": dict(sorted(Counter(row["status"] for row in rows).items()))},
            "source_formats": dict(sorted(format_counts.items())), "source_signal_coverage": coverage,
            "csv_power_metadata_rows": sum(row["csv_power"] for row in rows),
            "source_record_power_files": sum(row["record_power"] for row in parsed),
            "source_summary_power_files": sum(row["summary_power"] for row in parsed),
            "power_matrix_all_rows": dict(sorted(matrix.items())), "timing": timing}


def group(rows):
    parsed = [row for row in rows if row["status"] == "parsed"]
    with_file = [row for row in rows if row["reference"]]
    counts = Counter(row["format"] for row in with_file)
    signal_counts = {name: sum(row["signals"][name] for row in parsed) for name in SOURCE_SIGNALS}
    return {"csv_rows": len(rows), "file_backed_rows": len(with_file), "no_file_rows": len(rows) - len(with_file),
            "parsed_files": len(parsed), "parse_or_file_failures": len(with_file) - len(parsed),
            "format_counts": dict(sorted(counts.items())),
            "signals": {name: {"files": count, "denominator_parsed_files": len(parsed),
                               "percent": ratio(count, len(parsed))}
                        for name, count in signal_counts.items()},
            "source_record_power_files": sum(row["record_power"] for row in parsed),
            "source_summary_power_files": sum(row["summary_power"] for row in parsed),
            "csv_power_metadata_rows": sum(row["csv_power"] for row in rows)}


def breakdown(rows, key):
    groups = defaultdict(list)
    for row in rows:
        groups[row[key]].append(row)
    return {name: group(items) for name, items in sorted(groups.items())}


def cycling_cohorts(rows):
    result = {}
    for name in ("Ride", "Virtual Ride", "Other"):
        selected = [row for row in rows if row["cohort"] == name]
        parsed = [row for row in selected if row["status"] == "parsed"]
        combos = Counter()
        matrix = Counter()
        for row in parsed:
            combos.update(key for key, present in combination_flags(row["signals"], row["record_power"], row["csv_power"]).items() if present)
            matrix[power_key(row["record_power"], row["summary_power"], row["csv_power"])] += 1
        result[name] = {"population": group(selected), "combination_denominator_parsed_files": len(parsed),
                        "combinations": dict(sorted(combos.items())), "power_matrix_parsed_files": dict(sorted(matrix.items()))}
    return result


def structure_counts(rows):
    fit = [row for row in rows if row["status"] == "parsed" and row["format"] in (".fit", ".fit.gz")]
    xml = {family: [row for row in rows if row["status"] == "parsed" and row["format"] in ("." + family.lower(), "." + family.lower() + ".gz")]
           for family in ("TCX", "GPX")}
    def prevalence(items, key):
        counter = Counter()
        for row in items:
            counter.update(set(row["structure"][key]))
        return dict(sorted(counter.items()))
    result = {"FIT": {"denominator_parsed_files": len(fit),
                       "messages_by_file": prevalence(fit, "fit_messages"),
                       "record_fields_by_file": prevalence(fit, "fit_record_fields"),
                       "developer_fields_by_file": prevalence(fit, "fit_developer_fields"),
                       "files_with_device_clues": sum(row["structure"]["fit_device_clue"] for row in fit)}}
    for family, items in xml.items():
        result[family] = {"denominator_parsed_files": len(items),
                          "namespaces_by_file": prevalence(items, "xml_namespaces"),
                          "extension_tags_by_file": prevalence(items, "xml_extension_tags"),
                          "point_fields_by_file": prevalence(items, "xml_point_fields"),
                          "files_with_device_clues": sum(row["structure"]["xml_device_clue"] for row in items)}
        if family == "GPX":
            result[family]["files_with_numeric_nonpoint_summary_power_tags"] = sum(row["gpx_summary_power_tags"] > 0 for row in items)
    return result


def diagnostics(rows):
    events = []
    for row in rows:
        if row["status"] in ("parse_failed", "missing_or_unsafe_file"):
            events.append({"activity_id": row["id"], "format": row["format"],
                           "category": row.get("failure_category", row["status"])})
        if row.get("xml_whitespace"):
            events.append({"activity_id": row["id"], "format": row["format"],
                           "category": "leading_xml_whitespace", "bytes": row["xml_whitespace"]})
        if row["status"] == "parsed" and row["point_count"] == 0:
            events.append({"activity_id": row["id"], "format": row["format"], "category": "zero_points"})
    return {"event_count": len(events), "category_counts": dict(sorted(Counter(event["category"] for event in events).items())),
            "events": sorted(events, key=lambda event: (event["activity_id"], event["category"]))}


def census(source, inventory_path=None):
    source = Path(source).expanduser().resolve()
    if not source.is_dir():
        raise ValueError("source must be an existing extracted-export directory")
    rows, _fields = build_rows(source)
    verify_population(rows, inventory_path)
    for row in rows:
        if row["reference"]:
            inspect_one(source, row)
    by_year_type_format = Counter((row["year"], row["type"], row["format"]) for row in rows)
    result = {"schema_version": SCHEMA_VERSION, "tool_version": TOOL_VERSION,
              "source": "local extracted Strava export (path withheld)",
              "fit_parser": {"name": "fitdecode", "version": "0.11.0", "crc_check": "raise", "error_handling": "raise"},
              "xml_parser": "Python standard-library ElementTree",
              "methodology": {"population": "one CSV row per activity; exact Filename reference; no-file rows retained",
                              "signal": "presence means at least one source record/point with a decoded value; source summary power is separate",
                              "source_signal_denominator": "successfully parsed source files in each reported group",
                              "power": "three evidence flags; GPX numeric avgPower/maxPower tags outside points count as source summary metadata; provenance and summary semantics remain unknown",
                              "timing": "STRAVA-002 timing_summary: source order; large gap > max(30 s, 5 x median positive delta); intervals summarized per file",
                              "activity_type": "Ride and Virtual Ride are CSV labels/proxies, not physical indoor/outdoor truth"},
              "totals": tally(rows), "by_year": breakdown(rows, "year"),
              "by_activity_type": breakdown(rows, "type"),
              "by_year_type_format": [{"year": year, "activity_type": kind, "format": fmt, "csv_rows": count}
                                      for (year, kind, fmt), count in sorted(by_year_type_format.items())],
              "cycling_cohorts": cycling_cohorts(rows),
              "structure": structure_counts(rows), "diagnostics": diagnostics(rows)}
    return result


def markdown(report):
    totals = report["totals"]
    pop = totals["population"]
    lines = ["# STRAVA-003 historical data-coverage census", "",
             "Source: local extracted export; no raw streams, coordinates, names, descriptions, serials, or absolute paths.", "",
             "## Population", "",
             "| CSV rows | File-backed | No file | Attempted | Parsed | Failed |",
             "| ---: | ---: | ---: | ---: | ---: | ---: |",
             f"| {pop['csv_rows']} | {pop['source_file_backed_rows']} | {pop['no_file_rows']} | {pop['attempted_source_files']} | {pop['parsed_source_files']} | {pop['failed_source_files']} |", "",
             "Source formats (file-backed rows): " + ", ".join(f"{name} {count}" for name, count in totals["source_formats"].items()) + ".", "",
             "## Source signal coverage", "",
             "A signal is present when at least one decoded source point has a value. Percentages use parsed files as denominator; presence does not establish quality or provenance.", "",
             "| Signal | Files | Parsed-file denominator | % | Points with value |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for name, item in totals["source_signal_coverage"].items():
        lines.append(f"| {name} | {item['files']} | {item['denominator_parsed_files']} | {item['percent_of_parsed_files']} | {item['points_with_value']} |")
    lines += ["", "## Historical evolution", "", "Yearly counts include no-file rows; source-signal columns use parsed files in that year.", "",
              "| Year | CSV | FIT | TCX | GPX | No file | Parsed | GPS | HR | Cadence | Record power |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for year, item in report["by_year"].items():
        formats = item["format_counts"]
        def fmt(family):
            return sum(value for key, value in formats.items() if key.startswith("." + family))
        signals = item["signals"]
        lines.append(f"| {year} | {item['csv_rows']} | {fmt('fit')} | {fmt('tcx')} | {fmt('gpx')} | {item['no_file_rows']} | {item['parsed_files']} | {signals['gps']['files']} | {signals['heart_rate']['files']} | {signals['cadence']['files']} | {item['source_record_power_files']} |")
    lines += ["", "Full yearly signal, type, and year/type/format counts are in `coverage_census.json`.", "",
              "## Cycling evidence cohorts", "",
              "Counts below use parsed source files within each CSV Activity Type cohort. Activity Type does not prove physical riding context.", "",
              "| Cohort | CSV rows | Parsed | Source power | HR, no source power | Position + altitude, no source power | Position + altitude + HR, no source power | Cadence, no source power | CSV power, no source power |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, item in report["cycling_cohorts"].items():
        combo = item["combinations"]
        lines.append(f"| {name} | {item['population']['csv_rows']} | {item['combination_denominator_parsed_files']} | {combo.get('source_record_power', 0)} | {combo.get('heart_rate_without_source_record_power', 0)} | {combo.get('position_altitude_without_source_record_power', 0)} | {combo.get('position_altitude_heart_rate_without_source_record_power', 0)} | {combo.get('cadence_without_source_record_power', 0)} | {combo.get('csv_power_without_source_record_power', 0)} |")
    lines += ["", "## Power evidence", "",
              f"Source record power: {totals['source_record_power_files']} parsed files; source summary power: {totals['source_summary_power_files']} parsed files; CSV power metadata: {totals['csv_power_metadata_rows']} rows.",
              "The matrix covers all CSV rows; source flags are false when a source is absent or could not be parsed. Such rows remain separately counted in population status. No provenance classification stronger than unknown is supported by these flags.", "",
              "| Record | Summary | CSV | Rows |", "| ---: | ---: | ---: | ---: |"]
    for key, count in totals["power_matrix_all_rows"].items():
        bits = [part.split("=")[1] for part in key.split(",")]
        lines.append(f"| {' | '.join(bits)} | {count} |")
    lines += ["", "## Structural coverage", ""]
    fit = report["structure"]["FIT"]
    lines.append(f"FIT parsed files: {fit['denominator_parsed_files']}; session {fit['messages_by_file'].get('session', 0)}, lap {fit['messages_by_file'].get('lap', 0)}, event {fit['messages_by_file'].get('event', 0)}, device_info {fit['messages_by_file'].get('device_info', 0)}, developer_data_id {fit['messages_by_file'].get('developer_data_id', 0)}, field_description {fit['messages_by_file'].get('field_description', 0)}. Device clues: {fit['files_with_device_clues']}.")
    lines.append("FIT developer field names by file: " + (", ".join(f"{name} {count}" for name, count in fit["developer_fields_by_file"].items()) or "none") + ".")
    for family in ("TCX", "GPX"):
        item = report["structure"][family]
        lines.append(f"{family}: {item['denominator_parsed_files']} parsed; {len(item['namespaces_by_file'])} namespace families, {len(item['extension_tags_by_file'])} extension tags; device clues in {item['files_with_device_clues']}. Full file-prevalence counts are in JSON.")
    if family == "GPX":
        lines.append(f"GPX files with numeric avgPower/maxPower-like tags outside track points: {item['files_with_numeric_nonpoint_summary_power_tags']}; these are summary metadata evidence, not verified measurement or equivalent definitions.")
    timing = totals["timing"]
    lines += ["", "## Recording and timestamp evidence", "",
              f"Parsed-file denominator: {timing['denominator_parsed_files']}. Files with missing/invalid timestamps: {timing['files_with_missing_or_invalid_timestamps']}; duplicate timestamps: {timing['files_with_duplicate_timestamps']}; backward/incompatible timestamps: {timing['files_with_backward_or_incompatible_timestamps']}; one or more large gaps: {timing['files_with_large_gaps']}.",
              "Large gap means a positive interval greater than max(30 seconds, 5 × the file's median positive interval). Common/median interval distributions are in JSON; they are per-file summaries, not pooled stream estimates.", "",
              "## Parse and structural diagnostics", ""]
    diagnostic = report["diagnostics"]
    lines.append("Categories: " + (", ".join(f"{name} {count}" for name, count in diagnostic["category_counts"].items()) or "none") + ".")
    for event in diagnostic["events"]:
        lines.append(f"- Activity {event['activity_id']} ({event['format']}): {event['category']}" +
                     (f", {event['bytes']} leading whitespace bytes" if "bytes" in event else ""))
    lines += ["", "## Limits", "",
              "- File/field presence does not prove measurement quality, physical GPS capture, or measured power; Virtual Ride positions are especially ambiguous.",
              "- CSV power metadata, source record power, and source summary power remain distinct; provenance is unknown without explicit evidence.",
              "- CSV/source numeric reconciliation was intentionally outside this census; see STRAVA-002 for diagnostic comparisons and uncertainty.",
              "- A missing file reference has no established cause. Parse failures, if any, reduce source-coverage denominators and are reported above.",
              "- FIT uses fitdecode 0.11.0 with strict CRC/error handling. TCX/GPX use ElementTree and STRAVA-002 signal/timing definitions.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="root of an extracted Strava export")
    parser.add_argument("--output-dir", default="reports/STRAVA-003")
    parser.add_argument("--inventory", default="reports/STRAVA-001/inventory.json",
                        help="STRAVA-001 baseline JSON; use an empty string to omit")
    args = parser.parse_args(argv)
    try:
        source = Path(args.source).expanduser().resolve()
        output = Path(args.output_dir).expanduser().resolve()
        if output == source or source in output.parents:
            raise ValueError("output must be outside the extracted export")
        report = census(source, args.inventory or None)
        output.mkdir(parents=True, exist_ok=True)
        (output / "coverage_census.json").write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        (output / "coverage_census.md").write_text(markdown(report), encoding="utf-8")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"coverage census error: {exc}\n")
    print(f"Wrote {output / 'coverage_census.json'} and {output / 'coverage_census.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
