#!/usr/bin/env python3
"""Inventory an extracted Strava export without reading activity streams.

Only structural metadata and CSV values needed for aggregate evidence are retained.
The report never includes the absolute source path or CSV free-text fields.
"""

import argparse
import csv
import hashlib
import json
import math
import os
import re
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

SCHEMA_VERSION = 1
TOOL_VERSION = "1.0"
ACTIVITY_EXTENSIONS = {".fit", ".tcx", ".gpx", ".fit.gz", ".tcx.gz", ".gpx.gz"}
# These observed generic export labels are safe to show; unexpected names are hashed.
SAFE_TOP_LEVEL_NAMES = set("""activities activities.csv applications.csv bikes.csv blocks.csv clubs clubs.csv
comments.csv components.csv connected_apps.csv contacts.csv email_preferences.csv events.csv flags.csv
followers.csv following.csv general_preferences.csv global_challenges.csv goals.csv group_challenges.csv
intercom_tickets.csv local_legend_segments.csv logins.csv media media.csv memberships.csv messaging.json
mobile_device_identifiers.csv monthly_recap_achievements.csv orders.csv partner_opt_outs.csv posts.csv
privacy_zones.csv profile.csv profile.jpg reactions.csv routes routes.csv segments.csv shoes.csv
social_settings.csv starred_routes.csv starred_segments.csv structured_details.csv visibility_settings.csv""".split())
EXPECTED_FIELDS = {
    "activity_id": ("activity id", "id"),
    "date": ("activity date", "start date", "start date local"),
    "filename": ("filename", "file name"),
    "activity_type": ("activity type", "type"),
    "sport_type": ("sport type",),
    "distance": ("distance",),
    "elapsed_time": ("elapsed time",),
    "moving_time": ("moving time",),
    "elevation": ("elevation gain", "total elevation gain"),
    "power": ("average power", "weighted average power", "max power", "average watts", "max watts", "power count", "power"),
    "heart_rate": ("average heart rate", "max heart rate", "heart rate"),
    "cadence": ("average cadence", "cadence"),
    "trainer": ("trainer",),
    "commute": ("commute",),
    "private": ("private",),
}
DATE_FORMATS = (
    "%b %d, %Y, %I:%M:%S %p", "%B %d, %Y, %I:%M:%S %p",
    "%b %d, %Y, %I:%M %p", "%B %d, %Y, %I:%M %p",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d", "%b %d %Y", "%B %d %Y", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y",
)


def extension(name):
    lower = name.lower()
    for suffix in sorted(ACTIVITY_EXTENSIONS, key=len, reverse=True):
        if lower.endswith(suffix):
            return suffix
    return Path(lower).suffix or "[none]"


def safe_path(relative):
    """Show only mechanical activity paths; hash all other names."""
    parts = relative.split("/")
    name = parts[-1]
    safe_dir = all(part.lower() == "activities" for part in parts[:-1])
    safe_name = bool(re.fullmatch(r"[0-9]+(?:[_-][0-9]+)*\.(?:fit|tcx|gpx)(?:\.gz)?", name, re.I))
    if safe_dir and safe_name:
        return relative
    digest = hashlib.sha256(relative.encode("utf-8", "surrogatepass")).hexdigest()[:16]
    return "path-sha256:" + digest


def safe_id(value):
    value = (value or "").strip()
    return value if re.fullmatch(r"[0-9]{1,24}", value) else None


def safe_label(value):
    value = (value or "").strip()
    return value if re.fullmatch(r"[A-Za-z][A-Za-z0-9 _/-]{0,63}", value) else "[redacted]"


def normalized_header(value):
    return re.sub(r"\s+", " ", value.strip().lower().replace("_", " "))


def discover_fields(columns, original_columns):
    """Return all matching positions, including repeated Strava header names."""
    found = {}
    for key, aliases in EXPECTED_FIELDS.items():
        found[key] = [column for alias in aliases
                      for column, original in zip(columns, original_columns)
                      if normalized_header(original) == alias]
    return found


def parse_date(value):
    value = (value or "").strip()
    if not value:
        return None
    for format_string in DATE_FORMATS:
        try:
            return datetime.strptime(value, format_string).date().isoformat()
        except ValueError:
            pass
    return None


def classify_flag(value):
    value = (value or "").strip().lower()
    if value in {"true", "1", "yes"}:
        return "true"
    if value in {"false", "0", "no"}:
        return "false"
    return "unknown"


def locate_csv(source):
    matches = sorted(path for path in source.rglob("activities.csv") if path.is_file())
    if len(matches) != 1:
        raise ValueError(f"expected exactly one readable activities.csv, found {len(matches)}")
    return matches[0]


def read_csv(path):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            try:
                original_columns = next(reader)
            except StopIteration:
                raise ValueError("activities.csv is empty")
            if not original_columns:
                raise ValueError("activities.csv has no header")
            # Positional internal keys preserve values under repeated Strava names.
            totals = Counter(original_columns)
            columns = [f"{name or '[unnamed]'} [column {index + 1}]"
                       if totals[name] > 1 or not name else name
                       for index, name in enumerate(original_columns)]
            fields = discover_fields(columns, original_columns)
            if not any(fields[key] for key in ("activity_id", "date", "filename")):
                raise ValueError("activities.csv has no recognizable ID, date, or filename column")
            rows = []
            malformed = 0
            for values in reader:
                if len(values) != len(columns):
                    malformed += 1
                rows.append({column: values[index] if index < len(values) else ""
                             for index, column in enumerate(columns)})
            return original_columns, columns, fields, rows, malformed
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError(f"cannot read activities.csv as UTF-8 CSV: {exc}") from exc


def scan_files(source, output):
    files = {}
    skipped_symlinks = 0
    for root, directories, names in os.walk(source, followlinks=False):
        root_path = Path(root)
        directories[:] = sorted(directory for directory in directories
                                if not (root_path / directory).is_symlink()
                                and (root_path / directory).resolve() != output)
        for name in sorted(names):
            path = root_path / name
            if path.is_symlink():
                skipped_symlinks += 1
                continue
            relative = path.relative_to(source).as_posix()
            try:
                files[relative] = path.stat().st_size
            except OSError as exc:
                raise ValueError(f"cannot stat export file {safe_path(relative)}: {exc}") from exc
    return files, skipped_symlinks


def size_statistics(sizes):
    """Tiny means <1 KiB; p90 is the nearest-rank 90th percentile."""
    if not sizes:
        return {"count": 0, "minimum_bytes": None, "median_bytes": None,
                "p90_bytes": None, "maximum_bytes": None, "zero_byte_count": 0,
                "tiny_under_1024_bytes_count": 0}
    ordered = sorted(sizes)
    return {"count": len(ordered), "minimum_bytes": ordered[0],
            "median_bytes": statistics.median(ordered),
            "p90_bytes": ordered[math.ceil(0.9 * len(ordered)) - 1],
            "maximum_bytes": ordered[-1], "zero_byte_count": ordered.count(0),
            "tiny_under_1024_bytes_count": sum(size < 1024 for size in ordered)}


def add_candidate(selected, relative, reason, row=None, size=None):
    if relative not in selected:
        selected[relative] = {"file": safe_path(relative),
                              "activity_id": row["activity_id"] if row else None,
                              "date": row["date"] if row else None,
                              "format": extension(relative), "size_bytes": size,
                              "reasons": []}
    if reason not in selected[relative]["reasons"]:
        selected[relative]["reasons"].append(reason)


def select_candidates(matched, activity_files, unreferenced, alternate_files):
    """Deterministic diagnostic coverage, capped at 30 files."""
    selected = {}
    dated = sorted((row for row in matched if row["date"]),
                   key=lambda row: (row["date"], row["file"]))
    by_size = sorted(matched, key=lambda row: (row["size_bytes"], row["file"]))
    def choose(rows, reason):
        for row in rows:
            if len(selected) >= 30 and row["file"] not in selected:
                return
            add_candidate(selected, row["file"], reason, row, row["size_bytes"])
            return
    if dated:
        choose(dated[:1], "earliest dated activity")
        choose(dated[-1:], "latest dated activity")
    if by_size:
        choose(by_size[:1], "smallest matched file")
        choose(by_size[-1:], "largest matched file")
    # Activity Type is only a proxy for cycling modality; no stream data is read.
    choose((row for row in dated + matched if row["activity_type"] == "Virtual Ride"),
           "virtual/indoor proxy (Activity Type: Virtual Ride)")
    choose((row for row in dated + matched if row["activity_type"] == "Ride"),
           "outdoor-ride proxy (Activity Type: Ride)")
    for fmt in sorted({row["format"] for row in matched}):
        choose((row for row in dated + matched if row["format"] == fmt), "format " + fmt)
    for year in sorted({row["date"][:4] for row in dated}):
        choose((row for row in dated if row["date"].startswith(year)), "year " + year)
    for flag, reason in (("true", "trainer flag true"), ("false", "trainer flag false")):
        choose((row for row in matched if row["trainer"] == flag), reason)
    for present, reason in ((True, "power metadata present"), (False, "power metadata absent")):
        choose((row for row in matched if row["power_present"] == present), reason)
    for activity_type in sorted({row["activity_type"] or row["sport_type"] for row in matched
                                 if row["activity_type"] or row["sport_type"]}):
        choose((row for row in matched if (row["activity_type"] or row["sport_type"]) == activity_type),
               "activity type " + activity_type)
    for relative in sorted(alternate_files):
        if len(selected) >= 30 and relative not in selected:
            break
        add_candidate(selected, relative, "path mismatch diagnostic", size=activity_files[relative])
    for relative in sorted(unreferenced):
        if len(selected) >= 30 and relative not in selected:
            break
        add_candidate(selected, relative, "unreferenced activity file", size=activity_files[relative])
    # Add diverse files if the above yielded fewer than ten.
    for row in sorted(matched, key=lambda row: (row["date"] or "", row["file"])):
        if len(selected) >= min(10, len(activity_files)):
            break
        add_candidate(selected, row["file"], "additional dated coverage", row, row["size_bytes"])
    return sorted(selected.values(), key=lambda item: (item["file"], item["activity_id"] or ""))


def inventory(source, output=None):
    source = Path(source).expanduser().resolve()
    if not source.is_dir():
        raise ValueError("source must be an existing extracted-export directory")
    output = Path(output).expanduser().resolve() if output else (Path.cwd() / "strava-inventory-output").resolve()
    if output == source:
        raise ValueError("output directory cannot be the export root")
    csv_path = locate_csv(source)
    original_columns, columns, fields, rows, malformed = read_csv(csv_path)
    files, skipped_symlinks = scan_files(source, output)
    relative_csv = csv_path.relative_to(source).as_posix()
    if relative_csv not in files:
        raise ValueError("activities.csv is not a regular export file")
    csv_references = {row[fields["filename"][0]] for row in rows
                      if fields["filename"] and row[fields["filename"][0]].strip()}
    activity_files = {name: size for name, size in files.items()
                      if extension(name) in ACTIVITY_EXTENSIONS
                      and (name.startswith("activities/") or name in csv_references)}
    ext_counts = Counter(extension(name) for name in files)
    format_stats = defaultdict(lambda: {"count": 0, "bytes": 0})
    for name, size in activity_files.items():
        stats = format_stats[extension(name)]
        stats["count"] += 1
        stats["bytes"] += size
    top_level = {}
    for entry in sorted(source.iterdir()):
        if entry.resolve() == output:
            continue
        label = entry.name if entry.name in SAFE_TOP_LEVEL_NAMES else safe_path(entry.name)
        top_level[label] = {"kind": "directory" if entry.is_dir() else "file",
                            "files": 0, "bytes": 0}
    directory_depths = Counter()
    for name, size in files.items():
        component = name.split("/", 1)[0]
        label = component if component in SAFE_TOP_LEVEL_NAMES else safe_path(component)
        top_level[label]["files"] += 1
        top_level[label]["bytes"] += size
        directory_depths[str(name.count("/"))] += 1
    nonempty = {column: sum(bool(row[column].strip()) for row in rows) for column in columns}
    dates = [parse_date(row[fields["date"][0]]) if fields["date"] else None for row in rows]
    years = Counter(value[:4] for value in dates if value)
    type_counts = {key: Counter(safe_label(row[columns_for_key[0]]) for row in rows
                                if row[columns_for_key[0]].strip())
                   for key, columns_for_key in fields.items()
                   if key in {"activity_type", "sport_type"} and columns_for_key}
    referenced = Counter()
    matched = []
    alternate_files = set()
    matching = {"rows_with_reference": 0, "rows_without_reference": 0,
                "references_existing_exactly": 0, "references_missing_exactly": 0}
    anomalies = Counter()
    examples = defaultdict(list)
    def anomaly(code, activity_id=None, file=None):
        anomalies[code] += 1
        if len(examples[code]) < 25:
            examples[code].append({"activity_id": activity_id,
                                   "file": safe_path(file) if file else None})
    casefold_map = defaultdict(list)
    for name in files:
        casefold_map[name.casefold()].append(name)
    for index, row in enumerate(rows):
        activity_id = safe_id(row[fields["activity_id"][0]]) if fields["activity_id"] else None
        name = row[fields["filename"][0]] if fields["filename"] else ""
        if not name.strip():
            matching["rows_without_reference"] += 1
            if fields["filename"]:
                anomaly("row_without_file_reference", activity_id)
            continue
        matching["rows_with_reference"] += 1
        referenced[name] += 1
        if name in files:
            matching["references_existing_exactly"] += 1
            if name in activity_files:
                activity_type = safe_label(row[fields["activity_type"][0]]) if fields["activity_type"] else None
                trainer = classify_flag(row[fields["trainer"][0]]) if fields["trainer"] else "unknown"
                power_present = any(row[column].strip() for column in fields["power"])
                matched.append({"file": name, "activity_id": activity_id, "date": dates[index],
                                "year": dates[index][:4] if dates[index] else None,
                                "activity_type": activity_type, "sport_type":
                                safe_label(row[fields["sport_type"][0]]) if fields["sport_type"] else None,
                                "trainer": trainer, "power_present": power_present,
                                "format": extension(name), "size_bytes": files[name]})
            else:
                anomaly("reference_is_not_activity_format", activity_id, name)
            continue
        matching["references_missing_exactly"] += 1
        variants = [("case_mismatch", casefold_map.get(name.casefold(), []))]
        decoded = unquote(name)
        if decoded != name:
            variants.append(("percent_encoding_mismatch", [decoded] if decoded in files else []))
        nfc = unicodedata.normalize("NFC", name)
        if nfc != name:
            variants.append(("unicode_normalization_mismatch", [nfc] if nfc in files else []))
        slash = name.replace("\\", "/")
        if slash != name:
            variants.append(("path_separator_mismatch", [slash] if slash in files else []))
        stripped = name.strip().removeprefix("./")
        if stripped != name:
            variants.append(("path_decoration_mismatch", [stripped] if stripped in files else []))
        basename_matches = [candidate for candidate in activity_files if candidate.rsplit("/", 1)[-1] == name]
        if basename_matches:
            variants.append(("basename_only_reference", basename_matches))
        identified = False
        for code, candidates in variants:
            if candidates:
                anomaly(code, activity_id, name)
                alternate_files.update(candidate for candidate in candidates if candidate in activity_files)
                identified = True
                break
        if not identified:
            anomaly("missing_reference_unexplained", activity_id, name)
    duplicate_refs = {name: count for name, count in referenced.items() if count > 1}
    for name, count in duplicate_refs.items():
        anomaly("duplicate_csv_reference", file=name)
    duplicate_ids = {}
    if fields["activity_id"]:
        ids = Counter(safe_id(row[fields["activity_id"][0]]) for row in rows)
        duplicate_ids = {key: count for key, count in ids.items() if key and count > 1}
        for key in duplicate_ids:
            anomaly("duplicate_activity_id", activity_id=key)
    unreferenced = sorted(set(activity_files) - set(referenced))
    for name in unreferenced:
        anomaly("unreferenced_activity_file", file=name)
    if malformed:
        anomalies["malformed_csv_row"] = malformed
    if fields["date"]:
        unparsed = sum(bool(row[fields["date"][0]].strip()) and date is None
                       for row, date in zip(rows, dates))
        if unparsed:
            anomalies["unparseable_activity_date"] = unparsed
    coverage = defaultdict(Counter)
    coverage_by_type = defaultdict(Counter)
    coverage_by_sport_type = defaultdict(Counter)
    for row in matched:
        if row["year"]:
            coverage[row["year"]][row["format"]] += 1
        if row["activity_type"]:
            coverage_by_type[row["activity_type"]][row["format"]] += 1
        if row["sport_type"]:
            coverage_by_sport_type[row["sport_type"]][row["format"]] += 1
    warnings = []
    if not fields["filename"]:
        warnings.append("No recognized filename column; CSV-to-file association is unavailable.")
    if not fields["date"]:
        warnings.append("No recognized date column; historical CSV coverage is unavailable.")
    if skipped_symlinks:
        warnings.append(f"Skipped {skipped_symlinks} symlinked files; symlinked directories were also excluded.")
    if matching["rows_with_reference"] and matching["references_missing_exactly"]:
        warnings.append("Path mismatches are reported without automatic correction; format coverage uses exact matches only.")
    if not matched:
        warnings.append("No exact CSV-to-activity-file matches; format-by-year/type coverage is unavailable.")
    if any(row["power_present"] for row in matched):
        warnings.append("Power column presence is a CSV metadata proxy, not proof of measured power.")
    candidates = select_candidates(matched, activity_files, unreferenced, alternate_files)
    return {
        "schema_version": SCHEMA_VERSION, "tool_version": TOOL_VERSION,
        "source": "extracted Strava export (local path withheld)",
        "structure": {"file_count": len(files), "total_bytes": sum(files.values()),
                      "top_level": dict(sorted(top_level.items())),
                      "file_counts_by_directory_depth": dict(sorted(directory_depths.items())),
                      "extensions": dict(sorted(ext_counts.items())),
                      "activity_formats": dict(sorted(format_stats.items())),
                      "compressed_activity_count": sum(name.endswith(".gz") for name in activity_files),
                      "uncompressed_activity_count": sum(not name.endswith(".gz") for name in activity_files)},
        "csv": {"row_count": len(rows), "columns": original_columns,
                "column_details": [{"position": index + 1, "name": original_columns[index],
                                    "nonempty_count": nonempty[column]}
                                   for index, column in enumerate(columns)],
                "entirely_empty_columns": [name for name in columns if not nonempty[name]],
                "columns_with_values": [name for name in columns if nonempty[name]],
                "column_nonempty_counts": nonempty,
                "recognized_fields": fields,
                "expected_fields_absent": [key for key in EXPECTED_FIELDS if not fields[key]],
                "earliest_date": min((date for date in dates if date), default=None),
                "latest_date": max((date for date in dates if date), default=None),
                "counts_by_year": dict(sorted(years.items())),
                "counts_by_type": {key: dict(sorted(counts.items())) for key, counts in type_counts.items()}},
        "associations": {**matching, "duplicate_reference_count": len(duplicate_refs),
                         "duplicate_activity_id_count": len(duplicate_ids),
                         "unreferenced_activity_file_count": len(unreferenced),
                         "exact_matched_activity_file_rows": len(matched)},
        "file_format_coverage": {"by_year": {key: dict(sorted(value.items()))
                                              for key, value in sorted(coverage.items())},
                                 "by_activity_type": {key: dict(sorted(value.items()))
                                                      for key, value in sorted(coverage_by_type.items())},
                                 "by_sport_type": {key: dict(sorted(value.items()))
                                                   for key, value in sorted(coverage_by_sport_type.items())}},
        "file_sizes": {**size_statistics(list(activity_files.values())),
                       "definitions": "Tiny: <1024 bytes. P90: nearest-rank 90th percentile. Median: usual midpoint for even counts."},
        "anomalies": {"counts": dict(sorted(anomalies.items())),
                      "examples": {key: sorted(value, key=lambda item: (item["activity_id"] or "", item["file"] or ""))
                                   for key, value in sorted(examples.items())},
                      "example_limit_per_kind": 25},
        "candidate_files": candidates,
        "warnings": warnings,
    }


def markdown(report):
    structure, csv_report, associations = (report[key] for key in ("structure", "csv", "associations"))
    lines = ["# Strava export inventory", "", "Diagnostic inventory of local export metadata. No raw activity streams were parsed.", "",
             "## What was received", "",
             f"- {structure['file_count']} files, {structure['total_bytes']} bytes total",
             f"- {csv_report['row_count']} CSV activity rows",
             f"- Activity files: {sum(value['count'] for value in structure['activity_formats'].values())} "
             f"({structure['compressed_activity_count']} compressed)", "",
             "| Format | Files | Bytes |", "| --- | ---: | ---: |"]
    for fmt, values in structure["activity_formats"].items():
        lines.append(f"| {fmt} | {values['count']} | {values['bytes']} |")
    lines += ["", "Top-level entries:", ""]
    for name, values in structure["top_level"].items():
        unit = "file" if values["files"] == 1 else "files"
        lines.append(f"- {name} ({values['kind']}): {values['files']} {unit}, {values['bytes']} bytes")
    lines += ["", "## CSV and history", "",
              f"- Date range: {csv_report['earliest_date'] or 'unknown'} to {csv_report['latest_date'] or 'unknown'}",
              f"- Years: {', '.join(f'{year}: {count}' for year, count in csv_report['counts_by_year'].items()) or 'none reliably parsed'}",
              f"- CSV columns: {len(csv_report['columns'])}; exact ordered names and positional counts are in inventory.json",
              f"- Entirely empty columns: {', '.join(csv_report['entirely_empty_columns']) or 'none'}",
              f"- Useful fields absent: {', '.join(csv_report['expected_fields_absent']) or 'none'}", ""]
    for key, counts in csv_report["counts_by_type"].items():
        lines.append(f"- {key}: {', '.join(f'{label}: {count}' for label, count in counts.items())}")
    if report["file_format_coverage"]["by_year"]:
        lines += ["", "Exact-match activity formats by year:", "", "| Year | Formats and counts |", "| --- | --- |"]
        for year, formats in report["file_format_coverage"]["by_year"].items():
            lines.append(f"| {year} | {', '.join(f'{fmt}: {count}' for fmt, count in formats.items())} |")
    lines += ["", "## CSV-to-file association", "",
              f"- Rows with/without a reference: {associations['rows_with_reference']}/{associations['rows_without_reference']}",
              f"- Exact existing/missing references: {associations['references_existing_exactly']}/{associations['references_missing_exactly']}",
              f"- Unreferenced activity files: {associations['unreferenced_activity_file_count']}",
              f"- Duplicate references/IDs: {associations['duplicate_reference_count']}/{associations['duplicate_activity_id_count']}", "",
              "## File sizes", "",
              f"- Minimum/median/p90/maximum bytes: {report['file_sizes']['minimum_bytes']}, {report['file_sizes']['median_bytes']}, {report['file_sizes']['p90_bytes']}, {report['file_sizes']['maximum_bytes']}",
              f"- Zero byte/tiny (<1024 bytes): {report['file_sizes']['zero_byte_count']}/{report['file_sizes']['tiny_under_1024_bytes_count']}", "",
              "## Anomalies", ""]
    for kind, count in report["anomalies"]["counts"].items():
        lines.append(f"- {kind}: {count}")
    if not report["anomalies"]["counts"]:
        lines.append("- None detected")
    lines += ["", "## Candidate files for later inspection", "",
              "These are deliberately diverse diagnostic samples, not statistical samples.", "",
              "| File or path token | Activity ID | Format | Why selected |",
              "| --- | --- | --- | --- |"]
    for item in report["candidate_files"]:
        lines.append(f"| {item['file']} | {item['activity_id'] or 'unknown'} | {item['format']} | {', '.join(item['reasons'])} |")
    lines += ["", "## Limits", ""]
    for warning in report["warnings"]:
        lines.append("- " + warning)
    lines += ["- CSV field presence and file association do not establish data quality inside activity streams.",
              "- Matching uses exact relative paths; possible path variants remain anomalies.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="root of an already extracted Strava export")
    parser.add_argument("--output-dir", help="output directory (default: ./strava-inventory-output, outside source when needed)")
    args = parser.parse_args(argv)
    try:
        source = Path(args.source).expanduser().resolve()
        output = (Path(args.output_dir).expanduser().resolve() if args.output_dir else
                  (Path.cwd() / "strava-inventory-output").resolve())
        if not args.output_dir and (output == source or source in output.parents):
            output = source.parent / "strava-inventory-output"
        report = inventory(source, output)
        output.mkdir(parents=True, exist_ok=True)
        (output / "inventory.json").write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        (output / "inventory.md").write_text(markdown(report), encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"inventory error: {exc}\n")
    print(f"Wrote {output / 'inventory.json'} and {output / 'inventory.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
