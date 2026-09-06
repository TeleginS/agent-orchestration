# Скриншоты для доклада Manychat

21 кадр с оригинальных страниц GitHub, снятый 6 сентября 2026 года. Формат JPEG, 993 × 1204 пикселя. Кадры открываются локально без сети и авторизации.

[Открыть галерею](index.html) · [План с подробным кейсом](../manychat-meetup-agent-orchestration-talk.md) · [План с теорией](../manychat-meetup-agent-orchestration-talk-theory-and-practice.md)

## Как использовать

Номера ниже — слайды из двух планов. Несколько кадров для одного слайда — варианты или последовательное раскрытие; показывать их все подряд не нужно.

Для короткого варианта достаточно раннего одобрения и бага, добавленного правила, одобрения второго ревью, QA BLOCKED, пары находок, третьего ревью, QA GREEN и таблицы затрат.

В подробном варианте добавьте реальный diff assertions и уточнение reviewer о начальном нуле. Кадры отдельных issues и первое ревью пригодятся для вопросов.

Условную иллюстрацию «500 → 500» нужно оформить отдельно на слайде: это учебный пример, а не скриншот результата прогона. Схемы из теоретической части также остаются схемами слайдов.

В момент съёмки основной PR открыт. Зелёные тесты и одобрение в комментарии не означают merge. В таблице затрат измеренные токены подагентов отделены от оценки оркестратора.

## Каталог

| Кадр | Подробный кейс: слайд | Теория и практика: слайд | Оригинал |
|---|---|---|---|
| [Раннее одобрение и вывод о корректном учёте времени](01-pr143-approved.jpg) | 1 | 5 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/143#issuecomment-4886098768) |
| [QA-баг: двойной учёт времени](02-issue144-double-count.jpg) | 1 | 5 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/issues/144) |
| [Добавленное правило 11](03-rule11-added.jpg) | 4 | 5 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/commit/47fe4917052c82e7181e9de5321511ed8194c11c) |
| [Новый переход: исправление → ревью → повторный QA](03b-review-before-retest-transition.jpg) | 4 | 5 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/commit/47fe4917052c82e7181e9de5321511ed8194c11c) |
| [Заголовок коммита с изменением инструкций](03c-rule-change-date.jpg) | 4, запас | 5, запас | [GitHub](https://github.com/TeleginS/TrafficRulesApp/commit/47fe4917052c82e7181e9de5321511ed8194c11c) |
| [Цель основного PR и открытый статус](04-pr198-overview.jpg) | 5 | 6 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/198) |
| [Первое ревью: замечания](05-pr198-review1-findings.jpg) | 5, запас | 6, запас | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500796064) |
| [Первое ревью: условное одобрение](05b-pr198-review1-verdict.jpg) | 5, запас | 6, запас | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500796064) |
| [Второе ревью: APPROVAL](06-pr198-review2-approved.jpg) | 5 | 6 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500799535) |
| [Все 157 тестов зелёные, но QA BLOCKED](07-pr198-qa-blocked-tests.jpg) | 5 | 1, 6 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440) |
| [Находки QA: assertions и изоляция](08-pr198-qa-findings.jpg) | 6 | 6 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440) |
| [Коммит с исправлениями после QA](09-pr198-qa-fix-commit.jpg) | 7 | 7 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20) |
| [Реальный diff: before и проверка приращения](09b-pr198-delta-assertions-diff.jpg) | 6–7 | 6–7 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20) |
| [Третье ревью: правило 11 и APPROVAL](10-pr198-review3-gate.jpg) | 7 | 7 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469) |
| [Уточнение reviewer о доказательстве исправления](11-pr198-review3-proof-caveat.jpg) | 7 | 7 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469) |
| [Повторный QA: GREEN и результаты тестов](12-pr198-qa-green.jpg) | 7 | 7 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500811713) |
| [Затраты: 9 запусков, токены и длительность](13-run-cost-measured.jpg) | 8 | 8 | [GitHub](https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/examples/run-progress-store-tests/README.md#measured-subagent-tokens) |
| [Профиль проекта и найденные расхождения](14-pr198-profile-drift.jpg) | 9 | 9 | [GitHub](https://github.com/TeleginS/TrafficRulesApp/pull/198) |
| [Issue: проверка абсолютного значения](15-issue199-assertions.jpg) | 6, запас | 6, запас | [GitHub](https://github.com/TeleginS/TrafficRulesApp/issues/199) |
| [Issue: изоляция тестового хранилища](16-issue200-isolation.jpg) | 6, запас | 6, запас | [GitHub](https://github.com/TeleginS/TrafficRulesApp/issues/200) |
| [Для вопросов: две ветви выхода](17-issue201-exit-branches.jpg) | Вопросы | Вопросы | [GitHub](https://github.com/TeleginS/TrafficRulesApp/issues/201) |

Оригиналы TrafficRulesApp требуют доступа к приватному репозиторию. Локальные кадры и [текстовые копии источников](../resources/trafficrulesapp/README.md) доступны без него.

[Метаданные кадров](capture-log.json) содержат источники, соответствие слайдам, размеры и контрольные суммы файлов.
