# Adapter: Claude Code

`/orchestrator` runs in the main conversation. The five stage wrappers run their
canonical skills in separate subagents using `context: fork`, `agent: general-purpose`
and `background: false`. Each wrapper forwards `$ARGUMENTS` and loads the shared skill
plus [`runtime.md`](runtime.md); the workflow stays in the library.

## Install

Complete the [shared installation](../README.md#shared-installation) first. For a new
installation, run the following from the adopting project root only after confirming
`.claude/skills` is a real directory or absent:

```bash
if [ -L .claude/skills ]; then
  printf '%s\n' 'Existing .claude/skills symlink: follow the migration instructions first.'
else
  mkdir -p .claude/skills
  for role in orchestrator task-planner developer code-reviewer qa-tester settings-optimizer; do
    if [ -e ".claude/skills/$role" ] || [ -L ".claude/skills/$role" ]; then
      printf 'Preserving existing skill: %s\n' "$role"
    else
      cp -R "agent-orchestration/adapters/claude-code/skills/$role" ".claude/skills/$role"
    fi
  done
fi
```

Review any same-name skill that was preserved before using it. Do not replace unrelated
skills. If the library has another location, provide its absolute physical root in the
invocation; wrappers default to `<project-root>/agent-orchestration`.

### Migrate an existing installation

An existing `.claude/skills -> ../.agents/skills` link exposes shared canonical skills.
**Do not copy wrappers through this link**: a role may itself link into the library,
which would overwrite the canonical skill with Claude metadata.

First inventory the existing entries and preserve their resolved targets. Replace only
the top-level `.claude/skills` symlink with a real directory, retaining the old link as
a backup outside skill discovery. Recreate each unrelated entry as a link to its
previous target. For these six pipeline names, preserve any custom content separately,
then install the Claude wrappers as real directories. Inspect per-role symlinks too;
never copy a wrapper into a symlinked role directory. This is a reviewed migration,
not a blanket copy or removal of the skills tree.

After verifying the new commands, retire only the old pipeline files from
`.claude/agents/`: `ai-orchestrator.md`, `task-planner.md`, `developer.md`,
`code-reviewer.md`, `qa-tester.md` and `settings-optimizer.md`. Preserve custom edits
and unrelated agents. Update project instructions that still say to launch
`ai-orchestrator` through the Agent tool. Migrate existing role memory using the
[shared memory guidance](../../memory/README.md).

## Run

```text
/orchestrator Task: <the task>. Active profile: /absolute/project/profile.md
```

The main conversation can resolve product questions with the user before delegating.
It invokes stage skills through the native Skill tool and supplies the complete handoff
defined in `PIPELINE.md`. See [`runtime.md`](runtime.md) for path resolution and launch
behavior. The mode, gates and stop conditions come from the canonical pipeline.

## Models and compatibility

| Skill | Wrapper model |
|---|---|
| `orchestrator` | `opus` |
| `task-planner` | `opus` |
| `developer` | `sonnet` |
| `code-reviewer` | `sonnet` |
| `qa-tester` | `sonnet` |
| `settings-optimizer` | `haiku` |

These preserve the previous adapter defaults. Change model metadata in the installed
Claude wrappers to configure this host; do not change canonical skills. Respect an
explicit user model override through the host's supported controls and report an
unsupported selection before launching.

Claude documents `background: false` for foreground forked skills in v2.1.218 and
later. Verify command discovery and that a stage runs as a fork when adopting the
adapter; do not assume that reading a wrapper's Markdown applies its frontmatter.
[Claude Code skill documentation](https://code.claude.com/docs/en/skills).
