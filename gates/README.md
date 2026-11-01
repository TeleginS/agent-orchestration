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
| [`merge-gate.py`](../adapters/claude-code/hooks/merge-gate.py) (Claude Code) | `gh pr merge`, `gh api .../pulls/N/merge`, a push to a protected branch (refspec, `HEAD`, bare `git push` while on it, `...:<branch>` anywhere in a pushing command), `--force*`, `-f`, `+refspec`, `--mirror`, `--all`, deleting a protected branch | Feature-branch pushes, `gh pr create/view`, a fast-forward that `allow_base_push` accepts |
| [`release-gate.py`](../adapters/claude-code/hooks/release-gate.py) (Claude Code) | Every command that matches a `release_commands` rule, also behind `xcrun`, `bundle exec`, `npx` | Everything else. With no rules configured, it blocks nothing |
| [`secrets-gate.py`](../adapters/claude-code/hooks/secrets-gate.py) (Claude Code) | Read/Edit/Write of configured secret files, and Bash commands that open them (`cat`, `source`, `<`, `>>`, `cp`, `grep ... file`, globs like `.env*`) | `secret_allow` names, `ls`/`stat`/`test`, `git check-ignore`, the grep pattern argument, git pathspecs after `--` |

Protected branches default to `main` and `master`. Every block exits 2 with a message
that names the owner as the route to approval. A block is the gate working; an agent
reports it rather than looking for a way around it.

**Allowed base pushes.** Some release flows commit straight to the base branch, such
as a version bump made by an owner-invoked release tool. Point `allow_base_push` (Claude hook)
and `agent-gates.allowBasePush` (pre-push) at one project script. It receives
`<remote_sha> <local_sha> <branch>` for a fast-forward and exits 0 to allow it. Keep it
strict: compare `git diff --raw --no-renames` against an allowlist of paths and
lines, and reject renames, deletions, symlinks and mode changes, because each of them can hide a
code change inside a "version-only" range.

## Install in a project

1. Copy the Claude hooks and choose the configuration:

   ```bash
   mkdir -p .claude/hooks
   cp agent-orchestration/adapters/claude-code/hooks/*.py .claude/hooks/
   cp agent-orchestration/adapters/claude-code/hooks/gates.example.json .claude/hooks/gates.json
   ```

   Edit `gates.json`: protected branches, secret names, release commands, optional
   allow script. Keys are documented in [`config.py`](../adapters/claude-code/hooks/config.py).
2. **Run the self-test before wiring anything**: `python3 .claude/hooks/selftest.py`.
   A broken PreToolUse hook blocks every later tool call, including the one that would
   fix it. The self-test also validates `gates.json`; an invalid file falls back to the
   defaults at run time.
3. Merge the `hooks` block from
   [`settings.example.json`](../adapters/claude-code/hooks/settings.example.json) into the
   **tracked** `.claude/settings.json`, so the gates travel with the repository rather
   than one machine's local settings.
4. Copy [`git/pre-push`](git/pre-push) into a tracked directory such as `.githooks/`.
   The owner activates it once per clone: `git config core.hooksPath .githooks`. Set
   `agent-gates.protectedBranch` (repeatable) and `agent-gates.allowBasePush` there if
   the defaults do not fit. Test it against a throwaway bare remote, never the real
   origin; the self-test does this when it finds the script.
5. Where the hosting plan allows it, add a server-side branch rule: PR required, no force
   push, no deletion. Do not require approvals on a single-owner repository, because the
   owner cannot approve their own PR.

Claude Code, Codex and other harnesses are all covered by `pre-push` and the server rule.
Only Claude Code also gets the PreToolUse hooks, which stop a command before it runs and
explain why.

## Known gaps

- **Indirection.** The Claude hooks parse command text. `G=git; $G push origin main`
  or a push inside a script file is not seen as a push. The raw `:<branch>` count
  catches some forms. `pre-push` sees the actual push and closes the gap for
  protected branches and force pushes.
- **Server-side merges.** `gh pr merge` run from a non-Claude tool, or through the web
  UI, is an API call that no local hook sees. Only a server-side branch rule closes it.
- **Local refs.** `merge-gate.py` checks an allowed base push against the local
  remote-tracking ref, which an agent can rewrite. `pre-push` compares against the
  real remote sha.
- **Release commands are a list.** The release gate blocks only what `release_commands`
  names. `python -m twine upload` or a custom deploy script needs its own rule, or a
  project-specific hook.

## Command wrappers

Hooks receive the command after any rewriting by other hooks. A global rewrite such as
RTK turns `git push` into `rtk git push`. `lib.py` strips `rtk`, `env`, `sudo`, `time`,
`nohup`, `command` and similar prefixes, plus variable assignments, before matching. It
also expands `bash -c "..."` and `eval`, and ignores heredoc bodies. When you add a
wrapper to the environment, add it to `WRAPPERS` in `lib.py` and add a self-test case.
