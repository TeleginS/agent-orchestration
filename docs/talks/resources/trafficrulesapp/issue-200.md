# Issue #200: [BUG] New Progress tests are not isolated: UserDefaults.standard instead of a dedicated suite

> Снимок от 2026-09-06. [Оригинал в GitHub — нужен доступ к TrafficRulesApp](https://github.com/TeleginS/TrafficRulesApp/issues/200).

Создан: 2026-09-01T21:38:29Z. Состояние на момент снимка: open.

## Описание

#### Description

`ProgressStoreTests` and `TestSessionProgressTests` operated on `UserDefaults.standard` and relied on a hand-maintained key list in `clearUserDefaults()`.

`removeObject` on `UserDefaults.standard` clears only the application domain and cannot remove a value arriving from another domain — which is precisely what this task already hit: seven failing tests against a store that was not zero, caused by a hand-seeded preferences file at the simulator's device-level path for `com.telegins.RUSAutoescuelaDGT`, sitting underneath the app container.

Full isolation is reachable **without a single production change**: `ProgressStore.init(defaults:)` (`ProgressStore.swift:39`), `MistakesStore.init(defaults:)` and `TestResultsStore.init(defaults:)` all accept an injected `UserDefaults`, and `TestSession.init` takes all three stores by injection.

#### Steps to reproduce

1. Place a plist containing `progress*` values in a domain the test process does not clear.
2. Run `ProgressStoreTests`.

#### Expected behaviour

The run's outcome depends only on the contents of the repository.

#### Actual behaviour

The outcome depends on the state of the simulator. Some tests fail falsely; the five timing tests (#199) go green falsely.

#### Root cause

Non-hermetic storage. Confirmed on a live machine: after a serial run the iPhone 17 container retained `progressSolvedQuestionIds => [1767]`, `progressCorrectSubmissions => 1`, `progressTotalSubmissions => 2`; the iPhone 11 Pro Max container held older residue including `progressTotalTestSeconds => 18.6`.

#### Suggested fix

Build a per-test ephemeral suite in `setUp` and inject it into every store:

```swift
private var suiteName: String!
private var defaults: UserDefaults!

override func setUp() {
    super.setUp()
    suiteName = "ProgressStoreTests.\(UUID().uuidString)"
    defaults = UserDefaults(suiteName: suiteName)
}

override func tearDown() {
    defaults.removePersistentDomain(forName: suiteName)
    super.tearDown()
}
```

Minimum acceptable alternative, if the existing project style is to be preserved (risk 4 in #193): fix #199 — then residual state produces a loud failure instead of false green.

#### Affected files

- `TrafficTestAppTests/ProgressStoreTests.swift`
- `TrafficTestAppTests/TestSessionProgressTests.swift`

#### Severity

`Low`

#### Scope

`In-scope` — introduced by PR #198.
