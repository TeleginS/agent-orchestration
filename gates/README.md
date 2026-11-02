# Human gates

The pipeline runs without a human between three decision points, and those three
belong to the owner:

1. **Accepting a design decision**: the clarified requirements or ADR that Step 0
   records before planning.
2. **Merging a PR** into a protected branch.
3. **Publishing a release**: an app-store upload, a package publish, a production deploy.

Skills are advisory. A prompt that says "never merge" holds until a model decides a
merge is the helpful next step, or a stage misreads its assignment. Anything that must
hold is backed by something deterministic: a hook, a server-side branch rule, or the
project's verification command. The first gate is a conversation and needs no script.
The other two are enforced by the scripts here.

## What is enforced

| Script | Blocks | Lets through |
|---|---|---|
| [`git/pre-push`](git/pre-push) (any tool) | Pushes to protected branches; non-fast-forward pushes to any branch | Feature-branch pushes, new branches, branch deletion, a fast-forward to a protected branch that the project's allow script accepts |
| [`merge-gate.py`](hooks/merge-gate.py) (Claude Code / local Codex) | `gh pr merge`, `gh api .../pulls/<n>/merge` and the GraphQL merge mutations, `gh alias set`, a push to a protected branch (refspec, `HEAD`, bare `git push` while on it, `...:<branch>` anywhere in a pushing command, through a configured git alias), `--force*`, `-f` in any option cluster, `+refspec`, `--mirror`, `--all`, deleting a protected branch, `git push --no-verify`, changes to `core.hooksPath`, `alias.*`, `agent-gates.allowBasePush` or `agent-gates.protectedBranch` (`-c`, `git config`, `GIT_CONFIG_*`), a push or `gh pr`/`gh api` fed by `xargs` | Feature-branch pushes, `gh pr create/view`, `git config --get`, a fast-forward that `allow_base_push` accepts |
| [`release-gate.py`](hooks/release-gate.py) (Claude Code / local Codex) | Every command that matches a `release_commands` rule, also behind `xcrun`, `bundle exec`, `npx`, `pnpm/yarn exec`, `uvx`, `uv run`, `pipx run`, `poetry run`, with a version suffix (`npm@latest`), or fed by `xargs` (then the command name alone decides) | Everything else. With no rules configured, it blocks nothing |
| [`secrets-gate.py`](hooks/secrets-gate.py) (Claude Code / local Codex) | Read/Edit/Write/Grep and `apply_patch` (add/update/delete/move) of configured secret files or children of configured directories, and Bash commands that open or overwrite them (`cat`, `source`, redirections, `cp`, `grep ... file`, `git diff/log/show` with secret paths, globs like `.env*` or `*.p8`, brace expansions like `.{env,}`), ignoring letter case | `secret_allow` names outside protected directories, `ls`/`stat`/`test` without protected redirections, metadata-only git pathspecs, the grep pattern argument, globs with no literal part (`*`) |

Protected branches default to `main` and `master`. Every block exits 2 with a message
that names the owner as the route to approval. A block is the gate working; an agent
reports it rather than looking for a way around it.

**Allowed base pushes.** Some release flows commit straight to the base branch, such
as a version bump made by an owner-invoked release tool. Point `allow_base_push` (tool hook)
and `agent-gates.allowBasePush` (pre-push) at one project script. It receives
`<remote_sha> <local_sha> <branch>` for a fast-forward and exits 0 to allow it; any other
exit, including a usage error from a script that expects a different argument count,
rejects the push. Wrap an existing checker rather than editing its contract. Keep it
strict: compare `git diff --raw --no-renames` against an allowlist of paths and
lines, and reject renames, deletions, symlinks and mode changes, because each of them can hide a
code change inside a "version-only" range.

## Install in a project

The Python engine and its self-test live in [`hooks/`](hooks/); [`tests/`](tests/)
exercises the published host wiring against installed copies
(`python3 -m unittest discover -s gates/tests`). Both hosts install the same scripts;
the host-specific files only wire up events. Python 3 and git are
required. Run these examples from the adopting project root. Inspect existing hooks,
symlinks and custom configuration before copying; merge updates rather than replacing
unrelated hooks or an existing `gates.json`.

### Claude Code

```bash
mkdir -p .claude/hooks
cp agent-orchestration/gates/hooks/*.py .claude/hooks/
if [ ! -e .claude/hooks/gates.json ] && [ ! -L .claude/hooks/gates.json ]; then
  cp agent-orchestration/gates/hooks/gates.example.json .claude/hooks/gates.json
fi
python3 .claude/hooks/selftest.py
```

After the self-test passes, merge the `hooks` block from
[`settings.example.json`](../adapters/claude-code/hooks/settings.example.json) into the
tracked `.claude/settings.json`. Existing settings commands still use the same hook
filenames. When upgrading, replace the old Python implementation with the shared
scripts above; keep project-specific rules. The old library entry points under
`adapters/claude-code/hooks/` are compatibility launchers for use inside the library,
not scripts to copy into another project.

### Local Codex

```bash
mkdir -p .codex/hooks
cp agent-orchestration/gates/hooks/*.py .codex/hooks/
if [ ! -e .codex/hooks/gates.json ] && [ ! -L .codex/hooks/gates.json ]; then
  cp agent-orchestration/gates/hooks/gates.example.json .codex/hooks/gates.json
fi
python3 .codex/hooks/selftest.py
```

After the self-test passes, merge
[`hooks.example.json`](../adapters/codex/hooks.example.json) into the tracked
`.codex/hooks.json`, or translate its event groups into the existing inline `[hooks]`
configuration in `.codex/config.toml`. Use one representation per layer to avoid
running a gate twice. The example locates the scripts from the git project root;
for another layout or a non-git working directory use explicit absolute paths.

In the Codex CLI, the owner reviews and trusts the project and hook definitions via
`/hooks`. New or changed untrusted hooks are skipped; an installed file does not mean
an active gate. Check that `features.hooks` has not been disabled by local or managed
configuration. Confirm the hooks are loaded and trusted in the actual host, including
when delegating. Codex normalizes shell/`exec_command` calls to `Bash`, and supplies
patches as `apply_patch` with `tool_input.command`. A denial exits 2 and prints its
reason to stderr. See the [official Codex hooks documentation](https://learn.chatgpt.com/docs/hooks).

These command hooks require local orchestration and execution. Cloud orchestration
needs supported managed controls; do not claim local command hooks protect it. Report
the actual coverage and any gaps in the profile's **Enforcement installed** field.

### Configuration and git protection (both hosts)

Edit the installed `gates.json`: protected branches, secret names, release commands,
and optional allow script. Keys are documented in [`config.py`](hooks/config.py).
The shared engine reads `AGENT_GATES_CONFIG` if set, otherwise `gates.json` beside
its scripts; it does not depend on a Claude environment variable. A missing config
uses defaults, including **no release rules**. A malformed config warns and uses those
same defaults at runtime; the self-test rejects it. Configure every publishing command
from the active profile before treating the release gate as installed.

Run `selftest.py` before wiring hooks and after changing scripts or configuration.
A broken hook can block later tool calls. Its git tests use throwaway bare remotes
that are removed afterwards; they never push to a real origin. Installed outside the
library, set `AGENT_GATES_PREPUSH` to the absolute pre-push script path to include
those tests. The self-test warns when no `gates.json` exists beside the scripts.

Copy [`git/pre-push`](git/pre-push) into a tracked directory such as `.githooks/`,
preserving any existing pre-push logic. The owner activates it once per clone:
`git config core.hooksPath .githooks`. Set `agent-gates.protectedBranch` (repeatable)
and `agent-gates.allowBasePush` there if needed. Keep the protected branch list and
allow script consistent with `gates.json`. Ensure the hook is executable. Run that
`git config` yourself, not through an agent: `merge-gate.py` blocks every change to
`core.hooksPath`, including this one, so that an agent cannot undo it later.

Where the hosting plan allows it, add a server-side branch rule: PR required, no force
push, no deletion. This alone does not reserve merging for the owner when an agent
uses the owner's credentials. Use server-side identity/access controls where available;
local hooks provide an additional command guard. Release and secrets protection also
require their own hooks or host controls; neither comes from `pre-push`.

## Known gaps

- **Indirection.** The tool hooks parse command text. `G=git; $G push origin main`,
  a push inside a script file, `python -c "os.system(...)"` or `find -exec` is not
  seen as a push. The raw `:<branch>` count catches some forms, and a `--no-verify`
  or `core.hooksPath` token under an unresolved head is blocked outright, so
  `pre-push` stays active and sees the actual push for protected branches and force
  pushes. The release and secrets gates have no second layer behind them.
- **Server-side merges.** `gh pr merge` from an unhooked tool, a direct MCP merge, a
  GraphQL mutation read from a file (`-f query=@file`, `--input`), or the web UI is
  outside these command parsers. Server-side identity/access controls are needed to
  reserve merging for the owner; a PR-required rule alone does not do that.
- **Local refs.** `merge-gate.py` checks an allowed base push against the local
  remote-tracking ref, which an agent can rewrite. `pre-push` compares against the
  real remote sha.
- **The hook file itself.** An agent with write access to the tracked hooks directory
  can edit `pre-push`. Add the directory name (for example `.githooks`) to
  `secret_names` to close its children, and keep the server-side branch rule as the
  backstop. A matching parent directory takes priority over a leaf `secret_allow` name.
- **Release commands are a list.** The release gate blocks only what `release_commands`
  names. `python -m twine upload` or a custom deploy script needs its own rule, or a
  project-specific hook. `gh` aliases defined before the session are not resolved; the
  gate blocks defining new ones.
- **Tool coverage.** The examples guard shell commands and known file tools. They do not
  inspect arbitrary MCP API calls, script contents, recursive reads (`grep -r KEY .`,
  `ls -a | xargs cat`, Grep over a directory), filesystem aliases or interactive input
  sent through `write_stdin`. Extend the host's policies for those paths; these parsers
  are not a complete sandbox boundary.

## Command wrappers

Do not depend on hook ordering or another hook's rewrite: Codex runs matching command
hooks concurrently. The parsers accept both plain commands and wrappers such as
`rtk git push`. `lib.py` strips `rtk`, `env`, `sudo`, `time`, `nice`, `timeout`,
`nohup`, `command`, `xargs` and similar prefixes together with their options and
option values (`sudo -u root`, `timeout 30`), plus variable assignments, before
matching. It also expands `bash -c "..."`, `eval`, `env -S "..."`, here-strings,
`echo "..." | sh` and heredocs piped into a shell, and ignores other heredoc bodies.
A command behind `xargs` is marked as receiving arguments from stdin; the merge and
release gates treat such a command conservatively. When you add a wrapper to the
environment, add it to `WRAPPERS` in `lib.py` with its value-taking options and add a
self-test case.
