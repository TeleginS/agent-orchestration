# Generic runtime adapter

The main conversation applies `<library-root>/skills/orchestrator/SKILL.md`.
`<library-root>/PIPELINE.md` is the shared runbook: it owns the steps, handoff fields,
transition criteria, loop limits and modes. This file supplies only launch mechanics
and environment context.

## Resolve the environment

Establish the target project's absolute root from the launch context or the main
conversation's repository root. Resolve the supplied library root physically, following
symlinks; otherwise use `<project-root>/agent-orchestration`. The project root is where
work and memory live; the library root supplies skills and conventions. Resolve the
profile, runtime adapter, canonical skill and artifact paths to absolute paths before
launching a child.

Identify the host's actual independent-agent primitive, available filesystem and shell
tools, configured model/reasoning choices, and whether a local permission configuration
exists. Report an unavailable required capability instead of naming another host's
tools. Apply any required working directory or environment setup through supported
launch options; use the active profile's build and test commands.

## Assemble a stage launch

Launch an independent subagent with these parts:

1. **Runtime context:** role, absolute project/library roots, canonical skill path,
   this runtime adapter's absolute path, working directory, available capabilities
   and ownership constraints.
2. **Canonical instructions:** tell the child to read
   `<library-root>/skills/<role>/SKILL.md`. If file loading is unavailable, include
   that file's full contents and the relevant references it requires; do not summarize
   checklists or invent a substitute procedure.
3. **Stage handoff:** include every applicable field required by `PIPELINE.md`: original
   task, active profile, design artifacts, mode, issues, branch/base, PR, findings,
   iteration, ownership, memory restrictions and limits on external writes. Use absolute
   paths and explicit absence where appropriate.

Subject to the task's memory restrictions before reading, the child loads
`<library-root>/memory/RULES.md`, then the shared role index at
`<project-root>/.agents/memory/<role>/MEMORY.md` and relevant notes. If files must be
inlined, provide these relevant inputs too and preserve their write policy. All memory
belongs to the target project; do not create a host-specific alternative root.

Use the host's configured defaults unless the user or host configuration specifies a
role model or reasoning choice. Pass explicit choices through supported launch options;
if they cannot be honored, report the mismatch before substituting. Merely including a
model name in a prompt does not select that model.

Wait for the result and return the canonical skill's report to the main orchestrator.
Use a separate agent from the implementer for review and another for QA. A host without
independent agents cannot complete these stages by applying the skills inline.

The main orchestrator follows the canonical pipeline's guardrails and mode throughout;
this adapter does not carry a second dry-run table or step counter policy. Optional
settings housekeeping is supported only if the runtime and active profile identify a
local permission configuration. In dry-run it is audit-only, including no memory writes.
