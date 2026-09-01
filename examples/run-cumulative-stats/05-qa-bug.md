# Step 5 — QA finds the bug: issue #144

Produced by `qa-tester` while working scenario 5 of #142 ("time across all flows, exactly
once per path"). Labels: `bug`, `severity:high`, `component:SessionTracker`.

This is the artifact worth studying. It does not say "time is sometimes double-counted."
It gives the exact re-entrancy hazard, the pre-existing guard that proves the codebase
already knew about it, the four-step timing-dependent reproduction, and the one-line fix.
The developer's next pass is mechanical because of that.

---

## [BUG] `exitSession()` double-counts session time into StatsStore when it fires after natural completion

### Description

`SessionTracker.exitSession()` (the `statsStore.totalFocusSeconds +=` lines added in PR
#143 / issue #139) has no guard against being invoked **after** the session already
completed naturally via `completeSession()`, `timeExpired()` or `completeFreeform()`. If
`exitSession()` runs a second time on an already-completed session, it unconditionally
adds another `duration` / `abandonedDuration` to `StatsStore.totalFocusSeconds`,
double-counting time for that session. It also calls `sessionStore.add(result)` again on
the normal (non-freeform) branch, saving a duplicate record.

This directly violates the acceptance criterion of issue #139 — *"No double counting of
time on normal completion or on exit"* — and the QA task's explicit requirement that "no
path both adds time AND falls through to another path that also adds."

### Root cause

`SessionTracker.kt` already has a `naturalCompletionLogged` flag (pre-existing, predates
this PR) that exists specifically to stop `trackSessionAbandonedIfNeeded()` from emitting a
duplicate **analytics** "abandoned" event once the completion event has already fired:

```kotlin
if (sessionId == null || naturalCompletionLogged) return
```

That guard proves the codebase already recognizes `exitSession()` can be re-entered after
natural completion. This PR added the new time-accumulation code *outside* it:

```kotlin
fun exitSession() {
    stopTimer()
    trackSessionAbandonedIfNeeded()   // no-ops correctly if naturalCompletionLogged

    if (isFreeform) {
        sessionCompleted = true
        isFreeform = false
        val abandonedDuration = sessionStartTime?.let { now() - it } ?: 0
        statsStore.totalFocusSeconds += abandonedDuration   // <-- runs even if already completed
        return
    }

    sessionCompleted = true
    val missedIds = misses.keys.toList()
    // ...
    val duration = sessionStartTime?.let { now() - it } ?: 0
    statsStore.totalFocusSeconds += duration                // <-- runs even if already completed
    sessionStore.add(result)                                // <-- duplicate record
    // ...
}
```

Neither branch checks `sessionCompleted` / `naturalCompletionLogged` before adding time or
saving the result.

### Steps to reproduce (concrete, timing-dependent)

1. Start a **timed focus session** (25 min).
2. A couple of seconds before the timer reaches 0, tap the header "✕" (exit) → the "Save
   and exit?" confirmation dialog appears.
3. Let the countdown reach 0 while the dialog is still showing. The tracker's timer
   coroutine fires `timeExpired()` in the background — an `AlertDialog` does not suspend
   it. That sets `sessionCompleted = true`, adds `duration1` to
   `statsStore.totalFocusSeconds`, and requests the results screen.
4. Still looking at the now-stale dialog, tap "Save and exit" → `exitSession()` runs. It
   correctly skips the abandon analytics event (guarded), but unconditionally computes
   `duration2 = now - sessionStartTime` (greater than `duration1`), adds it to
   `statsStore.totalFocusSeconds` again, and saves a second record.

**Result:** `totalFocusSeconds` contains `duration1 + duration2` for a single session
instead of one duration, and `SessionStore` holds two records for one run — one
"completed", one "abandoned".

The same hazard applies to `completeSession()` / `completeFreeform()` racing a pending exit
confirmation — any path where `exitSession()` fires after a natural-completion path has
already run.

### Expected behaviour

Time is added to `StatsStore.totalFocusSeconds` **exactly once** per session, regardless of
how many exit-related paths are entered. `exitSession()` should no-op — skipping time
accumulation and record saving — if the session already completed naturally, the same way
`trackSessionAbandonedIfNeeded()` already does for analytics.

### Actual behaviour

`exitSession()` unconditionally re-adds the session duration to `totalFocusSeconds` and
re-saves a record even when the session already completed naturally, causing
double-counted all-time focus time.

### Suggested fix

Add a guard at the top of `exitSession()` that returns early if `sessionCompleted` (or
`naturalCompletionLogged`) is already true, before `stopTimer()`'s side effects, the time
accumulation, or `sessionStore.add(...)`.

### Affected files

- `app/src/main/java/com/example/habitat/viewmodel/SessionTracker.kt`

### Severity

`High` — corrupts an all-time metric the whole feature exists to display, and silently
duplicates session records.

### Scope

`In-scope` — introduced by PR #143 (issue #139).

---

## What made this findable

Three things, in order of importance:

**The acceptance criterion was specific.** "No double counting of time on normal
completion or on exit" is testable. Had the epic said "statistics should be accurate", QA
would have checked the happy path and moved on.

**The epic flagged it as the top risk** and assigned verification to the QA child issue.
QA arrived already knowing where to push hardest.

**QA reasoned about interleaving, not structure.** The reviewer asked "does any path call
another?" — correctly answered no. QA asked "can this function run twice?" — a different
question, answerable only by thinking about the timer and the dialog as concurrent actors.

The `naturalCompletionLogged` flag is the detail that turns a hypothesis into a filed bug.
Its existence proves someone already hit this re-entrancy once, for analytics, and fixed
it narrowly. Finding the old guard is what let QA state the root cause instead of just
reporting a symptom.
