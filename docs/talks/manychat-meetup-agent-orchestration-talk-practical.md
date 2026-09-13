# Митап для Manychat — Практический маршрут агентной разработки

> **Четвёртый вариант:** короткая зацепка → одна карта четырёх ответственностей → PR #198 → стоимость → устройство репозитория сегодня → применимые контракты передачи работы.
>
> **Формат:** 14 основных страниц + 2 запасных = **16 страниц**. Нумерация страниц **1–16** одинакова в сценарии и английских заметках; дополнительных состояний 6a/6b нет; титул входит в нумерацию как страница 1. 18 минут содержания + 2 минуты запаса; вопросы после доклада, вне этих 20 минут.
>
> **Презентация:** [PowerPoint](decks/manychat-practical-workflow-en.pptx) · [PDF](decks/manychat-practical-workflow-en.pdf).
>
> **Язык:** английские надписи и полный текст речи; русские пояснения для подготовки. [Английские заметки выступающего](decks/manychat-practical-workflow-en-speaker-notes.md).

**Главная мысль:** процесс определяется тем, какие результаты роли передают друг другу. Реальный прогон показывает пользу повторных проверок и их стоимость; нынешняя структура репозитория помогает разделить процедуры, контекст проекта и запуск.

## Структура и тайминг

| Страница | Интервал | Заголовок |
|---|---|---|
| 1 | 0:00–0:15 | Agent Orchestration |
| 2 | 0:15–1:00 | 157 tests passed. QA blocked the PR. |
| 3 | 1:00–2:00 | An agent is a loop |
| 4 | 2:00–3:30 | One map, four responsibilities |
| 5 | 3:30–5:00 | Changed code needs fresh evidence |
| 6 | 5:00–6:30 | 32 new tests. One delivery route. |
| 7 | 6:30–7:30 | Review improved the patch |
| 8 | 7:30–9:00 | Green tests. Weak evidence. |
| 9 | 9:00–11:00 | Prove the change, isolate the state |
| 10 | 11:00–12:30 | Fix → review → QA |
| 11 | 12:30–14:00 | The observed cost |
| 12 | 14:00–15:00 | How the repository works today |
| 13 | 15:00–17:00 | Define what each stage hands over |
| 14 | 17:00–18:00 | Three things to take back |
| 15 | Backup — questions only | Full workflow and transition conditions |
| 16 | Backup — questions only | The zero-baseline caveat |

Основная английская речь: около **1948 слов** без запасных страниц, источников и указаний показа. Паузам для чтения фрагментов и движения по графу оставлено место внутри интервалов. 18:00–20:00 не заполнять дополнительной темой заранее.

**Контрольные точки:** на 2:00 открыта карта; на 5:00 начинается PR #198; на 9:00 показан механизм; на 12:30 кейс закончен; на 14:00 отделено нынешнее устройство репозитория; на 17:00 начинается заключение.

## Правила показа

- Четыре центральные роли всегда стоят в одинаковых местах: Plan → Develop → Review → QA. Orchestrator и профиль показаны отдельно, не как дополнительные последовательные шаги. Полные 11 шагов — запасная страница 15.
- На страницах 4–5 карта подписана `Current documented workflow`; страницы 6–10 посвящены сохранённой последовательности review и QA в PR #198. Текущий граф не выдаётся за полный исторический trace.
- Скриншоты обрезать до читаемого отчёта и вердикта, оставляя идентификатор. Серый означает контекст, бирюзовый текущий этап, янтарный возврат, зелёный явный успешный вердикт. Дублировать цвет словами.
- На странице 7 Review 1 — conditional approval. На странице 9 число 500 — illustrative example. На странице 9 `before = 0` показан и произносится в основном докладе; запасная страница только раскрывает подробности.
- Страница 12 показывает новое устройство репозитория. Не называть main-conversation orchestration впервые изобретённой после этого кейса: основная беседа исполняла эту роль уже в измеренном запуске. Изменение состоит в нынешнем общем контракте и упаковке, а не в доказанном приросте качества.
- Основной доклад заканчивается страницей 14. Запасные страницы не показывать автоматически после благодарности.

## Страница 1. Agent Orchestration — 0:00–0:15

**На экране и показ:** Заголовок, Sergei Telegin и кликабельная ссылка github.com/TeleginS/agent-orchestration. Допустимый короткий подзаголовок: Checks, handoffs and shared skills.

### Что сказать

Hi, I’m Sergei Telegin. I’ll show you one real task from my AI development workflow: what the agents checked, why the work came back, and what those extra passes cost.

## Страница 2. 157 tests passed. QA blocked the PR. — 0:15–1:00

**На экране и показ:** Два крупных фрагмента одного QA-отчёта: 157 passed и BLOCKED. Короткая подпись TrafficRulesApp · PR #198. Механизм пока не раскрывать. Кадр [07](screenshots/07-pr198-qa-blocked-tests.jpg).

**Источники:** S3, S5.

### Что сказать

TrafficRulesApp is my personal iOS app for the Spanish driving theory exam. In this task, agents were adding tests. The reviewer approved the change. All 157 tests passed. QA still blocked the pull request.

The problem was in what some of those tests could prove. We’ll follow the task through one map, see the finding and its repair, and look at the cost. The question to keep in mind is: what evidence should one stage give the next?

## Страница 3. An agent is a loop — 1:00–2:00

**На экране и показ:** Одна простая схема: Context → Model → Tool call → Tool result → Model. Назначение harness поясняется подписью под петлёй. Не добавлять обзор SDK, MCP или продуктов.

**Источники:** S11.

### Что сказать

An agent works through a loop. The model receives context and chooses an action. A tool reads a file, edits code, or runs a test. The execution environment, often called a harness, performs that action and returns the result.

The model can then choose another action. A developer might inspect code, make a change, read a test failure and try again.

For this talk, that is enough theory. The next question is how several such loops work together. Someone must provide the task and decide what result allows the next role to begin. My orchestrator coordinates that through written instructions. The diagram we’ll use describes those instructions; it does not enforce them.

## Страница 4. One map, four responsibilities — 2:00–3:30

**На экране и показ:** Простая горизонтальная карта: Plan → Develop → Review → QA. Orchestrator — отдельно под маршрутом; Project profile — общий текстовый контекст рядом. Подписи результатов: Criteria / Patch + checks / Findings or approval / Evidence + verdict. Связи между этапами серые. Над картой Current documented workflow. Полные шаги 0–10 находятся на запасной странице 15.

**Источники:** S10.

### Что сказать

Here is the map we’ll keep using. Four responsibilities: planning, implementation, review and QA.

The planner turns the request into acceptance criteria and work items. The developer implements those requirements and supplies the change and its checks. The reviewer examines the actual diff against the task. QA runs the suite and checks the acceptance criteria and relevant behavior.

These responsibilities overlap. Separate contexts do not make the agents statistically independent: they can share a model and repeat an assumption. The useful distinction is the additional check each role is asked to perform.

The orchestrator coordinates the whole route. It carries the task, the project profile and previous results between stages. It also handles preparation and completion: clarification, branch hygiene, artifact review and issue cleanup. We’ll keep those details on a backup slide.

Notice the labels between the boxes. A stage hands over something another stage can inspect. A message saying “done” is not enough to explain why the task should move forward.

## Страница 5. Changed code needs fresh evidence — 3:30–5:00

**На экране и показ:** Прежняя карта с выделенными Develop, Review и QA. Под ней два текстовых маршрута: Review findings → Develop → Review и QA findings → Develop → Review → QA. Справа датированная вставка: 26 Aug 2026 · Rule 11. Подпись Loop limits: 3 iterations, then escalate. Не вводить отдельный слайд про PR #143.

**Источники:** S1, S2, S10.

### Что сказать

There are two ways back. Review findings can send the patch to the developer. QA findings can also send it back, but a QA fix goes through review before QA tests it again.

The reason is simple: the fix changes the code. Approval of an earlier version does not cover that change automatically.

There is a short history behind this rule. In July, QA found double-counted session time after a reviewer had approved PR 143. On August 26, a versioned change explicitly added review of QA fixes to the instructions: rule eleven.

That establishes a documented process change. It does not establish that the July bug was its only cause, or reconstruct every setting in the old sessions.

Today, both repair loops have a three-iteration limit, then escalation with the remaining blockers. Those limits and transitions are instructions the orchestrator must follow. Now we can look at a later run where the additional review is visible in the reports.

## Страница 6. 32 new tests. One delivery route. — 5:00–6:30

**На экране и показ:** Прежняя карта, 32 new tests, 125 → 157 и scope: ProgressStore/session tests, 0 production-code changes. Подпись PR #198 · ProgressStore and TestSession coverage. Не раскрашивать всю подготовку и cleanup как подтверждённые одним screenshot.

**Источники:** S3, S8, S9.

### Что сказать

The task in PR 198 was to add unit tests for ProgressStore and for recording progress when a test session ends. That included the protection against counting time twice after completion, connecting this work to the earlier bug.

The final change contained 32 new tests. The suite grew from 125 to 157. It also added a project profile, with commands and project-specific constraints. Application code did not need to change.

We are looking at saved reports and screenshots from that run, not a new test session performed for this presentation. The map is our guide to the intended route; the reports show the visits we can actually trace.

Keep the task’s goal in mind: useful tests of existing behavior. Success required more than increasing the test count. A test needed to fail when the behavior it claimed to protect was broken. That is where both review and QA had work to do.

## Страница 7. Review improved the patch — 6:30–7:30

**На экране и показ:** Одна страница с двумя короткими фрагментами: Review 1: conditional approval → Developer follow-up → Review 2: APPROVAL. Использовать [05b](screenshots/05b-pr198-review1-verdict.jpg) и [06](screenshots/06-pr198-review2-approved.jpg). Не подписывать первый review как BLOCKED. Сохранить прежнее положение reviewer на карте.

**Источники:** S4.

### Что сказать

The first review gave conditional approval with quality findings. It did not report critical blockers. Two findings were worth a short follow-up: a missing integration check for an important progress rule, and a check connecting the expected theme count to the bundled data.

The developer addressed them. The second review approved the patch after examining those changes and running the suite.

That was useful work. The point of the next finding is not that review did nothing. It improved the patch, and QA then found a different weakness.

On our map, we have visited the same reviewer twice. Each visit concerns a different state of the code. The second approval is what takes this task into QA.

## Страница 8. Green tests. Weak evidence. — 7:30–9:00

**На экране и показ:** Вернуть [07](screenshots/07-pr198-qa-blocked-tests.jpg), рядом краткие находки из [08](screenshots/08-pr198-qa-findings.jpg): Assertion checks total / Shared starting state. Третью находку обозначить одной строкой Exit branches, без отдельного разбора. Подсветить QA: findings на знакомой карте.

**Источники:** S5.

### Что сказать

The QA report records successful runs on two simulator destinations, including a full run with parallel testing disabled. It also says BLOCKED, with three in-scope findings.

Two findings belong together. Five tests asserted that accumulated session time was greater than zero. The tests also used shared storage and manually cleared a list of keys.

The task required each terminal action to contribute time. A positive total did not necessarily show that this particular action had contributed anything. Old values could make the assertion pass.

The third finding concerned distinguishing two exit branches. We’ll leave its details for questions.

This does not make all 157 tests useless. QA specifically identified the affected checks and acknowledged checks that were sound. The useful distinction is between a test executing successfully and the test establishing the behavior its name and acceptance criterion promise. Let’s make that distinction concrete.

## Страница 9. Prove the change, isolate the state — 9:00–11:00

**На экране и показ:** Крупно учебная иллюстрация: Before 500s → After 500s; after > 0: PASS; after > before: FAIL. Обязательно Illustrative example. Ниже две части исправления: Compare before/after + One temporary store per test. Удерживать рисунок во время объяснения. Видимая оговорка: Repaired isolated fixture: before = 0. Для технических вопросов реальный diff на странице 16.

**Источники:** S5, S6.

### Что сказать

Imagine the store contains 500 seconds before the call. The call adds nothing. Afterward, the store still contains 500 seconds.

“Is the total greater than zero?” passes. “Did the total increase after this call?” fails. Pause on those two questions: they establish different things. Five hundred is an illustrative value, not a measurement from this QA run.

Why could there be an old value? These tests used UserDefaults.standard, shared application storage. They cleared a known list of keys, but that did not give each test control over every possible source of starting state. The saved findings describe contamination encountered during implementation.

The repair had two parts. Each test received its own temporary storage suite through injection points already present in the application. The assertions captured the value just before the terminal call and checked for an increase afterward.

Isolation controls the starting state. The comparison expresses the contribution of the action under test. Both matter to the explanation; we should examine the fixture and the assertion together.

There is a qualification: in the repaired isolated fixture, the starting value is zero. The two comparisons are numerically equivalent there. We should not credit the whole improvement to the new assertion alone.

The developer made these changes in the test files without changing production code. But the work is not finished when the developer reports the fix. We have changed the patch, so we need fresh review evidence before another QA verdict.

## Страница 10. Fix → review → QA — 11:00–12:30

**На экране и показ:** Три этапа Fix → Review → QA, с подписью Fix 114cb54. Рядом два обрезанных фрагмента: [Review 3: APPROVAL](screenshots/10-pr198-review3-gate.jpg) и [QA Pass 2: GREEN](screenshots/12-pr198-qa-green.jpg). Крупно: 4 full runs / 157 passed in each. Оговорка о before = 0 остаётся в речи и на предыдущей странице. Внизу Open at capture · 6 Sep 2026. Полный caveat — страница 16.

**Источники:** S6, S7.

### Что сказать

The developer pushed the fixes to the same pull request. Review iteration three explicitly invoked rule eleven and checked the QA fixes before the work returned to QA.

The reviewer approved and explicitly made the qualification we just discussed: in the isolated fixture, “before” is zero. The explanation must account for both changes. The delta form expresses the requirement; isolation removes the shared-state problem.

That is useful scrutiny of both the patch and the explanation of what it proves.

QA then returned GREEN. Its report records four full runs with 157 passing tests each, including a deliberately polluted shared store to test the isolation.

At the September 6 screenshot capture, the PR was still open. We have a recorded approval and green QA, not evidence of a merge. Completion work still follows on the map. Now let’s attach costs to the visits we just saw.

## Страница 11. The observed cost — 12:30–14:00

**На экране и показ:** Три показателя: 9 subagent launches; 1,097,667 subagent tokens; ≈1h 31m summed stage wall time. Разбивка посещений: Planner 1 / Developer 3 / Reviewer 3 / QA 2. Источник [13](screenshots/13-run-cost-measured.jpg). Видимая сноска Orchestrator usage excluded · No matched single-agent baseline. Не добавлять долларовые оценки или 20-run выборку.

**Источники:** S8.

### Что сказать

The saved report gives us nine subagent launches and 1,097,667 subagent tokens. The recorded stage wall times add up to about one hour and thirty-one minutes. That is the sum of those stage durations, not a separate measurement of my total time on the task.

The visits explain the count: one planner, three developer passes, three reviews and two QA passes. Review used slightly more tokens than implementation in this run.

Orchestrator tokens were mixed into the main conversation and estimated separately, so they are excluded here. I’m also keeping estimated dollar costs off this slide.

For 32 new tests, these are substantial coordination costs. We saw useful findings, but there was no matched single-agent run. This example does not establish a general quality or cost advantage.

What I would measure next is confirmed findings, missed defects and human intervention time, alongside tokens and duration. That would help decide which checks are worth retaining for this kind of task.

## Страница 12. How the repository works today — 14:00–15:00

**На экране и показ:** Две колонки: Canonical skills и Thin host adapters. Под ними Main conversation и Shared context: Project profile + explicitly read role memory. Показан путь skills/<role>/SKILL.md. Видимая оговорка: влияние новой упаковки на стоимость и качество не измерено.

**Источники:** S10.

### Что сказать

The repository has since changed its packaging. The reusable procedures now live in canonical skills. The orchestrator stays in the main conversation, where it can clarify requirements, and delegates the stages to separate agents.

Thin host adapters provide launch behavior and model configuration. Model and reasoning choices can be configured per role where the host supports them; otherwise its defaults apply. A skill contains instructions. Loading it alone does not create an independent agent.

The project profile supplies commands and constraints. Each role explicitly reads relevant shared project memory under common rules.

These changes make the responsibilities of the files clearer. The historical run we just examined predates this packaging. I am not claiming measured improvements in cost or quality from the migration.

## Страница 13. Define what each stage hands over — 15:00–17:00

**На экране и показ:** Одна таблица из четырёх строк: Planner → criteria, dependencies + linked issues; Developer → PR/diff + check results; Reviewer → prioritized findings or APPROVAL; QA → test results, classified bugs + GREEN/BLOCKED. Версию изменения, контекст и ограничения объяснить устно. Под таблицей — назначение orchestrator и напоминание о локальных артефактах в dry-run. Никаких заявлений о существующем автоматическом контроллере.

**Источники:** S10.

### Что сказать

Here is the part you can apply without copying my entire workflow: define what each stage hands over.

For the planner, I want criteria someone can actually check, dependencies and linked work items with a clear scope. The developer needs those criteria, project context and execution constraints. It returns a pull request and diff, the version it changed, and what it built or tested.

The reviewer needs the actual diff and requirements, not only the developer’s summary. Its report should identify the reviewed version, prioritized findings or explicit approval. After a fix, the next reviewer also needs the previous findings so it can establish what changed.

QA needs the same requirements and current change. It returns evidence for acceptance criteria, test results, classified bugs and an explicit GREEN or BLOCKED verdict. Calling a bug pre-existing needs evidence from the base version; uncertainty is not a reason to mark the work green.

The orchestrator carries these results onward while preserving the task’s constraints. That includes the branch, ownership, mode and any limits on writes. In a dry run, local plans, diffs and findings replace tracker and PR artifacts.

Today this is largely an instruction contract. A future controller could check that required artifacts exist and refer to the current version. It could reject stale approval. It would still not prove that the review itself was correct.

## Страница 14. Three things to take back — 17:00–18:00

**На экране и показ:** Три коротких строки: Define the output of each stage / Pass artifacts that others can verify / Repeat verification after code changes. Крупная кликабельная ссылка github.com/TeleginS/agent-orchestration. Последняя страница основного выступления; 18:00–20:00 остаётся запасом.

**Источники:** S10.

### Что сказать

Three things to take back.

First, define the output of each stage. Say what it must deliver and what permits the next stage to begin.

Second, pass artifacts that others can verify: requirements, the actual diff, findings and test results. Give the next role something it can inspect.

Third, repeat verification after code changes. A fix needs evidence for the new version, including review before fresh QA.

Start with one type of task and inspect the handoffs in real runs. The repository includes the skills, profiles, workflow and saved examples we discussed. Thank you. I’m happy to take questions after the talk.

## Страница 15. Full workflow and transition conditions — Backup — questions only

**На экране и показ:** Карта всех шагов 0–10 по PIPELINE-GRAPH.md. Между рядами обозначены возвраты после review/QA и переход QA green к artifact checks. Внизу — clarification, лимиты и optional settings. Классификацию pre-existing и состояние issues до merge объяснить устно. Никакой стрелки GREEN → merged. Эта страница не входит в 18 минут.

**Источники:** S10.

### Что сказать

This is the complete documented workflow. The main conversation first resolves project context and any missing product decisions. Planning establishes the work, branch preparation protects unrelated changes, and the developer produces the patch.

The review loop permits up to three completed verdicts, counting the initial review. The QA repair loop counts each developer fix and its review as an iteration, even if review blocks a return to QA. Moving between roles does not reset that counter.

A verified pre-existing bug is recorded as separate work and does not block this change. Its classification needs comparable base-version evidence. An unconfirmed origin remains a blocker until classified.

After green QA, artifact review, issue cleanup and any applicable settings work still happen. Unmerged work keeps its issue references and stays open. In dry-run mode, planning and findings stay local and the workflow writes neither to the tracker nor the remote.

The diagram documents these transitions. It is not an executable controller and does not provide automatic recovery.

## Страница 16. The zero-baseline caveat — Backup — questions only

**На экране и показ:** Реальный [diff](screenshots/09b-pr198-delta-assertions-diff.jpg) и читаемый фрагмент [reviewer caveat](screenshots/11-pr198-review3-proof-caveat.jpg). Справа: before = 0; after > 0 / after > before; Numerically equivalent for these five tests. Ссылки на #199, #200, #201 — в источниках. Не смешивать mutation example с окончательным committed fixture.

**Источники:** S5, S6, S7.

### Что сказать

The dirty-store example explains the original risk. If the store was already positive, an assertion on the absolute total could pass when the terminal action added nothing.

The repair also changed the fixture. In the committed isolated tests, the initial value is zero. Therefore greater than zero and greater than the prior value are numerically equivalent in that fixture. The reviewer explicitly pointed this out.

The delta form states the intended contribution and remains useful if a future fixture starts with seeded progress. Isolation removes dependence on shared old values. Both changes are reasonable, but the mutation demonstration with a dirty store should not be presented as the starting state of the repaired suite.

The third finding added checks distinguishing the two exit branches. If you want the full discussion, the saved issues and the final review and QA reports contain the details.

## Репетиция

Проверить весь основной маршрут с изображениями и движением указателя. Не зачитывать полные комментарии. На странице 9 выдержать паузу после двух сравнений, чтобы аудитория сама увидела различие.

Если к пятой минуте кейс ещё не открыт, сократить историческую вставку на странице 5 и перечисление housekeeping на странице 4. Если к 12:30 не завершён кейс, убрать дополнительную детализацию первого review. Сохранить механизм загрязнения, две части исправления, оговорку о нуле и review перед повторным QA.

Нынешнюю архитектуру показать за минуту через назначение файлов; команды установки и списки моделей оставить для разговора после доклада. На странице 13 дать аудитории время прочитать четыре строки handoff-таблицы.

Материалы доступны локально в [каталоге скриншотов](screenshots/README.md). Нужны только выбранные кадры; полные GitHub-страницы не обязательны для выступления и могут требовать доступ к приватному репозиторию.

## Источники и границы выводов

История PR основана на локальных копиях и скриншотах от 6 сентября 2026 года. Это сохранённые отчёты агентов, а не заново воспроизведённая тестовая сессия или полный runtime trace. На дату съёмки PR #198 был открыт; перед выступлением статус можно проверить отдельно, но основной текст фиксирует именно исторический статус.

- **S1 — Ранний кейс:** [PR #143](resources/trafficrulesapp/pr-143.md), [QA-баг #144](resources/trafficrulesapp/issue-144.md).
- **S2 — Датированное изменение:** [коммит 47fe491 от 26 августа 2026](resources/trafficrulesapp/commit-47fe491.md). Подтверждает добавление review после QA-фиксов, но не единственную причину решения и не полный контекст старых сессий.
- **S3 — Основной кейс:** [PR #198](resources/trafficrulesapp/pr-198.md).
- **S4 — Ранние ревью:** [Review 1](resources/trafficrulesapp/pr-198.md#issuecomment-5500796064), [Review 2](resources/trafficrulesapp/pr-198.md#issuecomment-5500799535). Первый вердикт — conditional approval с quality findings, без critical/architectural/bug blockers.
- **S5 — QA findings:** [QA Pass 1](resources/trafficrulesapp/pr-198.md#issuecomment-5500803440), [assertions #199](resources/trafficrulesapp/issue-199.md), [изоляция #200](resources/trafficrulesapp/issue-200.md), [ветви выхода #201](resources/trafficrulesapp/issue-201.md).
- **S6 — Исправление и проверка:** [коммит 114cb54](resources/trafficrulesapp/commit-114cb54.md), [Review 3](resources/trafficrulesapp/pr-198.md#issuecomment-5500807469). Сохранить оговорку `before == 0`: эффект нельзя целиком приписать одной замене assertion.
- **S7 — Повторный QA:** [QA Pass 2](resources/trafficrulesapp/pr-198.md#issuecomment-5500811713), включая четыре полных прогона по 157 тестов и deliberate shared-store contamination.
- **S8 — Затраты именно этого прогона:** [измерения подагентов](../../examples/run-progress-store-tests/README.md#measured-subagent-tokens). Девять длительностей дают 1h 30m 55s, округлённо 1h 31m. Это сумма stage wall times; затраты основной беседы отдельно не измерены. Токены подагентов — 1,097,667. Не соединять их с 20 историческими прогонами или оценкой счёта провайдера.
- **S9 — Профиль:** [коммит 9a26da8](resources/trafficrulesapp/commit-9a26da8.md).
- **S10 — Текущий репозиторий:** [README](../../README.md), [PIPELINE.md](../../PIPELINE.md), [граф](../../PIPELINE-GRAPH.md), [канонические skills](../../skills/README.md), [адаптеры](../../adapters/README.md), [правила памяти](../../memory/RULES.md), [Codex model configuration](../../adapters/codex/README.md#models-and-runtime-capabilities). Это нынешнее устройство, а не конфигурация измеренного исторического запуска. Новые launcher-механизмы не объявляются end-to-end проверенными этим кейсом.
- **S11 — Минимальные определения:** [сохранённое интервью](resources/transcripts/ai-agents-harness.md) и [предыдущий walkthrough](manychat-meetup-agent-orchestration-talk-graph-walkthrough.md). Сценарий не вводит новых утверждений о конкретных SDK, API или доступности моделей.

Цена и качество multi-agent процесса не сравниваются с одним агентом: сопоставимого контрольного запуска нет. Отдельные агенты не означают статистическую независимость. Программная проверка переходов и актуальности approval — предложенное развитие, а не существующая возможность набора Markdown-файлов.
