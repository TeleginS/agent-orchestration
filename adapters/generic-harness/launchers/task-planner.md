# Launcher: task-planner — Step 1

**Launch:** subagent, foreground. Pipeline steps are sequential.

**Prompt = 3 parts:**

1. The shim (see [`../orchestrator-runbook.md`](../orchestrator-runbook.md)), role name
   `task-planner`.
2. The full contents of `agents/task-planner.md`.
3. Step context:
   - The user's task text, verbatim — not your paraphrase
   - The Step 0 design artifact paths, or an explicit "no design artifacts applied"
   - The active profile path
   - Repository root and tracker remote

**Expect back:** the epic/overview issue (number + URL) and every child issue
(number + URL), labelled `epic:<name>`, `size:*`, and `blocked` where a dependency is
unmet. For an atomic task, one issue with no epic. If the tracker is unavailable, the
full structure as markdown instead.

**Transition criterion:** the numbers and URLs of the overview and all child issues are
collected. You need them for Steps 3, 5 and 8 — nothing else is holding them.
