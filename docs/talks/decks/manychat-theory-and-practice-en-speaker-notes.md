# Speaker notes

## Title slide. Agent Orchestration

TIMING: about 10–15 seconds, within the first minute of the talk.

Hello, I am Sergei Telegin. Today I will talk about agent orchestration. The project and its role instructions are available on GitHub.

https://github.com/TeleginS/agent-orchestration

This title slide precedes the ten content slides. Keep the original timing checkpoints and the two-minute buffer.

## 1. 157 tests passed. QA still blocked the PR

TIMING: 0:00–1:00. Planned pace, including pauses and discussion of the evidence. Keep 18:00–20:00 free as a buffer. Audience questions follow the talk.

TrafficRulesApp is my personal iOS app for the Spanish driving theory exam. I run some development work through a team of AI agents. In this task, the agents added tests. A reviewer approved the result and all 157 tests passed. Yet the next agent, QA, blocked it because of weaknesses in the tests themselves.

I will return to the exact failure mechanism after we establish how an agent works and how several agents become a process. We need to distinguish the model's choice of actions, the software that executes them, and the rules that determine which stage comes next. At the end, I will show what the extra stages cost in this same run. The findings were useful, and the coordination consumed substantial resources.

SOURCES
https://github.com/TeleginS/TrafficRulesApp/pull/198
https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500799535
https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440

GitHub screenshots captured on 6 September 2026. Saved agent reports, not an independent rerun. Original private sources require access. Speaker notes and slide wording are in English.

## 2. The agent loop

TIMING: 1:00–3:00. Planned pace, including pauses and discussion of the evidence. Keep 18:00–20:00 free as a buffer. Audience questions follow the talk.

For this talk, an agent is a system that chooses actions, uses tools and decides how to continue from their results. Follow one example throughout: adding a test to an iOS project. The model can ask to read a file. A tool performs the actual read. The returned contents become part of the next model context. After a change, the model can request a test run and use the failure to choose another action.

The harness is the software that runs this loop. It assembles context, executes allowed tool calls, handles errors and decides when to continue or stop. Some choices can stay with the model, while the runtime imposes limits on permissions or retries. The model name alone tells us little about these controls.

There is a practical distinction between asking an agent to run tests and having software require a test result before allowing completion. My published repository mainly defines role instructions and a route for an orchestrator agent to follow. It does not itself implement a durable execution engine. Pause on that distinction before moving to several agents.

SOURCES
https://www.anthropic.com/engineering/building-effective-agents
https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/PIPELINE.md
../resources/transcripts/ai-agents-harness.md

GitHub screenshots captured on 6 September 2026. Saved agent reports, not an independent rerun. Original private sources require access. Speaker notes and slide wording are in English.

## 3. Delegation separates tasks and context

TIMING: 3:00–5:00. Planned pace, including pauses and discussion of the evidence. Keep 18:00–20:00 free as a buffer. Audience questions follow the talk.

An orchestrator delegates work and combines results. A separate evaluator can inspect an output against explicit criteria and send feedback for another attempt. These patterns can be combined in a delivery process.

Here the developer receives a task to implement. The reviewer receives requirements and the real change. QA later receives a behavioral assignment. Each role has a different expected output and an intentionally assembled context.

The content of the handoff matters. If the reviewer only receives the developer's summary that everything is done, it may repeat the same assumptions. It needs the actual diff, the requirements and the relevant test evidence. That also means some information must travel between otherwise separate contexts.

A new role does not guarantee independent judgment. Agents can share the same model, the same missing context and the same mistaken premise. The practical test is whether this role contributes an additional useful check.

There is a cost to these boundaries. Each agent reads context, may investigate the code again and writes a report. The orchestrator must preserve enough detail for the next stage. That leads to the next design question: who decides which stage follows a finding or a fix?

SOURCES
https://www.anthropic.com/engineering/building-effective-agents
https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/PIPELINE.md

GitHub screenshots captured on 6 September 2026. Saved agent reports, not an independent rerun. Original private sources require access. Speaker notes and slide wording are in English.

## 4. Stage freedom and transition rules

TIMING: 5:00–7:00. Planned pace, including pauses and discussion of the evidence. Keep 18:00–20:00 free as a buffer. Audience questions follow the talk.

A process graph makes stages and transition conditions visible. In a route implemented in code, the runtime can check those conditions before continuing. In a model-directed process, some control remains with the model.

A node can be a complete development task. The developer can choose which files to inspect and which implementation to try. Its output must include the change and check results for the reviewer. We do not need a separate graph node for every file search or edit.

One useful transition condition is approval of the current version. If code changes afterward, the old approval no longer establishes that someone reviewed this version. The route should require a fresh review. If the process keeps returning for repairs, a retry limit should lead to a stop and human escalation.

Enforcing the presence of an approval does not prove the reviewer is right. Execution guarantees and review quality are separate concerns. Making the graph too detailed also creates more transitions to maintain and less room for useful local choices.

My repository defines roles, handoffs and repair loops, while leaving implementation choices inside roles. Much of the routing is currently a prompt for the orchestrator. The next slide shows one versioned change in that route.

SOURCES
https://www.anthropic.com/engineering/building-effective-agents
https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/PIPELINE.md

GitHub screenshots captured on 6 September 2026. Saved agent reports, not an independent rerun. Original private sources require access. Speaker notes and slide wording are in English.

## 5. My pipeline changed after earlier runs

TIMING: 7:00–9:00. Planned pace, including pauses and discussion of the evidence. Keep 18:00–20:00 free as a buffer. Audience questions follow the talk.

The normal route runs from planning through development, review and QA to a final report. Review findings go back to the developer. QA findings also go back to the developer, but the changed code must pass review before the next QA run. The added step matters because approval of an earlier version does not cover a later fix automatically.

In July, the cumulative-statistics PR had an approval followed by a QA finding about double-counted time. I continued tuning the pipeline. A commit on 26 August explicitly added rule 11 to the orchestrator instructions: QA fixes need another review before QA can be green. The September test-coverage run contains an explicit report for this review step.

The diagram summarizes the route and leaves out Git and issue housekeeping. The current generic instructions limit each repair loop to three iterations before escalation. These are instructions for the orchestrator, not transitions enforced by this diagram.

I have not recovered the full context of the historical sessions. Versioned files establish this change, but cannot reconstruct uncommitted prompts, model settings or the main conversation. Nor do they establish that the earlier bug was the sole cause of rule 11.

SOURCES
https://github.com/TeleginS/TrafficRulesApp/commit/47fe4917052c82e7181e9de5321511ed8194c11c
https://github.com/TeleginS/TrafficRulesApp/pull/143
https://github.com/TeleginS/TrafficRulesApp/issues/144
https://github.com/TeleginS/TrafficRulesApp/pull/198
https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/PIPELINE.md

GitHub screenshots captured on 6 September 2026. Saved agent reports, not an independent rerun. Original private sources require access. Speaker notes and slide wording are in English.

## 6. Accumulated time or this call’s contribution?

TIMING: 9:00–11:00. Planned pace, including pauses and discussion of the evidence. Keep 18:00–20:00 free as a buffer. Audience questions follow the talk.

The requirement concerned the contribution of a particular terminal call: that path must add session time. Five tests instead checked that the accumulated total was greater than zero.

Imagine a store with 500 seconds before the call and the same 500 seconds afterward. The method has added nothing, but a greater-than-zero assertion still passes. Comparing the result with a snapshot from before the call exposes the missing contribution. The number 500 on this slide is an illustrative example, not a measured value from the QA run.

The mechanism connects directly to isolation. These tests used shared UserDefaults.standard storage and manually cleared a list of keys. Old progress could come from other tests or survive from another run. A positive total therefore did not necessarily come from the action being tested.

The fix addressed both parts: snapshot the prior value and assert an increase, and give each test a separate temporary suite through the stores' existing injection parameters. No production-code changes were necessary. This controls the starting state and expresses the behavioral requirement.

QA found three issues overall. The third concerned distinguishing the two exit branches. We can discuss it after the talk. The main point here is the connection between a weak assertion and shared state. The other tests retained their value.

SOURCES
https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440
https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500799535
https://github.com/TeleginS/TrafficRulesApp/issues/199
https://github.com/TeleginS/TrafficRulesApp/issues/200
https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20

GitHub screenshots captured on 6 September 2026. Saved agent reports, not an independent rerun. Original private sources require access. Speaker notes and slide wording are in English.

## 7. The fix gets its own review

TIMING: 11:00–13:00. Planned pace, including pauses and discussion of the evidence. Keep 18:00–20:00 free as a buffer. Audience questions follow the talk.

This is the new route in a concrete run. The developer addressed the QA findings in the fix commit. Review iteration 3 explicitly invokes rule 11 and evaluates the QA fixes. Only after its approval does the work return to QA.

The review does more than confirm that the code changed. It qualifies the explanation of the fix. With the isolated suite, the initial value is zero in these five tests. In that state, greater than zero and greater than before are numerically equivalent. We therefore cannot credit the entire effect to replacing the assertion alone.

The delta assertion expresses the intended contribution. The isolated suite controls the starting state. Those changes work together. The reviewer also verified the injection and checked whether shared application data could leak into the new suite.

QA then repeated the checks and returned GREEN. Its report records four full runs, each with 157 passing tests, including a deliberately polluted shared store. The screenshots show the first row as a readable excerpt of the larger table.

The outcome was reviewed changes and green QA in an open pull request. The decision to merge remains separate. Now we can discuss what these extra passes cost.

SOURCES
https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20
https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469
https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500811713

GitHub screenshots captured on 6 September 2026. Saved agent reports, not an independent rerun. Original private sources require access. Speaker notes and slide wording are in English.

## 8. The cost of this run

TIMING: 13:00–15:00. Planned pace, including pauses and discussion of the evidence. Keep 18:00–20:00 free as a buffer. Audience questions follow the talk.

These numbers come from the saved cost report for the same ProgressStore test task. There were nine subagent launches, about an hour and a half of elapsed work and roughly 1.10 million subagent tokens. The exact recorded token count is 1,097,667.

The role breakdown is three developer passes, three review passes, two QA passes and one planning pass. Each return to a role requires context, investigation, checks and another report. The extra passes produced findings, but they were not free.

The token figure excludes the orchestrator. Its tokens were mixed with the main session and only estimated in the source report. Elapsed time comes from that report, not from the timestamps of GitHub comments. Comments can appear after the underlying work.

I am also not presenting an estimated dollar range as a provider invoice. Model choice, input and output tokens, and caching affect such an estimate.

For 32 new tests, this is substantial overhead. I have no matched single-agent control, so this run does not establish a price or quality advantage for multiple agents. It does show the checks we paid for and the findings they produced. For future runs, I also want to record the time I spend intervening and reading reports.

SOURCES
https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/examples/run-progress-store-tests/README.md
https://github.com/TeleginS/TrafficRulesApp/pull/198

GitHub screenshots captured on 6 September 2026. Saved agent reports, not an independent rerun. Original private sources require access. Speaker notes and slide wording are in English.

## 9. What I changed and what comes next

TIMING: 15:00–17:00. Planned pace, including pauses and discussion of the evidence. Keep 18:00–20:00 free as a buffer. Audience questions follow the talk.

The first change is the review of QA fixes that we just saw. Another is separating general role instructions from project facts. A shared profile holds the build and test commands, architecture and project constraints. This run added a profile and corrected drift reported by the agents.

The evidence included the question count, the number of test files and the way test results were counted. A particularly useful example was 156 versus 157. Parallel console output lost part of a line, so counting passed messages with grep undercounted tests. The agents used the structured xcresult summary to establish that 157 tests ran. The process needs a better source for the next report, rather than just a corrected number in the current report.

Profiles can themselves become stale. Reviewers can misread evidence. Reports should record the scenario, the version and the way the result was obtained.

Today, much of this route lives in prompts. A possible next step is runtime enforcement of transitions, retry limits and review for the current code version. A runtime can enforce the existence of an approval without proving that the review is correct. Checkpoints and automatic recovery also require more than this prompt repository provides.

Finally, the right amount of decomposition depends on the task. An extra role may repeat an investigation the previous agent already performed. For a small change, one agent and suitable tests may be enough. To compare pipeline versions fairly, I need comparable tasks, recorded conditions and the amount of human intervention.

SOURCES
https://github.com/TeleginS/TrafficRulesApp/commit/9a26da875489315c3164ebeb14e1b8af7c57b177
https://github.com/TeleginS/TrafficRulesApp/pull/198
https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469
https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/PIPELINE.md
https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/examples/run-progress-store-tests/README.md

GitHub screenshots captured on 6 September 2026. Saved agent reports, not an independent rerun. Original private sources require access. Speaker notes and slide wording are in English.

## 10. A first experiment in your own project

TIMING: 17:00–18:00. Planned pace, including pauses and discussion of the evidence. Keep 18:00–20:00 free as a buffer. Audience questions follow the talk.

If you want to try this approach, begin with one type of task and a clear result for every stage. Save the reports and examine which checks brought useful findings and which only added cost.

In the earlier case, QA found a bug after approval. Later, versioned instructions explicitly added review of QA fixes. In the September run, the reports show that step checking both the code and the explanation of the result. The history supports a concrete change in the process, while leaving the full historical session state unknown.

That is how I want to tune the pipeline: use observed gaps, change a rule or a source of context, and inspect what happens in the next run. The checks themselves need evidence too.

The repository contains the roles, profiles and run examples. Thank you. Questions follow the talk. Keep the remaining two minutes as a buffer rather than adding another topic.

SOURCES
https://github.com/TeleginS/agent-orchestration

GitHub screenshots captured on 6 September 2026. Saved agent reports, not an independent rerun. Original private sources require access. Speaker notes and slide wording are in English.
