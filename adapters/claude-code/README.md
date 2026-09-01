# Adapter: Claude Code

Claude Code auto-discovers subagents from `.claude/agents/*.md`. Each file's frontmatter
registers the agent; its `description` drives delegation; its body is the prompt.

These six files are thin wrappers. The body tells the agent to read the canonical role
prompt and the active profile at launch, so the real content stays in one place.

## Install

```bash
cp -r agent-orchestration/adapters/claude-code/agents/. .claude/agents/
```

Then create your profile:

```bash
cp agent-orchestration/profiles/_template.md agent-orchestration/profiles/active.md
```

Fill it in. That's the adoption work — the six role prompts need no editing.

If you vendored this repository somewhere other than `<project-root>/agent-orchestration/`,
update the paths inside the copied files.

## Run

Launch the orchestrator with the task, in the main conversation:

> Use the ai-orchestrator agent: <the task>

It resolves the profile, then works through [`../../PIPELINE.md`](../../PIPELINE.md),
launching the other five by name via the Agent tool.

For a task needing product or design decisions, do that clarification in the main
conversation **first** — Step 0 stops the pipeline otherwise, and correctly so. The
orchestrator cannot run an interactive design conversation from inside a subagent.

## What this harness provides

| Pipeline assumption | Claude Code |
|---|---|
| Subagent launching | Agent tool, by registered name |
| Persistent agent memory | `memory: project` in frontmatter → `.claude/agent-memory/<name>/` |
| Local permission config | `.claude/settings.local.json` → **Step 9 applies** |
| Loop guardrails | Not enforced by the harness — the orchestrator counts them |

## Model selection

Set per role in the frontmatter. The defaults here reflect what each role actually does:

| Role | Model | Why |
|---|---|---|
| `ai-orchestrator` | opus | Holds the whole run's state and makes the scope calls |
| `task-planner` | opus | Decomposition quality sets the ceiling for everything downstream |
| `developer` | sonnet | Volume work against a specified plan |
| `code-reviewer` | sonnet | Volume work against an explicit checklist |
| `qa-tester` | sonnet | Volume work against explicit criteria |
| `settings-optimizer` | haiku | Mechanical pattern consolidation |

Adjust to taste. The two worth spending on are the planner and the orchestrator: a bad
decomposition or a mis-sequenced run costs more than a weaker implementation pass, which
the review loop is there to catch.

## Naming

The orchestrator is registered as `ai-orchestrator` rather than `orchestrator` because
Claude Code matches delegation against the description and name, and the bare word is
generic enough to collide. The other five keep their canonical names.
