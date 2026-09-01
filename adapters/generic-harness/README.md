# Adapter: Generic Harness

For any harness with a `subagent`-style primitive but **no agent registry** — nowhere to
declare an agent by name and have the framework load its prompt.

The orchestrator role is played by the main session. Each pipeline step launches a
subagent whose prompt the orchestrator assembles by hand:

```
prompt = shim + contents of agents/<role>.md + step context
```

This is the most portable adapter and the most explicit. Nothing is implicit in a
framework, which also means nothing is enforced by one — the iteration guardrails are
counters the orchestrator keeps itself.

## Files

- [`orchestrator-runbook.md`](orchestrator-runbook.md) — the shim text, prompt assembly,
  preconditions, guardrails, and the dry-run mapping. Read this alongside
  [`../../PIPELINE.md`](../../PIPELINE.md), which remains the flow itself.
- [`launchers/`](launchers/) — one file per role: what to pass in, what to expect back,
  and the criterion for moving on.

The launchers do not contain role prompts. They are the step contract; the role prompt
is `agents/<role>.md`, read at assembly time.

## Install

Vendor this repository at `<project-root>/agent-orchestration/` and create your profile:

```bash
cp agent-orchestration/profiles/_template.md agent-orchestration/profiles/active.md
```

Nothing to register. Point your session at the runbook:

> Act as the orchestrator per `agent-orchestration/adapters/generic-harness/orchestrator-runbook.md`.
> Task: <the task>

## What this harness provides

| Pipeline assumption | Generic harness |
|---|---|
| Subagent launching | Manual prompt assembly per the runbook |
| Persistent agent memory | Not provided — see [`../../memory/README.md`](../../memory/README.md) for the file-based fallback, which the shim loads explicitly |
| Local permission config | Usually none → Step 9 usually does not apply; check your profile |
| Loop guardrails | **Not enforced.** The runbook makes them explicit counters. |

## Why the guardrails matter more here

On a harness with a registry, a runaway loop is at least visible as a stack of named
subagent calls. Here it is just the main session doing the same thing repeatedly, which
is much easier to miss — for the user and for the orchestrator.

The 3-iteration cap is not a performance tuning knob. A review loop that has not
converged in three passes is telling you the task is under-specified or the finding is
wrong, and a fourth pass will not discover that.
