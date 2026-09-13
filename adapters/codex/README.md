# Adapter: Codex

Invoke `$orchestrator` in the main conversation after installing the canonical skills
under `.agents/skills/`. Independent stages use the thin files in [`agents/`](agents/)
to load the same canonical skills with [`runtime.md`](runtime.md). The orchestrator
TOML is optional compatibility wiring; it is not the normal entry point.

## Install

Complete the [shared installation](../README.md#shared-installation), then install the
four stage loaders from the adopting project root:

```bash
mkdir -p .codex/agents
for role in task-planner developer code-reviewer qa-tester; do
  if [ -e ".codex/agents/$role.toml" ] || [ -L ".codex/agents/$role.toml" ]; then
    printf 'Preserving existing loader: %s\n' "$role"
  else
    cp "agent-orchestration/adapters/codex/agents/$role.toml" ".codex/agents/$role.toml"
  fi
done
```

Inspect a preserved same-name loader and merge its custom host settings with the new
canonical skill pointer. Keep unrelated agents and `.codex/config.toml` intact. If
`.codex/agents` itself is a symlink, inspect its destination before installing.

If an older installation includes `.codex/agents/orchestrator.toml`, retire it after
updating launch instructions to `$orchestrator`, or explicitly retain it for a workflow
that needs a delegated coordinator. Do not install it by default. A delegated
coordinator must return unresolved user decisions to the main conversation.

The optional [`environments/environment.toml`](environments/environment.toml) is a
setup template. Merge needed setup commands into the project's existing environment;
do not copy the entire adapter over `.codex/` and overwrite local configuration.

## Run

```text
$orchestrator Task: <the task>. Active profile: /absolute/project/profile.md.
Runtime adapter: /absolute/project/agent-orchestration/adapters/codex/runtime.md
```

The main conversation resolves the active profile and follows the canonical pipeline.
It passes the complete handoff to each stage. All roles explicitly use
`<project-root>/.agents/memory/<role>/` through the canonical skills and shared memory
rules. This adapter does not provide local permission-allowlist housekeeping, so it
has no `settings-optimizer` TOML.

## Models and runtime capabilities

Every role file in `agents/` includes commented examples for `model` and
`model_reasoning_effort`. **You can set the model and reasoning effort separately for
each role:** remove the leading `#` from those two lines in the installed
`.codex/agents/<role>.toml` and adjust the values to models and effort levels supported
by your host. For example, enable these settings in `.codex/agents/developer.toml`:

```toml
model = "gpt-5.6-terra"
model_reasoning_effort = "high"
```

The commented examples come from TrafficRulesApp's role assignments:

| Role | Example model | Example reasoning effort |
|---|---|---|
| `orchestrator` (optional delegated role) | `gpt-5.6-sol` | `medium` |
| `task-planner` | `gpt-5.6-sol` | `high` |
| `developer` | `gpt-5.6-terra` | `high` |
| `code-reviewer` | `gpt-5.6-sol` | `high` |
| `qa-tester` | `gpt-5.6-sol` | `high` |

While the lines remain commented, they set no overrides: the host's configured
defaults apply unless the user overrides them. Settings in `orchestrator.toml` apply
only when that optional delegated role is launched; invoking `$orchestrator` in the
main conversation does not switch the main session's model or reasoning effort.
Keep model choices in host configuration, separate from canonical skills. The fields
are documented in the [official Codex subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents).

The available launch tool varies across Codex hosts. Use registered roles if the actual
tool supports them. Otherwise read the installed TOML and apply its instructions and
configured model/reasoning through supported spawn parameters, following
[`runtime.md`](runtime.md). Do not assume a particular `agent_type` argument exists or
that merely reading a TOML configures a child. If a requested option cannot be honored,
report the mismatch and resolve it before launching; do not silently substitute the
parent model. Independent review and QA still require separate agents.
