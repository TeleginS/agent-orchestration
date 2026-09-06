# Issue #144: [BUG] exitTest() double-counts session time into ProgressStore when it fires after natural completion

> Снимок от 2026-09-06. [Оригинал в GitHub — нужен доступ к TrafficRulesApp](https://github.com/TeleginS/TrafficRulesApp/issues/144).

Создан: 2026-07-05T13:47:20Z. Состояние на момент снимка: closed.

## Описание

#### Описание
`TestSession.exitTest()` (added `progressStore.totalTestSeconds +=` lines in PR #143 / issue #139) has no guard against being invoked **after** the test session already naturally completed via `completeTest()`, `timeExpired()`, or `completePractice()`. If `exitTest()` runs a second time on an already-completed session, it unconditionally adds another `duration`/`abandonedDuration` to `ProgressStore.totalTestSeconds`, double-counting time for that session. It also calls `resultsStore.add(result)` again in the normal (non-practice) branch, saving a duplicate/incorrect `TestResult`.

This directly violates the acceptance criterion of issue #139: *"Нет двойного учета времени при обычном завершении и при exit"* and the QA task's explicit requirement that "No path both adds time AND falls through to another path that also adds."

#### Root cause
`TestSession.swift` already has a `naturalCompletionLogged` flag (pre-existing, predates this PR) that exists specifically to stop `trackTestAbandonedIfNeeded()` from emitting a duplicate **analytics** "abandoned" event once `trackTestCompleted()` has already fired (`guard testSessionId != nil, !naturalCompletionLogged else { return }`, `TrafficRulesApp/ViewModels/TestSession.swift` ~line 469-470). This proves the codebase already recognizes that `exitTest()` can be re-entered after natural completion.

However, this PR added the new time-accumulation code to `exitTest()` *outside* that guard:

```swift
func exitTest() {
    stopTimer()
    trackTestAbandonedIfNeeded()   // no-ops correctly if naturalCompletionLogged

    if isPracticeMode {
        testCompleted = true
        isPracticeMode = false
        let abandonedDuration = testStartTime.map { Date().timeIntervalSince($0) } ?? 0
        progressStore.totalTestSeconds += abandonedDuration   // <-- runs even if already completed
        return
    }

    testCompleted = true
    let incorrectIds = Array(incorrectAnswers.keys)
    ...
    let duration = testStartTime.map { Date().timeIntervalSince($0) } ?? 0
    progressStore.totalTestSeconds += duration                // <-- runs even if already completed
    resultsStore.add(result)                                  // <-- duplicate TestResult
    ...
}
```

Neither branch checks `testCompleted`/`naturalCompletionLogged` before adding time (or before saving the result).

#### Шаги воспроизведения (concrete, timing-dependent)
1. Start a **Timed Test** (30Q/30min).
2. A couple seconds before the timer reaches 0, tap the header "✕" (exit) button → the "Save and exit?" confirmation alert appears (`TestView.swift` line ~122/289).
3. Let the countdown reach 0 while the alert is still showing. `TestManager`'s timer fires `timeExpired()` in the background (SwiftUI timers are not paused by `.alert`): this sets `testCompleted = true`, adds `duration1` to `progressStore.totalTestSeconds`, and requests `showTestResults = true`.
4. Still looking at the (now stale) alert, tap "Save and exit" → `TestSession.exitTest()` runs. It skips the abandon analytics event (guarded), but unconditionally computes `duration2 = now - testStartTime` (> `duration1`) and adds it to `progressStore.totalTestSeconds` again, and saves a second `TestResult`.

Result: `ProgressStore.totalTestSeconds` now includes `duration1 + duration2` for a single session instead of one duration, and `TestResultsStore` has two results for one test run (one "completed", one "abandoned/incomplete").

The same hazard applies to `completeTest()`/`completePractice()` racing with a pending exit confirmation — any path where `exitTest()` fires after the session's natural-completion path has already run.

#### Ожидаемое поведение
Time is added to `ProgressStore.totalTestSeconds` **exactly once** per session, regardless of how/how many times exit-related code paths are entered. `exitTest()` should no-op (skip time accumulation and result-saving) if the session was already naturally completed — e.g. by checking `!naturalCompletionLogged` / `!testCompleted` before doing any of its work, the same way `trackTestAbandonedIfNeeded()` already does for analytics.

#### Фактическое поведение
`exitTest()` unconditionally re-adds session duration to `progressStore.totalTestSeconds` (and re-saves a `TestResult`) even when the session already completed naturally, causing double-counted all-time time-on-tests.

#### Корневая причина
See above — new `progressStore.totalTestSeconds +=` lines in `exitTest()` are not covered by the existing `naturalCompletionLogged`/`testCompleted` re-entrancy guard, which only protects the analytics abandon event.

#### Предлагаемое исправление
Add a guard at the top of `exitTest()` (or wrap its body) that returns early if `testCompleted` (or `naturalCompletionLogged`) is already `true`, before doing `stopTimer()`'s side effects, time accumulation, or `resultsStore.add(...)`:

```swift
func exitTest() {
    guard !testCompleted else { return }
    stopTimer()
    ...
}
```

#### Затронутые файлы
- `TrafficRulesApp/ViewModels/TestSession.swift` (`exitTest()`, ~lines 381-411; the pre-existing `naturalCompletionLogged` guard pattern is at ~lines 460-470)

#### Severity
`High` — corrupts the new all-time "Время" (time-on-tests) cumulative statistic, the metric this PR/epic (#136) was built to make reliable, and duplicates saved test results in a timing-dependent way. Not a crash, but every occurrence permanently inflates a cumulative counter with no way for the user to correct it (short of "Очистить историю", which wipes everything).

#### Scope
`In-scope` — the double-counted write (`progressStore.totalTestSeconds +=`) is new code added by PR #143 / issue #139. The underlying re-entrancy hazard in `exitTest()` (missing guard) predates this PR (the `naturalCompletionLogged` flag and un-guarded `exitTest()` body already existed on `master`), but this PR placed new statistics-critical code inside that pre-existing unguarded path without extending the guard, which is exactly the "no double-count" acceptance criterion of #139 that this issue violates.

Related: Epic #136, issue #139, PR #143.
