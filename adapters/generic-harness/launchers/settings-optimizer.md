# Launcher: settings-optimizer — Step 9 (optional)

Only if the active profile names a local permission config for this harness. Most
generic harnesses have none — in that case skip the step and say so in the final report.

**Launch:** subagent, foreground. Standalone: no task context needed.

**Prompt = 2 parts:**

1. The shim (see [`../orchestrator-runbook.md`](../orchestrator-runbook.md)), role name
   `settings-optimizer`.
2. The full contents of `agents/settings-optimizer.md`, plus the active profile path —
   it carries the settings file location and the command prefixes any generalized
   pattern must preserve.

**Expect back:** what was removed and why ("covered by pattern X" / "session junk"),
what was generalized (old entries → new pattern), and what was left untouched. The agent
does not run git itself.

**Orchestrator actions afterward:**

- Changes made → confirm you are on the PR branch; check whether the settings file is
  tracked by git; if tracked, commit and push it to the PR; if untracked or ignored,
  leave the local edit and note it in the final report.
- No changes → note that in the final report.

In dry-run mode this is audit-only: the agent reports what it *would* change and edits
nothing.
