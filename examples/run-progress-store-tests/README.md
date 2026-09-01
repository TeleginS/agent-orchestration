# Live run: ProgressStore test coverage

The first end-to-end run of **this** version of the pipeline — the restructured one in this
repository, with stack-neutral roles and a project profile. Not the ancestor that produced
the [20-run outcome data](../README.md#what-actually-happens-across-20-runs).

Everything below is measured, not estimated, except where a line says otherwise.

- **Task**: add unit tests for the one store in a production iOS app that had none
- **Date**: 2026-09-01
- **Harness**: Claude Code, roles read directly from `agents/` — the orchestrator role was
  played by the main session
- **Repository**: private, so the PR and issues are not linkable. This report is
  self-contained.

## Result

| | |
|---|---|
| Pipeline steps run | 0–10 |
| Subagent launches | 9 |
| Review iterations | 3 |
| QA passes | 2 |
| Bug-fix loop iterations | 1 |
| Loop guardrail (cap 3) hit | never — worst was iteration 3 of 3 in review |
| Commits | 4 |
| Files changed | 3 (+758 lines) |
| Production code changed | **0 lines** |
| Tests before → after | 125 → 157 |
| Tracker issues created | 12 |

## Cost

### Measured: subagent tokens

| Step | Role | Tokens | Tool calls | Wall clock |
|---|---|---|---|---|
| 1 | task-planner | 113,654 | 24 | 7m 10s |
| 3 | developer | 159,422 | 59 | 24m 52s |
| 4 · iter 1 | code-reviewer | 134,464 | 30 | 7m 57s |
| 4 · fix | developer | 74,767 | 19 | 4m 00s |
| 4 · iter 2 | code-reviewer | 95,164 | 20 | 5m 41s |
| 5 | qa-tester | 164,345 | 37 | 12m 31s |
| 6a | developer | 96,169 | 30 | 8m 32s |
| 6b | code-reviewer | 118,791 | 36 | 6m 43s |
| 6c | qa-tester | 140,891 | 47 | 13m 29s |
| **Total** | **9 launches** | **1,097,667** | **302** | **1h 31m** |

By role — the shape is more interesting than the total:

| Role | Launches | Tokens | Share |
|---|---|---|---|
| code-reviewer | 3 | 348,419 | 32% |
| developer | 3 | 330,358 | 30% |
| qa-tester | 2 | 305,236 | 28% |
| task-planner | 1 | 113,654 | 10% |

**Reviewing cost slightly more than implementing.** Three review passes out-spent three
developer passes. If you are budgeting a pipeline like this, the intuition that review is
a cheap rubber stamp on top of the real work is wrong — it is the same order of magnitude,
and on this run it was the largest single line item.

### Estimated: the orchestrator

Not directly measured. The orchestrator ran in the main session, so its usage is mixed in
with the surrounding conversation. Its work was 9 launch prompts, 9 report reads, ~40 of
its own tool calls, and the tracker writes. Because each turn re-sends a growing context,
a defensible range is **400k–900k tokens**, midpoint ~600k.

Treat the total as **≈1.7M tokens**, of which 1.1M is measured and 0.6M is an estimate.

### Dollars

Two things are unknown, so this is a band, not an invoice:

1. **The input/output split.** The reported per-agent figure is a total. Agentic loops are
   heavily input-weighted — each turn re-sends the transcript — so this assumes **92%
   input / 8% output**.
2. **Cache hit rate.** Cache reads bill at a fraction of fresh input. With the heavy
   prompt caching this harness does, the real figure lands nearer the low end.

At [Claude Opus 5](https://docs.claude.com/en/docs/about-claude/pricing) rates
($5.00 / $25.00 per MTok in/out), on the measured 1.1M subagent tokens:

| Scenario | Cost |
|---|---|
| Opus 5, no caching | ~$7.25 |
| Opus 5, heavy caching | ~$4 |
| Sonnet 5, no caching | ~$2.90 |

Adding the estimated orchestrator share, the whole run lands at roughly:

> ### ≈ $6 – 13, call it **$10**

Which is the number worth arguing about. See *Was it worth it* below.

### Could it be cheaper? The same run on DeepSeek V4-Pro

The pipeline is harness- and vendor-agnostic by construction, so the obvious question is
what the same token counts cost elsewhere. Rates below are from
[DeepSeek's official pricing docs](https://api-docs.deepseek.com/quick_start/pricing),
checked 2026-09-02. Third-party pricing pages disagreed with the official card by about
2x — check the source, not an aggregator.

**DeepSeek V4-Pro, per MTok:**

| | Off-peak | Peak |
|---|---|---|
| Input, cache hit | $0.022 | $0.044 |
| Input, cache miss | $0.66 | $1.32 |
| Output | $1.98 | $3.96 |

Peak is 01:00–04:00 and 06:00–10:00 UTC, weekdays only. Everything else — including all
weekend hours — is off-peak, at half.

Applying the same measured tokens and the same 92/8 split:

| Scenario | Subagents | Whole run |
|---|---|---|
| No cache, off-peak | $0.84 | **$1.30** |
| 70% cache hits, off-peak | $0.39 | **$0.60** |
| 90% cache hits, off-peak | $0.26 | **$0.40** |
| No cache, peak | $1.68 | $2.60 |

Roughly **$1 against $10** — 5–15x cheaper, and the conclusion survives generous
assumptions. Even if the model needed 1.5x the tokens to converge, the run lands at
$0.90–1.95; at 2x it stays under $3.

**Three things that comparison does not say.**

*Token counts do not transfer between vendors.* The 1.1M figure is what these models
needed. A different model takes a different number of turns, and different tokenizers give
different counts for identical text (usually within ±20% on English and code). There is
a concrete signal here: the ancestor of this repository shipped a DeepSeek harness
adapter whose runbook records one deliberate divergence — *"loop iterations: Claude Code,
no limit; DSH, a 3-iteration guardrail per loop"*. The cap was added on the DeepSeek side.
That is circumstantial evidence that its loops converged less readily and had to be
constrained. If so, extra turns eat into the saving — though, per the arithmetic above,
not the saving itself.

*Peak windows are a lever Claude does not have.* This run took 1h 31m. Landing entirely
inside a weekday peak window doubles the bill; moving it to a weekend or a non-peak hour
halves it back, for free.

*Benchmarks do not settle the question this pipeline turns on.* V4-Pro posts strong
agentic-coding numbers — SWE-Bench Verified ~91.2%, Terminal Bench 2.1 87.9%,
LiveCodeBench 93.5%. But the moment that justified this run's cost was QA noticing that an
assertion had quietly become a tautology *under contamination that had occurred an hour
earlier in the same run*. That is connecting two non-adjacent observations and then
distrusting a green test — not a benchmark task. Nothing in those scores predicts it
either way.

**The practical read:** cost is probably not the deciding variable. The gap between $1 and
$10 matters across hundreds of runs; across dozens it is noise next to one missed bug.
The thing actually worth measuring is whether the loops converge in the same number of
iterations. If review and QA need three passes instead of one, you pay not in tokens but
in the guardrail firing and escalating to a human — which costs more than any rate
difference. The [generic-harness adapter](../../adapters/generic-harness/) already exists,
so testing that is one dry-run on the same task.

## What the pipeline found

Nothing here was planted. All of it came out of agents doing their assigned step.

### Two production defects

- **A latent re-entrancy bug.** The planner, reading the code to decompose the task,
  noticed that a guard added to fix an earlier double-counting bug reads an *analytics*
  flag rather than session state — so two consecutive exit calls still double-count time
  and save a duplicate record. Unreachable from the current UI, one call site inside a
  modal. It declined to write a test for it (the test would be red, and the task was
  tests-only) and escalated to the orchestrator instead. Filed as its own issue.
- **A test-isolation defect** in three pre-existing test classes, labelled `pre-existing`,
  excluded from the fix loop, filed for a separate task.

### Three defects in the pipeline's own output

QA blocked the first submission on three findings — in code the reviewer had approved one
step earlier. See below.

### Three profile drifts

The precedence rule — *observed code > profile > role prompt* — earned its place on the
first run:

| Drift | Found by | Reality |
|---|---|---|
| Question count stated as 2,863 | task-planner, Step 1 | 2861 — and the project's own `CLAUDE.md` carries the stale figure |
| Test-file count stated as 13 | code-reviewer, Step 4 | 15 on this branch |
| No authoritative way to count tests | qa-tester + code-reviewer | Parallel log writer clobbers a line; `grep -c` undercounts by one |

Each was reported in the agent's own output, corrected in the profile mid-run, and the
corrections were committed with the work.

## The headline: QA blocked what review approved

This is the same pattern as the [harvested example](../run-cumulative-stats/), reproduced
live rather than retold.

The reviewer approved at iteration 2 after real work — it traced the new test against
production to prove it could not pass vacuously, checked that the wrong-answer construction
could not collide with the correct one, and recounted the suite itself rather than trusting
the developer's number.

QA then blocked. Five tests asserted an **absolute** accumulated value (`total > 0`) rather
than a **delta** around the call. Whenever the store is non-zero on entry, that assertion is
a tautology — it cannot fail even if the line it exists to cover were deleted.

Not hypothetical: that exact contamination had already happened earlier in the same run. A
stale preferences file, sitting in a domain the test process cannot clear, made seven tests
fail against a store that was never zero. It cost the developer most of its debugging time
in Step 3.

**The reviewer read the change. QA asked what else could happen.** Both did their job. Only
the second question finds this.

Two smaller things worth noting from the same loop:

- The developer proved its own fix by **mutation testing** — it temporarily removed the
  accumulation, confirmed the old assertion still passed and the new one failed, then
  deleted the scaffolding before committing.
- The reviewer then **corrected that proof**: with the hermeticity fix also applied, the
  "before" value is always zero, so the delta form is numerically identical to the old one
  *today*. The fix is right, but as regression-resistance for a future change, not as a
  defect being closed now. QA disagreed on the merits and said why. Nobody papered over it.

Rule 11 — every code change after QA begins passes review before QA re-tests — is what put
the reviewer in that position at all. It is the rule most likely to feel like overhead, and
it is the one that caught an unexplained drop in the test count (a log-parsing artifact, not
a lost test) before QA re-ran.

## Was it worth it

Honestly assessed, for a task a competent engineer would scope at half a day:

**Against it.** ~$10 and 1.5 hours of wall clock for 32 unit tests is not obviously cheap.
The pipeline also produced three defects in its own output that a single careful engineer
plausibly would not have written — the tautological assertion in particular is the kind of
thing you avoid by habit.

**For it.** The run surfaced a production bug nobody was looking for, three stale facts in
project documentation (one of which had been wrong in `CLAUDE.md` for an unknown length of
time), and a test-isolation defect predating the task. It caught its own three defects
before they merged. And the artifacts — 12 issues with real acceptance criteria, five review
and QA reports with reasoning, a PR body that states what was *not* verified — are the part
a half-day of solo work usually does not produce.

**The honest summary:** the pipeline is not cheaper than a good engineer on a small task. It
is more thorough than most engineers are on a task this boring, and it writes everything
down. Whether that trade is worth $10 depends entirely on whether anyone reads the writing.

## What this run does not prove

One task, one project, one operator, one harness. The task was unusually well-suited: no
product decisions (so Step 0's design gate passed trivially), a runnable test suite, an
existing tracker, and acceptance criteria that were already specific because a reviewer had
named the invariants a year earlier.

A task with genuine ambiguity would have stopped at Step 0 — correctly, but that is a
different run and it is untested here.
