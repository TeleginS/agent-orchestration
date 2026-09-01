# Step 1 — Child issues #137–#142

Six children, cross-linked to epic #136. Two are reproduced in full below: the one the
bug later came from (#139) and the QA task (#142).

What to notice: **#139's acceptance criteria already contain the invariant that was later
violated** — *"No double counting of time on normal completion or on exit."* The planner
wrote it, the developer implemented against it, the reviewer verified it, and it was
still wrong. That is not a failure of any one of them; it is why the pipeline has four
independent passes instead of one.

---

## #139 — Capture hooks in SessionTracker (check-in counters, time, reset)

Labels: `size:M`, `component:SessionTracker`, `ready-for-agent`,
`epic:cumulative-stats`, `component:Stats`

### Description

Capture data for `StatsStore` (#137) from `SessionTracker` at every relevant point.
Symmetric with the existing `streakStore.markHit/markMiss` calls.

1. **Check-in submitted** — in `SessionTracker.submitCheckIn()`: every check-in
   increments `statsStore.totalCheckIns`; if the check-in succeeded, also
   `statsStore.completedCheckIns += 1` and `statsStore.markCompleted(habitId)`.

2. **Time accumulation on ALL terminal paths** — add the session's elapsed time to
   `statsStore.totalFocusSeconds` in:
   - `completeSession`
   - `timeExpired`
   - `exitSession` (normal path)
   - `exitSession` — the freeform-abandon early return (currently returns early)
   - `completeFreeform` (**currently persists no time — a fixable bug**)

   Time must be added **exactly once** on each path — neither skipped nor double-counted.

3. **Reset** — `SessionTracker.clearHistory()` must additionally call `statsStore.reset()`.

Freeform flows contribute to completed + consistency + time like every other flow.

File: `app/src/main/java/com/example/habitat/viewmodel/SessionTracker.kt`

### Acceptance criteria

- [ ] Every check-in increments `totalCheckIns`; a successful one also increments
      `completedCheckIns` and calls `markCompleted`.
- [ ] Elapsed time is added to `totalFocusSeconds` on all five paths — exactly once.
- [ ] Freeform increases completed / consistency / time.
- [ ] `clearHistory()` calls `statsStore.reset()`.
- [ ] **No double counting of time on normal completion or on exit**; verified on the
      freeform flow.
- [ ] Build is green.

### Dependencies

- Blocked by: #137 (`StatsStore` must exist)
- Blocks: #142 (QA)

### Size

`M`

### Epic

Part of #136 (Redesign the home statistics widget — cumulative Stats)

---

## #142 — QA: Stats correctness (time, completed, closed, consistency)

Labels: `size:M`, `qa`, `epic:cumulative-stats`, `component:Stats`

### Description

Acceptance verification of the cumulative Stats after the hooks (#139), the widget (#140)
and the detail screen (#141) land. Manual QA plus the domain invariants from ADR-0008.

Scenarios:

1. **Completed monotonicity** — check in successfully → completed rises; then fail a
   check-in on the same habit → completed does **not** fall (the habit only returns to
   the misses list).
2. **No completed double-count** — a repeat success on an already-completed habit does
   not increase `completedCount`.
3. **Closed at full coverage** — complete every habit in one category → `closed
   categories` increases by 1; partial coverage does not close it.
4. **Consistency** — every check-in moves the denominator; `%` = `completed/total×100`;
   with 0 check-ins it does not crash and shows a sensible value.
5. **Time across all flows** — time accumulates on `completeSession`, `timeExpired`,
   `exitSession` (normal and freeform-abandon) and `completeFreeform`; freeform time
   counts; **exactly once per path**, no skips and no double counts.
6. **Widget** — 4 metrics correct, no midnight reset; tapping the card pushes "My stats".
7. **Detail** — 6 categories, totals summing to 240, rows read-only.
8. **Reset** — "Clear history" zeroes Stats along with sessions and misses.
9. **Fresh start** — a new or cleared user sees `0/240`, `0/6`, 0 time, 0% consistency.

File defects as issues per the repo convention and link them to #136.

### Acceptance criteria

- [ ] All 9 scenarios above pass on an emulator at `minSdk 26`.
- [ ] Special attention: no time double-count, and completed monotonicity.
- [ ] Every defect found is filed as an issue (severity + component) and linked to #136.
- [ ] Green light to close out the epic.

### Dependencies

- Blocked by: #139 (hooks), #140 (widget), #141 (detail screen)

### Size

`M`

### Epic

Part of #136

---

## The other four, in brief

| # | Title | Size | Notes |
|---|---|---|---|
| #137 | `StatsStore` + wiring/injection | M | Blocks everything else |
| #138 | `heroIllustration` placeholder drawable | S | Independent; only blocks #140 |
| #140 | Home Stats widget | L | Depends on #137, #138 |
| #141 | Detail screen "My stats" | M | Depends on #137 |

`#138` is the useful shape to copy: an independent `S` task, carved out precisely so the
missing art asset never blocks the logic work. The planner is not just splitting by
feature area — it is splitting to shorten the dependency chain.
