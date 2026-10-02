# Independent Phase 1 Readiness Review — Astra, Pass 2

**Date:** 2026-10-02  
**Reviewer:** Dex using GPT-6.0 Astra  
**Repository snapshot reviewed:** `origin/main` at `1fc90d0`  
**Status:** Review evidence; non-controlling. Accepted findings must be incorporated into controlling requirements, design documents, task briefs, or repository guidance before they become implementation instructions.

This is the second independent readiness/usability audit. It verifies corrections from the first review, directly inspects the approved mockups, and adds usability observations.

---

**1. Executive conclusion**

**Ready to author P1-01 JIT and begin Phase 1.**

The conclusion is unchanged from the first review, but confidence is higher. The corrections resolve the important documentation ambiguities without adding an architecture phase. The approved mockups are now available, identifiable, and directly inspectable.

RideWorks still has a coherent progression: understand one ride, compare rides, summarize history, connect training intent with outcomes, assess training state, then adapt planning. **P1-01 → P1-02 → P1-03 remains the right sequence.**

The most significant new observations concern the mockups:

- Their layout is useful, but their sample numbers and analytical statements are not internally consistent.
- Several prominent controls imply capabilities that must remain absent from Phase 1.
- The Dashboard emphasizes volume and fitness scores more than the product’s stated priority of 20-minute performance.
- Branding is appropriately assigned to P1-03, provided it remains a small design exercise.

I reviewed freshly fetched `origin/main` at **`1fc90d0`**, inspected both PNGs directly, verified their hashes, reran the research tests, and reproduced the legacy power defect. Review and tests used an isolated snapshot; no repository files were modified.

**2. Previous findings — verification**

| Previous finding or recent correction | Assessment | Repository evidence |
|---|---|---|
| Repository purpose and product identity | **Corrected satisfactorily.** RideWorks is consistently named in current controlling documents. Historical names remain appropriately permitted. | [AGENTS.md introduction](https://github.com/k14krug/my_strava/blob/1fc90d0/AGENTS.md#L3); [PR-014](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/PRODUCT_REQUIREMENTS.md#L117) |
| Mockups inaccessible | **Corrected satisfactorily.** Both images exist, are readable, and match their documented SHA-256 hashes. Their old “Cycling Training” title is explicitly superseded. | [Mockup README](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/mockups/README.md) |
| Phase 1 incorrectly referenced REV-004 | **Corrected satisfactorily.** Historical context is removed from Phase 1 coverage and P1-03 traceability. PR-013/014 are included. | [Phase 1 §2](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/PHASE_1_ACCEPTANCE.md#L17), [§8](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/PHASE_1_ACCEPTANCE.md#L268) |
| Weak timing justification | **Corrected satisfactorily.** The contract cites exact one-second deltas and complete power/HR coverage, and requires eligibility to be checked again. The research JSON supports those claims. | [Phase 1 §3](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/PHASE_1_ACCEPTANCE.md#L35) |
| Undefined 20-minute calculation details | **Corrected satisfactorily at planning level.** Complete windows, endpoints, zero watts, missing values, rounding, tolerance, and independent verification are explicitly assigned to P1-02. The exact method properly awaits its JIT. | [Phase 1 §4.4](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/PHASE_1_ACCEPTANCE.md#L112) |
| Elapsed versus timer duration | **Corrected satisfactorily.** Both must remain distinct, including the representative ride’s 3,620/3,621-second discrepancy. | [Phase 1 §4.2](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/PHASE_1_ACCEPTANCE.md#L82) |
| Availability confused with provenance | **Corrected satisfactorily.** The distinction is explicit; its smallest implementation is correctly delegated to P1-01. | [Phase 1 §5](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/PHASE_1_ACCEPTANCE.md#L169) |
| First-use and restart journey unspecified | **Corrected satisfactorily at planning level.** Startup, selection, reopening, units/timezone, and chart interaction now belong to P1-03. Browser upload is not imposed. | [Phase 1 §8, P1-03](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/PHASE_1_ACCEPTANCE.md#L268); [TASKS.md](https://github.com/k14krug/my_strava/blob/1fc90d0/TASKS.md#L149) |
| DESIGN-002 implied broader initial implementation | **Corrected satisfactorily.** Structural compatibility is required now; real enrichment is explicitly Phase 2. | [DESIGN-002, first implementation slice](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/design/DESIGN-002.md#L228) |
| Historical state diagram implied Activity ownership | **Corrected satisfactorily.** Both diagram and prose establish independent, time-aware state. | [DESIGN-002, decision summary](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/design/DESIGN-002.md#L18) |
| Legacy `.clinerules` appeared authoritative | **Corrected satisfactorily.** It now explicitly retires the old technical decisions. | [.clinerules](https://github.com/k14krug/my_strava/blob/1fc90d0/.clinerules) |
| Previous review and handoff needed durable preservation | **Corrected satisfactorily in substance.** All eleven review sections are present and marked non-controlling. Formatting and citation links were flattened, reducing readability but not changing the findings. STATUS names the appropriate next action. | [Preserved review](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/reviews/2026-10-02-phase-1-readiness-astra.md); [STATUS.md](https://github.com/k14krug/my_strava/blob/1fc90d0/STATUS.md) |
| Legacy calculation/schema risks | **Still unresolved in code, appropriately.** No implementation was authorized. These remain exclusion/revalidation requirements, not reasons to repair the retired app first. | See section 11 below. |
| P1-01 implementation contract missing | **Still unresolved, as planned.** No P1-01 JIT exists. Authoring it remains the next step. | [Task briefs](https://github.com/k14krug/my_strava/tree/1fc90d0/docs/tasks) |

**3. New blocking issues**

**None before P1-01.**

The expected Analyst-authored JIT and normal authorization remain necessary. Its unwritten storage, failure, and extraction details are ordinary task preparation—not newly discovered product blockers.

The earlier mockup-access dependency is resolved. Icon selection and Owner UI approval belong to P1-03.

**4. Non-blocking corrections worth making now**

1. **Retire one stale product question.** Product Requirements §13, question 1 still asks which metrics belong on the first activity page. Phase 1 §4.2 already answers that. Change it to ask which *additional metrics beyond the approved Phase 1 minimum* might be useful later. [Current wording](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/PRODUCT_REQUIREMENTS.md#L571)

2. **Clarify mockup content authority.** Add a short README statement that sample values, comparisons, workout classifications, and analytical claims are illustrative—not formulas, test fixtures, or accepted training policies. The existing authority language covers appearance and unavailable features, but does not explicitly address contradictory example data.

3. **Apply the omission rule to the entire shell.** Phase 1 §4.6 names future panels, but P1-03 should also omit unsupported header buttons, navigation destinations, synchronization indicators, notifications, and account controls. This is an application of existing scope, not a new product restriction.

Restoring the preserved review’s Markdown tables and links would improve reference use, but is optional housekeeping.

**5. P1-01 JIT checklist — revised**

The prior checklist remains sound. The following is the complete implementation boundary I would expect; **new emphasis** identifies additions from this review.

1. **Authority and discretion.** Cite controlling requirements/designs, declare invocation and review boundaries, and identify ordinary implementation choices Dex may make. Routine helper structure, internal naming, and test organization should not require approval.

2. **Input envelope.** Accept a configurable local path. Explicitly support the selected `.fit.gz` artifact and distinguish compression from FIT content. Declare whether uncompressed `.fit` is also accepted. **New emphasis:** specify behavior for unsupported content or multiple sessions; do not silently select the first session or build a generalized multisport importer.

3. **Runtime and storage boundary.** Choose one simple durable storage approach, private application-data location, entry point, and dependency set. Keep operation independent of the legacy app factory. **New emphasis:** the data location must remain stable across restarts and changes in working directory.

4. **Original preservation.** Preserve received bytes, hash, size, packaging, and content format. Verify the stored copy. Parse the same preserved artifact that integrity metadata identifies. Never normalize or recompress the only preserved original.

5. **Activity and Source identity.** Use stable, separate identities and an explicit association basis. Do not require Strava IDs, equate filenames with identity, or enforce one Source per Activity.

6. **Repeat import.** Identical-artifact import after restart must return the established activity without duplicating it. State the boundary for differently compressed or otherwise different artifacts; generalized reconciliation remains deferred.

7. **Typed evidence.** Specify source fields, units, null handling, and timestamp meaning. Include every required source summary, including maximum HR, native power/HR samples, and necessary session/lap/event timing. State which other information is intentionally recoverable only from the original. **New emphasis:** do not confuse developer-field names with understood standard fields or present an unextracted field as observed absent.

8. **Native timing.** Preserve record order and duplicate timestamps. Retain meaningful boundaries and elapsed/timer distinctions. Timestamp alone must not be a unique sample key. Import fidelity and eligibility for a particular calculation are separate questions.

9. **Availability and origin.** Keep source attribution, measured/estimated/unknown origin, signal availability, and missing samples distinguishable. A small typed representation is enough; no general metadata framework is needed.

10. **Versions and retrieval.** Record parser and material extraction/mapping versions. Define how P1-02 retrieves source summaries and ordered native records without importing research-report JSON. **New emphasis:** provide an extraction identity/version that lets subsequent calculations recognize changed inputs.

11. **Failure and rebuild.** Define success, partial-write handling, retry behavior, and failed re-extraction. Preserve the last usable extraction when a rebuild fails. Rebuild must work without the external input path. **New emphasis:** identify how dependent results become stale after successful re-extraction; implementation can remain a simple version comparison in P1-02.

12. **Verification and handoff.** Authorize privacy-safe synthetic fixtures. Cover actual decoder integration, integrity, persistence, identical-artifact reimport, missing/zero values, native timing, and failure preservation. Run the representative local-file acceptance procedure and document exact commands and compact results. Retain Analyst acceptance as the completion boundary.

The new emphasis strengthens failure handling and the handoff between tasks. It does not justify another design task or infrastructure layer.

**6. Phase 1 usability review**

The main usability risk is producing a page that displays the right data but is awkward to return to.

**Phase 1 — should do:** make the complete journey short and repeatable:

1. Start RideWorks using one documented command or launcher.
2. Import the file through the authorized path.
3. Receive a clear success result identifying the saved ride.
4. Open it from an Activities entry or simple saved-ride view.
5. Review facts, chart, and best 20-minute result.
6. Open source details only when needed.
7. Restart and find the same ride without re-importing it.

A single-row Activities view is sufficient initially. It does not require a Dashboard or a history-management feature set.

**Phase 1 — should do:** use a readable fallback title based on source-supported type and date when no activity name is available. The mockup’s “Zwift Race” is not a suitable fallback for the actual representative ride. Keep the durable application ID accessible but visually secondary.

**Phase 1 — should do:** make one chart cursor expose elapsed time, power, and HR together, with explicit units and actual sample values. Distinguish the two vertical scales clearly. Do not use smoothing or tooltip interpolation to invent precision.

**Phase 1 — should do:** distinguish unavailable from zero. A missing metric can say “Unavailable”; details should explain whether it was absent from the inspected source or not extracted. A legitimate zero must remain zero.

**Phase 1 — should do:** expose one clearly named “Source & calculation details” disclosure. Normal review should not require reading hashes, parser versions, internal IDs, or evidence-status badges beside every value.

**Phase 1 — optional:** provide a “Show on chart” action for the winning 20-minute window and simple zoom/reset. These improve understanding without requiring interval detection.

Historical comparisons, zones, coaching statements, and planned-workout interpretation should wait for their respective phases.

**7. Activity mockup observations**

These observations come from the actual [Activity Review image](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/mockups/activity-review.png), not its prose description.

**The hierarchy is fundamentally useful.** The bold ride title, horizontal metric row, large power/HR chart, and supporting right column create a recognizable review screen. The chart deserves its central position.

**Phase 1 — should do: simplify the top row around available ride facts.** The current six cards include Normalized Power and Training Load, both excluded from Phase 1. Their sparklines and six-week deltas also depend on history. Replace those slots with required source-backed facts where useful; do not preserve six cards merely for symmetry. Duration is currently small text under the title and deserves more prominence.

**Phase 1 — should do: give best 20-minute power an explicit result panel.** In the mockup, the exact 20-minute result is buried in “Compare to Recent,” while the Power Curve occupies more space. The Phase 1 compact performance panel should clearly name the result and its calculated status without requiring a curve.

**Phase 1 — should do: rebuild the right column from factual content.** Four existing rows—Workout Type, Intensity, FTP Impact, and Recovery Needed—depend on classification or interpretation. Source, source-supported type, elapsed/timer duration, maximum power/HR, cadence, and source details can make this column useful now. It need not retain the mockup’s exact row count.

**Phase 1 — should do: remove unsupported controls as well as panels.** “Compare,” “AI Summary,” “Edit FTP,” “AI Usage,” the Strava sync status, and workout-phase chart annotations should not appear as inert or misleading controls. Keep the navigation rail, but show useful destinations only.

**The sample analysis is contradictory.** The “Compare to Recent” table reports 20-minute power of 243 W versus 218 W, while the Power Curve’s current-ride trace appears near 100 W at 20 minutes and lies below the recent trace. The adjacent insight claims stronger 5–20-minute performance. These cannot serve as a consistent analytical example. No image redraw is necessary before implementation; the README authority clarification is enough.

**Phase 2–3:** avoid treating every upward comparison as good. The mockup renders higher average HR and higher training load with green upward arrows. An increase establishes direction, not benefit. Use neutral comparisons unless a supported interpretation exists.

**Phase 1 — should do:** tighten terminology. “Elevation” should identify whether it means elevation gain; “Time” should identify elapsed time; “Source” should distinguish an imported FIT file from the application/device that created it. A Zwift badge does not establish that RideWorks imported through a Zwift integration.

**Phase 1 — optional:** reduce decorative duplication. The header contains five badges, while source and ride type repeat in the right column. Keep information that helps identify the ride; avoid repeating every label.

The layout can survive the missing future panels well. The chart, a compact 20-minute panel, and a shorter factual right column are sufficient. Do not fill the resulting space with invented insights.

**8. Dashboard mockup observations**

The [Dashboard image](https://github.com/k14krug/my_strava/blob/1fc90d0/docs/mockups/dashboard.png) is strongest as a navigation and recent-activity overview. Its answer to “How am I doing?” is less settled.

**Phase 2–3:** make 20-minute performance more prominent. The top row contains FTP, Fitness Score, this-week miles, last-seven-days miles, and yearly miles. The emphasized product metric—20-minute power—has no direct trend panel. A clear 20-minute trend or recent result belongs ahead of an undefined fitness score.

**Phase 2–3:** reduce overlapping volume summaries. “This Week Miles,” “Last 7 Days,” YTD Miles, and Mileage Progress consume substantial space. Calendar-week and rolling-week totals are different, but both need a rider reason to be prominent. The YTD progress bar is also repeated inside Mileage Progress.

**Phase 2–3:** preserve the recent-activity table as the main route into review. Its date, title, basic facts, and row affordance are useful. Make the activity title/row open the durable Activity identity. Comparison actions can be added here once Phase 2 supports them.

**Phase 2–3:** identify comparison populations. “Last 6 Weeks” could mean a period maximum, average of ride bests, or something else. The lower-right Power Curve also says “This Ride” without making the selected ride sufficiently explicit. Label the ride and comparison basis.

**Later:** “Fitness Score,” its daily increases, recovery judgments, and automated seven-day plan updates require the training-state/planning work. In particular, the sentence promising that the plan “automatically updates” describes later adaptive behavior, not a Phase 3 dashboard requirement.

**Phase 2–3:** use “Insights” only when useful evidence-backed findings exist. A notification that an “AI summary is available” adds less value than a direct, specific finding with a route to its evidence.

**Probably unnecessary:** the duplicated synchronization timestamps, profile chrome, notification bell, and permanent AI Usage destination need independent justification for this single-rider product.

The real current architectural implications are modest: stable Activity links, preserved timestamps, explicit metric provenance/version, and a representation that can hold more than one activity. Dashboard layout does not require aggregate caches, a goal engine, or a planning schema in P1-01.

**9. Usability ideas backlog**

These are recommendations, not additional acceptance requirements unless already covered by the contract.

| Idea | User benefit | Suggested phase | Complexity | Product decision? |
|---|---|---|---|---|
| Simple saved-ride entry and stable activity URL | Find the ride again after restart | Phase 1 — should do | Low | No |
| Readable source-based fallback title | Identify unnamed imports | Phase 1 — should do | Low | No |
| Shared power/HR cursor with exact values | Inspect what happened at one moment | Phase 1 — should do | Medium | Interaction choice in P1-03 |
| Explicit units, timezone, elapsed/timer labels | Avoid ambiguous values | Phase 1 — should do | Low | Display preference at UI review |
| “Source & calculation details” disclosure | Investigate suspicious values without clutter | Phase 1 — should do | Low | No |
| Visible unavailable reasons; preserve zero | Avoid false completeness | Phase 1 — should do | Low | No |
| Highlight the winning 20-minute window | Connect the result to the ride | Phase 1 — optional | Low–medium | Analyst scope choice |
| Zoom and one-step reset | Inspect brief changes | Phase 1 — optional | Medium | Analyst scope choice |
| Remember the last-opened ride | Reduce repeat navigation | Phase 1 — optional | Low | No |
| Compare from activity/table entries | Make historical comparison discoverable | Phase 2–3 | Medium | Yes |
| Click trend points to open contributing rides | Explain performance history | Phase 2–3 | Medium | No, once trend semantics exist |
| One prominent goal-progress summary | Keep goals visible without repetition | Phase 2–3 | Low–medium | Yes: goal type |
| Explain recommendation evidence and changes | Build trust in planning | Later | High | Yes |
| Permanent AI Usage page and summary notifications | Little established rider benefit | Probably unnecessary | Medium | Yes, if reconsidered |
| Extensive account controls or onboarding | Adds friction for one rider | Probably unnecessary | Medium | Yes, if access needs change |

**10. RideWorks branding/icon observations**

PR-014 is appropriately scoped: RideWorks is settled, artwork is not, and Owner approval occurs before final UI acceptance. It does not block P1-01.

**Phase 1 — should do:** put the RideWorks wordmark and a compact mark in the existing top-left shell position. Use RideWorks in the browser title, preferably with the activity name. The identity should help orientation without competing with training information.

**Phase 1 — should do:** design a small mark that works in the shell and favicon context, with recognizable shape at small sizes, a monochrome treatment, and adequate contrast on light and dark backgrounds. A detailed cycling illustration that only works at the full mockup size would be a poor application icon.

**Recommendation:** keep this as a bounded design step inside P1-03, producing a concrete mark shown at actual usage sizes for Owner review. A separate small task is reasonable only if parallel scheduling helps; it should not become a prerequisite design program.

**Later:** native launcher packages or installed-web-app assets should be added if those delivery modes are chosen.

**Probably unnecessary:** a full identity system, extensive brand guidelines, multiple themes, or a large logo exploration before the first useful screen.

**11. Repository/code observations**

All previous legacy risks remain accurate. No application, research-tool, or test changes occurred between the prior audited snapshot and this one.

The legacy Activity model still requires Strava identity; the loader substitutes zeros for absent values; startup assumes MariaDB and creates tables; historical FTP falls back to 200 W; research summarization loses information needed for normalized streams. These should remain outside the new slice unless specifically adapted and verified.

The power defect is still reproducible: a 1,200-sample sequence containing 1,199 × 100 W and one final 1,000 W sample produces **1,000 W** as legacy best-20-minute power instead of the complete sample-window mean of **100.75 W**. [Legacy calculation](https://github.com/k14krug/my_strava/blob/1fc90d0/jobs/power_metrics.py#L125)

Additional traps found in this pass:

- **Identity confusion already exists in a route.** `TrainingLoad.activity_id` references the application Activity primary key, but the activity-detail route queries it using `activity.strava_id`. Do not copy that lookup pattern. [Model](https://github.com/k14krug/my_strava/blob/1fc90d0/strava/models.py#L113); [route](https://github.com/k14krug/my_strava/blob/1fc90d0/strava/main/routes.py#L194)
- **Metric names disagree across persistence boundaries.** The stream loader assigns `best_1hr_power`, while the mapped model column is `best_60m_power`. This illustrates why legacy calculations and persistence cannot be assumed to form a verified reusable unit. [Loader](https://github.com/k14krug/my_strava/blob/1fc90d0/jobs/stream_loader.py#L156); [model](https://github.com/k14krug/my_strava/blob/1fc90d0/strava/models.py#L36)
- **Presentation also conflates zero with missing.** Expressions such as `value or "N/A"` in the old template hide legitimate zero values. [Activity template](https://github.com/k14krug/my_strava/blob/1fc90d0/strava/templates/main/activity.html#L43)
- **The old launcher is not local-only by default.** It binds to `0.0.0.0`. The new local-first entry point should make its intended exposure explicit instead of inheriting this behavior accidentally. [run.py](https://github.com/k14krug/my_strava/blob/1fc90d0/run.py#L7)

These findings justify a clear reuse boundary, not a cleanup campaign.

The reusable assets remain the research diagnostics, strict parsing examples, field inventories, deterministic reporting, privacy checks, and synthetic-test patterns.

**Verification:** all **17 research tests passed** in the isolated snapshot:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Both mockup hashes match the README. I did not rerun the personal archive or calculate its actual best-20-minute result. Static mockup inspection also cannot establish real hover behavior, keyboard usability, or responsive layout.

**12. Things that should remain deferred**

Do not delay P1-01 for:

- a final database, web framework, or generic storage abstraction;
- complete stream-storage architecture or a parser plugin system;
- bulk history, XML production import, synchronization, or generalized matching;
- complete provenance UI or metadata frameworks;
- generalized gap/interpolation policy;
- historical-state resolution algorithms;
- power curves, zones, training load, or FTP estimation;
- dashboard aggregates, goals, planning, or AI infrastructure;
- cloud deployment, multi-user authentication, or native packaging;
- icon artwork or full visual design;
- a broad legacy rewrite.

One real representative ride remains enough for Phase 1 product acceptance, supported by synthetic tests for reusable behavior and failure conditions.

**13. Recommended actions before development**

| Order | File/area | Exact action and reason | Blocks P1-01? |
|---|---|---|---|
| 1 | `docs/tasks/P1-01.md` | Author the JIT using the revised checklist, including ordinary implementation discretion. Converts settled intent into executable work. | **Yes—expected prerequisite** |
| 2 | `docs/PRODUCT_REQUIREMENTS.md`, §13 question 1 | Reword the question around additions beyond the approved Phase 1 metrics. Prevents reopening settled scope. | No |
| 3 | `docs/mockups/README.md` | State that sample numbers, comparisons, and training claims are illustrative and do not establish analytical policy. | No |
| 4 | `docs/PHASE_1_ACCEPTANCE.md`, §4.6 or future P1-03 JIT | Explicitly apply deferred-capability omission to shell controls and navigation, not just panels. Prevents misleading UI. | No |
| 5 | P1-01 implementation boundary | Name excluded legacy startup/models/calculation paths and specify the private runtime-data location. Prevents accidental inheritance of old assumptions. | Part of item 1 |

No additional readiness review or architecture task is necessary before authoring P1-01.

**14. Owner questions**

**None before P1-01.**

Before P1-03, one usage decision is worth confirming: **is initial UI acceptance for a desktop browser, or must phone/tablet use also be part of Phase 1?** That determines the practical layout and chart-interaction target.

The icon should return to Ken as concrete candidates shown in the application, favicon, and small-size contexts. There is no need to reopen the product name or request an abstract branding strategy first.
