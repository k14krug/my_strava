# Independent Phase 1 Readiness Review — Astra

**Date:** 2026-10-02  
**Reviewer:** Dex using GPT-6.0 Astra  
**Repository snapshot reviewed:** `origin/main` at `e8c8710`  
**Status:** Review evidence; non-controlling. Accepted findings must be incorporated into controlling requirements, design documents, task briefs, or repository guidance before they become implementation instructions.

This file preserves the independent readiness audit requested before Phase 1 development. It is intentionally kept separate from the controlling RideWorks product requirements and accepted design decisions.

---

1. Executive conclusion
Classification: Ready to author P1-01 JIT and begin Phase 1.
The project has enough product and design direction to begin responsibly once the Analyst commits the P1-01 JIT. I found no reason to insert another architecture phase, reopen broad data discovery, or expand Phase 1 to historical import.
This is readiness to begin development—not implementation authorization or Phase 1 acceptance. The missing JIT is the expected next deliverable.
The strongest remaining risks are specific and manageable:
- Import durability, duplicate handling, and re-extraction need an executable contract in P1-01.
- The legacy power calculation is demonstrably incorrect and must not become the new calculation or verification oracle.
- The approved mockups are referenced but unavailable in the materials I could access. That blocks faithful visual implementation later, not P1-01.
- A few older design statements need clearer phase boundaries.
I fetched origin and audited origin/main at e8c8710, including research reports, code, tests, and relevant GitHub acceptance/review history. The local checkout remains on the older research branch; all file references below point to the audited remote snapshot. I ran tests in an isolated /tmp snapshot. No working-tree files, JITs, issues, or PRs were changed.
2. What is already strong
The product has a coherent purpose. The rider questions connect activity review, historical performance, goals, workout outcomes, training state, and planning. They avoid making data ingestion itself the roadmap. The six phases form a reasonable progression. Dashboard’s conditional “next workout” area does not require pulling Phase 4 planning into Phase 3. Product requirements, §§1, 3, 7
Phase 1 ends with a useful experience. Its completion criteria require a real activity page, power/HR review, best 20-minute power, inspectable evidence, and Ken’s usability acceptance. Storage alone explicitly cannot complete the phase. Phase 1, §§1, 7
The evidence model is sufficiently settled. Application identity, source ownership, unchanged originals, native timing, separate derivations, conservative association, and historical state provide meaningful constraints without prescribing a large architecture. DESIGN-002’s rejection of a universal observation/EAV store is particularly useful for keeping this personal application simple. DESIGN-001, “Settled conceptual model”; DESIGN-002, “Decision summary”
The research is adequate for this decision. It examined the complete export, separated evidence channels, recorded limitations, and closed broad discovery explicitly. The completed research has durable Analyst acceptance on GitHub. There is no evidence-based reason to inventory the archive again before P1-01. STRAVA-003 findings; research acceptance
The governance is workable. Analyst-owned JITs, explicit invocation authorization, mandatory stops, separate implementation/review/acceptance states, and Owner visual review give an agent adequate boundaries. /AUTOTASK changes execution cadence without transferring decision ownership. These controls should remain; they do not need additional approval layers. AGENTS.md, “Execution Control” and “/AUTOTASK”
3. Blocking issues
The only present implementation-authorization blocker is the missing Analyst-authored P1-01 JIT. STATUS.md correctly records that implementation is unauthorized and names the JIT as the next action. This is planned sequencing, not evidence of an unfinished product definition. Current handoff
The JIT must settle the immediate import contract described in section 8 below. In particular, Dex should not start with unspecified rules for:
- what bytes are preserved and where;
- what constitutes a successful durable import;
- what repeat import and failed re-extraction do;
- which typed evidence must survive normalization;
- how the imported result is independently verified.
These are bounded JIT decisions. They do not require a final database, framework, parser architecture, or historical reconciliation design.
There is also a later blocking dependency: the Activity mockup must be accessible before P1-03’s visual implementation and acceptance. I could not inspect either approved mockup and cannot assess their actual appearance or fidelity from prose.
4. Non-blocking issues worth correcting now
Strengthen the timing justification. “One-second median and no large gaps” is insufficient, by itself, to establish a complete one-second series: the research defines a large gap as greater than max(30 seconds, 5 × median). Fortunately, the detailed evidence establishes much more for this ride:
- 3,621 timestamped records;
- 3,620 positive deltas, all exactly one second;
- no duplicate, backward, or missing timestamps;
- power and HR present on every record.
Use that evidence and require a fresh eligibility check during local acceptance. This is a documentation improvement, not a newly discovered sampling problem. Representative record in STRAVA-002 JSON; timing definition
Specify narrow 20-minute semantics in P1-02. Complete-window eligibility, endpoint convention, inclusion of zero watts, missing-value behavior, rounding, and verification tolerance remain unspecified. They can be defined for this regular series without solving arbitrary gaps or interpolation.
There is already a useful boundary case: the report records 3,620 seconds elapsed but 3,621 seconds timer time. Preserve and label both source values; do not “correct” them into agreement or call timer time moving time.
Make provenance terminology operational. Origin and availability are different dimensions. A value can be supplied by FIT while its measured/estimated origin remains unknown. A signal can be observed absent, unavailable because it was not inspected, or present with missing samples. A small explicit representation is sufficient; one overloaded status enum would be confusing.
Clarify the first user journey before P1-03. Define how Ken starts the app, imports or selects the ride, and opens it again after restart. A CLI import returning an Activity ID or URL can satisfy the narrow slice; an upload workflow is not inherently required. Display units, timezone labeling, and minimal chart interaction also belong in that task’s acceptance procedure.
5. Things that should remain deliberately deferred
Do not delay P1-01 for:
- final database architecture or a general repository abstraction;
- final frontend framework or complete navigation;
- a parser plugin system;
- bulk history, TCX/GPX production support, or Strava synchronization;
- cross-source matching thresholds and universal source selection;
- generalized stream alignment, interpolation, or resampling;
- historical-state resolution algorithms;
- arbitrary-duration curves, longitudinal eligibility, or personal-record policy;
- goals, workout planning, training-state models, or estimated outdoor power;
- generic derivation dependency graphs, distributed jobs, or commercial deployment architecture.
Some physical storage choice is unavoidable. The smallest useful boundary is one configurable local application-data location, preserved originals, durable Activity/Source records, versioned typed extraction, and a callable read interface. Choose one simple implementation in the JIT; do not build multiple interchangeable storage backends.
The real future-compatibility protections are stable IDs, source relationships, explicit units/timing, and reproducible derivations. Those matter far more now than hypothetical framework longevity.
6. Contradictions or stale repository material
Reference	Finding and controlling interpretation
DESIGN-002, “Requirements for the first implementation slice”	Its wording can be read as requiring multiple sources, enrichment, and representative-case demonstrations immediately. The newer Phase 1 contract explicitly defers those cases. Clarify that P1-01 preserves structural compatibility; real enrichment proof belongs to Phase 2.
Phase 1, §2 and §8 P1-03	Both reference REV-004, which means historical context. That is explicitly Phase 2. Remove it from Phase 1 coverage rather than relying on “as applicable to one ride.” Add PR-013 to the visual task’s traceability.
.clinerules, “Technical Decisions”	Presents Flask, SQLAlchemy, and Chart.js as settled decisions. Current requirements defer framework choices and AGENTS.md denies legacy architectural authority. Mark this file as retired context or remove the obsolete guidance.
DESIGN-002, conceptual diagram	Drawing historical state beneath Activity could imply Activity ownership. The adjacent prose and historical-state section explicitly say it is independent and time-aware; those statements control. A diagram annotation would avoid confusion.
DESIGN-002 PR #9	Closed, not merged, but not an outstanding approval problem. Its closing explanation states the accepted design landed directly on main in 713e275. Do not revive the stale PR or its task/status snapshots.
Current AGENTS.md introduction	The earlier workbench-only description supplied with this session is older than the refreshed repository direction. Current main explicitly establishes this repository as the application repository. A separate future repository must not be assumed.


The research reports’ old “next design decision” language is historical evidence, not an active instruction. It does not need rewriting.
7. Phase 1 and task-sequence assessment
Keep P1-01 → P1-02 → P1-03. Each task has a distinct product reason and a useful review boundary.
Task	Product reason	Appropriate verification
P1-01	Make the ride durable and usable without reacquiring its source	Original-byte integrity, reopen after restart, stable identity on repeat import, faithful extraction, rebuild from preserved original, explicit failure behavior
P1-02	Establish trustworthy facts and the central calculated result	Source-field mapping, native streams, complete-window tests, independent 20-minute calculation, method/input provenance
P1-03	Make those facts useful to the rider	Real browser review, correct labels and unavailable states, chart readability, provenance access, mockup comparison, Ken’s acceptance


Do not split P1-01 into a separate architecture task. Review its concrete storage and extraction contract at normal Analyst acceptance before P1-02. Likewise, accept the analysis before UI presentation can obscure calculation defects. P1-03 needs the explicit HARD — Owner visual/usability boundary, followed by normal Analyst closeout.
The representative ride is appropriate. It has the required source richness, length, timing, and signals. A source-rich virtual ride is also relevant to the archive’s dominant cohort. It need not prove outdoor usefulness, estimated power, or general historical import.
One real ride is sufficient for product acceptance, but not sufficient as the entire software test population. Synthetic cases should cover absent fields, zero values, duplicate timestamps, gaps, invalid files, repeat imports, and incomplete calculation windows. Unsupported cases can be preserved and rejected for analysis explicitly; they do not require implementing general recovery policies.
The acceptance contract is mostly testable. Hashes, identity, extraction, stream timing, source attribution, and calculations support objective checks. “Useful enough,” visual character, and recognizable layout are legitimate Owner judgments. Record the reviewed build, ride, and resulting changes rather than pretending those criteria are automated.
Independent power verification should use a separately expressed calculation—not call the production rolling-window helper again. Synthetic expected results establish formula behavior; the local real-file comparison establishes that the implementation handles the actual evidence.
8. P1-01 JIT readiness checklist
The JIT should specify the following before Dex begins:
1. Authority and execution. Requirements used, accepted design references, Allowed Invocation, review boundary, stop conditions, and explicit exclusion of later task functionality.
2. Input contract. Accept a local file path; identify the representative artifact; declare supported packaging. The selected artifact is .fit.gz, so “single FIT” must not accidentally mean uncompressed-only.
3. Minimal application boundary. Entry point, module location, local runtime/dependencies, storage mechanism, and how P1-02 will retrieve the result. Avoid importing the legacy application merely to access its models.
4. Original preservation. Preserve the received .fit.gz bytes unchanged, record hash and size, identify FIT as the parseable content, and retain a durable application-managed location. A temporary extraction directory is not the durable original.
5. Identity and association. Generate application-owned Activity identity; create a distinct Source association; retain the association basis. Neither the artifact filename nor its hash becomes Activity identity. Do not require Strava identity.
6. Repeat-import scope. Define behavior for the identical established artifact, including after restart. State the limits for different packaging or different files that might describe the same ride. Do not infer equivalence from a filename.
7. Typed extraction contract. Map source fields, units, types, timestamp interpretation, and unavailable states. Include every Phase 1 summary field, especially source max_heart_rate, plus native power/HR records and the timing structure needed to interpret them. State which additional fields remain recoverable only from the original.
8. Timing preservation. Retain record order and enough identity to preserve duplicate timestamps; distinguish source timestamps, elapsed time, timer time, and session/lap/event boundaries. Do not key records uniquely by timestamp.
9. Provenance and versions. Record parser version, material extraction/mapping version, source field context, and extraction identity sufficient for subsequent derivations. Do not classify FIT power as measured merely because it exists.
10. Failure and rebuild behavior. Define when import becomes successful; prevent partial work from appearing as a complete activity; make retries safe. Failed re-extraction must not destroy the last usable extraction or create a new Activity. No general transaction framework is needed, but the behavior must be explicit.
11. Verification and evidence. Authorize safe synthetic fixtures; test the actual decoder path or explicitly document its local integration coverage. Require integrity, persistence, idempotency, missingness, timing, and rebuild checks. Record exact local commands and compact results without committing personal streams.
12. Acceptance and handoff. Require Analyst review of the resulting representation and real-data evidence. Keep TASKS.md in progress until accepted. Identify ordinary implementation choices Dex may resolve without stopping.
The exact best-20-minute formula belongs in P1-02. P1-01 must preserve the evidence needed to calculate it, not prematurely implement the analysis.
9. Repository/code observations
Useful reuse exists, primarily in research tooling.
The inventory, gzip/FIT reading, field inspection, timing diagnostics, deterministic reports, privacy checks, and synthetic-test patterns are useful references. Their narrow dependency file also avoids inheriting the entire retired application stack.
However, the research summarizer is not a ready-made normalized importer:
- add_point_signal() omits missing values from diagnostic signal lists, so those lists cannot become aligned durable streams.
- frame_values() selects values by field name for summarization.
- Event handling records counts rather than preserving event timing.
- The compact session summary omits max_heart_rate, although the representative file’s field inventory shows it exists.
These choices fit research reporting; copying its output model into P1-01 would lose required meaning. Research extraction helpers
The legacy power calculation is unsafe to reuse unchanged.
rolling_average() includes trailing windows that never reach the requested duration. I reproduced this with 1,200 samples: 1,199 at 100 W and the last at 1,000 W. The complete sample-window mean is 100.75 W; the legacy function reports 1,000 W as best 20-minute power. It also removes invalid samples and uses zero for several unavailable results. Power calculation
This is a confirmed implementation defect, not an alternative analytical preference. Exclude this routine or correct and independently verify it within P1-02; do not repair unrelated legacy metrics now.
The legacy schema and startup path would impose unwanted constraints.
- Activity has its own primary key, but requires a unique non-null Strava ID and stores source-like summaries and derivations together.
- The loader substitutes zero for absent facts and stores several values in presentation units.
- The app factory registers legacy routes and calls db.create_all(); configuration assumes MariaDB.
- Training-load code substitutes 200 W when historical FTP is missing and falls back to regression-estimated normalized power.
- The old Activity template contains training-load and segment features, not the required native power/HR review.
These are reasons to isolate the new slice’s entry point and data model—not reasons to rewrite or delete the whole old application. Models; loader; startup; FTP fallback
Verification performed: all 17 research tests passed using:
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
The existing FIT unit test uses synthetic decoded messages, not binary FIT decoding. Passing this suite therefore does not establish importer correctness. I did not rerun the personal-data census or compute the representative ride’s actual 20-minute result during this audit. FIT test
10. Recommended changes before development
1. Author docs/tasks/P1-01.md. Include the checklist above, especially durable storage, repeat-import/re-extraction behavior, extraction fields, and independent acceptance evidence. This is the required implementation prerequisite.
2. Clarify docs/design/DESIGN-002.md, “Requirements for the first implementation slice.” Explicitly distinguish Phase 1 structural compatibility from Phase 2 enrichment demonstrations. This can be a short clarification alongside the JIT.
3. Tighten docs/PHASE_1_ACCEPTANCE.md, §§2, 3, 4.4, and 8. Correct REV-004 traceability, add PR-013 where appropriate, cite exact timing evidence, and assign calculation semantics/tolerance to P1-02.
4. Retire .clinerules as active guidance. Mark its technical decisions as historical so they cannot silently govern implementation.
5. Add accessible, version-identified mockup references to docs/PRODUCT_REQUIREMENTS.md, PR-013, and Phase 1 §4.6. Complete this before P1-03. Do not substitute a prose reconstruction for the approved images.
6. In the P1-01 JIT, name the legacy exclusion boundary and private output location. Update .gitignore only if the chosen runtime location needs it. No broad code relocation or dependency modernization is necessary.
No wholesale governance rewrite is warranted. Avoid artificial intermediate gates; use the existing task acceptance boundaries and a clear Owner gate for the UI.
11. Questions for the Owner
No new Owner product or architecture decision is required before the Analyst authors P1-01.
Before P1-03, the team needs access to the already-approved Activity mockup and an unambiguous version reference; the Dashboard mockup should be made accessible at the same time. That is recovery of existing design authority, not a request to reopen the design.
