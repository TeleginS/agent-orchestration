# Codex runtime

Use the canonical skill for role behavior and `<library-root>/PIPELINE.md` for the
workflow, complete handoff, modes and loop limits. The main conversation is the default
orchestrator and applies the skill directly.

## Paths and context

Resolve the target project root from explicit launch context, or the main conversation's
repository root for direct invocation. Resolve the supplied library root physically,
following symlinks; otherwise use `<project-root>/agent-orchestration`. Pass these as
separate absolute paths. Resolve skill links to their physical library before following
library-relative references.

Every child receives the absolute canonical skill and runtime adapter paths, project and
library roots, active profile and design artifacts, plus original task, mode, issues,
branch/base, PR, prior findings and iteration, ownership, memory restrictions and limits
on external writes from the canonical handoff. State an explicit absence for fields
that do not apply. The skill
explicitly loads `<library-root>/memory/RULES.md` and the role's index at
`<project-root>/.agents/memory/<role>/MEMORY.md` plus relevant notes, subject to the
task's memory restrictions before reading; there is no separate Codex memory root.

## Launching stages

Inspect the current host's available subagent tool and the installed
`<project-root>/.codex/agents/<role>.toml` before selecting a launch route.

1. If the tool supports registered custom roles, launch the named stage with the full
   handoff using its supported schema. The registered loader reads the canonical skill.
2. Otherwise read the installed TOML yourself. Pass its `developer_instructions` and
   the full handoff to an independent subagent. Resolve any configured `model` and
   `model_reasoning_effort`, including explicit user overrides, into the host's actual
   supported model/reasoning spawn options. Do not assume parameter names are shared
   across hosts or that reading the TOML applies those settings automatically.
3. If no model or reasoning is configured or requested, use the host's configured
   defaults; do not introduce new tuning. If an explicit choice or another configured
   launch constraint cannot be honored, report that mismatch and resolve the choice
   before starting the child. Do not claim the configured model ran without evidence.

When no installed loader exists, the library's corresponding TOML supplies the default
loader instructions. A project-specific loader or explicit user setting takes priority.
A host with no independent-agent capability cannot provide this pipeline's independent
review and QA: report the missing capability instead of performing those checks as the
implementer. Wait for each stage's output before taking a dependent transition.

The optional orchestrator TOML supports explicitly requested delegated coordination.
It does not relocate an already-running main-conversation orchestrator. A delegated
coordinator forwards questions requiring user input to its parent and does not invent
answers.

This runtime has no local permission allowlist to consolidate. Report that capability
when the canonical pipeline considers optional settings housekeeping. Follow canonical
dry-run rules for all writes, including memory; settings audits never update memory.
