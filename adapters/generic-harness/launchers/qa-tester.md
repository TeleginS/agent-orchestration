# Launcher: qa-tester — Step 5, and the re-tests in Step 6

**Launch:** subagent, foreground. Only after the reviewer's `✅ APPROVAL` — never
directly after a developer pass.

**Prompt = 3 parts:**

1. The shim (see [`../orchestrator-runbook.md`](../orchestrator-runbook.md)), role name
   `qa-tester`.
2. The full contents of `agents/qa-tester.md`.
3. Step context:
   - The user's task text, verbatim
   - The issue numbers, for acceptance criteria — every checkbox gets verified
   - The developer's implementation or fix summary
   - The PR number
   - The active profile path, which carries the test command
   - The current iteration number

**Expect back:**

- Two separate lists: in-scope bugs (with issue numbers) and pre-existing bugs (with
  issue numbers, labelled `pre-existing`)
- The test suite result
- An explicit verdict: green, or blocked with the in-scope list

**Mandatory gate:** the test suite runs before any verdict, using the profile's command,
after discovering the actual targets or devices rather than assuming. Failures **and**
skips become bug issues first. Re-run after every fix pass.

If a QA report arrives with a verdict and no test result, it is incomplete — relaunch it.

**Transition criterion:**
- Green → Step 7
- In-scope bugs → Step 6 fix loop
- Pre-existing bugs → straight into the final report; they never block this run

**Guardrail:** third iteration still blocked → STOP and escalate.
