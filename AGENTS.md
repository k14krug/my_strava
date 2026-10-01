# AGENTS.md

## my_strava Research Workbench

This repository is a retired Strava application that is now available as a research and development workbench for the Personal Cycling Training App project.

The old application is not a compatibility target. Existing code may be reused, changed, isolated, or removed when a task requires it.

The repository's immediate purpose is to support evidence-gathering and experiments against real cycling data before implementation decisions are made for the future application.

Research code in this repository is not automatically production architecture for the future application.

---

## Roles

### Ken — Owner

Ken makes product, training-analysis, privacy, priority, and final design decisions.

Ken also controls local source data that should not be committed, including bulk Strava exports and personal activity archives, and runs local-data commands when required.

### AI Analyst — ChatGPT

The AI Analyst:

* helps define requirements, experiments, and tasks
* distinguishes ideas, working assumptions, agreed principles, and actual design decisions
* authors and commits the detailed JIT task brief before Dex begins implementation
* creates or updates GitHub issues when useful
* reviews pull requests, experiment outputs, and implementation behavior
* leaves implementation feedback on GitHub
* interprets experimental results with Ken and proposes next work
* does not directly control Dex's local environment

### Dex — Codex Agent

Dex:

* implements assigned work locally from the Analyst-authored JIT brief
* does not author or substantively redesign JIT task briefs
* runs local verification and requested experiments
* asks Ken to run commands only when access to Ken's local-only data or environment is required
* commits and pushes changes
* opens or updates pull requests
* reads and addresses Analyst feedback
* keeps repository status current

### Communication Between Agents

The AI Analyst and Dex do not communicate through a private side channel.

**GitHub is their shared durable communication channel.**

The Analyst may place instructions or review feedback in:

* committed JIT task briefs
* GitHub issues
* pull-request descriptions
* pull-request comments
* review comments

Dex must read the relevant repository documents, issue, PR, and unresolved review comments before beginning or completing work.

Do not rely on Ken to manually relay technical details when the information is already available through GitHub.

---

## Repository Working Files

### `AGENTS.md`

Permanent development, research, data-handling, and workflow rules.

Do not use this file for current task status or transient experiment results.

### `TASKS.md`

The durable task list.

Each task should have:

* task ID
* short description
* status
* scope
* acceptance criteria where useful

Use these statuses unless the repository establishes another convention:

```text
pending
in_progress
blocked
done
```

Only one implementation/research task should normally be `in_progress`.

### `STATUS.md`

Short current handoff state for humans and agents.

Keep it concise and current. Include as applicable:

* current task
* branch
* PR
* implementation/research state
* verification or experiment performed
* blockers
* next action

Do not turn `STATUS.md` into a historical journal. Git and GitHub already provide history.

### `docs/tasks/<TASK-ID>.md`

Detailed just-in-time task brief for the current task.

The AI Analyst authors and commits this brief before Dex starts implementation.

If the selected task has no Analyst-authored JIT brief after repository refresh, Dex must stop and report the missing brief. Dex must not create, reconstruct, expand, or substantively redesign the JIT itself.

---

## Task Lifecycle

### Pending

Before work begins:

* `TASKS.md`: `pending`
* `STATUS.md`: `pending` when the task is the current handoff but has not begun

### Implementation / experiment

Once Dex starts:

* `TASKS.md`: `in_progress`
* `STATUS.md`: `in_progress`

### Ready for Analyst review

When implementation and required local verification/experiments are complete:

* `TASKS.md`: remain `in_progress`
* `STATUS.md`: `ready_for_review`

Do not mark the task `done` merely because code ran or tests passed.

### Analyst requests changes

While addressing feedback:

* `TASKS.md`: remain `in_progress`
* `STATUS.md`: `in_progress`

After changes are implemented, verified, and pushed:

* `TASKS.md`: remain `in_progress`
* `STATUS.md`: `ready_for_review`

### Analyst accepts task

Once the AI Analyst explicitly accepts the work and no implementation/review work remains:

* `TASKS.md`: `done`
* `STATUS.md`: `done`

The PR may still await mechanical merge. Do not make an already-accepted PR merge the persisted Next Action.

Do not automatically begin the next task.

---

## Requirements and Design Sources

`docs/PRODUCT_REQUIREMENTS.md` is the controlling product requirements document. Product phases, design work, and JIT task briefs must trace to it unless Ken explicitly supersedes a requirement.

The Personal Cycling Training App project documents are the primary source for product principles and settled design context.

When relevant project documents are available in this repository, the JIT brief must identify them under `Requirements Used`. When they are not checked into this repository, the Analyst must carry the relevant requirements into the JIT explicitly rather than asking Dex to infer them.

Current strong principles include:

* build a durable useful personal training history from the best available sources
* preserve original source data whenever practical
* retain provenance where it matters
* distinguish measured, known, calculated, estimated, inferred, and missing data
* treat FTP, weight, zones, bike configuration, and similar athlete state historically
* make important calculations reproducible and replaceable
* do not manufacture precision
* keep activity analysis, longitudinal analysis, training-state assessment, and training planning conceptually distinct
* prefer transparent, explainable analysis
* use Strava as a useful source without making it the product specification or a single point of failure
* do not build mechanisms to evade Strava controls, rate limits, or policies
* treat Sauce and other existing implementations as research references, not authorities

A JIT task may add task-specific requirements but must not silently convert an exploratory idea into a settled product decision.

If a new proposal conflicts with an older source, surface the conflict. Prefer Ken's most recent explicit decision.

---

## Research vs Product Design

This repository is allowed to contain deliberately temporary research code.

Examples include:

* bulk-export inventory scripts
* FIT/TCX/GPX inspection utilities
* data-quality probes
* one-off comparison reports
* algorithm prototypes
* calibration experiments
* validation scripts

A successful experiment does **not** automatically establish:

* the future database schema
* the future application framework
* production package structure
* final algorithms
* final UI
* permanent data representation

Record what an experiment demonstrates and what remains uncertain.

Do not refactor experimental code into a proposed production architecture unless the JIT explicitly asks for that decision.

---

## Local Data and Privacy

Raw personal source data is local-only by default.

Do **not** commit:

* Strava bulk-export ZIP files or extracted bulk archives
* collections of FIT, TCX, or GPX activity files
* access tokens, refresh tokens, client secrets, passwords, or credentials
* local databases containing personal activity history
* environment files containing secrets
* generated artifacts that expose unnecessary personal/location data

Small deliberately selected test fixtures may be committed only when the JIT explicitly permits them or Ken explicitly approves them.

Prefer committing compact derived inventories, summaries, test fixtures, and reports that contain only the information needed for the research task.

Analysis tools should accept local paths as inputs rather than assuming Ken's directory layout.

Never modify original source activity files in place.

---

## Data and Analysis Discipline

Preserve evidence separately from interpretation.

Where practical, analysis outputs should make clear:

* source
* whether a value was measured, supplied, calculated, estimated, or inferred
* assumptions
* algorithm/version when material
* missing inputs
* uncertainty or confidence when material

Do not silently substitute generic cycling assumptions for known rider data.

Do not use today's FTP, weight, zones, or bike configuration for historical activities unless the task explicitly establishes that as an acceptable approximation.

For externally changing facts such as Strava API behavior/policy, FIT specifications, library capabilities, or current third-party software behavior, verify against current authoritative sources when the task depends on them.

---

## JIT Task Brief Requirements

Every `docs/tasks/<TASK-ID>.md` brief must contain, as applicable:

1. Purpose
2. Background / question being answered
3. Requirements Used
4. Scope
5. Explicit non-goals
6. Inputs and local-data expectations
7. Required implementation or experiment
8. Required outputs/artifacts
9. Verification / test procedure
10. Acceptance criteria
11. Stop-and-report conditions

The JIT expands a `TASKS.md` entry but must not silently redefine its purpose.

If implementation reveals a material conflict, ambiguity, missing requirement, unexpected data condition, or evidence that invalidates the planned experiment, Dex should stop and report it rather than inventing policy.

---

## Repository Sync

Never begin work from a stale checkout.

### Initial remote refresh is unconditional

At the start of `/TASK`, Dex must:

1. Confirm there are no unexpected local changes that would make switching branches unsafe.
2. Run `git fetch origin --prune`.
3. Only after fetching, evaluate task, branch, PR, JIT, and repository state.

### Starting a new task

1. Confirm the worktree is clean.
2. Fetch `origin`.
3. Checkout `main`.
4. Pull with fast-forward only: `git pull --ff-only origin main`.
5. Verify the selected pending task has an Analyst-authored `docs/tasks/<TASK-ID>.md` on refreshed `main`.
6. If missing, stop and report it.
7. Create or switch to the task branch.

### Continuing an existing task or review

1. Confirm there are no unexpected local changes.
2. Fetch `origin`.
3. Checkout the existing task branch.
4. Pull that branch with fast-forward only.
5. Read the relevant issue, PR, and latest unresolved/recent Analyst feedback.

Do not require switching to `main` in the middle of existing task work.

---

## Start-of-Work Procedure

Before changing code:

1. Read `AGENTS.md`.
2. Read `TASKS.md`.
3. Read `STATUS.md`.
4. Read the Analyst-authored `docs/tasks/<TASK-ID>.md`.
5. Read source documents named in the JIT.
6. Inspect relevant existing code and tests.
7. Read the relevant issue/PR if one exists.
8. Read unresolved PR review comments.
9. Continue existing `in_progress` work before starting another task.

If repository state, task files, GitHub state, source data, or instructions conflict, report the conflict rather than guessing.

---

## `/TASK`

When Ken invokes `/TASK`, Dex should:

1. Perform the unconditional remote refresh and appropriate repository sync.
2. Read `AGENTS.md`, `TASKS.md`, and `STATUS.md`.
3. Continue the current `in_progress` task if one exists.
4. Otherwise select the next appropriate `pending` task.
5. Verify the Analyst-authored JIT exists; stop if it does not.
6. Read the JIT and its `Requirements Used` sources.
7. Mark the task `in_progress` in `TASKS.md` and `STATUS.md`.
8. Implement only that task.
9. Add/update tests where appropriate.
10. Run required verification or experiments.
11. Update status according to the Task Lifecycle.
12. Make focused commits.
13. Push/update the PR when appropriate.
14. Report what changed, verification/results, and blockers or unresolved findings.

Do not automatically begin another task.

---

## Testing and Verification

Testing requirements depend on the task.

For software behavior:

* add tests for meaningful reusable behavior
* run the relevant test suite
* never claim a test passed without running it
* do not weaken or delete a test merely to make code pass

For research/analysis tasks:

* make the experiment reproducible
* record the exact command(s) used
* separate code correctness from conclusions drawn from Ken's data
* report unexpected input/data conditions
* prefer machine-readable outputs plus a concise human-readable summary when useful

Do not add CI, GitHub Actions, containers, databases, or other infrastructure unless the JIT calls for them.

---

## Scope Discipline

While working a task:

* stay within JIT scope
* do not modify unrelated legacy code
* do not add speculative product features
* do not perform opportunistic refactors unless required
* do not silently make product/design decisions
* do not turn a research script into production architecture without instruction
* keep implementation understandable
* preserve provenance and reproducibility

Record newly discovered work as follow-up rather than automatically expanding scope.

---

## Git and Pull Requests

Use focused commits.

A PR should make it easy for the Analyst to determine:

* what question/problem was addressed
* what changed
* what command/tests/experiment were run
* what outputs were produced
* what the evidence supports
* what remains unresolved

If the Analyst leaves actionable review feedback, address it before declaring the task ready for acceptance.

A pushed branch or passing local test run is not final acceptance.

---

## Completion Standard

A task is complete when:

1. JIT-requested behavior or experiment is complete.
2. Required verification has been run.
3. Required outputs are reproducible and understandable.
4. Source data/provenance distinctions are preserved.
5. No prohibited personal source data or secrets were committed.
6. No unrelated changes are included.
7. `TASKS.md` is current.
8. `STATUS.md` is current.
9. Applicable review feedback has been addressed.
10. The AI Analyst has explicitly accepted the task.

When finished, provide a concise handoff containing:

* task completed
* material files changed
* verification/experiment performed
* important findings
* branch/PR
* blockers or follow-up work
