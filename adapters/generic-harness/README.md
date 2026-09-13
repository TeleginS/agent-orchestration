# Adapter: Generic Harness

The main conversation runs the canonical orchestrator skill. It launches independent
stage agents with the appropriate canonical skill and the current handoff. This adapter
needs no role registry and supplies no model defaults.

Complete the [shared installation](../README.md#shared-installation), then start with:

> Apply `/absolute/project/agent-orchestration/skills/orchestrator/SKILL.md` in this
> conversation, using `/absolute/project/agent-orchestration/adapters/generic-harness/orchestrator-runbook.md`
> as the runtime adapter. Active profile: `/absolute/project/profile.md`. Task: ...

[`orchestrator-runbook.md`](orchestrator-runbook.md) covers prompt assembly, paths and
host capabilities. [`launchers/`](launchers/) contains optional role selectors for
hosts that need explicit launcher files. The [canonical pipeline](../../PIPELINE.md)
owns every step, gate, report transition and dry-run behavior.

A host must support independent stage agents to run the full pipeline. Loading a
review skill into the implementing agent is not an independent review. Model choices
come from explicit user preferences or the host configuration; if the host cannot
honor a configured choice, report the mismatch before launching.

All roles load shared memory explicitly from `<project-root>/.agents/memory/<role>/`
under the canonical [memory rules](../../memory/RULES.md). The runtime's permission
configuration capability and active profile determine whether optional settings
housekeeping applies.
