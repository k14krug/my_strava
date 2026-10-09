# Phase 3 Acceptance — Useful Dashboard

**Status:** accepted / complete — Owner and Analyst accepted PR #19 on 2026-10-08  
**Phase goal:** Make RideWorks useful before opening an individual Activity.  
**Primary question:** **How am I doing overall right now?**  
**Merge:** `5e5bceed0244ae1fa64ec3a45a101f49be5b8f15`

## 1. Product decisions controlling Phase 3

The Owner explicitly settled these decisions before Phase 3 implementation:

1. **Annual cycling mileage is the first RideWorks goal.**
2. **Virtual Ride mileage counts fully toward the annual cycling mileage goal.**
3. **Outdoor Ride mileage also counts.** The Phase 2 power-quality exclusion for outdoor rides does not affect distance/goal eligibility.
4. **File-backed distance is preferred when available.**
5. Reuse the accepted history-presentation distance boundary rather than inventing a generic canonical distance:
   - first understood file-backed session distance;
   - then current Strava API summary distance;
   - never guess units from unspecified CSV-only values;
   - retain provenance and alternatives in source evidence.
6. Phase 3 should implement a **useful subset** of the supplied dashboard direction. It must not invent Fitness Score, training load, recovery/readiness or adaptive planning merely to imitate the mockup.
7. A yearly goal target is **not** inferred from the mockup. The rider sets the target explicitly.

These decisions refine GOAL-001/002/003, DASH-001 through DASH-006 and the Phase 3 delivery outcome in `docs/PRODUCT_REQUIREMENTS.md`.

## 2. Phase 3 user-visible outcome

After Phase 3, opening RideWorks at `/` should provide a useful overview without requiring the rider to open Activities or Performance first.

The first dashboard must answer, at a glance:

- How much have I ridden recently?
- How am I progressing toward my annual mileage goal?
- What is my current 20-minute Performance context?
- What were my most recent rides?
- Is there a recent, explainable change worth noticing?

The dashboard is a summary/navigation surface. Detailed evidence stays available on Activities and Performance.

## 3. Navigation and routes

### 3.1 Home becomes the dashboard

`/` becomes **Home**.

The sidebar becomes:

- Home
- Activities
- Performance
- Settings

The Activities browser moves to `/activities`.

All internal links, pagination, filter forms and tests must use `/activities`.

For practical compatibility, a request to `/` carrying the old Activities-browser filter parameters
(`q`, `type`, `from`, `to`, `sort`, `page`, `tz`) should redirect to the equivalent
`/activities?... ` URL rather than silently interpreting those parameters as dashboard state.

The RideWorks brand link opens Home.

### 3.2 Activity routes remain stable

Existing `/activities/<activity_id>` routes remain unchanged.

## 4. Annual cycling mileage goal

### 4.1 Narrow first goal model

Do **not** build a generic goal engine.

Persist only the narrow concept needed now:

- calendar year;
- annual cycling mileage target in miles;
- updated-at timestamp.

One target per year is sufficient.

A simple year-specific setting is preferred over a generic polymorphic goal schema.

### 4.2 Settings behavior

Settings gains an **Annual cycling mileage goal** section for the current browser-local calendar year.

The rider may:

- set/update the current-year target in miles;
- clear the target.

Validation:

- numeric;
- finite;
- greater than zero;
- reasonable bounded input (implementation may choose a simple high bound such as 100,000 mi);
- no silent coercion of invalid input.

Use the existing local POST/action-nonce pattern. No account/profile system.

If no target exists, Home must still show actual YTD mileage and a clear **Set annual goal** link/action to Settings.

Do not seed the mockup's 2,500 mi example or any other default.

### 4.3 Goal contribution rules

The annual cycling mileage goal includes Activities whose current presentation classification is cycling:

- Ride;
- Virtual Ride;
- equivalent accepted cycling/biking classification.

It excludes Run, Walk, Rowing and other non-cycling Activities.

**Virtual Ride mileage counts exactly like outdoor Ride mileage.**

Distance contribution for each Activity uses the accepted `history.presentation(snapshot)` distance selection:

1. understood file-backed distance when present;
2. otherwise current Strava API summary distance;
3. otherwise distance unavailable and excluded from the mileage total.

Do not use Strava CSV distance when its source units are unspecified.

Known zero distance is valid and contributes zero.

The dashboard should retain enough aggregate provenance to say how many contributing Activities used file distance, API distance, or had distance unavailable.

### 4.4 Calendar/timezone semantics

Dashboard calendar aggregates use the rider's **browser timezone** for absolute timestamps.

- YTD = January 1 through the current local date/time.
- Last 7 days = the trailing seven calendar days ending today, inclusive.
- Current-year goal uses the browser-local current year.

For a source date that has a supported date but unknown timezone, use the supplied source date as already represented by the accepted history presentation; do not invent an offset.

Activities with no supported date cannot contribute to time-bounded dashboard mileage. Count them as excluded/missing-date evidence rather than silently placing them in a period.

The dashboard must make the browser timezone available server-side using the same bounded local-time pattern already used by Activities. Do not use server timezone as a hidden substitute.

### 4.5 Targeted historical summary reconciliation

Phase 3 acceptance additionally requires reconciliation of the eight known 2026
outdoor Ride Activities that currently have preserved GPX + export evidence and
established Strava IDs but no known-unit retained distance.

The Owner authorized up to eight direct `GET /activities/{id}` Strava summary
requests for these established IDs only.

Requirements:

- use existing `activity:read_all` authorization;
- sequential requests, accepted token/rate-limit behavior;
- no historical list crawl and no stream requests;
- persist through the existing Strava summary allowlist/provenance model;
- retain GPX originals unchanged;
- current API summary distance/duration may fill presentation values only when
  the preferred file summary value is unavailable;
- reruns are idempotent;
- normal future Sync now must already provide this fallback for newly observed
  rides, so this is a bounded historical repair rather than an ongoing crawl.

Phase 3 is not accepted until the post-enrichment YTD total is independently
reconciled against the Owner-reported approximately 1,631-mile Strava total or
any residual difference is explicitly explained.

## 5. Dashboard contents

The supplied dashboard mockup is visual direction, not a literal feature checklist.

### 5.1 Top summary cards

The first useful dashboard should contain three prominent summary cards:

1. **Recent Mileage**
   - **This Week:** actual cycling distance from the current local Monday through today;
   - **Last 7 Days:** cycling distance over the trailing seven local calendar days;
   - include the comparison with the immediately preceding seven-day period when calculable;
   - keep wording neutral (e.g. “12.4 mi more than previous 7 days”);
   - do not duplicate annual-goal information here;
   - on desktop, the two mileage submetrics may sit side-by-side inside the card;
   - on phone, stack them cleanly.

2. **Current 42-day best**
   - reuse current Performance-v2 evidence and accepted `performance_view` semantics;
   - watt value and contributing Activity link;
   - no new power model.

3. **Latest eligible 20-minute ride**
   - latest current Performance-v2 eligible result;
   - watt value/date/Activity link;
   - if recent-context is available, show neutral difference from the prior six-week best.

Cards show Unavailable rather than inventing values.

Do **not** put Current FTP, Fitness Score, Training Load, readiness or a generalized Power Curve on the Phase 3 dashboard.

### 5.2 Recent Activities

Show approximately the six newest cycling Activities.

At minimum:

- local date/time;
- title;
- Ride / Virtual Ride classification;
- distance;
- duration;
- **average power** from purpose-specific source summary evidence;
- link to Activity Review.

Recent-Activities average-power selection is:

1. understood file-backed session `avg_power`;
2. understood single-lap TCX `avg_power` when needed;
3. otherwise current Strava API summary `average_watts`;
4. otherwise Unavailable.

Do not use unspecified Strava CSV power or recalculate this table value from
stream samples.

Use accepted presentation evidence/provenance.

A **View all Activities** link opens `/activities`.

Do not add workout tags, training-load values or inferred ride purpose in Phase 3.

### 5.3 Mileage Progress

Provide a meaningful annual-mileage visualization.

Preferred first representation:

- completed recent-week cycling-distance bars (approximately 11 completed weeks);
- a current partial-week bar showing **actual Monday-through-today cycling miles**;
- an overlaid historical **needed miles/week** line showing, after each completed week, the weekly average still required to reach the annual target by year end;
- YTD actual/target progress below or beside it;
- miles remaining and current needed average miles/week below YTD progress.

The exact chart geometry is implementation-level. The required meaning is:

- completed-week actual cycling miles;
- current partial-week actual bar, visually identifiable as incomplete but using the same actual-mile semantics as every other bar;
- historical/current needed-miles-per-week line;
- clearly defined local calendar buckets;
- YTD actual and target;
- miles remaining;
- current needed average miles/week;
- target pace context when a target exists.

Weekly required pace at a completed week is calculated from cumulative actual
mileage through that Sunday and the remaining days after that Sunday. The
current required pace uses actual YTD mileage through today and remaining days
after today. If the goal is met, required pace is zero; if no calendar time
remains while miles remain, it is Unavailable.

The current week's actual mileage must agree between the This Week Miles card,
the current chart bar and the diagnostic payload.

No smoothing or inferred missing mileage.

### 5.3.1 Mileage chart interaction

Weekly bars and required-pace points must use an immediate custom
RideWorks tooltip/readout rather than relying on delayed native SVG
`<title>` behavior.

On pointer hover/focus, show **only the mileage value and unit** (for example
`57.3 mi`), not the date/week label. Pointer response should be immediate;
pointer leave hides it. Keyboard focus must expose the same value.

### 5.4 20-minute Performance snapshot

Reuse current Performance-v2 history rather than adding a power curve.

A compact dashboard chart/snapshot may show:

- rolling 42-day best over a useful recent range (for example six months or one year); and/or
- the latest eligible 20-minute results.

It should link to the full Performance page.

Do not implement arbitrary-duration power curves in Phase 3.

### 5.5 Useful insights

Phase 3 may show only deterministic, explainable insights from already accepted evidence.

Initial allowed insight types:

- annual mileage ahead/behind linear calendar pace;
- latest eligible best-20 relative to its accepted previous-six-week context;
- a new current 42-day best when that is directly supported by Performance-v2 history.

Do not label this area “AI Insights” unless actual AI behavior is later designed and approved.

Do not generate motivational or training-prescriptive text.

If no useful insight is supported, omit the section or show a quiet “No notable change” state rather than filling space.

### 5.6 Sync status

Home may show current Strava connection/last-successful-sync status using already retained local sync state.

A Settings link is sufficient. Phase 3 does not add background sync.

## 6. Goal pace calculation

When a target is configured:

```
calendar_fraction =
  elapsed local calendar days through today / total days in current local year

target_to_date = annual_target_miles * calendar_fraction
pace_difference = actual_ytd_miles - target_to_date
```

Use the local calendar date, not a fixed 365-day denominator. Leap years must work.

The display is neutral:

- “18 mi ahead of calendar pace”
- “18 mi behind calendar pace”
- “On calendar pace”

Do not claim this is the training volume the rider *should* have completed. It is only linear progress toward the rider's mileage target.

## 7. Distance aggregation provenance

Mileage aggregates are presentation/goal calculations, not canonical Activity facts.

For every aggregate calculation retain/return enough diagnostic information to inspect:

- contributing Activity count;
- file-distance contribution count and miles;
- API-distance contribution count and miles;
- distance-unavailable count;
- date-unavailable count;
- activity classifications included/excluded;
- browser timezone and period boundaries.

This diagnostic evidence may be collapsed/secondary in the UI.

Do not persist cheap weekly/YTD aggregates merely because they appear on the dashboard; recalculate them from durable Activity/source evidence unless measurement shows a real need to persist.

## 8. Performance integration

Phase 3 consumes, but does not redefine, STRAVA-004:

- current policy: `virtual-power-evidence-v2`;
- method: `best-average-power-v1`;
- 1,200 s;
- file/API eligibility and provenance rules unchanged;
- automatic post-sync convergence unchanged;
- exception-only Performance freshness banner unchanged.

If Performance is pending/incomplete, dashboard Performance cards/charts must not silently plot stale/missing results. Reuse the existing exception banner behavior.

## 9. Deferred mockup elements

The following visible mockup concepts are intentionally **not Phase 3 requirements**:

- Current FTP card/history — requires explicit historical FTP design;
- Fitness Score / Fitness Trend — Phase 5 training-state model;
- Training Load — Phase 5 model selection;
- Next Workout / Plan navigation — Phase 4 planned-workout representation;
- “Tomorrow should be easy because you raced” — Phase 4/5 interpretation;
- adaptive seven-day plan — Phase 6;
- FTP update suggestion — later evidence/athlete-state decision;
- full arbitrary-duration Power Curve — future Performance enhancement;
- AI Usage / AI summary surfaces — no approved product role yet.

Do not create placeholder calculations for these concepts.

## 10. Visual direction

Use the supplied dashboard mockup as layout/visual inspiration:

- strong summary cards;
- recent activities as the main content block;
- useful right/bottom summary panels;
- restrained RideWorks blue/green visual language;
- information-dense but not cramped;
- desktop first, usable on phone.

Preserve the accepted RideWorks brand assets and established visual character.

Do not clone irrelevant Strava/Zwift/provider branding from the mockup.

## 11. Acceptance evidence

Phase 3 is accepted only after live browser verification against the accepted review store.

Required evidence:

1. Home at `/`; Activities at `/activities`.
2. Annual mileage target can be set/changed/cleared through Settings.
3. No default goal is invented.
4. Virtual Ride and outdoor Ride distances both contribute.
5. File-backed distance wins over API distance on a controlled overlap example.
6. API distance supplies an API-only recent ride.
7. Unspecified CSV-only distance is not guessed.
8. YTD / last-7 / prior-7 aggregates independently reproduce from source evidence.
9. Browser timezone boundary checks in at least Los Angeles and Tokyo.
10. Leap-year pace unit test.
11. Goal percentage/miles remaining/ahead-behind pace and current needed miles/week independently reproduce.
12. Historical/current needed-miles/week line independently reproduces from cumulative actual mileage and remaining calendar time; current chart bar independently matches actual This Week Miles.
13. Mileage chart tooltip responds immediately and shows only miles, not dates.
14. Recent Activities links/evidence/Avg Pwr match the accepted source-precedence rules and Activities history.
15. Current 42-day best/latest eligible cards match Performance.
16. Compact Performance visualization matches Performance-v2 source points.
17. Insight statements reproduce from accepted deterministic evidence.
18. Normal successful Sync now updates dashboard data without a second rebuild action.
19. Performance update failure state remains visible on Home.
20. Restart retains goal setting and produces the same dashboard.
21. Desktop and phone Chromium layouts have no overflow/unusable controls.
22. Full automated regression suite passes.
23. The eight identified YTD outdoor rides receive only bounded established-ID
    Strava summary enrichment; selected distances/durations and provenance
    independently verify, and distance-unavailable count is recomputed.
24. Post-enrichment RideWorks YTD mileage and residual difference versus the
    Owner-reported approximately 1,631-mi Strava total are explicitly
    reconciled.
25. A focused normal-sync test proves future Strava-synchronized GPX rides can
    receive API summary distance/duration fallback without historical crawling.
26. Phase 4/5/6 concepts remain unimplemented.

## 12. Owner acceptance

At HARD — Owner, provide the running Home dashboard and Settings goal section.

The Owner should be able to answer:

- Does Home tell me something useful before I open a ride?
- Is annual mileage progress prominent enough?
- Does Virtual mileage count as expected?
- Is goal pace understandable rather than judgmental?
- Are recent rides and 20-minute Performance useful at a glance?
- Does the dashboard avoid fake Fitness/Training/Plan concepts?

Explicit Owner approval precedes Analyst acceptance.

## 13. Analyst acceptance

After Owner approval, verify:

- mileage evidence selection/provenance;
- timezone/calendar math;
- annual goal persistence and no generic-goal overbuild;
- Performance-v2 reuse without policy drift;
- deterministic insights;
- route/navigation regression;
- sync/freshness behavior;
- independent aggregate checks;
- full tests/Chromium/restart/integrity.

Only then mark Phase 3 accepted.

Phase 4 must not begin automatically.
