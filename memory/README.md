# Agent Memory

Each role accumulates institutional knowledge about the project it works in. This is the
layout and the rules; the content is per-project and does not live in this repository.

## Layout

One directory per role, under a memory root the harness decides:

```
<memory-root>/
├── orchestrator/
│   ├── MEMORY.md          # index — one line per note, no content
│   ├── process-<topic>.md
│   └── history-<topic>.md
├── task-planner/
├── developer/
├── code-reviewer/
├── qa-tester/
└── settings-optimizer/
```

On Claude Code with `memory: project`, the root is `.claude/agent-memory/`. On harnesses
without built-in memory, pick a root, keep it in version control, and have the shim load
`<root>/<role>/MEMORY.md` at launch — the generic-harness shim already does.

## Note format

```markdown
---
name: <short-kebab-case-slug>
description: <one-line summary — this is what future-you reads to decide relevance>
metadata:
  type: user | feedback | project | reference
---

<the fact. For feedback and project types, follow with **Why:** and **How to apply:**>
```

Link related notes with `[[slug]]`. A link to a note that doesn't exist yet is fine — it
marks something worth writing.

`MEMORY.md` is an **index**, not a memory: one line per note,
`- [Title](file.md) — hook`, no frontmatter. It is loaded into context every session, so
keep it short. Never write note content into it.

## What to record

| Type | Content |
|---|---|
| `user` | Role, expertise, preferences — how to collaborate with this person |
| `feedback` | Guidance on how to work, from corrections **and** confirmations. Always include the why. |
| `project` | Ongoing work, goals, constraints not derivable from the code. Convert relative dates to absolute. |
| `reference` | Pointers to external systems — dashboards, trackers, channels |

Record from success as well as failure. A memory file containing only corrections
produces an agent that avoids its past mistakes and drifts away from the approaches the
user already validated — cautious in a way nobody asked for.

## What NOT to record

- Code structure, architecture, file paths, conventions — **these belong in the
  profile**, which is versioned, reviewed, and read by every role at launch. A duplicate
  in memory is a second source of truth that nobody updates.
- Git history and who-changed-what — `git log` is authoritative.
- Fix recipes — the fix is in the code and the reason is in the commit message.
- Ephemeral task state — that is what the run itself is for.

These exclusions hold even when asked directly. If someone asks you to remember a PR
list, ask what was *surprising* about it and record that instead.

## Staleness

A note naming a file, module or flag is a claim about when it was written. Before acting
on one, verify the thing still exists. When memory and the code disagree, the code wins
and the note gets corrected or deleted.

This is the same precedence rule the profile follows, for the same reason: hand-written
descriptions of a moving codebase are always the part that is wrong.

## Sharing

Project-scoped memory in version control is shared across the team and across harnesses.
Write it for the next person, not as a private scratchpad — and keep anything personal
out of a directory that ships in the repository.
