# The Pipeline

The canonical delivery pipeline. Everything else in this repository is derived from
this file: the role prompts implement their slice of it, the harness adapters just
change how a step is launched.

One task in, one reviewed and QA'd pull request out. Eleven steps, two loops, and a
small set of rules that keep the loops from running forever or lying about their
results.

## Roles

| Role | Owns | Never does |
|---|---|---|
| `orchestrator` | Sequencing, git branch/commit hygiene, issue cleanup, the final report | Writes code. Decomposes tasks. Reviews. |
| `task-planner` | Decomposing the task into tracker issues with acceptance criteria | Implements anything |
| `developer` | Implementation, fix passes, opening the PR | Reviews its own work. Closes unmerged issues. |
| `code-reviewer` | Reviewing the diff, blocking or approving | Fixes the code it reviews |
| `qa-tester` | Verifying acceptance criteria, running the test suite, filing bug issues | Fixes bugs |
| `settings-optimizer` | Consolidating the harness's local permission config | Touches app code or git state |

The orchestrator is a pure coordinator. Its power is that it holds the only complete
picture; its discipline is that it never uses that picture to shortcut a step.

## Profile resolution

Every role is stack-neutral. Before Step 0 the orchestrator resolves the **active
profile** and passes its path into every single subagent launch. Resolution order:

1. A profile path given explicitly by the user or the launching context.
2. `profiles/active.md`.
3. The only file in `profiles/` that is not `README.md` or `_template.md`.

If none resolves, STOP and ask. A pipeline run without a profile will produce
plausible-looking work against invented conventions.

**Precedence, always:** observed code > active profile > role prompt. Profiles drift;
the repository does not. When a role finds the profile contradicting the code, it
follows the code and flags the drift in its report.

---

## Step 0 — Design artifact check

Before planning, establish whether the task is grounded in durable design artifacts:
the domain glossary and any decision records covering this area (see
`conventions/domain-docs.md` for where those live).

**Why this gate exists:** substantial product changes should start from decisions that
were deliberately sharpened, not from a raw idea. The design docs give the rest of the
pipeline a source of truth to converge on. Without them, four agents will each invent
a slightly different version of the feature and the disagreement will surface as QA
bugs.

The orchestrator **cannot** run that clarification itself — it is an interactive,
user-driven conversation that happens before the orchestrator is launched.

| Situation | Action |
|---|---|
| Artifacts exist and cover the task | Treat as source of truth, pass paths to every subagent, go to Step 1 |
| Artifacts missing, task is small/operational (bug fix, build fix, test update, copy tweak, tooling chore, an already-specific request) | Go to Step 1, note explicitly that no design artifacts applied |
| Artifacts missing and the task needs product/design decisions | **STOP.** Return to the user asking for a design pass first. Never fabricate the design. |

This is the only planned stop before development starts.

## Step 1 — Planning

Launch `task-planner` with the full task text plus the Step 0 artifact paths (or an
explicit "no design artifacts applied").

**Expected output:** an Epic/Overview issue plus one child issue per subtask, each with
acceptance criteria, dependencies and a size label. For an atomic task, a single issue
with no epic is correct.

**Transition criterion:** the numbers and URLs of the overview issue and every child
issue are collected.

## Step 2 — Branch creation

The orchestrator does this itself. It is a git operation, not implementation.

1. Check the tree first: `git status --porcelain`. If tracked files were modified by a
   parallel session, do **not** force anything — report and resolve explicitly with the
   user. Never carry unrelated changes into the feature branch.
2. `git checkout <base> && git pull origin <base>`, where `<base>` is the **Base
   branch** declared in the active profile — never assumed. If the pull fails on local
   modifications, STOP and report rather than resolving silently.
3. Derive a branch name from the task: `feature/<short-name>` for new functionality,
   `fix/<short-name>` for bug fixes.
4. `git checkout -b <branch> && git push -u origin <branch>`. Pushing a branch with no
   unique commits is fine — it points at the base commit until the developer pushes.

**Transition criterion:** the branch exists on the remote.

## Step 3 — Development

Launch `developer` with: the original task text, the issue URLs, the branch name (work
**only** on it), an instruction to read each issue from the tracker rather than
guessing, and an instruction to open a PR when the implementation is done.

**Transition criterion:** the PR exists and its number is collected.

## Step 4 — Review loop

Fetch the base branch first so the diff is computed against a fresh base.

Launch `code-reviewer` with the PR number, the original task, and the issue URLs for
acceptance criteria. The reviewer reads the actual diff, not a summary of it, and
**leaves its findings on the PR** rather than only returning them to the orchestrator.

```
  ┌─ CRITICAL / ARCHITECTURAL / BUG found
  │     → developer fix pass (same branch, no new PR)
  │     → re-review
  └─ back to the top, until APPROVAL
```

- Blocking findings → orchestrator relaunches `developer` with the complete finding
  list, the PR number, and an explicit "do not open a new PR".
- Quality-only findings → send the significant ones back; note the trivial ones and
  conditionally approve.
- Clean → **APPROVAL**, go to Step 5.

**Guardrail:** at most 3 iterations. Still blocked after the third → STOP and escalate
to the user with the full finding list. A loop that cannot converge in three passes has
a problem the loop itself cannot fix.

## Step 5 — QA

Launch `qa-tester` with the original task, the issue URLs (for acceptance criteria),
the developer's implementation summary, and the PR number.

QA verifies every acceptance criterion, hunts for bugs by its own methodology, and
files a tracker issue for **every** bug found — including ones it will not fix.

**Mandatory gate:** QA runs the project's test suite (command in the active profile)
before reaching any verdict. Failures or skips become bug issues. The suite is re-run
after every fix pass.

## Step 6 — Bug-fix loop

Split findings by scope first:

- **In-scope** — introduced by, or directly related to, this PR's changes. These enter
  the loop.
- **Pre-existing** — present before this task started. Still filed as issues, labelled
  `pre-existing`, but they do **not** block this pipeline and do not enter the loop.
  They go into the final report and await a separate task.

For in-scope bugs, in strict order:

1. `developer` gets the bug issue numbers and the PR number, pushes to the same branch,
   and does **not** close the issues — the PR is unmerged. It comments on each instead.
2. The fixes go through `code-reviewer` — review scoped to the QA fixes and directly
   affected code. Blockers send it back to 1.
3. Only after APPROVAL does `qa-tester` re-test, re-running the test suite.

Loop until: all in-scope bugs are fixed in the PR, no new in-scope bugs are opened, and
every fixed issue carries a PR reference comment while staying open.

**Guardrail:** at most 3 iterations, then STOP and escalate.

## Step 7 — Stray artifact review

QA is green. Check what accumulated in the working tree that nobody committed.

Legitimately expected: design documents produced for this feature, and agent memory
updates (see `memory/README.md`) — both are durable records that belong with the PR.

1. `git status --porcelain` to see exactly what is uncommitted.
2. **Read the list.** Stage only intended, durable paths. Never `git add .` — scratch
   files, build output, secrets, large binaries and unrelated edits do not go in.
3. Confirm you are on the PR branch, not the base branch.
4. If uncertain about a path, leave it uncommitted and list it in the final report for
   the user to decide.

## Step 8 — Issue cleanup

Leave the tracker accurate without marking unmerged work as done.

Comment on every issue this pipeline created — the epic, the children, and the resolved
in-scope bugs — referencing the PR: `Implemented in PR #NN; close after merge.`

**Close an issue only when** the orchestrator has been explicitly told the PR merged,
or the task involved no PR and the work is already on the target branch.

**Never close:**
- Issues created as deliberate follow-up or backlog — work this task intentionally did
  not do.
- Issues labelled `pre-existing`.

Unsure whether an open issue is "ours, now done" or "deliberate future backlog"? Do not
close it. List it in the final report. Closing the wrong issue erases a tracked task.

Verify with a tracker query and report which issues were closed and which were left
open on purpose, with the reason.

## Step 9 — Settings housekeeping (optional)

Only meaningful on harnesses that accumulate a local permission allowlist. Skip it
where the profile says the harness has none.

Launch `settings-optimizer` — it needs no task context. It only ever edits the settings
file and never runs git itself. If it changed something: confirm you are on the PR
branch, check whether the file is tracked, and if so commit and push it to the PR. If
untracked or ignored, leave the local edit and note it in the report.

## Step 10 — Final report

- What was implemented, and the PR number/URL
- Review status
- QA status, including the test suite result
- Artifact commit summary — what was committed, what was deliberately left and why
- Issue cleanup summary — closed, and left open on purpose with the reason
- Settings housekeeping result, if Step 9 ran
- Known limitations and follow-up recommendations
- Any profile drift the roles reported

---

## Strict rules

1. The orchestrator **never** writes code. Not one line.
2. The orchestrator **never** decomposes a task itself.
3. QA is never skipped.
4. Planning is never skipped, however small the task.
5. Every subagent gets full context, including the active profile path.
6. Announce every launch before it happens, and summarize its result after.
7. A subagent that fails or answers vaguely gets relaunched with clarification — the
   orchestrator never fills the gap itself.
8. Unmerged work is not closed (Step 8). Never close deliberate backlog or
   `pre-existing` issues.
9. Never blanket-commit artifacts (Step 7).
10. Design artifacts are used when they exist and required only for ambiguous
    product/design work.
11. **Every code change made after QA begins must pass review before QA can be called
    green.** QA bug fixes are code, and unreviewed code is how a green QA run ships a
    regression.
12. Loops are capped at 3 iterations, then escalate.

## Dry-run mode

The same pipeline with no writes to the tracker or remote. Useful for evaluating the
pipeline on a new project before pointing it at a real repository.

| Step | Dry-run behaviour |
|---|---|
| 1 | Planner returns the plan as markdown instead of creating issues; save it under `run-plans/<slug>.md` |
| 2 | Local branch only, no push |
| 3 | Implementation on the local branch, no PR; report is the file list plus summary |
| 4 | Review of the local diff against the base branch; identical report format |
| 5 | Bugs as a markdown list split in-scope / pre-existing, instead of issues |
| 6 | Fix loop stays local; issue closure becomes a checklist in the run plan |
| 7 | Artifacts listed, not committed |
| 8 | Skipped — no issues exist |
| 9 | Audit only: report what *would* change, without editing the file |
| 10 | Final report plus an offer to re-run for real |

The mode is fixed at launch and recorded on the first line of the run plan.
