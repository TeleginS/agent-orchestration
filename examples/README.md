# Examples

What the pipeline actually produces, and how it actually behaves.

Everything here is drawn from **20 real orchestrated runs** on one production mobile app.
The artifacts are anonymized — the domain is remapped onto the
[Habitat example profile](../profiles/example-mobile-app.md) — but the issue bodies,
review comments, bug reports and outcomes are what the pipeline wrote, not illustrations
of what it might write.

Where something is reconstructed rather than copied, the file says so at the top.

## Contents

- **[run-cumulative-stats/](run-cumulative-stats/)** — one complete run through all
  eleven steps, including the bug-fix loop, with the artifacts the pipeline wrote. Start
  here to see what it produces.
- **[run-progress-store-tests/](run-progress-store-tests/)** — the first live run of
  **this** version of the pipeline, with measured token counts, wall clock and a costed
  estimate. Read this for what it costs and whether it was worth it.
- **[artifacts/](artifacts/)** — the output contracts, indexed: what shape each role
  returns and why the orchestrator depends on it.

---

## What actually happens across 20 runs

Claims about multi-agent pipelines are cheap. These are the outcomes.

| | Count |
|---|---|
| Orchestrated runs | 20 |
| Merged | 19 |
| Closed without merging | 1 |
| Runs where review sent work back | 2 |
| Runs where QA filed bugs | 8 |
| Times either loop hit the 3-iteration cap | 0 |

**The review loop fires rarely.** Eighteen of twenty runs were clean first-pass approvals.
If you are evaluating whether the reviewer step earns its cost, that number cuts both ways:
it is mostly a tax, and the two times it fired it caught things that would have shipped.

**QA fires far more often than review** — roughly 40% of runs produced at least one bug
issue, on code a reviewer had just approved. That ratio is the empirical argument for
keeping them as separate steps with QA running second. If review caught everything, QA
would be idle. It isn't.

**Neither loop ever reached three iterations.** The worst observed was iteration 2. The
guardrail has never actually stopped a run — which is the right amount of times for a
circuit breaker to trip.

---

## The two send-backs

### #189 — the pipeline catching its own agents

A small cleanup: remove a dead factory method. The acceptance criterion was literal —
*the symbol is absent repo-wide, `grep` returns 0*.

The reviewer approved, then QA filed bug #190: the working tree still had three matches
for the symbol. They were in a memory note **the reviewer itself had written during the
review of that same PR**, quoting the dead symbol verbatim to explain what was being
removed. Agent memory files are committed at the end of a pipeline run, so the note would
have reintroduced the symbol into the tracked tree and broken the criterion the PR existed
to satisfy.

The same class of error had already been caught earlier in that run, in the developer's
own notes file. Twice in one PR, two different agents documented their work by writing
down the exact string the work was deleting.

Two things this illustrates. First, an agent pipeline produces artifacts of its own, and
those artifacts are part of the repository — Step 7's rule against blanket-committing
exists because of runs like this. Second, the check that caught it was a literal `grep`
written into an acceptance criterion three steps earlier. A criterion phrased as "clean up
the dead code" catches nothing.

The PR was approved on iteration 2 and merged.

### #36 — the run that shipped nothing

A large feature: a new tab, a card browser, local image matching. The reviewer returned
two blocking findings — a gesture conflict that double-advanced the pager, and a
retroactive protocol conformance on a standard-library type that leaked module-wide.

Both were fixed. The PR was still closed without merging, on a product call, after the
work was done.

It is in this list deliberately. A set of examples where every run ships reads as
marketing. The pipeline's job is to produce a reviewed, tested change — deciding whether
to merge it stays with a person, and sometimes the answer is no.

That run also produced the most useful artifact of the twenty: a list of recurring defect
categories for the UI framework in question, harvested from the bugs QA found. One of them
was a bug the reviewer approved and QA caught — the same pattern as
[run-cumulative-stats](run-cumulative-stats/), from an unrelated feature. That is what
agent memory is for; see [`../memory/README.md`](../memory/README.md).

---

## What this data does not tell you

It is one project, one team, one stack, one operator. The pipeline in this repository is
also a **restructured** version of the one that produced these numbers — same flow and
guardrails, rewritten prompts, and a profile indirection the original did not have. The
outcomes above are evidence that the *design* works.

That the restructured version also works is a separate claim, and it now has exactly one
data point: [run-progress-store-tests](run-progress-store-tests/), where the profile seam
and every guardrail behaved as designed on a real task — including QA blocking work the
reviewer had approved, and the precedence rule catching three stale facts in the profile
on its first outing.

One run is not twenty. Run it in dry-run first. See
[`../PIPELINE.md`](../PIPELINE.md#dry-run-mode).
