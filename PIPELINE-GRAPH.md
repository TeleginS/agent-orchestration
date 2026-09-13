# Pipeline State Graph

The state machine described in [PIPELINE.md](PIPELINE.md). View it on GitHub or in a
renderer that supports Mermaid's
[`stateDiagram-v2` syntax](https://mermaid.js.org/syntax/stateDiagram.html).

```mermaid
stateDiagram-v2
    [*] --> S0: task from the user

    state "Step 0 — design artifact check" as S0
    state "Clarify decisions with the user in the main conversation" as CLARIFY_DESIGN
    state "Step 1 — task-planner - decompose into tracker issues" as S1
    state "Step 2 — branch from base (dirty-tree guard)" as S2
    state "Step 3 — developer - implement on branch, open PR" as S3
    state "Step 5 — QA - acceptance criteria, test suite, bug issues" as S5
    state "STOP — blockers after 3 review iterations" as STOP_REVIEW
    state "STOP — blockers after 3 QA iterations" as STOP_QA
    state "Step 7 — stray artifact review" as S7
    state "Step 8 — issue cleanup (close only after merge)" as S8
    state "Step 9 — settings-optimizer (optional)" as S9
    state "Step 10 — final report" as S10

    S0 --> S1: artifacts cover it / task is operational
    S0 --> CLARIFY_DESIGN: product decisions required
    CLARIFY_DESIGN --> S0: agreed decisions recorded in design artifacts

    S1 --> S2: complete plan and issue identifiers collected
    S2 --> S3: branch exists on remote
    S3 --> S4: PR created

    state "Step 4 — review loop" as S4 {
        direction LR
        state "code-reviewer - review diff, comment on PR" as R4
        state "developer - fixes on the same branch" as F4
        R4 --> F4: CRITICAL / ARCHITECTURAL / BUG
        F4 --> R4: re-review
    }
    S4 --> STOP_REVIEW: blockers after 3 iterations
    S4 --> S5: APPROVAL

    S5 --> S7: QA green
    S5 --> S6: in-scope bugs found
    S5 --> S7: only verified pre-existing bugs — filed, non-blocking

    state "Step 6 — bug-fix loop" as S6 {
        direction LR
        state "developer - fix bugs (issues stay open)" as F6
        state "code-reviewer - review the QA fixes (rule 11)" as RV6
        state "qa-tester - re-test + re-run the suite" as Q6
        F6 --> RV6
        RV6 --> F6: blockers
        RV6 --> Q6: APPROVAL
        Q6 --> F6: new in-scope bugs
    }
    S6 --> STOP_QA: blockers after 3 iterations
    S6 --> S7: fixed, issues open until merge

    S7 --> S8
    S8 --> S9
    S9 --> S10
    S10 --> [*]
```

## Legend

- **Every arrow is a transition** taken once the step's criterion is met. `stateDiagram-v2`
  cannot style individual transitions, so the distinctions live in the labels.
- **Verified pre-existing bugs** are filed as issues and included in the final report.
  If these are the only findings, continue to Step 7; artifact review, issue cleanup,
  and optional housekeeping still follow. Findings with unconfirmed origin remain
  blocking, as described in [Step 6](PIPELINE.md#step-6--bug-fix-loop).
- **Nested states** — the two loops. Step 4 is reviewer ⇄ developer. Step 6 is
  fix → review → re-test, and the review in the middle is rule 11: no code reaches a
  green QA verdict unreviewed.
- **Iteration guardrail** — both loops cap at 3 passes, then stop and escalate rather
  than grinding.
- **CLARIFY_DESIGN** — requirements are clarified in the main conversation before
  planning begins. Profile, planning, and working-tree problems can also pause the run;
  their checks are specified in [PIPELINE.md](PIPELINE.md). This graph shows real mode;
  the canonical [dry-run table](PIPELINE.md#dry-run-mode) replaces external artifacts
  with local ones.
