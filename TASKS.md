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

**Acceptance contract:** `docs/PHASE_1_ACCEPTANCE.md`

### P1-01 — Durable single-FIT activity import

**Status:** pending

**Purpose:** Import the Phase 1 representative FIT as a durable application-owned Activity + Source, preserve the original artifact unchanged, and persist the minimum typed source evidence/native streams needed by Phase 1.

**Scope summary:**

* use the representative activity identified by the Phase 1 acceptance contract
* create durable application-owned Activity identity
* associate the FIT Source and preserve original artifact/integrity evidence
* extract typed source/session/stream evidence without destructive canonicalization
* preserve native timing
* support re-extraction without reacquiring the original

**Acceptance:** See `docs/PHASE_1_ACCEPTANCE.md`; detailed acceptance will be expanded in `docs/tasks/P1-01.md`.

**Dependencies:** DESIGN-001, DESIGN-002, and Phase 1 acceptance contract complete.

---

### P1-02 — Single-ride analysis core

**Status:** pending

**Purpose:** Produce the trusted analytical inputs needed by the Phase 1 activity-review experience.

**Scope summary:**

* expose the required FIT-backed summary evidence
* expose native power and heart-rate streams
* calculate reproducible best 20-minute power as an application derivation
* keep source summaries and application derivations distinct
* provide verification suitable for later UI consumption

**Acceptance:** See `docs/PHASE_1_ACCEPTANCE.md`; detailed acceptance will be expanded in `docs/tasks/P1-02.md`.

**Dependency:** P1-01 complete.

---

### P1-03 — Activity review experience and Phase 1 acceptance

**Status:** pending

**Purpose:** Turn the Phase 1 evidence and analysis into the first useful rider-facing post-ride review experience.

**Scope summary:**

* activity identity/header
* required summary metrics
* native-timing power and heart-rate review
* best 20-minute result
* practical provenance/inspectability details
* implement the approved Strava Activity screen mockup as the preferred layout/visual reference, using only capabilities genuinely available in Phase 1
* Owner visual/usability acceptance against both the representative ride and the approved mockup

**Acceptance:** `docs/PHASE_1_ACCEPTANCE.md` plus the future `docs/tasks/P1-03.md`.

**Dependency:** P1-02 complete.

---

## Follow-up work

Phase 1 is now defined by a product acceptance contract and three ordered implementation tasks. No implementation task is authorized until the Analyst authors the corresponding JIT. Phase 2 remains historical context and ride comparison; do not pull Phase 2 features into Phase 1 merely because they are convenient to implement.
