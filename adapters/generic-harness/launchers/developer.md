# Launcher: developer — Step 3, and the fix passes in Steps 4 and 6

**Launch:** subagent, foreground.

**Prompt = 3 parts:**

1. The shim (see [`../orchestrator-runbook.md`](../orchestrator-runbook.md)), role name
   `developer`.
2. The full contents of `agents/developer.md`.
3. Step context — the common part:
   - The user's task text, verbatim
   - The issue numbers and URLs, to be read from the tracker rather than guessed
   - The branch name, with an explicit "work only on this branch, not the base branch"
   - The active profile path
   - Plus the mode below

**Modes:**

| Mode | Extra context | Instruction |
|---|---|---|
| Initial implementation (Step 3) | — | Open a PR against the base branch; return its number and URL |
| Review fix pass (Step 4) | The reviewer's complete finding list, the PR number | Push to the same branch; do **not** open a new PR |
| QA bug fix pass (Step 6) | The bug issue numbers, the PR number | Push to the same branch; do **not** close the issues — comment `Fixed in PR #NN; verified after merge before closing.` on each |

**Expect back:** the changed files, the mechanism of the change, the build and test
result, any assumptions worth verifying, any profile drift found, and the PR number on
the initial pass.

**Transition criterion:** changes are pushed to the branch, and on Step 3 the PR exists.

A fix pass that reports "addressed" without saying which findings it addressed is not a
result — relaunch it asking for the mapping.
