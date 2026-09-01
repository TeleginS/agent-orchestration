# Profile: Habitat (example)

> **This is a worked example, not a real project.** It shows the level of detail that
> actually helps an agent. Copy `_template.md` for your own — don't edit this one.
>
> Habitat is a fictional cross-platform habit-tracking mobile app with a subscription
> tier. It was chosen because it exercises every section: gating rules, localization,
> a two-layer data model, and a release gate.
>
> **Precedence: observed code > this profile > the role prompts.**

## Identity

- **Project**: Habitat — habit tracking with streaks, reminders and a paid analytics tier
- **Repository root**: `/path/to/habitat`
- **Remote / tracker**: `example-org/habitat`, GitHub Issues
- **Base branch**: `main`

## Stack

- **Language / runtime**: Kotlin 1.9 / JVM 17
- **Framework**: Jetpack Compose, Android
- **Minimum platform / target**: `minSdk 26`, `targetSdk 34`
- **Architecture pattern**: MVVM — Compose UI, `ViewModel` per screen, repositories below
- **Key dependencies**: Room (persistence), Hilt (DI), a third-party billing SDK

## Layout

```
habitat/
├── app/src/main/java/com/example/habitat/
│   ├── ui/            # Compose screens and components
│   ├── viewmodel/      # one per screen
│   ├── data/           # repositories, Room DAOs, entities
│   ├── domain/         # entitlement, streak and quota logic
│   └── di/             # Hilt modules
├── app/src/main/res/values{,-es,-de}/strings.xml
└── app/src/test/       # unit tests
```

- **Source**: `app/src/main/java/com/example/habitat/`
- **Tests**: `app/src/test/` (unit), `app/src/androidTest/` (instrumented)
- **Resources**: `app/src/main/res/`
- **Naming trap**: business rules live in `domain/`, not in `data/`. The repositories in
  `data/` are thin and must stay that way.

## Commands

```bash
# Build
./gradlew :app:assembleDebug

# Test — the mandatory QA gate
./gradlew :app:testDebugUnitTest

# Lint / format
./gradlew :app:lintDebug ktlintCheck

# Discover connected devices before an instrumented run
adb devices -l
```

- **Required prefix or environment**: `JAVA_HOME` must point at JDK 17. A newer JDK on
  `PATH` makes Gradle fail with an unhelpful toolchain error.
- **Known-bad invocations**: bare `gradle` — this project only builds through the
  wrapper. `./gradlew test` runs every variant and takes ~8 minutes; use the
  `testDebugUnitTest` target above.

## Architecture invariants

- **Core modules**:
  - `EntitlementPolicy` (`domain/`) — the only place that decides whether a capability
    is available
  - `QuotaStore` (`domain/`) — free-tier counters, `DAILY_LIMIT = 5`
  - `HabitRepository` (`data/`) — Room-backed CRUD, no business rules
  - `StreakCalculator` (`domain/`) — pure, timezone-aware
  - `BillingManager` (`data/`) — wraps the billing SDK, exposes `isSubscribed: StateFlow`
- **Single decision points**: every gating check goes through `EntitlementPolicy`.
  A screen that reads `BillingManager.isSubscribed` directly is a bug, not a shortcut.
- **State and persistence**: Room for habit data; `DataStore` for preferences. Keys are
  declared in `data/PreferenceKeys.kt` — never inline a key string.
- **Data model layering**: `HabitEntity` (Room row) → `Habit` (domain model, streak
  resolved, reminders parsed). Conversion happens in `HabitRepository` and nowhere else.
- **Does NOT exist**: `PremiumManager`, `HabitManager`, `UserSession`. All three appear
  in older issues and were removed in the 2.0 refactor — code referencing them will not
  compile.

## Critical flags and release gates

- `BuildConfig.DEBUG_ENTITLEMENT_OVERRIDE` must be `false` in release builds. Check
  `app/build.gradle.kts`.
- The Terms and Privacy URLs in `ui/paywall/PaywallScreen.kt` must be real, not the
  `example.com` placeholders.
- The billing SDK's product catalog must have the current offering flagged active in the
  vendor dashboard — a release with no active offering shows an empty paywall.

## Access control / gating rules

- **Habit tracking**: unlimited, free
- **Active habits**: 5 free (`QuotaStore.DAILY_LIMIT`), unlimited on subscription
- **Analytics dashboard**: subscription only
- **Reminder scheduling**: 1 per habit free, unlimited on subscription
- **Data export**: subscription only
- Subscribers never consume quota — the counter is not incremented for them at all,
  rather than incremented and ignored.

## Localization

- **Mechanism**: `stringResource(R.string.key)` in Compose; `context.getString()`
  elsewhere. No user-facing literal ever appears inline.
- **Locale files**: `values/strings.xml`, `values-es/strings.xml`, `values-de/strings.xml`
  — all three are updated together or none is.
- **Content vs UI**: same mechanism for both; this project has no separate content layer.

## Review checklist additions

- 🔴 **Critical**: `DEBUG_ENTITLEMENT_OVERRIDE` false; no gating check bypassing
  `EntitlementPolicy`; no Room migration that drops a column without a migration test
- 🟠 **Architectural**: business logic out of composables; repositories stay thin;
  dependencies injected via Hilt, never constructed inline; `StreakCalculator` stays pure
- 🟡 **Correctness**: streak logic across DST transitions and timezone changes; quota
  reset at local midnight, not UTC; `StateFlow` collection scoped to the lifecycle
- 🟢 **Quality**: all three `strings.xml` updated; `LazyColumn` for unbounded lists;
  `minSdk 26` respected without an `@RequiresApi` escape hatch

## Anti-patterns

- `remember` holding state that belongs in the `ViewModel` — it dies on rotation
- Collecting a flow inside a composable without `collectAsStateWithLifecycle`
- `runBlocking` anywhere outside a test
- A new Hilt module for a single binding that fits an existing one
- Room queries returning entities straight to the UI, skipping the domain model

## Known risk areas

- `StreakCalculator` — recurring DST and timezone-change defects
- `QuotaStore` — day-boundary resets have regressed twice
- `BillingManager` — async purchase callbacks race with screen initialization
- Instrumented tests — flaky on cold emulator boots; re-run once before filing a bug

## Output language

- **Tracker issues and PR text**: English
- **Code, identifiers, commit messages**: English
- **Technical terms**: unchanged

## Harness settings

- **Local permission config**: `.claude/settings.local.json`
- **Habitual command prefixes** to preserve when generalizing: `./gradlew` (never bare
  `gradle`), and `JAVA_HOME=$JDK17_HOME` where it appears
