# Launcher: settings-optimizer

Use the [generic runtime adapter](../orchestrator-runbook.md) to launch an independent
agent with the resolved absolute path to `skills/settings-optimizer/SKILL.md` and the complete
current stage handoff. Apply the host's configured model and reasoning choices through
supported launch options.

The canonical skill defines the work and return contract. The canonical `PIPELINE.md`
defines when this stage runs and what permits the next transition. Wait for the result
before continuing dependent work.
