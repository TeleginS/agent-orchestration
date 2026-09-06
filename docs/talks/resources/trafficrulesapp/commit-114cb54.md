# Коммит 114cb54

> Снимок от 2026-09-06. [Оригинал в GitHub — нужен доступ к TrafficRulesApp](https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20).

SHA: `114cb54a883fcfed25f98e08c97d9d3ff9407e20`. Дата коммита: 2026-09-01T21:10:24Z.

## Сообщение

Fix QA findings on ProgressStore tests

Assert deltas, not absolute totals, on the five accumulation paths — the
old `> 0` form was a tautology whenever the store was non-zero on entry.

Isolate both new test classes in a per-test ephemeral UserDefaults suite
instead of clearing a hand-maintained key list on .standard, using the
existing defaults injection on ProgressStore, TestResultsStore and
MistakesStore.

Distinguish the two exitTest branches: practice saves no TestResult, the
normal branch saves exactly one.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

Ниже — изменения всех файлов этого коммита, полученные через GitHub API.

## TrafficTestAppTests/ProgressStoreTests.swift

```diff
@@ -17,20 +17,26 @@ final class ProgressStoreTests: XCTestCase {
     /// берётся из QuestionBank, здесь фиксируется только id.
     private let smallestThemeId = 3
 
+    private var suiteName: String!
+    private var defaults: UserDefaults!
+
     override func setUp() {
         super.setUp()
-        clearUserDefaults()
+        suiteName = "ProgressStoreTests.\(UUID().uuidString)"
+        defaults = UserDefaults(suiteName: suiteName)
     }
 
     override func tearDown() {
-        clearUserDefaults()
+        defaults.removePersistentDomain(forName: suiteName)
+        defaults = nil
+        suiteName = nil
         super.tearDown()
     }
 
     // MARK: - Start at zero
 
     func testFreshStoreIsZero() {
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
 
         XCTAssertEqual(store.solvedCount, 0)
         XCTAssertEqual(store.correctSubmissions, 0)
@@ -42,18 +48,18 @@ final class ProgressStoreTests: XCTestCase {
     // MARK: - Solved
 
     func testMarkSolvedIsIdempotent() {
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
 
         store.markSolved(42)
         store.markSolved(42)
 
         XCTAssertEqual(store.solvedCount, 1)
-        let stored = UserDefaults.standard.array(forKey: "progressSolvedQuestionIds") as? [Int]
+        let stored = defaults.array(forKey: "progressSolvedQuestionIds") as? [Int]
         XCTAssertEqual(stored?.count, 1)
     }
 
     func testSolvedSetOnlyGrows() {
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
 
         store.markSolved(1)
         store.markSolved(2)
@@ -65,15 +71,15 @@ final class ProgressStoreTests: XCTestCase {
     // MARK: - Accuracy
 
     func testAccuracyIsZeroWithoutSubmissions() {
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
 
         store.correctSubmissions = 3
 
         XCTAssertEqual(store.accuracyPercent, 0, "no division by zero on an empty history")
     }
 
     func testAccuracyRoundsRatherThanTruncates() {
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
 
         store.correctSubmissions = 5
         store.totalSubmissions = 5
@@ -91,15 +97,15 @@ final class ProgressStoreTests: XCTestCase {
     // MARK: - Persistence
 
     func testProgressPersistsAndReloads() {
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
 
         store.markSolved(7)
         store.markSolved(9)
         store.correctSubmissions = 4
         store.totalSubmissions = 6
         store.totalTestSeconds = 125
 
-        let reloaded = ProgressStore()
+        let reloaded = ProgressStore(defaults: defaults)
         XCTAssertEqual(reloaded.solvedQuestionIds, [7, 9])
         XCTAssertEqual(reloaded.correctSubmissions, 4)
         XCTAssertEqual(reloaded.totalSubmissions, 6)
@@ -109,7 +115,7 @@ final class ProgressStoreTests: XCTestCase {
     // MARK: - reset
 
     func testResetClearsEveryFieldInMemory() {
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
         store.markSolved(1)
         store.correctSubmissions = 4
         store.totalSubmissions = 6
@@ -124,16 +130,16 @@ final class ProgressStoreTests: XCTestCase {
     }
 
     func testResetClearsStorage() {
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
         store.markSolved(1)
         store.correctSubmissions = 4
         store.totalSubmissions = 6
         store.totalTestSeconds = 125
 
         store.reset()
 
-        XCTAssertNil(UserDefaults.standard.array(forKey: "progressSolvedQuestionIds"))
-        let reloaded = ProgressStore()
+        XCTAssertNil(defaults.array(forKey: "progressSolvedQuestionIds"))
+        let reloaded = ProgressStore(defaults: defaults)
         XCTAssertEqual(reloaded.solvedCount, 0)
         XCTAssertEqual(reloaded.correctSubmissions, 0)
         XCTAssertEqual(reloaded.totalSubmissions, 0)
@@ -153,15 +159,15 @@ final class ProgressStoreTests: XCTestCase {
 
     func testFreshStoreClosesNoTheme() {
         let bank = QuestionBank()
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
 
         XCTAssertEqual(store.closedThemesCount(in: bank), 0)
         XCTAssertFalse(store.isThemeClosed(smallestThemeId, in: bank))
     }
 
     func testThemeClosesWhenEveryQuestionIsSolved() {
         let bank = QuestionBank()
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
 
         bank.getQuestionIds(for: smallestThemeId).forEach(store.markSolved)
 
@@ -171,7 +177,7 @@ final class ProgressStoreTests: XCTestCase {
 
     func testThemeStaysOpenWithOneQuestionLeft() {
         let bank = QuestionBank()
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
 
         bank.getQuestionIds(for: smallestThemeId).dropLast().forEach(store.markSolved)
 
@@ -181,7 +187,7 @@ final class ProgressStoreTests: XCTestCase {
 
     func testUnknownThemeIsNotClosed() {
         let bank = QuestionBank()
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
 
         XCTAssertTrue(bank.getQuestionIds(for: 99).isEmpty)
         XCTAssertFalse(store.isThemeClosed(99, in: bank), "a theme with no questions must not count as Closed")
@@ -191,7 +197,7 @@ final class ProgressStoreTests: XCTestCase {
 
     func testThemeProgressGoesFromZeroToFull() {
         let bank = QuestionBank()
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
         let total = bank.getQuestionCount(for: smallestThemeId)
 
         let initial = store.themeProgress(themeId: smallestThemeId, in: bank)
@@ -207,7 +213,7 @@ final class ProgressStoreTests: XCTestCase {
 
     func testOtherThemesSolvedQuestionsDoNotCount() {
         let bank = QuestionBank()
-        let store = ProgressStore()
+        let store = ProgressStore(defaults: defaults)
         let otherThemeId = 0
 
         bank.getQuestionIds(for: otherThemeId).forEach(store.markSolved)
@@ -216,17 +222,4 @@ final class ProgressStoreTests: XCTestCase {
         XCTAssertEqual(progress.solved, 0)
         XCTAssertFalse(store.isThemeClosed(smallestThemeId, in: bank))
     }
-
-    // MARK: - Helpers
-
-    private func clearUserDefaults() {
-        [
-            "progressSolvedQuestionIds",
-            "progressCorrectSubmissions",
-            "progressTotalSubmissions",
-            "progressTotalTestSeconds"
-        ].forEach {
-            UserDefaults.standard.removeObject(forKey: $0)
-        }
-    }
 }
```

## TrafficTestAppTests/TestSessionProgressTests.swift

```diff
@@ -22,14 +22,17 @@ final class TestSessionProgressTests: XCTestCase {
     private var resultsStore: TestResultsStore!
     private var mistakesStore: MistakesStore!
     private var bank: QuestionBank!
+    private var suiteName: String!
+    private var defaults: UserDefaults!
 
     override func setUp() {
         super.setUp()
-        clearUserDefaults()
+        suiteName = "TestSessionProgressTests.\(UUID().uuidString)"
+        defaults = UserDefaults(suiteName: suiteName)
         bank = QuestionBank()
-        progressStore = ProgressStore()
-        resultsStore = TestResultsStore()
-        mistakesStore = MistakesStore()
+        progressStore = ProgressStore(defaults: defaults)
+        resultsStore = TestResultsStore(defaults: defaults)
+        mistakesStore = MistakesStore(defaults: defaults)
         session = TestSession(
             analytics: NoopAnalytics(),
             resultsStore: resultsStore,
@@ -44,7 +47,9 @@ final class TestSessionProgressTests: XCTestCase {
         resultsStore = nil
         progressStore = nil
         bank = nil
-        clearUserDefaults()
+        defaults.removePersistentDomain(forName: suiteName)
+        defaults = nil
+        suiteName = nil
         super.tearDown()
     }
 
@@ -53,46 +58,53 @@ final class TestSessionProgressTests: XCTestCase {
     func testCompleteTestAccumulatesTime() {
         session.start(.quick(from: bank))
         letSessionRun()
+        let before = progressStore.totalTestSeconds
 
         session.completeTest()
 
-        XCTAssertGreaterThan(progressStore.totalTestSeconds, 0)
+        XCTAssertGreaterThan(progressStore.totalTestSeconds, before)
     }
 
     func testTimeExpiredAccumulatesTime() {
         session.start(.timed(from: bank))
         letSessionRun()
+        let before = progressStore.totalTestSeconds
 
         session.timeExpired()
 
-        XCTAssertGreaterThan(progressStore.totalTestSeconds, 0)
+        XCTAssertGreaterThan(progressStore.totalTestSeconds, before)
     }
 
     func testCompletePracticeAccumulatesTime() {
         startPractice(questionCount: 2)
         letSessionRun()
+        let before = progressStore.totalTestSeconds
 
         session.completePractice()
 
-        XCTAssertGreaterThan(progressStore.totalTestSeconds, 0)
+        XCTAssertGreaterThan(progressStore.totalTestSeconds, before)
     }
 
     func testExitFromPracticeAccumulatesTime() {
         startPractice(questionCount: 2)
         letSessionRun()
+        let before = progressStore.totalTestSeconds
 
         session.exitTest()
 
-        XCTAssertGreaterThan(progressStore.totalTestSeconds, 0)
+        XCTAssertGreaterThan(progressStore.totalTestSeconds, before)
+        XCTAssertTrue(resultsStore.testResults.isEmpty, "выход из практики не сохраняет TestResult")
     }
 
     func testExitFromTestAccumulatesTime() {
         session.start(.quick(from: bank))
         letSessionRun()
+        let before = progressStore.totalTestSeconds
 
         session.exitTest()
 
-        XCTAssertGreaterThan(progressStore.totalTestSeconds, 0)
+        XCTAssertGreaterThan(progressStore.totalTestSeconds, before)
+        XCTAssertEqual(resultsStore.testResults.count, 1, "выход из теста сохраняет ровно один незавершённый результат")
     }
 
     func testTerminalPathOnUnstartedSessionAccumulatesNothing() {
@@ -223,7 +235,7 @@ final class TestSessionProgressTests: XCTestCase {
         XCTAssertEqual(progressStore.totalSubmissions, 0)
         XCTAssertEqual(progressStore.totalTestSeconds, 0)
 
-        let reloaded = ProgressStore()
+        let reloaded = ProgressStore(defaults: defaults)
         XCTAssertEqual(reloaded.solvedCount, 0)
         XCTAssertEqual(reloaded.correctSubmissions, 0)
         XCTAssertEqual(reloaded.totalSubmissions, 0)
@@ -279,19 +291,6 @@ final class TestSessionProgressTests: XCTestCase {
     private func letSessionRun() {
         RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.05))
     }
-
-    private func clearUserDefaults() {
-        [
-            "testResults",
-            "incorrectQuestions",
-            "progressSolvedQuestionIds",
-            "progressCorrectSubmissions",
-            "progressTotalSubmissions",
-            "progressTotalTestSeconds"
-        ].forEach {
-            UserDefaults.standard.removeObject(forKey: $0)
-        }
-    }
 }
 
 private final class NoopAnalytics: AnalyticsManaging {
```
