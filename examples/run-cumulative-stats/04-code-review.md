# Step 4 — Code review, iteration 1

Produced by `code-reviewer`, posted on PR #143. Approved on the first pass — which is the
common outcome (see the calibration data in [`../README.md`](../README.md)).

Read the **Time accounting** section carefully, then read
[`05-qa-bug.md`](05-qa-bug.md). The reviewer's analysis is correct and the approval was
justified — and QA still found a double-count. Understanding why is the whole point of
this example.

Note also how the verdict is posted: as a PR **comment**, not a formal approval, because
every agent shares one account and the platform blocks approving your own PR. The
orchestrator gates on the reported verdict string, not on the platform's review state.
See [`../../conventions/issue-tracker.md`](../../conventions/issue-tracker.md).

---

## Code Review — `feature/cumulative-stats` (PR #143) — Iteration 1

**Verdict: ✅ APPROVED** (posted as a comment — the platform blocks self-approval via
`gh pr review --approve` since I am authenticated as the PR author: *"Can not approve your
own pull request"*.)

Reviewed against the locked design (ADR-0008, the `CONTEXT.md` glossary, epic #136 and
child issues #137–#141). Verified by reading the diff, cross-referencing the habit catalog
(240 rows, `habitId` globally unique, `categoryId` 0–5 summing 38/52/41/29/44/36 = 240),
and a full `./gradlew :app:assembleDebug`.

### Time accounting (highest risk item) — correct

`SessionTracker.kt`: `statsStore.totalFocusSeconds += duration` appears exactly once in
each of the four terminal paths, with no cross-calls between them:

- `completeSession()` (lines 350–351)
- `timeExpired()` (lines 158–159)
- `exitSession()` normal path (lines 399–400) and the freeform-abandon early return
  (lines 389–390, which `return`s immediately, so the normal-path add below is unreachable
  for that call)
- `completeFreeform()` (lines 370–371) — previously persisted nothing; now fixed per the ADR

No path calls another end-path function, so no double counting and no missed path.

### Completed monotonicity — correct

`StatsStore.markCompleted` guards with `!completedHabitIds.contains(id)` before inserting
— insert-only, idempotent, never removed elsewhere. Uses `currentHabit.id` (`= habitId`),
confirmed globally unique across all 240 habits (not per-category), so cross-category
collisions in the `Set<Long>` are not possible.

### Check-in counters — correct

`totalCheckIns += 1` unconditionally in `submitCheckIn()`; `completedCheckIns += 1` and
`markCompleted` placed inside the success branch immediately alongside the existing
`streakStore.markHit`, symmetric with the existing `markMiss` placement.

### Denominators — correct

`StatsStore.closedCategoryCount` / `isCategoryClosed` / `categoryProgress` all go through
`repository.getHabitIds(for:)` (new, index-backed via `habitsByCategory`, not a linear
scan) and the widget uses `repository.totalHabitCount`. No reference to the static
category manifest anywhere in the new code. Verified 240 = the sum of the 6 categories.

### Reset — correct

`clearHistory()` calls `statsStore.reset()`, which clears `completedHabitIds`,
`completedCheckIns`, `totalCheckIns` and `totalFocusSeconds` (the three scalar fields zero
out through their persistence writes; `completedHabitIdsKey` is removed explicitly —
functionally complete, if slightly inconsistent in style; not blocking).

### Wiring — correct

`StatsStore` constructed in the app graph, provided via Hilt, threaded into
`SessionTracker` identically to `sessionStore` / `streakStore`.

### UI — correct

`StatsWidget`: hero `heroIllustration` (placeholder drawable present, resolves cleanly)
plus 4 metrics (Habits `completed/240` + mini bar, Categories `closed/6` + mini bar, Time
adaptive `Xh Ym` / `Xm`, Consistency `%`). The whole card is one clickable surface with
the ripple suppressed on the inner elements — full-card tap target, pushes (not a sheet)
to `StatsDetailScreen`, consistent with the rest of the codebase, `minSdk 26`-safe, builds
green.

`StatsDetailScreen`: nav title `stats.title` + `stats.subtitle`, 6 read-only
`CategoryProgressRow`s (completed green / total gray + progress bar), no clickable
modifiers or gating on the rows.

### Localization — correct

All `stats.*` keys (`title`, `subtitle`, `habits`, `categories`, `time`, `consistency`,
`time.format.hm`, `time.format.m`) present and consistent across `values`, `values-es`,
`values-de`; lint clean on all three.

### Standard checklist

- `DEBUG_ENTITLEMENT_OVERRIDE` untouched (`false`)
- No unsafe non-null assertions in new code
- No leaks — `StatsStore` held by the graph, no back-reference from it into the tracker
- Architecture respected: all business logic in `StatsStore` / `SessionTracker`,
  composables are thin
- No breaking persistence key changes — only new keys added (`statsCompletedHabitIds`,
  `statsCompletedCheckIns`, `statsTotalCheckIns`, `statsTotalFocusSeconds`)
- Old today-scoped computed properties on `SessionStore` and the unused
  `home.todayProgress` / `home.noMisses` keys are left in place — explicitly left to this
  PR's discretion by the epic, not a defect
- `assembleDebug` succeeds

### Non-blocking quality notes

1. No `StatsStoreTests.kt` was added, unlike every sibling store (`StreakStoreTests`,
   `SessionStoreTests`, `QuotaStoreTests`). Given the epic's own risk callout on time
   double-counting and monotonicity, dedicated unit tests — asserting that each terminal
   path adds duration exactly once, and that `markCompleted` is idempotent — would harden
   this against regressions. Worth adding before or alongside the QA pass (#142); not a
   blocker for this PR.
2. `StatsStore.reset()` removes `completedHabitIdsKey` explicitly but relies on the
   persistence writes to zero the other three keys — functionally equivalent, just
   stylistically inconsistent within one method.

Out of scope per the review brief (not flagged): foreground-only time accounting, real
illustration art, category-row deep linking.

---

## Why this approval was right, and still not enough

The reviewer read every terminal path and proved a true statement: **no terminal path
calls another terminal path**, so within a single completion sequence, time is added once.

The defect QA found lives outside that frame. It is not about one path calling another —
it is about `exitSession()` being invoked *again*, from the UI, after a terminal path
already ran. Nothing in the diff shows that; it requires reasoning about how a background
timer interleaves with a modal dialog that does not pause it.

That is the seam between the two steps. A reviewer reads the change. QA runs the program
and asks what else can happen. Collapsing them into one pass — the obvious efficiency —
removes exactly the pass that catches this class of bug.

Note also non-blocking finding #1: the reviewer flagged the missing store tests *and named
the exact invariant they should assert*. Had those tests existed, they still would not have
caught this one — a unit test over the store would not model the dialog race either. The
reviewer was right that they were worth having, and right not to block on them.
