# Canonical Role Prompts

These six files are the single source of truth for what each agent is. Everything in
`adapters/` points here; nothing there duplicates a role body.

| File | Pipeline step |
|---|---|
| `orchestrator.md` | Owns the whole run — see [`../PIPELINE.md`](../PIPELINE.md) |
| `task-planner.md` | 1 |
| `developer.md` | 3, plus fix passes in 4 and 6 |
| `code-reviewer.md` | 4, plus the review gate in 6 |
| `qa-tester.md` | 5, plus re-tests in 6 |
| `settings-optimizer.md` | 9 (optional) |

## What belongs in a role prompt

The role's identity, responsibilities, workflow, output contract, and the judgment calls
it has to make. Everything that would still be true if the project switched languages
tomorrow.

## What does not

Anything stack- or project-specific: build commands, module names, framework rules,
file layout, release gates, the output language. That lives in the active profile
(`profiles/`), which every role reads at launch and the orchestrator passes to every
subagent.

The split is the load-bearing idea of this repository. Fusing the two — which is the
natural way to write these prompts — produces six files that must all be rewritten for
each new project, and that silently rot as the project moves. Keeping them apart means
adopting the pipeline for a new stack is one file.

## Precedence

Observed code > active profile > role prompt.

Profiles are written by hand and go stale. When a role finds the profile describing a
module that no longer exists, it follows the code and reports the drift in its output.
The orchestrator collects those reports into the final summary so the profile can be
corrected.

## Editing these

- Keep them stack-neutral. A stack detail that sneaks into a role prompt is a detail
  that has to be found and removed by the next person adopting this.
- Keep the output contracts stable. The orchestrator parses them by shape — issue
  numbers, PR numbers, the literal `✅ APPROVAL`, the two-list QA report.
- If you add a rule that constrains the pipeline rather than the role, it belongs in
  `PIPELINE.md` under Strict Rules instead.
