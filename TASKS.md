# TASKS.md

## Status values

```text
pending
in_progress
blocked
done
```

Only one implementation/research task should normally be `in_progress`.

---

## Planned work

### STRAVA-001 — Inventory latest Strava bulk export

**Status:** done

**Purpose:** Inspect Ken's latest local Strava bulk export and produce a compact, reproducible inventory that tells us what source data actually exists before detailed import design begins.

**Scope summary:**

* inspect the export structure and `activities.csv`
* inventory activity-file formats and historical coverage
* identify associations, obvious gaps, and unusual cases useful for later investigation
* produce compact machine-readable and human-readable outputs suitable for Analyst review
* keep the raw export and personal activity archive out of Git

**Acceptance:** See `docs/tasks/STRAVA-001.md`.

**Dependency:** Workflow bootstrap complete.

---

### STRAVA-002 — Deep inspect representative activity files

**Status:** done

**Purpose:** Deeply inspect the STRAVA-001 diagnostic candidates and compare source-file evidence with Strava CSV metadata before making importer or historical-data-model decisions.

**Scope summary:**

* parse the 23 candidate FIT/TCX/GPX files at a diagnostic level
* compare source-file evidence with corresponding `activities.csv` rows
* characterize signal availability, timing behavior, device/session/lap metadata, and power provenance evidence
* characterize the 13 CSV rows without filename references
* keep raw activity streams and personal source files out of Git

**Acceptance:** See `docs/tasks/STRAVA-002.md`.

**Dependency:** STRAVA-001 complete.

---

### STRAVA-004 — Strava activity-stream enrichment and FIT comparison

**Status:** in_progress

**Purpose:** Validate current Strava activity streams against preserved FIT evidence on the four accepted overlap rides, then—only if the evidence supports it—use bounded post-export Strava stream enrichment to power honest Activity Review graphs for API-only rides.

**Scope summary:**

* fetch only time/watts/heartrate/cadence/moving streams for the four live overlap rides first
* compare Strava stream metadata, timing and values against preserved FIT evidence
* experimentally compare best-20 only when API timing independently satisfies accepted complete-window semantics
* preserve API stream provenance distinctly from FIT/native-file evidence
* keep FIT-backed review authoritative when a supported FIT exists
* allow API-only post-export rides to gain stream-backed power/HR charts when evidence is adequate
* keep trusted Performance eligibility unchanged in this task
* perform only bounded recent/post-export stream access; no historical stream harvest

**Acceptance:** See `docs/tasks/STRAVA-004.md`.

**Allowed invocation:** `/TASK` or `/AUTOTASK`.

**Current result:** Stage A comparison and Stage B implementation verified on draft [PR #18](https://github.com/k14krug/my_strava/pull/18); stopped at Gate 1 — HARD — Owner. Four exact power/HR overlaps; seven API-only charts (five power+HR, two HR-only); 236 full / 50 focused tests and Chromium/restart/idempotence/integrity checks passed. Trusted Performance remains 1,022 eligible / 0 pending. See `reports/STRAVA-004/verification.md`. Awaiting Owner review; Analyst acceptance remains pending.

**Dependency:** Phase 2 accepted / complete.

---

### STRAVA-003 — Historical data-coverage census

**Status:** done

**Purpose:** Quantify the source-data characteristics discovered by STRAVA-001/002 across the complete Strava export so later historical-data design is grounded in prevalence, not a 23-file sample.

**Scope summary:**

* account for all 1,434 CSV rows and attempt all 1,421 referenced activity files
* quantify FIT/TCX/GPX signal and structural coverage by year and activity cohort
* quantify Ride and Virtual Ride evidence combinations relevant to later historical analysis and estimated-power research
* keep source record power, source summary power, and Strava CSV power metadata distinct
* quantify recording/timestamp characteristics and parse/outlier conditions
* produce a durable findings document separating evidence, unknowns, implications, and candidate design decisions

**Acceptance:** See `docs/tasks/STRAVA-003.md`.

**Dependency:** STRAVA-002 complete.

---

### DESIGN-001 — Durable activity and provenance model

**Status:** done

**Purpose:** Establish the conceptual model for durable Activity identity, source evidence, provenance, historical state, derivations, and conservative source reconciliation before storage/import implementation design.

**Decision:** See `docs/design/DESIGN-001.md`.

**Dependency:** STRAVA-003 complete.

---

### DESIGN-002 — Source-centered storage and import representation

**Status:** done

**Purpose:** Translate DESIGN-001 into the simplest practical logical storage/import representation while preserving immutable source evidence, typed normalized extraction, native timing, historical context, and reproducible derivations.

**Decision:** See `docs/design/DESIGN-002.md`.

**Dependency:** DESIGN-001 complete.

---

## Phase 1 — Useful single-ride review

**Status:** accepted / complete — P1-03 accepted at Gate 2 and PR #12 merged on 2026-10-04.

**Acceptance contract:** `docs/PHASE_1_ACCEPTANCE.md`

### P1-01 — Durable single-FIT activity import

**Status:** done

**Purpose:** Import the Phase 1 representative FIT as a durable application-owned Activity + Source, preserve the original artifact unchanged, and persist the minimum typed source evidence/native streams needed by Phase 1.

**Scope summary:**

* use the representative activity identified by the Phase 1 acceptance contract
* create durable application-owned Activity identity
* associate the FIT Source and preserve original artifact/integrity evidence
* extract typed source/session/stream evidence without destructive canonicalization
* preserve native timing
* support re-extraction without reacquiring the original
* establish a clean RideWorks application/runtime boundary with no compatibility obligation to the retired Strava application; legacy application code may be ignored or removed if that is simpler

**Acceptance:** See `docs/PHASE_1_ACCEPTANCE.md` and `docs/tasks/P1-01.md`.

**Dependencies:** DESIGN-001, DESIGN-002, and Phase 1 acceptance contract complete.

---

### P1-02 — Single-ride analysis core

**Status:** done

**Purpose:** Produce the trusted analytical inputs needed by the Phase 1 activity-review experience.

**Scope summary:**

* expose the required FIT-backed summary evidence
* expose native power and heart-rate streams
* define the narrow complete-window semantics for the representative ride and calculate reproducible best 20-minute power as an application derivation
* independently verify the 20-minute result without using the production calculation as its own oracle
* keep source summaries and application derivations distinct
* provide verification suitable for later UI consumption

**Acceptance:** See `docs/PHASE_1_ACCEPTANCE.md` and `docs/tasks/P1-02.md`.

**Dependency:** P1-01 complete.

---

### P1-03 — Activity review experience and Phase 1 acceptance

**Status:** done

**Purpose:** Turn the Phase 1 evidence and analysis into the first useful rider-facing post-ride review experience.

**Scope summary:**

* activity identity/header
* required summary metrics
* native-timing power and heart-rate review
* best 20-minute result
* practical provenance/inspectability details
* implement `docs/mockups/activity-review.png` as the preferred layout/visual reference, using only capabilities genuinely available in Phase 1
* use the **RideWorks** product name consistently in the user-facing application shell
* integrate the settled RideWorks branded application icon/mark assets from the parallel branding workstream and obtain Owner visual approval
* define the narrow first user journey: start RideWorks, open/select the imported ride, reopen it after restart, and use appropriate units/timezone/chart interaction
* Owner visual/usability acceptance against both the representative ride and the approved mockup

**Acceptance:** `docs/PHASE_1_ACCEPTANCE.md` and `docs/tasks/P1-03.md`.

**Dependency:** P1-02 complete.

---

## Phase 2 — Historical context and performance history

**Status:** accepted / complete — P2-01 through P2-05 accepted; PR #17 merged on 2026-10-05.

**Acceptance contract:** `docs/PHASE_2_ACCEPTANCE.md`

### P2-01 — Historical Strava-export import and enrichment

**Status:** done

**Purpose:** Import the complete known Strava-export activity history through one durable, idempotent RideWorks workflow, preserving real source titles, CSV evidence, referenced FIT/TCX/GPX artifacts, CSV-only activities, and conservative source associations.

**Scope summary:**

* account for all 1,434 known export rows
* import/preserve all 1,421 referenced activity artifacts
* retain the 13 CSV-only activities without fabricating streams
* preserve actual source activity titles with provenance
* support FIT/TCX/GPX production import for the known export envelope
* migrate the accepted Phase 1 store safely
* enrich the already-imported Phase 1 representative Activity rather than duplicating it
* make reruns idempotent and failures explicit
* expose a source-aware history read boundary for later Phase 2 work

**Acceptance:** `docs/PHASE_2_ACCEPTANCE.md` and `docs/tasks/P2-01.md`.

**Allowed invocation:** `/TASK` or `/AUTOTASK`.

**Acceptance result:** accepted by Analyst on PR #13 and merged to `main` as `57c00ae396bfb1e9c2c4c72ff42c5628afda9940`. Complete 1,434/1,421/13 seeded acceptance and restart/idempotent rerun passed.

**Dependency:** Phase 1 accepted; Phase 2 acceptance contract complete.

---

### P2-02 — Scalable Activities browser

**Status:** done

**Purpose:** Make the full imported history practical to browse rather than rendering an unbounded list.

**Scope summary:**

* newest-first bounded pagination
* title search
* activity type/subtype filtering
* practical date filtering
* useful sorting
* source title presentation with derived fallback when necessary
* stable Activity Review navigation
* preserve the approved RideWorks visual character without recreating irrelevant Strava management features

**Acceptance:** `docs/PHASE_2_ACCEPTANCE.md` and `docs/tasks/P2-02.md`.

**Acceptance result:** Owner and Analyst accepted the corrected browser on PR #14; merged to `main` as `683c9880bb0b6ed1cd9569a58be61093ec2cce0e`. 142 tests and full-history HTTP/restart/Chromium checks passed, including multiple timezones and single-line local date/time.

**Allowed invocation:** `/TASK` or `/AUTOTASK`.

**Dependency:** P2-01 complete.

---

### P2-03 — Trusted 20-minute performance history

**Status:** done

**Purpose:** Build the first trusted longitudinal performance view from eligible Virtual Ride native source-power evidence.

**Scope summary:**

* reuse accepted `best-average-power-v1` complete-window semantics
* derive durable/versioned best-20 history from eligible Virtual Ride native streams
* exclude outdoor Ride power from the trusted Phase 2 trend
* never substitute CSV/source-summary watts for missing native streams
* present chronological 20-minute-power history with links to contributing activities
* make eligibility/provenance inspectable

**Acceptance:** `docs/PHASE_2_ACCEPTANCE.md` and `docs/tasks/P2-03.md`.

**Allowed invocation:** `/TASK` or `/AUTOTASK`.

**Acceptance result:** Owner and Analyst accepted the final Performance experience on PR #15; merged to `main` as `4f1a58d39177887e965ddd1a74db95c62c17e0b0`. 170 full / 28 focused tests passed; all 1,434 Activities accounted for and all 1,022 eligible trusted results independently verified.

**Dependency:** P2-02 complete.

---

### P2-04 — Six-week historical context in Activity Review

**Status:** done

**Purpose:** Put an eligible ride's best-20 result into recent historical context.

**Scope summary:**

* compare current eligible best-20 with the highest eligible result in the preceding 42 days
* exclude the current activity from its own baseline
* show unavailable when no eligible baseline exists
* keep presentation neutral rather than assuming higher/lower is inherently good/bad
* connect Activity Review to the trusted Performance history
* no manual pairwise ride-comparison feature

**Acceptance:** `docs/PHASE_2_ACCEPTANCE.md` and `docs/tasks/P2-04.md`.

**Allowed invocation:** `/TASK` or `/AUTOTASK`.

**Acceptance result:** Owner and Analyst accepted PR #16; merged to `main` as `16ef375434700ab7d2b5fb3a5c2cae000e049c12`. 186 tests passed; all 1,022 eligible comparisons independently verified (1,012 with prior baseline / 10 unavailable), with no archive/source reprocessing.

**Dependency:** P2-03 complete.

---

### P2-05 — Incremental Strava synchronization

**Status:** done

**Purpose:** Bring post-export activities and useful Strava metadata into RideWorks through a normal forward-looking sync path.

**Scope summary:**

* current Strava OAuth/API behavior re-verified from authoritative documentation in the JIT
* normal incremental/forward sync rather than historical bulk API harvesting
* user-invoked sync is acceptable for the first private single-rider implementation
* create new Activities or conservatively enrich existing local/FIT Activities
* retain Strava source identity/title/type/useful metadata with provenance
* keep credentials/tokens local and out of Git
* obey current rate-limit/terms/webhook obligations without enterprise sync infrastructure

**Acceptance:** `docs/PHASE_2_ACCEPTANCE.md` and `docs/tasks/P2-05.md`.

**Allowed invocation:** `/TASK` or `/AUTOTASK`.

**Acceptance result:** Owner and Analyst accepted PR #17; merged to `main` as `e78c8a6c2de4f4e21aaa2937ae33d1e011901947`. 219 tests passed; live sync created 7 post-export Activities, enriched 4 overlaps with no duplicates, restart reruns were idempotent, and explicit rebuild cleared 11 pending Performance results.

**Dependency:** P2-04 complete.

---

## Follow-up work

Phase 1 and Phase 2 are accepted and complete. STRAVA-004 is in progress at its HARD — Owner review gate. Phase 3 dashboard work remains not started.

Manual pairwise ride-to-ride comparison is not a Phase 2 requirement. It remains an optional future interaction if a concrete use case emerges.

Outdoor power remains preserved source evidence but is excluded from the trusted Phase 2 performance trend. Outdoor estimated-power reconstruction remains separate future work.

Phase 3 must not begin automatically after Phase 2.
