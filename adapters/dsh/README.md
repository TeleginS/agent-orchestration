# Adapter: DeepSeek Harness

DeepSeek Harness (DSH) discovers canonical skills from `.dsh/skills/` and
`.agents/skills/` under the project root, and from `$DSH_HOME/skills/` and
`$DSH_AGENTS_HOME/skills/` (default `~/.agents/skills/`) for the user. It follows
directory symlinks, so a link to a canonical skill directory is a complete install.

The pipeline stage launchers are **not adapted yet**: DSH has no launcher format
here for forked stage agents. This adapter therefore covers only the standalone
`save-session-log` utility. Load the canonical orchestrator skill manually for the
main conversation until stage launching is defined.

## Manual session logs

`save-session-log` is a utility, not a role, and DSH needs no wrapper: the skill
runs the converter from its own physical directory and the converter reads
`DSH_SESSION_ID` and `$DSH_HOME` from the environment. Link the canonical skill,
preserving an existing entry with the same name:

```bash
# Project scope: DSH sessions rooted at this project see the skill.
if [ -e .agents/skills/save-session-log ] || [ -L .agents/skills/save-session-log ]; then
  printf '%s\n' 'Preserving existing skill: save-session-log'
else
  mkdir -p .agents/skills
  ln -s ../../agent-orchestration/skills/save-session-log .agents/skills/save-session-log
fi
```

For every project on the machine, link the same directory into `$DSH_HOME/skills/`
(default `~/.dsh/skills/`) instead; the converter then takes the project root from
the session's working directory. Keep the target an absolute path or a path to the
vendored library that survives the shell's current directory.

DSH reads `disable-model-invocation` from skill frontmatter, but the canonical skill
keeps host-neutral frontmatter, so on DSH the skill stays model-invocable. Only its
description restricts it: it must not run until the user asks for a session log. It
reads `$DSH_HOME/sessions/<encoded project path>/<session id>/session[.vN].jsonl[.zstd]`,
writes `docs/ai-logs/` by default, and the pipeline never launches it.

A DSH transcript is zstd-compressed by default; the converter needs Python 3.14+,
the `zstandard` module, or the `zstd` CLI. Reasoning, system and developer messages,
injected runtime context, request headers, and teammate/subagent traffic are left
out of the log.
