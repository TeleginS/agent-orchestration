# Compatibility role entries

These six files preserve historical `agents/<role>.md` links and loaders. Each is a
small pointer to the canonical [skill](../skills/README.md); no role body is duplicated
here. New integrations should load `skills/<role>/SKILL.md` directly through the
appropriate [runtime adapter](../adapters/README.md).

| Entry | Canonical skill |
|---|---|
| [orchestrator.md](orchestrator.md) | [orchestrator](../skills/orchestrator/SKILL.md) |
| [task-planner.md](task-planner.md) | [task-planner](../skills/task-planner/SKILL.md) |
| [developer.md](developer.md) | [developer](../skills/developer/SKILL.md) |
| [code-reviewer.md](code-reviewer.md) | [code-reviewer](../skills/code-reviewer/SKILL.md) |
| [qa-tester.md](qa-tester.md) | [qa-tester](../skills/qa-tester/SKILL.md) |
| [settings-optimizer.md](settings-optimizer.md) | [settings-optimizer](../skills/settings-optimizer/SKILL.md) |

Edit shared role instructions in the canonical skill, pipeline rules in
[PIPELINE.md](../PIPELINE.md), project details in the active
[profile](../profiles/README.md), and launch/model configuration in the runtime
adapter. Keep these pointers small and preserve their paths for existing callers.
