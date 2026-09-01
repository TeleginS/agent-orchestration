# Launcher: code-reviewer — Step 4, and the review gate in Step 6

**Launch:** subagent, foreground. Fetch the base branch first so the diff is against a
fresh base.

**Prompt = 3 parts:**

1. The shim (see [`../orchestrator-runbook.md`](../orchestrator-runbook.md)), role name
   `code-reviewer`.
2. The full contents of `agents/code-reviewer.md`.
3. Step context:
   - The PR number and URL
   - The user's task text, verbatim
   - The issue numbers, for acceptance criteria
   - The active profile path
   - The current iteration number
   - **Step 6 only:** the bug issue numbers and the developer's fix summary, with the
     scope narrowed to the QA fixes and directly affected code

**Expect back:** either the `Code Review — Iteration N` block with findings grouped
🔴 / 🟠 / 🟡 / 🟢, or an explicit `✅ APPROVAL` with a summary of what was verified.

**In a real run the reviewer must also leave its findings on the PR**, not only report
them to you. A finding that exists only in your conversation is invisible to everyone
who later reads the PR.

**Transition criterion:**
- Blocking findings → back to the developer launcher with the complete list
- `✅ APPROVAL` → Step 5, or in Step 6, the QA re-test

**Guardrail:** third iteration still blocked → STOP and escalate to the user with the
full finding list. Do not start a fourth.
