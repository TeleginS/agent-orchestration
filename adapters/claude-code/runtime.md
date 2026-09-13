# Claude Code runtime

Use this file for launch mechanics; read the canonical skill for role behavior and
`<library-root>/PIPELINE.md` for sequencing, handoff requirements and modes.

## Paths and context

Resolve the target project root from the explicit launch context, or the main
conversation's repository root for a direct invocation. Resolve the supplied library
root physically, following symlinks; otherwise use `<project-root>/agent-orchestration`.
The wrapper location and current shell directory may differ from both roots.

Read `<library-root>/skills/<role>/SKILL.md`. The canonical skill loads the shared
memory rules and `<project-root>/.agents/memory/<role>/MEMORY.md` plus relevant notes,
subject to the task's memory restrictions before reading.
Do not enable a second role-memory store through Claude's agent metadata.

Every stage invocation includes absolute project/library roots, profile, runtime adapter
and artifact paths, plus the original task, mode, issue URLs, branch/base, PR, prior
findings and iteration, and file ownership, memory restrictions, limits on external
writes or other execution constraints required by the canonical handoff. State an
explicit absence for fields that do not apply. Pass
this context as skill arguments so `$ARGUMENTS` reaches the fork; do not rely on the
child inheriting the main conversation.

## Launching

The main conversation applies `orchestrator` directly. It invokes the other installed
skill names through the **Skill tool**, passing the full handoff as arguments. The
wrappers' fork metadata creates the stage subagent; `background: false` waits for its
result before the dependent transition. Do not launch the old named agents or load a
stage inline as a substitute for independent execution.

Use the model configured in the installed wrapper, subject to explicit user overrides
and supported host controls. If the requested skill or model is unavailable, report
the missing capability and supported alternatives before substituting. A successful
file read does not prove the host honored fork or model metadata.

The runtime has a local permission configuration at
`<project-root>/.claude/settings.local.json`; the active profile can specify its path
and relevant command prefixes. The canonical pipeline decides whether housekeeping
applies. Its dry-run rules remain authoritative: settings housekeeping is audit-only,
including no memory writes.
