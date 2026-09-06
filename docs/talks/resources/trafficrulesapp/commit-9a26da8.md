# Коммит 9a26da8

> Снимок от 2026-09-06. [Оригинал в GitHub — нужен доступ к TrafficRulesApp](https://github.com/TeleginS/TrafficRulesApp/commit/9a26da875489315c3164ebeb14e1b8af7c57b177).

SHA: `9a26da875489315c3164ebeb14e1b8af7c57b177`. Дата коммита: 2026-09-01T21:44:27Z.

## Сообщение

chore: add the agent-orchestration project profile

The active profile for the agent-orchestration pipeline: stack, layout, build
and test commands, architecture invariants, release gates, gating rules,
review checklist additions and known risk areas.

The pipeline's role prompts are stack-neutral; everything project-specific
lives here, and the orchestrator passes this path to every subagent. Committed
alongside .claude/agent-memory/, which follows the same convention.

Precedence is: observed code > this profile > the role prompts. Agents follow
the code when the profile is wrong and report the drift. Three such reports
came out of the run that produced this PR, and are already folded in — the
question count (2861, not the 2,863 CLAUDE.md still states), the test-file
count and baseline, and the fact that console grep undercounts test results
under the parallel log writer.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

Ниже — изменения всех файлов этого коммита, полученные через GitHub API.

## .claude/project-profile.md

```diff
@@ -0,0 +1,235 @@
+# Profile: TrafficTestApp
+
+> Active profile for the `agent-orchestration` pipeline. Pass this path to the
+> orchestrator at launch.
+>
+> **Precedence: observed code > this profile > the role prompts.** Agents follow the code
+> when this file is wrong and report the drift. Verified against the repository on
+> 2026-09-01.
+
+## Identity
+
+- **Project**: TrafficTestApp (RUS Autoescuela DGT Test) — iOS app for Spanish driving
+  exam preparation with Russian localization. **2861** questions across 9 themed
+  categories (0→221, 1→292, 2→274, 3→180, 4→331, 5→241, 6→453, 7→593, 8→276),
+  subscription-gated premium features.
+  Never hardcode the count — derive it from `QuestionBank`. Note that `CLAUDE.md` says
+  "2,863"; that figure is stale, `questions.json` and `CONTEXT.md` both say 2861.
+- **Repository root**: `/Users/sergei/Developer/TrafficRulesApp`
+- **Remote / tracker**: `TeleginS/TrafficRulesApp`, GitHub Issues
+- **Base branch**: `master`
+
+## Stack
+
+- **Language / runtime**: Swift 5.5+
+- **Framework**: SwiftUI
+- **Minimum platform / target**: iOS 15.6+
+- **Architecture pattern**: MVVM with singleton-ish stores injected as `EnvironmentObject`
+- **Key dependencies** (SPM, pinned): RevenueCat 5.83.2, Firebase 12.17.0,
+  PostHog 3.69.6
+
+## Layout
+
+```
+TrafficRulesApp/            <- source lives HERE
+├── ViewModels/             <- stores and policy objects (NOT "Managers/")
+├── Models/
+├── Services/               <- analytics
+├── Views/
+├── Resources/
+│   ├── {en,es,ru}.lproj/Localizable.strings
+│   ├── questions.json  themes.json  theory.json
+│   └── Images/
+└── Assets.xcassets
+TrafficTestAppTests/        <- unit tests
+TrafficTestApp.xcodeproj    <- project file
+```
+
+- **Source**: `TrafficRulesApp/`
+- **Tests**: `TrafficTestAppTests/` — 13 files / 125 tests on `master`; 15 files / 157 tests
+  with `feature/progress-store-tests`. Treat the count as a baseline: a drop is a
+  regression, not noise.
+- **Resources**: `TrafficRulesApp/Resources/`
+- **Naming traps** — these cost an agent several wrong greps each:
+  - Source is under `TrafficRulesApp/`. `TrafficTestApp` is only the `.xcodeproj` and
+    scheme name.
+  - Stores are in `ViewModels/`, **not** `Managers/`.
+  - The language-pair type lives in `Models/LanguageSettings.swift`. There is no
+    `LanguageSettingsManager.swift`.
+
+## Commands
+
+```bash
+# Build (compile check, no destination needed)
+DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild build -project TrafficTestApp.xcodeproj -scheme TrafficTestApp
+
+# Test — the mandatory QA gate
+DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild test -project TrafficTestApp.xcodeproj -scheme TrafficTestApp -destination "platform=iOS Simulator,name=iPhone 17"
+
+# Validate localization files
+find . -name "*.strings" -exec plutil -lint {} \;
+
+# Discover simulators before testing — never assume
+DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl list devices available | grep iPhone
+
+# Authoritative pass/fail counts — do NOT grep the console
+DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild test -project TrafficTestApp.xcodeproj -scheme TrafficTestApp -destination "platform=iOS Simulator,name=iPhone 17" -resultBundlePath /tmp/tests.xcresult
+xcrun xcresulttool get test-results summary --path /tmp/tests.xcresult
+```
+
+- **Never derive the test count from `xcodebuild` stdout.** The scheme is
+  `parallelizable = "YES"`, so the parallel log writer can clobber a
+  `Test case '...' passed` line mid-write and `grep -c` silently undercounts.
+  Use the `xcresulttool` command above. Parallel execution also means class order
+  varies between runs — tests must be order-independent — and inspecting simulator
+  `UserDefaults` after a run needs `-parallel-testing-enabled NO`.
+- **Test isolation**: `ProgressStore`, `TestResultsStore` and `MistakesStore` all accept
+  `init(defaults:)`, and `TestSession.init` takes all three by injection. New test classes
+  should build a per-test ephemeral suite
+  (`UserDefaults(suiteName: "<Class>.\(UUID().uuidString)")`, dropped in `tearDown` via
+  `removePersistentDomain(forName:)`) rather than the older sibling convention of
+  `UserDefaults.standard` plus a hand-maintained key list. A suite-named `UserDefaults`
+  does **not** fall through to the app's persistent domain — verified empirically.
+
+- **Required prefix**: every `xcodebuild` / `xcrun` invocation needs
+  `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`. This machine defaults to
+  CommandLineTools, so a bare `xcodebuild` fails with *"tool 'xcodebuild' requires
+  Xcode"*. Do **not** run `sudo xcode-select -s` — that permission is always denied and
+  wastes two or three calls.
+- **Known-bad invocations**:
+  - `-destination "...,name=iPhone 15"` — does not exist here. Available: **iPhone 17**,
+    **iPhone 11 Pro Max**.
+  - The active `grep` is `ugrep`, which rejects alternations with an empty branch
+    (`foo\(\|\.bar(` → `empty (sub)expression`). Use `-F` for literals or simpler `-E`
+    patterns.
+
+## Architecture invariants
+
+- **Stores** (`ViewModels/`): `AccessPolicy`, `DailyQuotaStore`, `MistakesStore`,
+  `ProgressStore`, `QuestionBank`, `SettingsManager`, `SubscriptionManager`,
+  `TestResultsStore`, `TestSession`.
+  **Models** (`Models/`): `LanguageSettings`, `LocalizationManager`, `Question`,
+  `SubscriptionTerms`, `TestConfiguration`, `TestResult`, `ThemeData`.
+  **Services** (`Services/`): `AnalyticsService`, `CompositeAnalyticsService`,
+  `PaywallAnalytics`, `PostHogAnalyticsService`.
+- **Single decision point — gating**: `AccessPolicy` (`ViewModels/AccessPolicy.swift`) is
+  the only place that decides access. `decision(for:)` is the pure verdict,
+  `requestStart(for:)` atomically consumes quota, `launch(_:)` / `launchRetry(_:)` are the
+  gated entry points that also build the `TestConfiguration` and the `PaywallContext`.
+  A view reading `subscriptionManager.isPremium` to gate something is a defect, not a
+  shortcut.
+- **Quota storage**: `DailyQuotaStore`, `static let dailyLimit = 3`.
+- **Test configuration**: `TestConfiguration` is a value type built only by its static
+  factories (`.quick`, `.timed`, `.practice`, `.theme`). Views build a config and call
+  `testSession.start(config)`, always behind `accessPolicy.launch`.
+- **Two-layer question model**: `QuestionData` (raw multilingual JSON) → `Question`
+  (language-resolved, answers shuffled). Conversion happens in `QuestionBank`. Answer
+  order is preserved across translations via `shuffleOrder` /
+  `init(from:language:preservingOrderFrom:)`.
+- **Question lookups**: `QuestionBank` maintains O(1) indexes by id and by theme. Use
+  them; do not linear-scan.
+- **Persistence**: `UserDefaults` throughout.
+- **Does NOT exist** — appears in older issues, memory notes and docs; code referencing
+  these will not compile:
+  - `TestManager` — renamed to `TestSession` (PR #134)
+  - `DailyAttemptsManager`, `ThemeAttemptsManager` — deleted (PR #118)
+  - `LanguageSettingsManager.swift` — the type lives in `Models/LanguageSettings.swift`
+  - `TestConfiguration.practiceFromCurrentErrors` — removed (PR #189)
+
+## Critical flags and release gates
+
+- **`debugPremiumMode`** — `private let` on `SubscriptionManager`, an init parameter
+  defaulting to `false` (`SubscriptionManager.swift:174`). It is **not** a mutable global
+  constant. Production code must never pass `true`; the only legitimate `true` is
+  `SubscriptionManagerTests.swift`. Reviewers: check call sites, not a constant
+  declaration — the old "verify the flag is `false`" instruction predates this refactor.
+- Terms and Privacy URLs in `PaywallView.swift` must point at real pages.
+- RevenueCat offerings must have the `Current` flag set — otherwise the paywall renders
+  empty.
+- See `RELEASE_CHECKLIST.md` for the full list.
+
+## Access control / gating rules
+
+Premium users are granted everything and **never consume quota**.
+
+| Kind | Free | Premium |
+|---|---|---|
+| Quick Test | 3 attempts/day, 10 questions | unlimited |
+| Practice | 3 attempts/day | unlimited |
+| Theme id `0` (basic) | 3 attempts/day, 10 questions | unlimited, 30 questions |
+| Theme id `> 0` | **denied** (`premiumRequired`) | 30 questions |
+| Timed Test | **denied** (`premiumRequired`) | 30 questions, 1800 s |
+
+- **Deliberate legacy bypass** (`AccessPolicy.launchRetry`, issue #108): a free user may
+  restart an *already started* premium theme (id > 0) without a paywall and without
+  consuming quota. This is intentional — do not "fix" it. Any denial in the retry path
+  maps to `.retryLimit(testType:)` regardless of kind.
+- **Subscriptions**: RevenueCat, entitlement `premium`, products
+  `traffic.test.premium.weekly` / `traffic.test.premium.monthly`. Bundle id
+  `com.telegins.RUSAutoescuelaDGT`.
+
+## Localization
+
+- **Mechanism**: `"key".localized` or `localizationManager.localized("key")`. No
+  user-facing string is ever hardcoded.
+- **Locale files** — all three updated together or none:
+  `TrafficRulesApp/Resources/{en,es,ru}.lproj/Localizable.strings`
+- **Content vs UI**: UI strings use `.strings`; question content uses multilingual fields
+  inside `questions.json`, resolved via `LanguageSettings.selectedPair.source`. These are
+  two separate systems — do not conflate them.
+
+## Review checklist additions
+
+- 🔴 **Critical**: no production call site passes `debugPremiumMode: true`; every gated
+  capability routes through `AccessPolicy`; RevenueCat entitlement string is exactly
+  `premium`; no `UserDefaults` key renamed or dropped without migration
+- 🟠 **Architectural**: business logic in stores, not in views; `TestConfiguration` built
+  only via its factories; question conversion only in `QuestionBank`; O(1) index lookups
+  not linear scans; dependencies injected (`isPremiumProvider`, `CustomerInfoProviding`),
+  not reached for via `.shared`
+- 🟡 **Correctness**: daily quota resets on the day boundary; `shuffleOrder` preserved
+  across language switches; the 30-minute timed test starts/stops/persists correctly; no
+  double-counting on `TestSession` terminal paths (`completeTest`, `timeExpired`,
+  `exitTest` both branches, `completePractice`)
+- 🟢 **Quality**: new keys present in all three `.strings`; `plutil -lint` clean;
+  `LazyVStack`/`LazyHStack` for long lists; no API newer than iOS 15.6 without
+  `@available`
+
+## Anti-patterns
+
+- `AnyView` as a crutch instead of proper view composition
+- `@MainActor` sprinkled by default without a concrete reason
+- `@StateObject` vs `@ObservedObject` chosen at random — ownership must be deliberate
+- Force-unwraps on values that can legitimately be nil
+- New protocols or generics where the codebase uses a plain struct or function
+- Section-header comments (`// MARK: - Private`) over a single member
+- Doc-comment blocks on trivial functions
+
+## Known risk areas
+
+- `DailyQuotaStore` — recurring day-boundary and midnight-rollover defects (#105, #135)
+- `TestSession` terminal paths — re-entrancy and double-counting. Twice now: #144 (a
+  session exited *after* completing naturally, because SwiftUI timers keep running behind
+  an `.alert`) and #192 (two consecutive `exitTest()` calls, because the guard reads the
+  analytics flag `naturalCompletionLogged` rather than session state). Treat any new code
+  on a terminal path as guilty until the re-entrancy question is answered.
+- Test isolation — #202: three `TestSession` test classes leave `progress*` keys in
+  `UserDefaults.standard`, which can make an absolute-value assertion pass vacuously
+- `SubscriptionManager` — async RevenueCat callbacks racing view initialization (#183)
+- Localization — keys missed in one of the three files whenever a new screen lands
+- Agent memory notes — quoting a symbol a PR is deleting reintroduces it into the tracked
+  tree (#190). Check the working tree before any memory commit.
+
+## Output language
+
+- **Tracker issues and PR text**: English. Historical issues up to #191 are in Russian —
+  match the language of the thread you are replying to, but write anything new in English.
+- **Code, identifiers, commit messages**: English
+- **Technical terms** (SwiftUI, RevenueCat, MVVM, entitlement): unchanged
+
+## Harness settings
+
+- **Local permission config**: `.claude/settings.local.json` — Step 9 applies
+- **Habitual command prefixes** the optimizer must preserve when generalizing:
+  `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer` on every `xcodebuild` and
+  `xcrun` pattern. A pattern built without it will never match and the prompts come back.
```
