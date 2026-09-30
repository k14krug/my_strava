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

## Follow-up work

Broad archive discovery is complete unless later design work identifies a specific unanswered evidence question. DESIGN-001 establishes the durable conceptual model. The next phase is to translate it into the simplest practical storage and import design for this private single-rider application; no implementation task is authorized yet.
