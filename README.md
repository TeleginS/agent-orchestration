# agent-orchestration

A multi-agent delivery pipeline you can point at any codebase. One task in, one reviewed
and QA'd pull request out.

Six specialized agents, eleven steps, two loops with guardrails. The orchestrator holds
the whole picture and delegates every piece of work; nothing it coordinates does it also
do itself.

```
task → plan → branch → implement → review ⇄ fix → QA → fix ⇄ review ⇄ retest → cleanup → report
                                    (×3 max)          (×3 max)
```

## What 20 real runs look like

Most published agent pipelines are a diagram and a promise. This one has outcomes.

| | |
|---|---|
| Orchestrated runs | 20 |
| Merged | 19 |
| Closed without merging | 1 |
| Runs where **review** sent work back | 2 |
| Runs where **QA** filed bugs | 8 |
| Times either loop hit its 3-iteration cap | 0 |

The interesting number is the gap between the last two. Review sends work back 10% of the
time; QA finds bugs 40% of the time — on code a reviewer just approved. That ratio is the
entire argument for keeping them as separate steps, and for running QA second.

Here is one of those eight, in full:

> The reviewer read every terminal code path and proved a true statement — no path
> double-counts session time — and approved. QA then found time being double-counted, via
> a race between a countdown timer and a modal dialog that no reading of the diff could
> reveal.

Nobody was careless, and the approval was correct. **A reviewer reads the change; QA runs
the program and asks what else can happen.** Merging the two steps — the obvious
efficiency — deletes the one that catches this.

[`examples/run-cumulative-stats/`](examples/run-cumulative-stats/) has that run end to end,
with the artifacts the pipeline actually wrote: epic, child issues, PR, review comment, bug
report, fix, re-review, re-test. [`examples/`](examples/) also covers the two send-backs —
one where the pipeline caught its own agents writing a deleted symbol back into the
repository, and one that shipped nothing at all.

For what a run **costs**, the measured numbers are in
[`examples/run-progress-store-tests/`](examples/run-progress-store-tests/): 1,097,667
subagent tokens across 9 launches, 302 tool calls, 1h 31m wall clock, broken down per step
and per role — plus a costed estimate and an honest argument about whether it was worth it.

### Status, stated plainly

Those 20 runs were produced by the **ancestor** of this repository: one project, one
stack, prompts with the project fused into them. What is published here is a
restructuring — same flow, same guardrails, rewritten role prompts, and a profile
indirection the original did not have.

The restructured version has now been run end to end **once**, on a real task in a real
repository: [`examples/run-progress-store-tests/`](examples/run-progress-store-tests/).
Every guardrail behaved as designed, the profile seam held, and the precedence rule caught
three stale facts in the profile on its first outing. That run has measured token counts,
wall clock and a costed estimate — **≈1.7M tokens, ~$10, 1.5 hours** for a task a
competent engineer would scope at half a day. Whether that trade is worth it is argued
honestly in the report rather than assumed.

One run is not twenty. Point it at something real in
[dry-run](PIPELINE.md#dry-run-mode) first — it touches neither your tracker nor your
remote — and treat your first live run as a shakedown.

## Map

- **[examples/](examples/)** — what the pipeline produces, and what 20 runs look like
  - **[run-cumulative-stats/](examples/run-cumulative-stats/)** — one complete run, every
    artifact, including the bug-fix loop
  - **[run-progress-store-tests/](examples/run-progress-store-tests/)** — the first live
    run of this version: measured tokens, wall clock, cost, and what it found
  - **[artifacts/](examples/artifacts/)** — the output contracts the orchestrator parses
- **[PIPELINE.md](PIPELINE.md)** — the runbook: every step, its transition criterion,
  the strict rules
- **[PIPELINE-GRAPH.md](PIPELINE-GRAPH.md)** — the same thing as a state diagram
- **[agents/](agents/)** — the six role prompts
- **[profiles/](profiles/)** — the one file you write to adopt this
- **[adapters/](adapters/)** — Claude Code, Codex, generic harness

## The idea

The natural way to write agent prompts is to bake the project into them: this reviewer
knows the framework and checks the billing SDK's entitlement flag, this developer knows
the module layout. It works, and it produces six files that must each be rewritten for
the next project and that quietly rot as this one moves.

So the prompts here are split along that seam:

- **`agents/<role>.md`** — how a reviewer reviews, how a planner decomposes, what a QA
  verdict requires. Stack-neutral, and true regardless of what the project is written
  in.
- **`profiles/<project>.md`** — build and test commands, module names, architecture
  invariants, release gates, the stack-specific checklist entries.

The orchestrator resolves the active profile once and passes its path into every
subagent launch. Adopting the pipeline for a new project means writing one profile, not
editing six prompts.

**Precedence is: observed code > profile > role prompt.** Profiles are written by hand
and go stale; roles are told to follow the code when the two disagree and to report the
drift, which surfaces in the final report so the profile can be fixed.

## Quick start

```bash
git submodule add <this-repo> agent-orchestration
cp agent-orchestration/profiles/_template.md agent-orchestration/profiles/active.md
```

Fill in `active.md` — [`example-mobile-app.md`](profiles/example-mobile-app.md) shows
the useful level of detail. Then install an adapter:

```bash
cp -r agent-orchestration/adapters/claude-code/agents/. .claude/agents/
```

Launch the orchestrator with your task and let it work through the pipeline.

## The roles

| Role | Owns | Never does |
|---|---|---|
| `orchestrator` | Sequencing, git hygiene, issue cleanup, the final report | Writes code. Decomposes. Reviews. |
| `task-planner` | Decomposition into tracker issues with acceptance criteria | Implements |
| `developer` | Implementation, fix passes, the PR | Reviews its own work |
| `code-reviewer` | Reviewing the diff, blocking or approving | Fixes what it reviews |
| `qa-tester` | Acceptance criteria, the test suite, filing bugs | Fixes bugs |
| `settings-optimizer` | Consolidating the harness's permission config | Touches code or git |

## Rules worth knowing before you run it

A handful of these exist because the obvious behaviour is the wrong one:

**Every code change made after QA begins passes review before QA can be called green.**
QA bug fixes are code. Skipping the review on them is how an unreviewed change ships
under a green verdict.

**Loops cap at three iterations, then stop and escalate.** A review loop that hasn't
converged in three passes is telling you the task is under-specified or the finding is
wrong. A fourth pass doesn't discover that.

**Bugs found outside the current change are filed but never block it.** QA labels them
`pre-existing`; Step 6 skips them and Step 8 refuses to close them. Filing everything and
scheduling separately beats the alternatives — silently not filing, or blocking a
finished PR on unrelated debt.

**Unmerged work is not closed.** Issues get a PR reference comment and stay open until
merge is confirmed. Closing the wrong one erases a tracked task.

**No blanket `git add .`.** Only durable artifacts, path by path. Anything uncertain goes
in the report for a human to decide.

**Step 0 can stop the pipeline before it starts** — when a task needs product decisions
nobody has made yet. Not because documentation is missing, but because four agents are
each about to decide it differently, and the disagreement will resurface as QA bugs.

## Harness support

| | Claude Code | Codex | Generic |
|---|---|---|---|
| Agent registry | ✅ `.claude/agents/` | ✅ `.codex/agents/` | ❌ manual assembly |
| Per-role model selection | ✅ | ✅ | ❌ |
| Automatic agent memory | ✅ | ❌ file-based fallback | ❌ file-based fallback |
| Step 9 (settings) | ✅ applies | ⊘ no permission config | ⊘ usually none |
| Loop guardrails | orchestrator | orchestrator | orchestrator |

Every adapter is a **pointer**, not a copy. Each registration file names the role, sets
whatever the harness needs, and tells the agent to read `agents/<role>.md`. Nothing
duplicates a prompt body — which is the failure this shape exists to prevent, and one the
original of this pipeline actually hit: a pipeline rule lived in one registration format
and was missing from the other.

## Also here

- **[conventions/](conventions/)** — swappable repo conventions the roles reference:
  the issue tracker (GitHub `gh` by default), triage labels, and where domain docs live
- **[memory/](memory/)** — the agent memory layout, and the rule that keeps it from
  becoming a second, stale copy of the profile

## Dry-run

The whole pipeline with no writes to the tracker or the remote — plan to markdown, local
branch, no PR, bugs as a list. Useful for evaluating it on a new project before pointing
it at anything real. See the table at the end of [PIPELINE.md](PIPELINE.md).
