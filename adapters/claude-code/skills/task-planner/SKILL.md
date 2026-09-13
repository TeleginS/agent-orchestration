---
name: task-planner
description: "Plan a delivery task into acceptance criteria and actionable work items."
model: opus
context: fork
agent: general-purpose
background: false
---

Resolve the target project root from the invocation context, or the main session's
repository root for a direct invocation. Use the supplied absolute library root, or
resolve `<project-root>/agent-orchestration` physically, following symlinks.

Read `<library-root>/adapters/claude-code/runtime.md`, then
`<library-root>/skills/task-planner/SKILL.md`, and apply that skill to this invocation:

$ARGUMENTS
