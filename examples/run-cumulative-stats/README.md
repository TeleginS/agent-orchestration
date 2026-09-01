# A complete run: cumulative statistics

One task through all eleven steps, including the bug-fix loop. Every artifact except the
final report is an anonymized copy of something the pipeline actually produced on a real
project — real issue bodies, a real PR description, the real review comment, the real bug
report.

The domain has been remapped onto the [Habitat example profile](../../profiles/example-mobile-app.md)
so the run and the profile match. The structure, the reasoning and the defect are
unchanged.

## Read in order

| | Step | Artifact |
|---|---|---|
| [01](01-epic.md) | 1 | Epic issue #136 — locked domain model, dependency graph, risks |
| [02](02-child-issues.md) | 1 | Child issues #137–#142 — acceptance criteria |
| [03](03-pull-request.md) | 3 | PR #143 — implementation summary and test plan |
| [04](04-code-review.md) | 4 | Code review, iteration 1 — approved |
| [05](05-qa-bug.md) | 5 | QA finds bug #144 |
| [06](06-fix-and-retest.md) | 6 | Fix → re-review → re-test |
| [07](07-final-report.md) | 10 | Final report *(reconstructed — see the note in the file)* |

Steps 2, 7, 8 and 9 are orchestrator housekeeping — branch creation, artifact review,
issue cleanup, settings — and are summarized in the final report rather than given their
own files.

## The thing to actually look at

The epic's risk section named time double-counting as the top hazard and assigned it to
QA. The developer implemented against an acceptance criterion that said, in as many words,
*"no double counting of time on normal completion or on exit."* The reviewer verified every
terminal path and proved a true statement: no terminal path calls another, so within one
completion sequence, time is added exactly once. It approved.

QA then found time being double-counted.

Nobody was careless. The reviewer's claim was correct and remains correct. The defect is
that `exitSession()` can be entered *again*, from the UI, after a terminal path has
already run — because the countdown keeps running behind a modal confirmation dialog. That
is invisible in a diff. Seeing it requires treating the timer and the dialog as concurrent
actors and asking what happens if both fire.

**A reviewer reads the change. QA runs the program and asks what else can happen.** They
are different questions, and merging the two steps — the obvious efficiency — is what
removes the one that catches this class of bug.

Two smaller things worth noticing:

**Specificity is what made it findable.** "No double counting of time on normal completion
or on exit" is a testable claim. "Statistics should be accurate" would have been checked
on the happy path and waved through. The planner's precision three steps earlier is what
gave QA somewhere to push.

**QA found the old guard.** The report does not say "time is sometimes double-counted." It
finds the pre-existing `naturalCompletionLogged` flag, notes that it exists to stop exactly
this re-entrancy for analytics, and shows the new code was added outside it. That is what
turns a symptom into a root cause and makes the fix a one-line change instead of an
investigation.

## What this run does not show

It converged fast: one review iteration, one bug, one fix pass, done. That is the common
case — see the [calibration data](../README.md#what-actually-happens-across-20-runs) for
how often the loops fire at all, and for a run that ended without shipping anything.
