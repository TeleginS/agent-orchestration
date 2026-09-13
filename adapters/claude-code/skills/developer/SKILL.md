---
name: developer
description: "Implement planned work or fix findings on the existing change branch."
model: sonnet
context: fork
agent: general-purpose
background: false
---

Resolve the target project root from the invocation context, or the main session's
repository root for a direct invocation. Use the supplied absolute library root, or
resolve `<project-root>/agent-orchestration` physically, following symlinks.

Read `<library-root>/adapters/claude-code/runtime.md`, then
`<library-root>/skills/developer/SKILL.md`, and apply that skill to this invocation:

$ARGUMENTS
