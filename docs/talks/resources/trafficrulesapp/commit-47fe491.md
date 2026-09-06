# Коммит 47fe491

> Снимок от 2026-09-06. [Оригинал в GitHub — нужен доступ к TrafficRulesApp](https://github.com/TeleginS/TrafficRulesApp/commit/47fe4917052c82e7181e9de5321511ed8194c11c).

SHA: `47fe4917052c82e7181e9de5321511ed8194c11c`. Дата коммита: 2026-08-26T20:23:20Z.

## Сообщение

Синхронизированы промпты агентов с кодом: актуальный гейтинг и менеджеры, правило 11, тест-гейт QA, DSH-ранбук

Сохранён фрагмент изменения инструкций оркестратора, на который ссылается доклад. Остальные файлы этого коммита здесь не дублируются.

## .claude/agents/ai-orchestrator.md

```diff
@@ -45,9 +45,10 @@ Do NOT proceed to Step 2 until planning is complete.
 
 ### Step 2 — Branch Creation
 Before development starts, create a feature branch from master:
-1. Ensure you are on master and it is up to date: `git checkout master && git pull origin master`
+0. Check the working tree first: `git status --porcelain`. If tracked files are modified by parallel sessions (e.g. `.claude/settings.local.json`), do NOT force anything — report to the user and resolve explicitly (commit/stash/ignore by path). Never carry unrelated changes into the feature branch/PR.
+1. Ensure you are on master and it is up to date: `git checkout master && git pull origin master`. If the pull fails due to local modifications, STOP and report instead of resolving silently.
 2. Derive a branch name from the task (e.g. `feature/add-statistics-screen` or `fix/timer-not-stopping`). Use `feature/` prefix for new functionality and `fix/` prefix for bug fixes.
-3. Create and push the branch: `git checkout -b <branch-name> && git push -u origin <branch-name>`
+3. Create and push the branch: `git checkout -b <branch-name> && git push -u origin <branch-name>`. Pushing a branch that has no unique commits yet is fine — it will point at master's commit until the developer pushes the first change.
 
 Collect the branch name and pass it to ios-developer in Step 3.
 Do NOT proceed to Step 3 until the branch exists on the remote.
@@ -102,9 +103,15 @@ For **in-scope bugs only**:
   b. Launch `.claude/agents/ios-developer.md` again, providing:
      - The GitHub Issue numbers/URLs of the bugs to fix (agent must `gh issue view <number>` each one)
      - The existing PR number (push fixes to the same branch, do NOT create a new PR)
-     - Instruction to close each fixed Issue via `gh issue close <number>`
-  c. After the developer confirms fixes, launch `.claude/agents/qa-bug-tracker.md` again to re-test.
-  d. Repeat this loop until qa-bug-tracker confirms all in-scope bug Issues are closed and no new ones are opened.
+     - Instruction NOT to close the bug Issues while the PR is unmerged; instead add a short comment to each fixed Issue such as `Fixed in PR #NN; verified after merge before closing.`
+  c. After the developer confirms fixes, launch `.claude/agents/ios-code-reviewer.md` again with:
+     - The PR number/URL
+     - The in-scope bug Issue numbers/URLs
+     - The developer's fix summary
+     - Instruction to review only the QA bug fixes plus any directly affected code, and to issue ✅ APPROVAL before QA re-test.
+  d. If ios-code-reviewer finds blocking issues in the QA bug fixes, loop back to Step 6.b with the review findings and the same existing PR.
+  e. Only after ios-code-reviewer approves the QA bug fixes, launch `.claude/agents/qa-bug-tracker.md` again to re-test.
+  f. Repeat this loop until qa-bug-tracker confirms all in-scope bug Issues are fixed in the PR, no new in-scope bug Issues are opened, and any fixed bug Issues have PR comments but remain open until merge unless the user explicitly instructs otherwise.
 
 ### Step 7 — Review Stray Artifacts
 Once QA is green, inspect whether the working tree contains uncommitted artifacts that accumulated during the run but were never committed by ios-developer.
@@ -127,7 +134,7 @@ Once QA is green and stray artifacts are reviewed, update the GitHub Issues that
 
 **Comment on all open Issues created by THIS task's pipeline:**
 - The Epic/Overview Issue and all child planning Issues from task-planner (Step 1).
-- All resolved in-scope bug Issues from qa-bug-tracker (these are normally already closed in Step 6 — verify and comment if any slipped through).
+- All resolved in-scope bug Issues from qa-bug-tracker (these should remain open until merge unless explicitly instructed otherwise; verify each has a PR/fix comment).
 
 Add a short comment referencing the PR number (e.g. `gh issue comment 27 --body "Implemented in PR #36; close after merge."`). Close issues only when the orchestrator is explicitly told the PR has merged, or when the task is a non-PR task whose work is already complete on the target branch.
 
@@ -175,6 +182,7 @@ Report to the user:
 8. **Do not close unmerged work by default (Step 8).** After QA is green, comment on this pipeline's Issues with the PR reference. Close them only after merge confirmation or when no PR is involved and the work is already complete on the target branch. NEVER close deliberate backlog/follow-up Issues or `pre-existing`-labelled Issues.
 9. **Never blanket-commit artifacts (Step 7).** Commit only durable design docs or agent memory that clearly belongs in the PR. Never commit scratch files; report anything uncertain.
 10. **Use design artifacts when they exist; require them only for ambiguous product/design work.** If a small operational task lacks `CONTEXT.md`/ADR coverage, proceed and note that no design artifacts applied.
+11. **Every code change after QA begins must pass code review before QA can be considered green.** QA bug fixes go through ios-code-reviewer before qa-bug-tracker re-tests them.
 
 ## Communication Style
 
@@ -187,7 +195,7 @@ Report to the user:
 
 This project is **TrafficTestApp (RUS Autoescuela DGT Test)** — an iOS app for Spanish driving exam preparation with Russian localization.
 - Platform: iOS 15.6+, Swift 5.5+, SwiftUI, MVVM architecture
-- Key managers: SubscriptionManager, QuestionBank, TestManager, DailyAttemptsManager, ThemeAttemptsManager, LocalizationManager, LanguageSettingsManager, SettingsManager, ThemesManager
+- Key managers: SubscriptionManager, QuestionBank, TestSession, DailyQuotaStore, AccessPolicy, MistakesStore, ProgressStore, TestResultsStore, SettingsManager (ViewModels/); LanguageSettingsManager, LocalizationManager, ThemesManager (Models/)
 - Premium gating via RevenueCat (entitlement: `premium`)
 - Localization: UI strings in `.lproj/Localizable.strings`, question content in `questions.json`
 - All state persisted via UserDefaults
```
