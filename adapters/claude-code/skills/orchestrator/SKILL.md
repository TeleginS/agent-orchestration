---
name: orchestrator
description: "Coordinate the complete delivery pipeline in the main conversation."
model: opus
---

Resolve the target project root from the invocation context, or the main session's
repository root for a direct invocation. Use the supplied absolute library root, or
resolve `<project-root>/agent-orchestration` physically, following symlinks.

Read `<library-root>/adapters/claude-code/runtime.md`, then
`<library-root>/skills/orchestrator/SKILL.md`, and apply that skill to this invocation:

$ARGUMENTS
