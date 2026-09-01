# Step 3 — Pull request #143

Produced by `developer` on branch `feature/cumulative-stats`, targeting `main`.

Two things worth copying from this PR body:

**It closes the implementation issues but not the QA one.** `Closes #137, #138, #139,
#140, #141` — #142 stays open, because QA has not run yet. The developer does not get to
declare its own work verified.

**The test plan has an unchecked box.** Manual QA is listed and explicitly left unticked,
pointing at #142. The developer states what it did *not* verify rather than leaving the
reader to assume it did.

---

## Summary

Implements Epic #136: replaces the home "Today's progress" (today-scoped) widget with a
cumulative, all-time **Stats** widget plus a per-category "My stats" detail screen.

Closes #137, #138, #139, #140, #141.

- **#137** — `StatsStore` (`DataStore`-backed): `completedHabitIds`, `completedCheckIns`,
  `totalCheckIns`, `totalFocusSeconds`, `markCompleted(id)`, `reset()`, plus computed
  `completedCount` / `consistencyPercent` / `closedCategoryCount(in:)` /
  `categoryProgress(categoryId:in:)`. Wired like `SessionStore` / `StreakStore`
  (constructed in the app graph, injected via Hilt, passed into `SessionTracker`).
- **#138** — `heroIllustration` drawable with a temporary vector placeholder, swappable
  for real art later with zero code changes.
- **#139** — `SessionTracker` capture hooks: every `submitCheckIn()` increments
  `totalCheckIns` / `completedCheckIns` and marks the habit completed, symmetric with the
  existing `streakStore.markHit/markMiss`. Every terminal path (`completeSession`,
  `timeExpired`, `exitSession` — both the freeform-abandon early return and the normal
  path — and `completeFreeform`) now accumulates its session duration into
  `statsStore.totalFocusSeconds` exactly once. This also fixes the pre-existing "freeform
  time uncounted" gap (`completeFreeform()` previously persisted no duration at all).
  `clearHistory()` now also calls `statsStore.reset()`.
- **#140** — `StatsWidget` replaces the old gradient card: hero `heroIllustration`, then
  Habits `completed/240` + mini bar, Categories `closed/6` + mini bar, Time (adaptive
  `Xh Ym` / minutes-only), Consistency `%`. The whole card is a clickable surface pushing
  `StatsDetailScreen`, using the same navigation pattern already used elsewhere in the app.
- **#141** — `StatsDetailScreen` ("My stats" + subtitle): a read-only list of the 6
  categories, each showing name + `completed/total` (green/gray) + progress bar. No
  navigation, gating, or tap targets on rows.
- Denominators come exclusively from `HabitRepository` (`totalHabitCount` = 240, new
  `getHabitIds(for:)` for per-category totals) — never the static category manifest.
- `stats.*` keys added to `values`, `values-es`, `values-de`.

## Test plan

- [x] `./gradlew :app:assembleDebug` — succeeds, no new warnings
- [x] `./gradlew :app:testDebugUnitTest` — full suite green
- [x] `./gradlew :app:lintDebug ktlintCheck` — clean
- [x] Installed on an emulator and screenshotted the home screen: the widget shows
      `0/240`, `0/6`, `0m`, `0%` with mini bars and the placeholder illustration rendering
      correctly (fresh install, matches "start at zero, no backfill")
- [ ] **Manual QA (per epic #136 checklist / issue #142)**: complete a habit via the
      timed and freeform flows to confirm monotonic completed count, a category closing
      only at full coverage, consistency reflecting every check-in including repeats, and
      freeform time now accumulating

`DEBUG_ENTITLEMENT_OVERRIDE` was not touched (still `false`).
