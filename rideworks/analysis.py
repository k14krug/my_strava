"""Phase 1 source evidence and one on-demand, explicitly contextual derivation."""

from datetime import datetime, timedelta

from .errors import RideWorksError
from .store import Store, SUMMARY_UNITS

BEST_20_METHOD = "best-average-power-v1"
WINDOW_SAMPLES = 1200
ONE_SECOND = timedelta(seconds=1)


class AnalysisError(RideWorksError):
    """Required source selection/evidence cannot safely support this analysis."""


def _timestamp(value):
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise AnalysisError("Invalid timestamp in current native extraction") from exc
    if parsed.tzinfo is None:
        raise AnalysisError("Current native extraction timestamp has no timezone")
    return parsed


def best_20_minute_power(records, *, activity_id, source_id, extraction_id):
    """Search native complete one-Hz 1,200-record windows; never repair evidence.

    The rolling integer sum and counts of missing power/bad adjacent timestamp
    deltas make this O(n). Comparing sums preserves unrounded ties exactly.
    """
    result = dict(
        activity_id=activity_id, source_id=source_id, extraction_id=extraction_id,
        origin="calculated", method=BEST_20_METHOD, duration_seconds=WINDOW_SAMPLES,
        required_sample_count=WINDOW_SAMPLES, status="unavailable", eligible=False,
        reason=None, eligible_window_count=0, start_record_index=None,
        end_exclusive_record_index=None, start_timestamp=None,
        end_exclusive_timestamp=None, sample_count=None, average_watts=None,
        rounded_watts=None,
    )
    timestamps = [_timestamp(record["timestamp"]) for record in records]
    for record in records:
        power = record["power"]
        if power is not None and (not isinstance(power, int) or power < 0):
            raise AnalysisError("Unexpected power value in current native extraction; analysis stopped")
    if len(records) < WINDOW_SAMPLES:
        result["reason"] = "activity_shorter_than_required"
        return result
    bad_edges = [0] + [int(a is None or b is None or b - a != ONE_SECOND)
                       for a, b in zip(timestamps, timestamps[1:])]
    total, missing, bad_timing = 0, 0, 0
    timestamp_windows, eligible_windows = 0, 0
    best_total, best_start = None, None
    for end, record in enumerate(records):
        power = record["power"]
        missing += power is None
        total += power if power is not None else 0  # missing tracked separately; never eligible as zero
        bad_timing += bad_edges[end]
        if end >= WINDOW_SAMPLES:
            leaving = records[end - WINDOW_SAMPLES]["power"]
            missing -= leaving is None
            total -= leaving if leaving is not None else 0
            # Remove only the edge crossing from the outgoing record into
            # this new window; a gap before its first sample is irrelevant.
            bad_timing -= bad_edges[end - WINDOW_SAMPLES + 1]
        if end < WINDOW_SAMPLES - 1 or bad_timing:
            continue
        timestamp_windows += 1
        if missing:
            continue
        eligible_windows += 1
        if best_total is None or total > best_total:
            best_total, best_start = total, end - WINDOW_SAMPLES + 1
    result["eligible_window_count"] = eligible_windows
    if best_start is None:
        result["reason"] = ("no_complete_timestamp_contiguous_window" if not timestamp_windows
                            else "no_complete_power_window")
        return result
    last = best_start + WINDOW_SAMPLES - 1
    result.update(
        status="available", eligible=True,
        start_record_index=records[best_start]["record_index"],
        end_exclusive_record_index=records[last]["record_index"] + 1,
        start_timestamp=records[best_start]["timestamp"],
        end_exclusive_timestamp=(timestamps[best_start] + timedelta(seconds=WINDOW_SAMPLES)).isoformat(),
        sample_count=WINDOW_SAMPLES, average_watts=best_total / WINDOW_SAMPLES,
        # Integer source watts permit exact nearest-watt rounding, halves up.
        rounded_watts=(best_total + WINDOW_SAMPLES // 2) // WINDOW_SAMPLES,
    )
    return result


def analyze_activity(store: Store, activity_id: str) -> dict:
    """Read one current FIT Source snapshot and return the Phase 1 package.

    No cached result, source ranking, SQL, reparsing or stream transformation.
    """
    snapshot = store.get_activity(activity_id)
    candidates = [evidence for evidence in snapshot["sources"]
                  if evidence["source"]["kind"] == "file_fit"
                  and evidence["source"]["content_format"] == "FIT"]
    if not candidates:
        raise AnalysisError("Activity has no usable current FIT Source")
    if len(candidates) != 1:
        raise AnalysisError("Multiple candidate FIT Sources require an evidence-selection decision")
    evidence = candidates[0]
    source, extraction = evidence["source"], evidence["extraction"]
    if not extraction or not extraction.get("extraction_id"):
        raise AnalysisError("FIT Source has no usable current extraction")
    best = best_20_minute_power(
        evidence["records"], activity_id=snapshot["activity"]["activity_id"],
        source_id=source["source_id"], extraction_id=extraction["extraction_id"],
    )
    return dict(
        activity=snapshot["activity"], source=source, extraction=extraction,
        source_summary=dict(source_id=source["source_id"],
                            extraction_id=extraction["extraction_id"],
                            evidence_kind="FIT session source summary", values=evidence["summary"],
                            units=SUMMARY_UNITS.copy()),
        native_records=evidence["records"], availability=evidence["availability"],
        best_20_minute_power=best,
    )


def compact_analysis(analysis: dict) -> dict:
    """CLI snapshot without raw streams or absolute runtime/source paths."""
    return {key: value for key, value in analysis.items() if key != "native_records"} | {
        "native_record_count": len(analysis["native_records"]),
    }
