"""Narrow typed FIT extraction. No signal repair or application calculations."""

from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
from pathlib import Path
import zlib

import fitdecode

from .errors import InvalidFitError

MAPPING_VERSION = "fit-v1"
PARSER_VERSION = "0.11.0"


@dataclass(frozen=True)
class Session:
    start_time: str | None
    timestamp: str | None
    sport: str | None
    sub_sport: str | None
    total_elapsed_time: float | None
    total_timer_time: float | None
    total_distance: float | None
    total_ascent: int | None
    avg_power: int | None
    max_power: int | None
    avg_heart_rate: int | None
    max_heart_rate: int | None
    avg_cadence: int | None


@dataclass(frozen=True)
class Record:
    record_index: int
    source_order: int
    timestamp: str | None
    power: int | None
    heart_rate: int | None


@dataclass(frozen=True)
class Lap:
    source_order: int
    start_time: str | None
    timestamp: str | None
    total_elapsed_time: float | None
    total_timer_time: float | None


@dataclass(frozen=True)
class Event:
    source_order: int
    timestamp: str | None
    event: str | None
    event_type: str | None
    timer_trigger: str | None


@dataclass(frozen=True)
class ParsedFit:
    session: Session
    records: list[Record]
    laps: list[Lap]
    events: list[Event]


def _timestamp(value):
    if value is None:
        return None
    # fitdecode's DefaultDataProcessor decodes FIT date_time as aware UTC.
    # Device-relative timestamps are integers and cannot be guessed into UTC.
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise InvalidFitError("Unsupported FIT timestamp: absolute UTC time is required")
    return value.astimezone(timezone.utc).isoformat()


def _label(value):
    return None if value is None else str(value)


def _values(frame):
    values = {}
    for field in frame.fields:
        if field.value is None:
            continue
        if field.name in values and values[field.name] != field.value:
            raise InvalidFitError(f"Conflicting decoded FIT field: {field.name}")
        values[field.name] = field.value
    return values


def packaging_for(path: Path) -> str:
    with path.open("rb") as stream:
        return "gzip" if stream.read(2) == b"\x1f\x8b" else "plain"


def decode_fit(path: Path, packaging: str) -> ParsedFit:
    if fitdecode.__version__ != PARSER_VERSION:
        raise InvalidFitError(f"fitdecode {PARSER_VERSION} is required")
    sessions, records, laps, events = [], [], [], []
    header_count = 0
    file_types = []
    activity_sessions = []
    opener = gzip.open if packaging == "gzip" else open
    try:
        with opener(path, "rb") as stream:
            with fitdecode.FitReader(
                stream, check_crc=fitdecode.CrcCheck.RAISE,
                error_handling=fitdecode.ErrorHandling.RAISE,
            ) as reader:
                for source_order, frame in enumerate(reader):
                    if frame.frame_type == fitdecode.FIT_FRAME_HEADER:
                        header_count += 1
                    if frame.frame_type != fitdecode.FIT_FRAME_DATA:
                        continue
                    if frame.name not in {"file_id", "activity", "session", "record", "lap", "event"}:
                        continue
                    v = _values(frame)
                    if frame.name == "file_id":
                        file_types.append(v.get("type"))
                    elif frame.name == "activity":
                        activity_sessions.append(v.get("num_sessions"))
                    elif frame.name == "session":
                        sessions.append(Session(
                            _timestamp(v.get("start_time")), _timestamp(v.get("timestamp")),
                            _label(v.get("sport")), _label(v.get("sub_sport")),
                            *(v.get(name) for name in (
                                "total_elapsed_time", "total_timer_time", "total_distance",
                                "total_ascent", "avg_power", "max_power", "avg_heart_rate",
                                "max_heart_rate", "avg_cadence")),
                        ))
                    elif frame.name == "record":
                        records.append(Record(len(records), source_order,
                                              _timestamp(v.get("timestamp")),
                                              v.get("power"), v.get("heart_rate")))
                    elif frame.name == "lap":
                        laps.append(Lap(source_order, _timestamp(v.get("start_time")),
                                        _timestamp(v.get("timestamp")),
                                        v.get("total_elapsed_time"), v.get("total_timer_time")))
                    elif frame.name == "event":
                        events.append(Event(source_order, _timestamp(v.get("timestamp")),
                                            _label(v.get("event")), _label(v.get("event_type")),
                                            _label(v.get("timer_trigger"))))
    except (OSError, EOFError, ValueError, zlib.error, fitdecode.FitError) as exc:
        raise InvalidFitError(f"Invalid {packaging} FIT artifact: {exc}") from exc
    if header_count != 1 or len(sessions) != 1:
        raise InvalidFitError("Exactly one FIT file and one activity session are supported")
    if any(t != "activity" for t in file_types):
        raise InvalidFitError("FIT content is not an activity file")
    if len(activity_sessions) > 1 or any(n not in (None, 1) for n in activity_sessions):
        raise InvalidFitError("Multiple activity sessions are unsupported")
    return ParsedFit(sessions[0], records, laps, events)
