# Launcher: production-triage

Use the [generic runtime adapter](../orchestrator-runbook.md) to launch an independent
agent with the resolved absolute path to `skills/production-triage/SKILL.md`, the
target project root, and the absolute active profile path. The agent needs the
profile's error-source tool; if the host cannot provide it, the skill stops without
filing anything.

This is a standalone stage run on request, not a pipeline step. The canonical skill
defines the work and return contract.
