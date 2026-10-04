# P1-03 verification — accepted

**Date:** 2026-10-03

**Branch / PR:** `task/p1-03-activity-review` / [#12](https://github.com/k14krug/my_strava/pull/12)

**Corrected implementation:** `cba2d0d` (supersedes the pre-correction `d2c5acd` build).

**State:** accepted / complete. Owner visual/usability/branding approval and Gate 2 Analyst acceptance are complete. PR #12 was merged to `main` as `7fce07b79c907910a514d1ea842921b047fee170`. Phase 2 has not begun.

**Authority:** the [HARD — Owner correction comment](https://github.com/k14krug/my_strava/pull/12#issuecomment-5971351156) and Analyst-authored P1-03 JIT. The Owner explicitly authorized the necessary verification/status publication within its privacy limits; the former publication blocker is resolved. Screenshots and private source/runtime artifacts remain local.

## Corrections addressed

### 1. Visual refinement

The approved `docs/mockups/activity-review.png` was reinspected. The refined screen uses the mockup's 56-pixel horizontal identity header, 156-pixel navigation rail, compact breadcrumb/header, icon-led metric cards, approximately 2.15:1 chart/summary column proportions, tighter typography/spacing, restrained light surfaces and borders, and a denser inset Ride Summary table. The best-20 and provenance disclosures remain secondary. Mark/wordmark placement and scale now follow the horizontal application-header treatment.

The native chart has a compact frame, legend beneath its heading, signal-colored axes, a readable sample strip, keyboard help, and a light power fill. Each fill segment follows the observed native points and closes independently at missingness/time breaks; it never bridges a gap. No native analytical values or timestamps changed. The readout shows rider-facing elapsed/power/HR values rather than debug record IDs; native indices remain inspectable through the unchanged payload and calculation/source details.

Only real Phase 1 elements were refined. No fake Dashboard/Performance/Plan/AI navigation, Compare, insights, normalized power, training load, zones, laps/intervals UI, workout, settings, sync/profile controls or placeholder metrics were added.

### 2. Deterministic derived title and future source-title requirement

Current FIT-only evidence has no actual source activity-name field. Activities, review heading and document title now use **`Virtual Ride — Sep 29, 2026`**, visibly labeled **Derived title**. Type **Cycling** and subtype **Virtual Activity** remain separate. Source details identify the missing actual name and fallback basis.

The fallback combines the source-derived type label with the source start date normalized to UTC and fixed English month names. It does not use today's date, import time, browser locale/timezone or a presumed original name. Missing dates/types remain explicit. Automated tests cover determinism, missingness, source preservation and date-boundary offsets. Browser verification confirmed identical headings in Pacific and UTC contexts while the activity-time presentation changed appropriately.

**Owner product finding / future requirement:** durable history assembly should preserve and prefer an actual source activity title when available, with provenance (for example Strava export/API `Activity Name`), while retaining type/subtype separately. This is recorded in `TASKS.md` and `rideworks/README.md`. P1-03 adds no title persistence/reconciliation or API/export enrichment.

### 3. Optional repository .env startup configuration

`rideworks/config.py` reads only `FLASK_DEBUG`, `FLASK_RUN_PORT` and `RIDEWORKS_DATA_DIR` from the optional checkout-root `.env`. It does not search from the current directory, parse unrelated legacy keys, execute shell text, expand variables or mutate exported environment variables. A safe `.env.example` is committed; the actual `.env` remains ignored and unchanged.

Precedence is CLI > exported environment > repository `.env` > established defaults. Data-directory default remains `~/.rideworks`; server port remains 8765, with decimal values 1–65535 accepted. Debug defaults off and accepts 0/1, false/true, no/yes and off/on case-insensitively. Quotes/comments/optional `export ` and last-file-assignment behavior are documented. Relative data-directory resolution at invocation is unchanged.

`FLASK_DEBUG` enables only console GET status/response timing; errors identify the exception class without browser tracebacks or private paths. Query strings and credentials are not logged. **No Flask debugger or automatic reloader exists**, and no Flask/runtime dependency was added. Loopback binding is unchanged regardless of debug mode. See `rideworks/README.md` for syntax, precedence, validation and installed-wheel behavior.

## Branding restore / integrity

Main was fetched at task start and again before this Owner handoff; it remains `203597d`, already merged into the task branch. The original branding-source blocker stays resolved.

Exact command:

```bash
python3 docs/branding/restore_board.py --output /tmp/rideworks-brand-direction-board.webp
```

Result: **6,888 bytes**, SHA-256 **`4dd937e2dc46f929e91fc201c32d138da6395d5c4c22fbbee8965e4b5376a81c`**, RIFF/WebP identity and size verified. The previously decoded/inspected board is 350 × 262. The approved-direction local SVG mark/favicon is unchanged; only shell placement/scale changed. Navy `#0F2A44`, Blue `#2563EB`, Green accent `#10B981` and Light gray `#E5E7EB` remain the identity palette. Ken explicitly approved the applied branding with the corrected visual/usability result on 2026-10-03, as recorded below.

## Automated verification

Exact final command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

**94 tests passed in 3.008 seconds**: 16 configuration tests, 14 P1-03 web/presentation tests, and all 64 existing P1-01/P1-02/research tests. Python 3.10.12 / existing fitdecode 0.11.0 / SQLite 3.37.2; no runtime dependencies added.

New coverage includes `.env` absence/loading/quotes/comments, CLI/exported/file precedence, overridden invalid values, invalid ports/debug/syntax, no expansion or environment mutation, checkout-root lookup, empty data directories, CLI integration, import-directory configuration, safe diagnostics and actual loopback HTTP requests in both debug modes. Title tests cover list/header/document identity, explicit derivation/type separation, fixed source-date determinism, UTC date boundaries, missing evidence and the complete Owner prohibition list. Existing evidence, unit, privacy, native-preservation, source/calculation and restart tests remain passing.

## Representative browser verification

The existing ignored `local_data/p1-03-review` store was reused, without re-import or re-extraction. Its initial creation used the accepted import command:

```bash
.venv/bin/python -m rideworks --data-dir local_data/p1-03-review import-fit local_data/p1-01-input/21538875902.fit.gz
```

Exact corrected startup command, from repository root:

```bash
.venv/bin/python -m rideworks --data-dir local_data/p1-03-review serve --port 8765
```

This explicit directory/port overrides any exported or `.env` selection. The existing local debug setting enabled the documented safe request diagnostics. No `.env` contents were published.

- Activities: **http://127.0.0.1:8765/**
- Representative Activity: **http://127.0.0.1:8765/activities/367ced97-422d-4bd8-aa1a-22092ae1ae26**
- Source: `51a09743-7958-4357-aad1-ba6418d0b08d`
- Current extraction: `9aa8b087-a252-492e-b875-147a69378a09`

Chromium opened Activities and clicked the real derived-title entry. At **1448 × 1086**, the screen was visually compared with the approved mockup and locally previewed. Additional **850**, **620** and **375** pixel widths had no horizontal overflow. Calculation/Source disclosures opened and required identities, parser `fitdecode` / `0.11.0`, mapping `fit-v1`, unknown sensor origin, availability and title basis were inspected.

| Required fact | Corrected browser result |
| --- | --- |
| Title / type / subtype | Derived `Virtual Ride — Sep 29, 2026` / Cycling / Virtual Activity |
| Local activity-time labels | PDT with GMT-7 in Pacific browser; UTC with GMT+0 in UTC browser; stored timestamps unchanged |
| Elapsed / timer | **1:00:20 / 1:00:21**, distinct labels |
| Distance / ascent | **13.41 mi / 840 ft**, presentation-only SI conversions |
| FIT average / maximum power | **118 W / 136 W** |
| FIT average / maximum HR | **111 bpm / 124 bpm** |
| FIT average cadence | **77 rpm** |
| Native payload / power path / HR path | **3,621 / 3,621 / 3,621** samples |
| Power and HR availability | Both 3,621 present / 0 missing; origin unknown |
| Calculated best 20-minute | **120 W**, explicitly RideWorks-calculated, separate from FIT average |
| Method / native samples / eligible windows | `best-average-power-v1` / 1,200 / 2,422 |
| Selected best window | record indices `[204, 1404)`; elapsed **3:24–23:24** |

The browser-native JSON digest remained **`47a7a9d14eb0bf0c847e8a3cbd84f66bb9106fd0f765b66f99caa396c4307131`**, matching the independently serialized Store record projection from the prior accepted UI verification. Pointer inspection of sample 204 and keyboard inspection of the final zero-power sample matched the stored native evidence. No stream dump was committed.

A real server stop/restart with the same command reopened the identical Activity URL, derived title, extraction, record count and best result without importing. The normal request log contained only loopback pages and the three local CSS/JS/SVG assets. No external CDN/network request or browser console error/warning was required for rendering.

The existing seven-record privacy-safe synthetic browser case was repeated. Missing values/timestamps, duplicate/backward times and a forward gap remain in native order. Power draws 5 positioned samples in 3 subpaths; HR draws 4 in 4 subpaths. The new power fill also has exactly 3 independently closed segments. Keyboard inspection preserves zero and unavailable power/HR/time; no invented connecting segment or sample was added.

Browser automation used the Playwright skill's Chromium opener and underlying `npx --package @playwright/cli playwright-cli` commands for resize, snapshot, real link/disclosure clicks, requests, console and browser assertions. Local `run-code` assertions checked exact payload/count/metrics, pointer/keyboard inspection, timezone contexts, viewport overflow, provenance, synthetic breaks/fill and restart identity. The CLI tools are verification-only; no application Node/build tooling was added.

## Gate 1 — HARD — Owner approval

On **2026-10-03**, Ken explicitly approved the corrected build in the task conversation and authorized the Gate 2 handoff:

> Owner review approved. The corrected P1-03 Activity Review visual/usability/branding result is acceptable. Proceed to Gate 2 — HARD Analyst review. Keep P1-03 `in_progress` until Analyst acceptance and do not begin Phase 2.

This approval covers the corrected visual/usability result and the RideWorks mark as applied. The reviewed branch head was **`207d7d8da7253a94513f5c3c3e15e090a3b7fe78`**, containing implementation `cba2d0d` and its verification handoff. The three earlier requested corrections are implemented and verified above; no further Owner correction accompanied this approval.

This Gate 2 update changes handoff documentation only. The **94-test** and representative browser results above apply to the unchanged implementation; they were not rerun for this documentation update.

With the desired data directory and port configured in the repository-root `.env`, normal startup needs no repeated CLI settings:

```bash
.venv/bin/python -m rideworks serve
```

Use the URL printed at startup. The explicit command in the verification procedure pins the prepared review store and port 8765 independently of local settings; its recorded URLs remain the reproducible review addresses.

## Gate 2 — HARD — Analyst acceptance

On **2026-10-04**, the Analyst reviewed PR #12 at head `472bd52dfa5ee66b0e354cf619c2d7545ffb595a` against `docs/tasks/P1-03.md` and `docs/PHASE_1_ACCEPTANCE.md` and **accepted P1-03 and Phase 1**.

The review confirmed the Owner-approved implementation was unchanged apart from Gate 2 documentation, the accepted P1-01/P1-02 data and analysis boundaries remained intact, the native chart preserved evidence without interpolation/resampling/smoothing, source summaries remained distinct from the 120 W RideWorks derivation, provenance/privacy/startup requirements were met, all 94 tests remained the recorded verification set, and no Phase 2 capability had been introduced.

The durable Analyst decision is recorded on PR #12. GitHub does not permit the connected account to submit an `APPROVE` review on its own PR, so the Gate 2 decision was recorded as a top-level PR comment instead.

PR #12 was then merged to `main` as `7fce07b79c907910a514d1ea842921b047fee170`. `TASKS.md` now records P1-03 = done and Phase 1 accepted/complete. `STATUS.md` records the accepted state. No Phase 2 implementation task was started.

Only authorized compact verification/status evidence, implementation, synthetic tests and safe documentation/example settings are published. No screenshots, private absolute paths, coordinates, FIT/source files, raw streams, database files, secrets, actual `.env` contents or unrelated personal data are included.
