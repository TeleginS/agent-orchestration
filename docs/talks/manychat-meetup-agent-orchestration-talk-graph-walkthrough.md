# Митап для Manychat — Пайплайн на карте: правила, возвраты и реальный прогон

> **Третий вариант:** общий граф пайплайна → приближение к циклу проверок → фактический маршрут PR #198 со скриншотами.

> **Презентация на английском:** [PowerPoint](decks/manychat-graph-walkthrough-en.pptx) · [PDF](decks/manychat-graph-walkthrough-en.pdf) · [Заметки выступающего](decks/manychat-graph-walkthrough-en-speaker-notes.md).

> **Формат:** 18 минут содержания, включая представление, и 2 минуты запаса. Вопросы после доклада, вне лимита 20 минут. Текст выступления и надписи слайдов — на английском. Режиссёрские пояснения — на русском.

> **Статус:** презентация собрана. Всего 17 страниц: титул, 10 содержательных слайдов с отдельными кадрами 6a–6c и 8a–8c, затем два запасных слайда. Основной доклад заканчивается на слайде 10, странице 15 PDF. Тайминги плановые, фактическую длительность нужно проверить вслух с переключениями.

**Главная мысль:** роли становятся процессом через условия передачи работы. Реальный прогон показывает, какие проверки принесли пользу, где понадобился возврат и сколько стоила координация.

Связанные варианты: [подробный кейс](manychat-meetup-agent-orchestration-talk.md) и [теория и практика](manychat-meetup-agent-orchestration-talk-theory-and-practice.md). Новый сценарий использует те же [скриншоты](screenshots/README.md) и [сохранённые источники](resources/trafficrulesapp/README.md).

## Структура и тайминг

Ненумерованный титульный слайд, 10 содержательных и 2 запасных слайда для вопросов. Основной доклад заканчивается на содержательном слайде 10. Запасные слайды не входят в 18 минут содержания.

| Интервал | Этап рассказа | Слайд | Что видит аудитория |
|---|---|---|---|
| 0:00–0:15 | Представление | Титул | Agent Orchestration, Sergei Telegin, GitHub |
| 0:15–1:00 | Зацепка | 1 | 157 passed и QA BLOCKED из одного отчёта |
| 1:00–2:30 | Устройство агента | 2 | Модель, инструменты, harness и передача результата |
| 2:30–4:30 | Общая карта | 3 | Все шаги 0–10, четыре области процесса |
| 4:30–6:00 | Приближение | 4 | Циклы review и QA, условия переходов и остановок |
| 6:00–7:30 | Подтверждённое изменение правил | 5 | PR #143, баг #144 и коммит с правилом 11 |
| 7:30–9:30 | Маршрут PR #198 до блокировки | 6 | Review 1, исправление, review 2, QA Pass 1 |
| 9:30–12:00 | Механизм находки | 7 | Старое состояние, слабый assertion, изоляция |
| 12:00–14:00 | Маршрут после блокировки | 8 | QA fix, review 3 и QA Pass 2 на той же карте |
| 14:00–16:00 | Стоимость маршрута | 9 | 9 запусков, время и токены того же прогона |
| 16:00–18:00 | Вывод и следующий шаг | 10 | Результат каждого этапа, запись запуска, GitHub |
| 18:00–20:00 | Запас | — | Паузы, пояснения, переключения |

**Контрольные точки:** на 2:30 открыта общая карта; на 7:30 начинается PR #198; на 12:00 понятен механизм находки; на 14:00 кейс завершён; на 16:00 начинается заключение.

## Как граф проходит через рассказ

Основа — [PIPELINE-GRAPH.md](../../PIPELINE-GRAPH.md), смысл переходов сверять с [PIPELINE.md](../../PIPELINE.md). Версия карты при подготовке сценария: [`db77602`](https://github.com/TeleginS/agent-orchestration/blob/db77602/PIPELINE-GRAPH.md).

Слайд 3 показывает все этапы, но сокращает подписи. Слайд 4 увеличивает центральную область. Слайды 6 и 8 сохраняют расположение узлов увеличенного фрагмента и подсвечивают подтверждённые события PR #198. Превращать каждый проход review в новый узел не нужно: повторные посещения видны по подписям проходов и подсветке.

| Область карты | Номера шагов | Английские подписи на общей карте |
|---|---|---|
| Preparation | 0, 1, 2 | Design check; Plan and issues; Branch setup |
| Implementation | 3 | Develop and open PR |
| Verification | 4, 5, 6 | Review loop; QA; Fix, review and retest |
| Completion | 7, 8, 9, 10 | Artifact check; Issue cleanup; Settings (optional); Final report |

Это четыре визуальные области, а не четыре новых состояния. Orchestrator управляет передачей работы между этапами и не изображается как ещё один последовательный шаг. Профиль проекта — общий источник контекста, а не дополнительный агент.

На общей карте сохранить ответвление к уточнению дизайна и остановки по лимиту циклов. Внутренности шагов 4 и 6 раскрывать на следующем слайде. Подробные подписи и все ветви вынести в запасной слайд A.

**Правила отображения:**

- Положение узлов в увеличенном фрагменте одинаково на слайдах 4, 6 и 8. Скриншот располагается рядом с картой, а не поверх переходов.
- Серый означает доступный маршрут, синий — текущий проход, янтарный — возврат на исправление, зелёный — подтверждённое одобрение или QA GREEN. Цвет дублируется словами и номером прохода.
- На слайдах 3–4 подпись `Current documented workflow`. На слайдах 6 и 8 — `PR #198: recorded review and QA sequence`. Текущая карта не выдаётся за восстановленный стейт исторической сессии.
- Скриншоты обрезать до читаемого фрагмента с идентификатором отчёта и вердиктом. Полные кадры доступны локально по ссылкам ниже.
- Последовательное раскрытие — состояния одного содержательного слайда. В статическом экспорте допустимы его копии с суффиксами 6a–6c и 8a–8c. Они делят тайминг исходного слайда и не добавляют материал.
- Изменения после QA проходят review до повторного QA. Verified pre-existing findings не блокируют завершение, но не позволяют пропустить шаги 7–9. Происхождение без доказательства остаётся блокером до уточнения.

## Титул — 0:00–0:15

**На слайде:**

> Agent Orchestration  
> Sergei Telegin  
> github.com/TeleginS/agent-orchestration

Ссылка на GitHub кликабельная. Других тезисов и подзаголовков на титуле нет.

### Что сказать

Hi, I’m Sergei Telegin. I’ll show you the agent pipeline I use in my own project, and follow one real task through its reviews, fixes and final checks.

## 1. Зацепка — 0:15–1:00

**Слайд 1: “157 tests passed. QA blocked the PR”**

TrafficRulesApp и два фрагмента одного QA-отчёта: результат полного набора тестов и `BLOCKED`. Механизм пока не раскрывать. Кадр: [07 — QA BLOCKED](screenshots/07-pr198-qa-blocked-tests.jpg). Источники: S3 и S5.

### Что сказать

TrafficRulesApp is my personal iOS app for preparing for the Spanish driving theory exam. I use a team of AI agents for some development tasks.

In this task, the agents added tests. The reviewer approved the change, and all 157 tests passed. Then QA blocked the pull request because it found weaknesses in the tests themselves.

We’ll follow that task through the actual process: where it moved forward, where it returned for repairs, and what the next review contributed. I’ll also show the cost of those extra passes.

## 2. Устройство агента — 1:00–2:30

**Слайд 2: “Model, tools and execution environment”**

Простой цикл модели и инструментов внутри рамки `Harness`. Результат работы передаётся следующей роли. Это единственная отдельная теоретическая схема; далее используется карта проекта.

На слайде короткие подписи `Context`, `Tool call`, `Tool result`, `Stage result`. Не добавлять отдельные определения API, MCP, multi-agent frameworks или список продуктов.

### Что сказать

First, a quick definition. The model receives context and chooses an action. A tool reads a file, runs a command, or interacts with another system. The execution environment, often called a harness, runs that action and returns its result to the model.

That cycle can continue through many steps. A developer agent might inspect the project, edit code, run tests, read an error and try again. We can give it freedom to investigate while defining what it must deliver at the end.

With several agents, someone must also decide which role works next and what context it receives. In my setup, an orchestrator agent does that. It passes the task, requirements and previous results between roles.

A role name alone gives us very little. The reviewer needs the actual diff and the requirements. QA needs acceptance criteria and a way to test them. Their reports determine the next step.

Most of those routing rules currently live in prompts. The graph I’m about to show describes the intended workflow. It does not execute or enforce that workflow by itself.

## 3. Общая карта — 2:30–4:30

**Слайд 3: “The complete delivery workflow”**

Все 11 шагов на одной карте в четырёх областях из таблицы выше. Направление чтения стабильное; вложенные циклы пока свернуты. Внизу: `Current documented workflow`. Коротко провести указателем по областям, не читать все подписи подряд.

Роли обозначить у соответствующих шагов. Визуально отделить оркестратора и общий профиль от выполняемых этапов. Источники: S10.

### Что сказать

Here is the complete route, including the work around writing and checking code.

Preparation starts with the design check. If the task needs a product decision that has not been made, the process stops for clarification. A small operational task can proceed without a separate design document. The planner then creates checkable requirements and issues. Branch setup checks the working tree so unrelated changes do not travel into the task.

The developer implements the change and opens a pull request. That takes us into verification: review, QA, and the repair loop we’ll examine next.

Completion still involves work. The orchestrator checks accumulated files, updates the task’s issues, optionally cleans up local settings, and produces a final report. A green QA result does not mean that the pull request has merged. Issues for unmerged work keep their PR references and remain open.

The orchestrator coordinates this whole route. The project profile supplies shared facts such as build commands and architecture constraints. Those facts are separate from the general role instructions.

The numbering gives us a stable map. When an agent returns for repairs, we can identify which stage it is revisiting and what result allows it to leave. Now let’s enlarge the verification area without changing the route.

## 4. Приближение к проверкам — 4:30–6:00

**Слайд 4: “Review and QA loops”**

Увеличить шаги 4–6. Слева оставить приглушённый вход `3 Develop and open PR`, справа — выход `7 Artifact check`. В шаге 4 показать reviewer и developer fix; в шаге 6 — developer fix, reviewer и QA retest.

Подписи переходов: `Findings`, `Approval`, `In-scope bugs`, `QA green`. Ответвления остановки: `Limit: 3 iterations`. Рядом со шагом 6: `Rule 11: review QA fixes before retesting`.

### Что сказать

There are two repair loops here. In the first, the reviewer checks the change and returns findings or approval. Findings can send the work back to the developer on the same branch. Approval allows QA to begin.

QA runs the project’s test suite and checks the acceptance criteria and behavioral scenarios. Bugs related to the task enter the second loop. The developer fixes them, the reviewer checks those fixes, and only then does QA retest.

That middle review matters because a fix changes the code. An approval of the previous version cannot establish that the new version is correct.

Both loops have a limit of three iterations. If blockers remain, the instructions require a stop and escalation. Existing bugs can remain separate work, but calling a bug pre-existing requires evidence from the base version. Uncertain origin does not justify a green verdict.

These are instructions for the orchestrator today. A future controller could enforce transitions and retry limits. It would still need good reviews and trustworthy test evidence inside those stages.

## 5. Подтверждённое изменение правил — 6:00–7:30

**Слайд 5: “A versioned change to the review route”**

Короткая хронология: `July 2026: PR #143` и `26 August: rule 11`. Слева — раннее одобрение и заголовок бага, справа — добавленное правило. Выделить тот же переход fix → review → QA, который уже показан на слайде 4.

Кадры: [01 — approval](screenshots/01-pr143-approved.jpg), [02 — bug #144](screenshots/02-issue144-double-count.jpg), [03 — rule 11](screenshots/03-rule11-added.jpg). При нехватке места оставить заголовок бага и правило, одобрение проговорить. Источники: S1–S2.

### Что сказать

The process has changed over time. In July, PR 143 added cumulative progress statistics. The reviewer approved the change. QA then found a scenario that could count session time twice.

The timer could complete the test while an exit confirmation dialog remained open. Confirming the exit afterward could add the time again. That is a concrete example of a behavioral scenario reaching QA after approval.

On August 26, the instruction history records an explicit rule: changes made after QA begins must pass code review before QA can become green. The diff also adds the reviewer between the developer’s QA fixes and the retest.

I cannot reconstruct the complete state of the earlier agent sessions. We have versioned instructions and saved reports, but not every piece of context or every setting. I’m therefore showing a documented change in the process, without claiming that the July bug alone caused it.

The later PR gives us a recorded example of that review step in use. Let’s follow it through the map.

## 6. Маршрут PR #198 до блокировки — 7:30–9:30

**Слайд 6: “PR #198: the route to QA”**

Та же геометрия увеличенного графа, что на слайде 4. Подсвечиваются только подтверждённые посещения review и QA. Подготовка и завершение не окрашиваются как доказанные одним скриншотом.

| Раскрытие | Подсветка карты | Свидетельство рядом |
|---|---|---|
| 6a | Review 1, возврат к developer | Conditional approval и замечания |
| 6b | Повторное посещение reviewer | Review 2: APPROVAL |
| 6c | Переход к QA | 157 passed, verdict BLOCKED |

Кадры: [05b — conditional approval](screenshots/05b-pr198-review1-verdict.jpg), [06 — review 2](screenshots/06-pr198-review2-approved.jpg), [07 — QA BLOCKED](screenshots/07-pr198-qa-blocked-tests.jpg). Источники: S3–S5.

**Точность подписи:** review 1 дал условное одобрение с замечаниями по качеству, а не критическую блокировку. Фактический дополнительный проход developer показать как ответ на замечания, без надписи `BLOCKED` на review 1.

### Что сказать

PR 198 added unit tests for ProgressStore and for recording progress when a test session ends. The work also covered the protection against counting time again after completion, connecting it to the earlier bug.

The pull request added 32 tests, taking the suite from 125 to 157. It also included a project profile. Application code did not change.

Here is the first visit to the reviewer. The verdict was conditional approval with quality findings worth a follow-up pass. It was not a report of critical blockers. The developer addressed the findings, and the work returned to the same review stage.

On the second visit, the reviewer approved the result. The task then reached QA. Notice that the map has not gained another reviewer box. The same role is checking a later state of the work.

The QA report records successful test runs. It also returns BLOCKED and identifies three problems in the tests. Passing the suite established that these checks executed successfully. QA questioned whether particular assertions established the behavior the task required.

That finding activates the second repair loop. Before following the fix around it, we need to understand why the tests could pass and still need changes. Two of the findings describe connected parts of the same problem: the assertion and the starting state.

## 7. Механизм находки — 9:30–12:00

**Слайд 7: “The assertion and the starting state”**

Основное место отдать учебному примеру и фрагменту QA findings. Маленький фрагмент знакомой карты показывает, что рассказ находится в точке `QA: findings`; новую схему пайплайна не вводить.

На слайде:

```text
Illustrative example

Before: 500 seconds
After:  500 seconds

after > 0        PASS
after > before   FAIL

Paired fix
Compare with the prior value
Give each test its own store
```

Число 500 явно подписано как иллюстрация. Кадр: [08 — QA findings](screenshots/08-pr198-qa-findings.jpg). Реальный [diff assertions](screenshots/09b-pr198-delta-assertions-diff.jpg) — запасной слайд B. Источники: S5–S6.

### Что сказать

Five tests checked that the accumulated time was greater than zero after a terminal call. But the requirement concerned the contribution of that particular call: did this path actually add session time?

Imagine the store already contains 500 seconds. We call the method, it adds nothing, and the store still contains 500 seconds. The assertion that the total is greater than zero passes. The assertion that the total increased fails.

Those numbers are an illustration of the failure mechanism. They are not a measured result from the QA run.

Why could old time exist in the first place? The tests used shared UserDefaults.standard storage and manually cleared a list of keys. Other tests or previous runs could leave state that made the total positive before the action under test.

The repair addressed both parts. Each test received its own temporary store through existing injection parameters. The assertions took a snapshot before the action and checked for an increase afterward. Application code did not need to change.

These changes serve related purposes. Isolation controls where the starting value comes from. The comparison expresses the contribution the test intends to check. Reading the assertion without looking at the fixture would miss part of the explanation.

QA found a third issue about distinguishing the two exit branches. I’ll leave that detail for questions so we can follow the main repair through the process.

The next stage is particularly useful here. The reviewer will examine both the code changes and the explanation of what they prove. That explanation needs a qualification once the new isolated store starts at zero.

## 8. Маршрут после блокировки — 12:00–14:00

**Слайд 8: “PR #198: fix, review and retest”**

Вернуть увеличенную карту в прежнее положение. Последовательно подсветить три внутренних узла шага 6.

| Раскрытие | Подсветка карты | Фрагмент рядом |
|---|---|---|
| 8a | Developer fix | Коммит `114cb54`, assertions и изоляция |
| 8b | Reviewer | Review 3: правило 11, APPROVAL, уточнение `before == 0` |
| 8c | QA retest | QA Pass 2: GREEN, четыре полных прогона по 157 тестов |

Кадры: [09 — fix](screenshots/09-pr198-qa-fix-commit.jpg), [10 — review 3](screenshots/10-pr198-review3-gate.jpg), [11 — proof caveat](screenshots/11-pr198-review3-proof-caveat.jpg), [12 — QA GREEN](screenshots/12-pr198-qa-green.jpg). Источники: S6–S7.

Условие `before = 0` и пояснение `Both changes matter` вывести читаемым текстом, а не заставлять аудиторию читать длинный комментарий. Внизу: `PR open at capture, 6 September 2026`. Стрелку в completion показать как дальнейший маршрут по правилам, без утверждения о merge.

### Что сказать

The developer pushes the QA fixes to the same pull request. The work then visits the reviewer before returning to QA. Review iteration three explicitly refers to rule 11.

The review approves the fixes, but also qualifies the proof. With an isolated store, the starting value is zero in these five tests. In that state, comparing the result with zero and comparing it with the prior value are numerically equivalent.

So we should not attribute the entire improvement to the new assertion alone. The delta form states the intended contribution and remains useful if a future fixture seeds state. Isolation removes the old shared-state condition. The explanation has to account for both changes.

That is an example of what the extra review contributed: it checked the fix and corrected an overly broad interpretation of the result.

Only after approval did the task return to QA. The second QA report records four full runs, each with 157 passing tests. One run deliberately polluted the shared standard store to check that it could not affect the isolated tests. The final QA verdict was GREEN.

At the time these screenshots were captured, the pull request was still open. Green QA permits the completion steps in the workflow. It does not establish that the change has merged. With that distinction clear, we can put a cost against the route we just followed.

## 9. Стоимость маршрута — 14:00–16:00

**Слайд 9: “The cost of this run”**

Слева компактная таблица измерений, справа фрагмент исходного отчёта. Под таблицей — число посещений ролей: `Planner 1`, `Developer 3`, `Reviewer 3`, `QA 2`. Не превращать их в дополнительные роли графа.

| Measure | Recorded result |
|---|---|
| Subagent launches | 9 |
| Reported elapsed time | About 1 h 31 min |
| Measured subagent tokens | 1,097,667 |

Видимое уточнение: `Orchestrator tokens excluded. No matched single-agent baseline.` Кадр: [13 — measured cost](screenshots/13-run-cost-measured.jpg). Источник: S8.

### Что сказать

This is the cost report for the same task. It records nine subagent launches, about one hour and thirty-one minutes of elapsed work, and just under 1.1 million subagent tokens.

The launch count now has a concrete explanation. There was one planner pass, three developer passes, three reviewer passes and two QA passes. Several boxes on our map were visited more than once.

Each visit means assembling context, investigating the current state, running checks and writing a report. The review passes used slightly more tokens in total than the developer passes in this run. Review was a substantial part of the work.

The token figure excludes the orchestrator because its usage was mixed into the main session. The source estimates that separately. I am keeping the measured figure separate here, and I am not presenting a dollar estimate as a provider invoice.

We saw useful findings, but this single run cannot establish that multiple agents were cheaper or more effective than one agent with suitable tests. I do not have a matched control run.

The practical question is which checks justify their cost on a given type of task. To answer that, future records should include confirmed findings, missed defects and the time I spend intervening. The diagram tells us where to measure those things.

## 10. Вывод и следующий шаг — 16:00–18:00

**Слайд 10: “What I would measure next”**

Вернуть общую карту уменьшенной, но без плотных подписей. Выделить передачи результатов между этапами. Рядом два тезиса: `A checkable result for each stage` и `A versioned record of each run`.

Ниже: `Next: validate approval and QA against the code version`. Это предложенное развитие, не существующая возможность. Внизу крупная кликабельная ссылка на репозиторий. Новую подробную дорожную карту в доклад не добавлять.

### Что сказать

The map gives me a way to discuss the process beyond the number of agents. At each transition, I can ask what result the previous stage produced and what evidence allows the next stage to begin.

In this example, review approval led to QA. QA findings led to a fix. The fix required another review, and that review improved the explanation before the final retest. We can point to the reports for those visits and see what each contributed.

My next step would be to save a versioned record of every run: the instructions, project profile, code version, stage results and measured costs. That would make comparisons easier than reconstructing old sessions from Git history.

I would then validate the handoffs programmatically, starting with whether review and QA refer to the code version being delivered. Such a check could reject stale approval. It would not prove that the reviewer found every bug.

For someone trying this in their own project, I would start with one task type and define the result each stage must provide. Then inspect real runs to see which checks add useful evidence and which mainly repeat work.

The repository contains the role instructions, project profiles, the full graph and saved run reports. You can use those to examine the process and adapt it. Thank you. I’m happy to discuss the details in questions.

## Запасные слайды — после доклада

### A. “Full workflow and transition conditions”

Полный граф из [PIPELINE-GRAPH.md](../../PIPELINE-GRAPH.md), адаптированный к широкому слайду с читаемыми подписями. Это справочный слайд, а не обязательный следующий шаг после заключения.

Сохранить все шаги 0–10 и внутренние циклы. По [PIPELINE.md](../../PIPELINE.md) пояснить условия, которые сокращены в обзорной карте: неопределённый дизайн; origin evidence для pre-existing findings; остановка после лимита; продолжение через шаги 7–9; правила открытых issues. Настройки — опциональны. Никакой автоматической стрелки `GREEN → merged`.

**Короткий ответ на вопрос о гарантиях:**

> The diagram describes the intended transitions. Today the orchestrator follows them through instructions. A controller could enforce required artifacts and retry limits, while the quality of the implementation and review would still need separate evaluation.

### B. “The test fix in the actual diff”

Показать [реальный diff](screenshots/09b-pr198-delta-assertions-diff.jpg), [уточнение reviewer](screenshots/11-pr198-review3-proof-caveat.jpg) и ссылки на [#199](resources/trafficrulesapp/issue-199.md), [#200](resources/trafficrulesapp/issue-200.md), [#201](resources/trafficrulesapp/issue-201.md).

**Короткий ответ про `before == 0`:**

> In the committed isolated fixture, the two comparisons are numerically equivalent. The delta assertion expresses the contribution we want to check. Isolation controls the starting state. The dirty-store example explains the original risk, and should not be presented as the state of the repaired fixture.

Если спрашивают про 156/157, использовать [review 3](resources/trafficrulesapp/pr-198.md#issuecomment-5500807469): подсчёт строк параллельного консольного вывода дал 156, структурированный `xcresult` подтвердил 157. В основной рассказ этот отдельный технический сюжет не включать.

## Репетиция и подготовка слайдов

- Во время общей карты за две минуты объяснить области и назначение завершения. Не читать все 11 этапов и каждое условие остановки.
- На увеличенном графе объяснить различие двух циклов один раз. В PR #198 далее называть конкретные посещения и новые свидетельства.
- На слайдах 6 и 8 сохранять карту неподвижной, переключать только подсветку и фрагмент отчёта. Не заставлять аудиторию заново искать reviewer.
- При отставании на минуту сократить рассказ о профиле на слайде 3, предысторию #143 и будущие измерения. Сохранить механизм находки, уточнение про ноль и повторное ревью.
- Не заполнять запас заранее. Паузы для чтения screenshots и движения указателя входят в плановый темп. Репетировать именно с ними.
- Перед митапом проверить статус #198. Пока использовать точную формулировку о состоянии на дату съёмки, 6 сентября 2026 года.
- Все изображения уже доступны локально. Новый текст и схемы подготовить на английском. Ссылки на оригинальный приватный репозиторий могут требовать авторизацию.

## Границы доказательств

Текущая карта служит навигацией по правилам. Сохранённые отчёты подтверждают конкретную последовательность review и QA в PR #198, но не восстанавливают полный runtime trace. Общую карту не окрашивать целиком как подтверждённый исторический маршрут на основании этих фрагментов.

Коммит `47fe491` подтверждает изменение инструкций 26 августа. Не утверждать, что PR #143 был единственной причиной этого изменения, и не выводить отсутствие этапа из отсутствия сохранённого отчёта.

Отчёты агентов не были заново воспроизведены при подготовке этого сценария. Числа затрат берутся из сохранённого отчёта, не из интервалов между комментариями GitHub. Историческую выборку 20 прогонов предшествующей версии не объединять с измерениями #198.

## Источники

Обозначения S1–S10 совпадают с предыдущими планами. Локальные копии содержат ссылки на оригиналы.

- **S1. Ранний кейс:** [PR #143](resources/trafficrulesapp/pr-143.md), [одобрение](resources/trafficrulesapp/pr-143.md#issuecomment-4886098768), [баг #144](resources/trafficrulesapp/issue-144.md).
- **S2. Изменение маршрута:** [коммит 47fe491](resources/trafficrulesapp/commit-47fe491.md), правило 11 и reviewer перед повторным QA.
- **S3. Основной кейс:** [PR #198](resources/trafficrulesapp/pr-198.md).
- **S4. Review до QA:** [iteration 1](resources/trafficrulesapp/pr-198.md#issuecomment-5500796064), [iteration 2](resources/trafficrulesapp/pr-198.md#issuecomment-5500799535).
- **S5. QA findings:** [Pass 1](resources/trafficrulesapp/pr-198.md#issuecomment-5500803440), [assertions #199](resources/trafficrulesapp/issue-199.md), [изоляция #200](resources/trafficrulesapp/issue-200.md).
- **S6. Исправление и review:** [коммит 114cb54](resources/trafficrulesapp/commit-114cb54.md), [iteration 3](resources/trafficrulesapp/pr-198.md#issuecomment-5500807469).
- **S7. Повторный QA:** [Pass 2](resources/trafficrulesapp/pr-198.md#issuecomment-5500811713).
- **S8. Измерения:** [сохранённый отчёт запуска](../../examples/run-progress-store-tests/README.md), раздел Measured: subagent tokens.
- **S9. Профиль:** [коммит 9a26da8](resources/trafficrulesapp/commit-9a26da8.md).
- **S10. Правила и карта:** [PIPELINE.md](../../PIPELINE.md), [PIPELINE-GRAPH.md](../../PIPELINE-GRAPH.md), [generic harness](../../adapters/generic-harness/README.md), [контракты результатов](../../examples/artifacts/README.md).

Теоретические определения опираются на [сохранённые материалы](resources/transcripts/ai-agents-harness.md) и теоретическую часть предыдущих планов. Дополнительных утверждений о возможностях конкретных SDK или моделей этот сценарий не вводит.
