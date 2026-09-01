# Adapter: Codex

Codex registers agents from `.codex/agents/*.toml`. Each file carries the name, the
delegation description, and `developer_instructions` as the prompt body.

Like the other adapters, these are thin: `developer_instructions` points at the
canonical role prompt in `agent-orchestration/agents/` rather than copying it.

## Install

```bash
cp -r agent-orchestration/adapters/codex/. .codex/
```

Then create your profile:

```bash
cp agent-orchestration/profiles/_template.md agent-orchestration/profiles/active.md
```

Edit `.codex/environments/environment.toml` to name your project and add any setup
script the agents need before running commands.

If you vendored this repository somewhere other than `<project-root>/agent-orchestration/`,
update the paths inside the copied `.toml` files.

## What this harness provides

| Pipeline assumption | Codex |
|---|---|
| Subagent launching | By registered name |
| Persistent agent memory | Not provided — see `agent-orchestration/memory/README.md` for the file-based fallback |
| Local permission config | None → **Step 9 does not apply**, skip it |
| Loop guardrails | Not enforced — the orchestrator counts them |

Only five roles are registered here. `settings-optimizer` is deliberately absent: it
exists to consolidate a harness-local permission allowlist, and this harness has none.

## A word of warning

Maintaining a third registration format for the same six roles is real overhead, and the
source this pipeline was extracted from had exactly the problem you'd expect: the TOML
copies drifted from the markdown ones, and a rule that existed in one was missing from
the other for months.

Keeping the bodies as pointers is what prevents that here. Do not "inline the prompt for
convenience" — that is the failure mode this adapter shape exists to avoid. If you don't
actually run the pipeline on Codex, delete this directory.
