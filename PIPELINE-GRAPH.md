# Pipeline State Graph

The state machine described in [PIPELINE.md](PIPELINE.md). Renders natively on GitHub;
any mermaid viewer or `mmdc` will also do.

> Syntax note: every state description is quoted (`state "..." as ID`). Bare colons in
> the text break the mermaid parser.

```mermaid
stateDiagram-v2
    [*] --> S0: task from the user

    state "Step 0 — design artifact check" as S0
    state "STOP — no design artifacts for a product decision" as STOP_DESIGN
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
    S0 --> STOP_DESIGN: product decisions required
    STOP_DESIGN --> S0: user-driven design pass produces the artifacts

    S1 --> S2: epic + child issues collected
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
    S5 -.-> S10: pre-existing bugs, outside this cycle

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

- **Solid arrow** — the normal transition once the step's criterion is met.
- **Dashed arrow** — flow outside the main cycle. Pre-existing bugs go straight to the
  report; they are filed but never block this run.
- **Nested states** — the two loops. Step 4 is reviewer ⇄ developer. Step 6 is
  fix → review → re-test, and the review in the middle is rule 11: no code reaches a
  green QA verdict unreviewed.
- **Iteration guardrail** — both loops cap at 3 passes, then stop and escalate rather
  than grinding.
- **STOP_DESIGN** — the only stop that can happen before development starts, and the
  only one the user can clear by doing work outside the pipeline.
