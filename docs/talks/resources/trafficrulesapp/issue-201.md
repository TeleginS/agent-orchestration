# Issue #201: [BUG] exitTest() tests do not prove which of the two branches ran

> Снимок от 2026-09-06. [Оригинал в GitHub — нужен доступ к TrafficRulesApp](https://github.com/TeleginS/TrafficRulesApp/issues/201).

Создан: 2026-09-01T21:38:35Z. Состояние на момент снимка: open.

## Описание

#### Description

Issue #196 counts five accumulation sites, two of which are inside `exitTest()` — the practice branch and the normal one. `testExitFromPracticeAccumulatesTime` and `testExitFromTestAccumulatesTime` asserted only that time grew. Neither asserted the property that distinguishes the branches: the practice branch saves no `TestResult`, the normal branch saves exactly one.

If `start(_:)` ever set `isPracticeMode` incorrectly, both tests would stay green while the claimed coverage of five accumulation sites silently became false.

#### Steps to reproduce

1. In `TestSession.start(_:)`, replace `isPracticeMode = config.kind == .practice` with `isPracticeMode = false`.
2. Run `TestSessionProgressTests`.

#### Expected behaviour

`testExitFromPracticeAccumulatesTime` fails — the practice branch never ran.

#### Actual behaviour

The test passes: the time was added by the non-practice branch.

#### Root cause

The assertion does not discriminate between branches. `TestSessionProgressTests.swift` lines 80–96.

#### Suggested fix

- `testExitFromPracticeAccumulatesTime`: add `XCTAssertTrue(resultsStore.testResults.isEmpty)`
- `testExitFromTestAccumulatesTime`: add `XCTAssertEqual(resultsStore.testResults.count, 1)`

Verified against `TestSession.swift`: the practice branch returns at :410 before reaching `resultsStore.add(result)`; the normal branch adds exactly one at :429.

#### Affected files

- `TrafficTestAppTests/TestSessionProgressTests.swift`

#### Severity

`Low`

#### Scope

`In-scope` — introduced by PR #198.
