# Output Contracts

The orchestrator parses subagent output **by shape**. It holds the only complete picture
of a run, and it reconstructs that picture from what each role hands back — issue numbers,
a PR number, a literal verdict string, two separated bug lists. A role that reports its
work in prose the orchestrator cannot parse has not finished its step.

This is the index of those contracts. Each links to a real instance in
[`../run-cumulative-stats/`](../run-cumulative-stats/) rather than restating it — the same
anti-duplication rule the adapters follow. A second copy of a contract is a copy that
drifts.

| Role | Step | Must return | Consumed by | Example |
|---|---|---|---|---|
| `task-planner` | 1 | Epic number + URL, every child number + URL | Steps 3, 5, 8 | [01](../run-cumulative-stats/01-epic.md), [02](../run-cumulative-stats/02-child-issues.md) |
| `developer` | 3 | Changed files, mechanism, build/test result, **PR number** | Steps 4, 5 | [03](../run-cumulative-stats/03-pull-request.md) |
| `developer` | 4, 6 | Findings addressed (mapped), pushed to same branch, no new PR | Steps 4, 6 | [06a](../run-cumulative-stats/06-fix-and-retest.md) |
| `code-reviewer` | 4, 6 | `Code Review — Iteration N` with 🔴/🟠/🟡/🟢 groups, **or** literal `✅ APPROVAL` | Loop control | [04](../run-cumulative-stats/04-code-review.md), [06b](../run-cumulative-stats/06-fix-and-retest.md) |
| `qa-tester` | 5, 6 | Two separated lists (in-scope / pre-existing) with issue numbers, **test suite result**, explicit verdict | Step 6 scope split, Step 8 | [05](../run-cumulative-stats/05-qa-bug.md), [06c](../run-cumulative-stats/06-fix-and-retest.md) |
| `settings-optimizer` | 9 | Removed (with reason) / generalized (old → new) / kept | Step 9 commit decision | [07](../run-cumulative-stats/07-final-report.md) |
| `orchestrator` | 10 | The Step 10 checklist | The user | [07](../run-cumulative-stats/07-final-report.md) |

## The four that carry weight

**The verdict string.** `✅ APPROVAL` gates Step 5 and the re-test in Step 6. It is matched
literally. On most setups the reviewer cannot formally approve on the platform — every
agent shares one account, and self-approval is blocked — so the orchestrator gates on this
string, never on the platform's review state. See
[`../../conventions/issue-tracker.md`](../../conventions/issue-tracker.md#the-self-approval-constraint).

**The iteration number.** The orchestrator caps both loops at 3. It cannot count what the
reviewer does not report. A review block without `Iteration N` breaks the guardrail
silently, which is the worst way for a guardrail to break.

**The two QA lists.** The in-scope / pre-existing split decides what blocks the run (Step
6) and what must stay open (Step 8). One merged list of bugs makes both decisions
impossible, and the natural failure is to treat unrelated debt as a blocker — or to close
it as fixed.

**The QA test result.** A verdict with no suite result is incomplete; the orchestrator
relaunches rather than accepting it. Without this, "green" degrades into "I read the code
and it looked fine", which is the reviewer's job and was already done.

## Reading a contract violation

The failure mode is not an error — it is a plausible-looking report the orchestrator
quietly misreads:

| Symptom | Likely cause |
|---|---|
| Loop runs past 3 | Reviewer omitted the iteration number |
| Unrelated debt blocks a finished PR | QA merged its two lists |
| Issues closed on an unmerged PR | Developer closed bug issues instead of commenting |
| Step 5 never starts | Reviewer described approval instead of emitting the literal string |
| A second PR appears mid-run | Fix pass was launched without "do not open a new PR" |

Every one of these is a prompt problem, not a model problem. If you change a role's report
format, check this table first.
