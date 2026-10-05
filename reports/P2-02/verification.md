# P2-02 verification — Gate 1 Owner review

**Date:** 2026-10-04.  
**Branch / PR:** `task/p2-02-activities-browser` / [#14](https://github.com/k14krug/my_strava/pull/14).  
**Implementation head:** `594856d2fe3f50b996397bd68ae4859969ccc321`; final handoff publication is documentation/evidence only.
**State:** implementation and local verification complete; stopped at **Gate 1 HARD — Owner**. P2-02 remains `in_progress`. Owner approval and final Analyst acceptance are pending.

## Result and implementation

All **1,434** imported Activities are browsable through the root Activities route.
The default shows **1,410 cycling Activities** newest-first, **30 rows per page**,
with 47 cycling pages. Date is a dedicated column/region beside Title, with its own visible heading. All activities includes the 24 non-cycling Activities and
has 48 pages. The header reports the matching count and total history population.

`rideworks/history.py` provides the narrow read-only presentation/query policy.
`rideworks/web.py` renders GET filters/pagination and stable Activity Review routes;
`rideworks/static/style.css` extends the established RideWorks shell with compact
controls/dense rows. `Store.activity_history(activity_id=None)` retains the accepted
metadata boundary and adds a bound-ID restriction for review metadata. No browser
list native records are loaded, no new schema/dependency/framework is introduced,
and no source observations are rewritten.

Available controls:

- case-insensitive partial title search (including punctuation and older retained source-title observations);
- Cycling, All activities, and observed type/subtype choices; known history includes Ride, Virtual Ride, Run, Walk and Rowing;
- inclusive From/To dates, including one-sided ranges;
- newest, oldest, longest duration and longest distance;
- deterministic previous/next pages that preserve filters/search/sort in the URL.

Invalid values show safe defaults or compact validation text; out-of-range pages
clamp to a valid page. Applying filters starts at page 1. Missing sort values stay
unavailable and come last; legitimate zero remains known. Ties use Activity ID.

For display, the latest non-empty Strava-export title is preferred. The fallback
is explicitly derived from source type/date. Type/subtype remain separate and
source-title/type provenance is inspectable. Date prefers a directly supplied
file session start, then supported CSV date evidence. Absolute instants render in
the browser's local timezone; From/To uses the **same displayed local calendar
day**, including historical daylight-saving rules. Offset-unknown dates retain
their source calendar day and explicit unknown timezone.
Unparsed date text is retained for display without entering date filters.

The Owner corrections in PR #14 and Analyst-authored JIT clarifications on `main`
at `56e1f1c` replace the original UTC-day filter rule. Browser JavaScript supplies
its IANA timezone in GET state (`tz`), which is preserved across form submissions
and pagination. Server-side standard-library `ZoneInfo` applies that zone to
known instants for filtering only. The browser updates this state on navigation
from another timezone. Missing/invalid zones never guess an absolute filter day;
a compact explanation requests JavaScript, while unknown-zone source dates can
still match their supplied day. No source timestamp/provenance is rewritten.

List duration/distance uses directly understood file-session values, or a single
TCX lap with its own semantics. Hover text identifies the source context.
Unestablished CSV units are not guessed or promoted into converted list summaries;
thin review exposes attributable supplied values/units and repeated-column context.

A single supported FIT Source retains the accepted chart, source summaries,
on-demand best-20 and provenance behavior. Its header now uses the preferred
source title. GPX, TCX, CSV-only and multiple-FIT cases have a useful thin review
of associated metadata, summaries and evidence availability. Native evidence that
exists but has no supported detailed review remains explicitly available evidence;
CSV-only native signals remain unavailable rather than zero or observed absent.
Nonexistent/malformed IDs remain safe 404s. No synthetic chart or best-20 is added.

## Automated verification

```bash
.venv/bin/python -m unittest discover -s tests
```

**142 tests passed** (all 123 accepted P1/P2-01 tests plus 19 focused P2-02 tests).
The final suite completed in 5.004 seconds, with loopback access for existing HTTP
server tests. No test was removed or weakened.

New generated-fixture coverage checks bounds/pages/counts; cycling/all/types/subtypes;
casefolded partial title search, retained prior titles and punctuation; one-/two-sided
dates and unknown timezone/day preservation; alternate sorts, zero/missing values
and stable ties; preserved GET state; invalid input/no results; HTML escaping and
latest non-empty title preference; derived fallback; metadata immutability; absence
of native-record queries while browsing; enriched FIT's unchanged native best-20;
TCX/GPX/CSV-only stable routes; browser-local file date versus unparsed CSV text; safe UUID
routes; and ambiguous FIT evidence without guessed source selection. Four added
checks cover dedicated Date structure/local-time hooks, local calendar boundaries
in winter/summer and around daylight-saving transitions, unknown-zone immutability,
and invalid/missing timezone behavior. The prior UTC-day test is strengthened to
assert both the local-day match and exclusion on the differing UTC day.

## Full-history local acceptance

The local-only review store was prepared for the initial Gate 1 run: seeded with
the accepted Phase 1 representative and populated through the accepted production
ZIP importer. The correction/restart/browser checks use that unchanged full-history
store; this presentation task does not reimport or replace source evidence.

Private input paths are redacted; command shapes were:

```bash
.venv/bin/python -m rideworks --data-dir '<local-review-store>' import-fit '<representative.fit.gz>'
.venv/bin/python -m rideworks --data-dir '<local-review-store>' import-strava-export '<local-export.zip>'
```

Import result: **1,434 rows**, **1,433 new Activities plus one seed reused/enriched**,
**1,421 referenced files** (1,420 imported plus one reused), **13 CSV-only Activities**,
**zero failures**, **zero unresolved associations**. Final population: 1,434.
Types: 1,264 Virtual Ride / 146 Ride / 22 Run / 1 Walk / 1 Rowing.
Formats: 1,264 FIT.GZ / 29 GPX / 76 GPX.GZ / 52 TCX.GZ.
Original source input was never modified; accepted working stores were not replaced.

Reproducible HTTP acceptance:

```bash
.venv/bin/python tools/verify_rideworks_browser.py \
  --data-dir '<local-review-store>' --representative '<representative.fit.gz>'
```

This starts two successive verification server processes on port 8767, checks
process ownership of the port, and stops each afterward. Full population,
root bounds/default order, different page 2 and return, all/type filters,
private-title search/display, date range with an explicitly supplied test timezone, deterministic alternate sorts,
representative enrichment, real FIT/TCX/GPX/CSV-only routes, privacy, SQLite integrity
and foreign keys pass. Results are identical across restart.

The representative's rich FIT review retains **118 W** source average and
**120 W** displayed best-20, alongside 3,621 native records. Both browser list and
header show its actual title; title provenance is source-supplied Strava export,
while chart/summary/native analysis remains FIT. The private title is not published.

Full-history root was 18,492 HTML bytes and about 152 ms in one local application
measurement; this is practical single-rider behavior, not a performance guarantee.

## Actual browser verification

Chromium was opened through the Playwright CLI skill with its managed Chromium
configuration. After establishing session `rideworks-p2-02` on the local server,
verification is reproducible with:

```bash
.venv/bin/python tools/verify_rideworks_browser_ui.py \
  --data-dir '<local-review-store>' --representative '<representative.fit.gz>' \
  --session rideworks-p2-02 --port 8766
```

The Python helper injects private local sample data into the checked-in CLI
run-code template, emits aggregate JSON only, and leaves private CLI artifacts
local/ignored. It uses the installed cached Playwright CLI, not a frontend test
framework or runtime dependency. The skill wrapper initializes `open`; the cached
CLI is called directly for subsequent commands because its current non-open
commands reject the wrapper's injected `--config` flag.

Actual DOM/browser interactions passed: first/second/previous pages, cycling/all
and individual type form submission, private-title search, From/To inputs, all
alternate sorts/reload stability, opening each real format from a result row,
rich title/provenance/native chart and keyboard inspection, thin-review availability,
and browser back navigation. Separate Chromium contexts in **America/Los_Angeles**,
**Asia/Tokyo** and **UTC** independently verified rendered local days against native
`Intl` calendar output, actual date-filter matches, exclusion on the differing UTC
day for a real midnight-crossing Source, and unchanged unknown-zone CSV-only dates.
The Date cell is outside Title in the DOM and independently scannable geometrically.
No horizontal overflow at **1448×1086**, **1024×900**
or **390×844**. Desktop screenshots were visually inspected for shell continuity,
filter density, readable rows, source-title enrichment and honest thin review.
Owner visual/usability approval remains pending. A four-pixel phone-summary overflow
detected by the strengthened browser run was corrected and the complete run repeated
successfully. Updated screenshots show the final Date-column presentation.

## Owner review startup and local screenshots

**Review this full-history instance: http://127.0.0.1:8766/**. It is running against
`local_data/p2-02-review` and shows **1,410 cycling / 1,434 total Activities**.
The older port-8765 process may still point to the separate one-Activity Phase 1
store. That is not the P2-02 review instance; use port 8766 and these counts to
confirm the correct store. The README makes this distinction explicit.
From repository root, its exact startup command is:

```bash
.venv/bin/python -m rideworks --data-dir local_data/p2-02-review serve --port 8766
```

Local-only screenshot paths:

- `output/playwright/p2-02-activities-desktop.png`
- `output/playwright/p2-02-noncycling-desktop.png`
- `output/playwright/p2-02-enriched-fit-desktop.png`
- `output/playwright/p2-02-csv-only-desktop.png`

These screenshots and all personal databases/source data/private browser snapshots
are ignored and are not attached, published or committed. `acceptance.json` contains
exact aggregate import/HTTP/Chromium outputs and test count, without private titles,
Activity IDs, native streams, coordinates, credentials or personal input paths.

## Required next decision

Under JIT §22 Gate 1, Owner reviews the full-history browser's visual/usability
result and records approval or bounded corrections. Keep P2-02 `in_progress` and
PR #14 open. After explicit Owner approval, record it and stop at Gate 2
**HARD — Analyst**. P2-03 has not begun.
