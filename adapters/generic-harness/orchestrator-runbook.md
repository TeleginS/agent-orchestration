# Orchestrator Runbook — Generic Harness

You are the orchestrator. The main session plays the role; every step-agent is a
subagent whose prompt you assemble by hand.

**The flow is [`../../PIPELINE.md`](../../PIPELINE.md).** Read it and follow it step by
step. This file is only the harness-specific delta: how to launch, what the harness does
not do for you, and how to run without a tracker.

Your role definition is [`../../agents/orchestrator.md`](../../agents/orchestrator.md).

## Prompt assembly

Every subagent launch is three parts, concatenated:

```
prompt = shim + full contents of agents/<role>.md + step context
```

Read the role file and paste it in. Do not summarize it — a summarized checklist is a
different checklist.

### The shim

Identical for every role except the substitutions:

> You are acting as the subagent `<role>` under the instructions below, running in
> `<harness name>` — **not** Claude Code. Repository: `<repo root>`.
>
> You have file read/write and a shell. You do **not** have Claude Code's Task/Agent or
> TodoWrite tools — don't try to call them; do the work yourself.
>
> The instructions below are your role: the checklists and the report format are
> mandatory. Return your report to the orchestrator in exactly the format your role
> specifies — for the reviewer, the `Code Review — Iteration N` block; for QA, the
> separated in-scope / pre-existing lists with issue numbers; for the developer, the
> changed files plus the PR number; for the planner, the issue numbers and URLs.
>
> The **active profile** is at `<profile path>`. Read it first. Precedence is: observed
> code > profile > this prompt. If the profile contradicts the code, follow the code and
> report the drift.
>
> Before starting, read your memory notes at `<memory root>/<role>/MEMORY.md` and any
> relevant entries it indexes. When you finish, update them per your role's memory
> section.

That last paragraph exists because this harness does not load agent memory for you. On a
harness that does, drop it.

## Preconditions

Check these once at the start of a session, by running the commands — not by trusting a
previous run's notes:

- [ ] Tracker CLI authenticated
- [ ] Working tree clean, on the base branch
- [ ] Design artifacts present, or the task is operational (Step 0 decides)
- [ ] A preflight build succeeds and the test suite runs — using the profile's commands
- [ ] The active profile resolves and matches what you see in the repository
- [ ] The task from the user is in hand

A preflight build that fails here fails for the developer too, three steps later, with
much less clarity about why.

## Guardrails you enforce yourself

Nothing in this harness counts iterations, enforces the review gate, or stops a loop.

- **Step 4** (review ⇄ developer): maximum 3 iterations. State the count in each
  progress message. Still blocked after the third → STOP, report the full finding list
  to the user.
- **Step 6** (fix → review → re-test): maximum 3 iterations, same handling.
- **Rule 11**: every code change after QA begins passes the reviewer before QA re-tests.
  It is easy to skip here because you are assembling the prompts by hand and the
  reviewer feels like an extra step. It is the step that stops an unreviewed fix from
  shipping under a green QA verdict.
- **Full context every time**: a hand-assembled prompt is easy to under-fill. The
  subagent has no memory of the previous step and no access to your conversation.

## Running without a tracker

Dry-run mode from `PIPELINE.md`, with the local paths this adapter uses:

| Step | Behaviour |
|---|---|
| 1 | Planner returns the plan as markdown; save to `run-plans/<slug>.md` (`mkdir -p run-plans`) |
| 2 | Local branch only, no push |
| 3 | Implementation on the local branch, no PR; report is the file list plus summary |
| 4 | Review of `git diff <base>...HEAD` locally; identical report format |
| 5 | Bugs as a markdown list, split in-scope / pre-existing |
| 6 | Fix loop local; issue closure becomes a checklist in the run plan |
| 7 | Artifacts listed, not committed |
| 8 | Skipped — no issues exist |
| 9 | Audit only: report what *would* change, without editing the file |
| 10 | Final report plus an offer to re-run for real |

Fix the mode at launch and record it on the first line of the run plan. A run that
switches modes halfway leaves half its state in the tracker and half on disk.

## Differences from a registry-based harness

| Aspect | Registry harness | This one |
|---|---|---|
| Launching | By registered name; framework loads the prompt | Manual assembly: shim + role file + context |
| Model per role | Declared in the agent's metadata | Whatever the harness gives you |
| Agent memory | Loaded automatically | Loaded by the shim, explicitly |
| Loop limits | Still the orchestrator's job | Still the orchestrator's job, with less visibility |
