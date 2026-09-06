# Issue #199: [BUG] Five terminal-path tests assert an absolute totalTestSeconds instead of a delta

> Снимок от 2026-09-06. [Оригинал в GitHub — нужен доступ к TrafficRulesApp](https://github.com/TeleginS/TrafficRulesApp/issues/199).

Создан: 2026-09-01T21:38:14Z. Состояние на момент снимка: open.

## Описание

#### Description

Five single-path tests in `TestSessionProgressTests` ended with `XCTAssertGreaterThan(progressStore.totalTestSeconds, 0)` — asserting the accumulated total rather than the increase contributed by the terminal path under test.

While the store enters the test at zero this works. The moment `totalTestSeconds` is non-zero on entry, the assertion becomes a tautology and the test physically cannot fail — even if `progressStore.totalTestSeconds += duration` were deleted from the method it claims to cover.

This is exactly the half of PR #143 invariant 1 ("every terminal path adds duration exactly once") that the task exists to pin. The other half ("not twice") was written correctly, with an `afterCompletion` snapshot and a comparison against it. The file was internally inconsistent.

Issue #196 explicitly required deltas: *"assert deltas (`let before = store.totalTestSeconds` → path → compare), not absolute seconds."*

#### Steps to reproduce

1. Make `progressStore.totalTestSeconds` non-zero on entry. This already happened during implementation: a hand-seeded preferences file at the simulator's device-level path sat *underneath* the app container domain, where `UserDefaults.standard.removeObject` from the test process cannot clear it — seven tests failed against a store that was never actually zero.
2. Delete `progressStore.totalTestSeconds += duration` from `completeTest()`, `timeExpired()`, `completePractice()` and both branches of `exitTest()`.
3. Run `TestSessionProgressTests`.

#### Expected behaviour

All five tests fail — the delta is zero.

#### Actual behaviour

All five pass — `totalTestSeconds` is greater than zero regardless.

#### Root cause

An assertion on the absolute value of an accumulating counter instead of on the delta around the call: `TestSessionProgressTests.swift` lines 59, 68, 77, 86, 95.

What makes the risk real rather than theoretical:

- the scenario already occurred in this task — seven tests failed against a non-zero store;
- the suite itself still leaves `progress*` in `UserDefaults.standard` (see the pre-existing issue): after a serial run the iPhone 17 container held `progressSolvedQuestionIds => [1767]`, `progressCorrectSubmissions => 1`, `progressTotalSubmissions => 2`;
- the only protection was a hardcoded six-key list in `clearUserDefaults()`. Adding a fifth `progress*` property to `ProgressStore` without updating both lists would silently turn all five tests into tautologies.

#### Suggested fix

Snapshot before the call, compare after — the form already used by the "not twice" tests:

```swift
func testCompleteTestAccumulatesTime() {
    session.start(.quick(from: bank))
    letSessionRun()
    let before = progressStore.totalTestSeconds

    session.completeTest()

    XCTAssertGreaterThan(progressStore.totalTestSeconds, before)
}
```

#### Affected files

- `TrafficTestAppTests/TestSessionProgressTests.swift` (lines 53–96)

#### Severity

`Medium`

#### Scope

`In-scope` — introduced by PR #198.
