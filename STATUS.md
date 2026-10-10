# STATUS.md

**Product:** RideWorks.
**Current handoff:** **P5-01 — Rolling Training Advisor**; Phase 5 begins with Home, Plan and honest recommendation-versus-actual context.
**State:** **pending implementation** — Owner direction and Analyst JIT prepared 2026-10-10; **Dex has not yet been invoked**. [P5-01 issue #25](https://github.com/k14krug/rideworks/issues/25).
**Accepted prior work:** P4-01/P4-02 and Phase 4 accepted/merged in [PR #24](https://github.com/k14krug/rideworks/pull/24), unchanged.
**Controlling direction:** [P5-01 design](docs/design/P5-01-rolling-training-plan.md), [Phase 5 acceptance](docs/PHASE_5_ACCEPTANCE.md), [implementation JIT](docs/tasks/P5-01.md), revised [product requirements](docs/PRODUCT_REQUIREMENTS.md). **Plan displays today through the next THREE upcoming hard recommendations**, with every intervening day, not a fixed week. Home displays today's same suggestion.
**Planning behavior:** Never recommend Rest/no ride; skipped past synced days count as assumed rest for planning (never as invented completed rides). Race / Threshold / VO2 types, generally one race plus one structured hard session in about seven days, two post-hard recovery dates with VO2's easier second day. Today's/heavy-legs and unexpectedly completed activities modify the rotation; all projected sessions remain conditional and distinct from actual/confirmed intent. No Zwift file integration or race search.
**Next action:** Under repository `AGENTS.md`, launch `/TASK P5-01` or `/AUTOTASK P5-01` in Dex. On invocation refresh `main`, begin this *single* pending task, implement and test, then STOP at **HARD — Analyst Gate 1**; Owner Gate 2 on the running Plan later. No Phase 6 or Phase 5 acceptance/merge now.
