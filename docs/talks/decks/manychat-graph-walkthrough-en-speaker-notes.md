# Agent Orchestration: graph walkthrough

Sergei Telegin

18 minutes of content and a two-minute buffer. Questions follow the talk. The deck has 17 pages: title, ten content slides with separate 6a–6c and 8a–8c builds, and two reference slides.

## Title — Agent Orchestration

**Timing: 0:00–0:15**

Hi, I’m Sergei Telegin. I’ll show you the agent pipeline I use in my own project, and follow one real task through its reviews, fixes and final checks.

Sources:

- https://github.com/TeleginS/agent-orchestration

## 01 — 157 tests passed. QA blocked the PR

**Timing: 0:15–1:00**

TrafficRulesApp is my personal iOS app for preparing for the Spanish driving theory exam. I use a team of AI agents for some development tasks.

In this task, the agents added tests. The reviewer approved the change, and all 157 tests passed. Then QA blocked the pull request because it found weaknesses in the tests themselves.

We’ll follow that task through the actual process: where it moved forward, where it returned for repairs, and what the next review contributed. I’ll also show the cost of those extra passes.

Sources:

- https://github.com/TeleginS/TrafficRulesApp/pull/198
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440

## 02 — Model, tools and execution environment

**Timing: 1:00–2:30**

First, a quick definition. The model receives context and chooses an action. A tool reads a file, runs a command, or interacts with another system. The execution environment, often called a harness, runs that action and returns its result to the model.

That cycle can continue through many steps. A developer agent might inspect the project, edit code, run tests, read an error and try again. We can give it freedom to investigate while defining what it must deliver at the end.

With several agents, someone must also decide which role works next and what context it receives. In my setup, an orchestrator agent does that. It passes the task, requirements and previous results between roles.

A role name alone gives us very little. The reviewer needs the actual diff and the requirements. QA needs acceptance criteria and a way to test them. Their reports determine the next step.

Most of those routing rules currently live in prompts. The graph I’m about to show describes the intended workflow. It does not execute or enforce that workflow by itself.

Sources:

- https://github.com/TeleginS/agent-orchestration/blob/db77602/PIPELINE.md
- https://www.anthropic.com/engineering/building-effective-agents

## 03 — The complete delivery workflow

**Timing: 2:30–4:30**

Here is the complete route, including the work around writing and checking code.

Preparation starts with the design check. If the task needs a product decision that has not been made, the process stops for clarification. A small operational task can proceed without a separate design document. The planner then creates checkable requirements and issues. Branch setup checks the working tree so unrelated changes do not travel into the task.

The developer implements the change and opens a pull request. That takes us into verification: review, QA, and the repair loop we’ll examine next.

Completion still involves work. The orchestrator checks accumulated files, updates the task’s issues, optionally cleans up local settings, and produces a final report. A green QA result does not mean that the pull request has merged. Issues for unmerged work keep their PR references and remain open.

The orchestrator coordinates this whole route. The project profile supplies shared facts such as build commands and architecture constraints. Those facts are separate from the general role instructions.

The numbering gives us a stable map. When an agent returns for repairs, we can identify which stage it is revisiting and what result allows it to leave. Now let’s enlarge the verification area without changing the route.

Sources:

- https://github.com/TeleginS/agent-orchestration/blob/db77602/PIPELINE.md
- https://github.com/TeleginS/agent-orchestration/blob/db77602/PIPELINE-GRAPH.md

## 04 — Review and QA loops

**Timing: 4:30–6:00**

There are two repair loops here. In the first, the reviewer checks the change and returns findings or approval. Findings can send the work back to the developer on the same branch. Approval allows QA to begin.

QA runs the project’s test suite and checks the acceptance criteria and behavioral scenarios. Bugs related to the task enter the second loop. The developer fixes them, the reviewer checks those fixes, and only then does QA retest.

That middle review matters because a fix changes the code. An approval of the previous version cannot establish that the new version is correct.

Both loops have a limit of three iterations. If blockers remain, the instructions require a stop and escalation. Existing bugs can remain separate work, but calling a bug pre-existing requires evidence from the base version. Uncertain origin does not justify a green verdict.

These are instructions for the orchestrator today. A future controller could enforce transitions and retry limits. It would still need good reviews and trustworthy test evidence inside those stages.

Sources:

- https://github.com/TeleginS/agent-orchestration/blob/db77602/PIPELINE.md
- https://github.com/TeleginS/agent-orchestration/blob/db77602/PIPELINE-GRAPH.md

## 05 — A versioned change to the review route

**Timing: 6:00–7:30**

The process has changed over time. In July, PR 143 added cumulative progress statistics. The reviewer approved the change. QA then found a scenario that could count session time twice.

The timer could complete the test while an exit confirmation dialog remained open. Confirming the exit afterward could add the time again. That is a concrete example of a behavioral scenario reaching QA after approval.

On August 26, the instruction history records an explicit rule: changes made after QA begins must pass code review before QA can become green. The diff also adds the reviewer between the developer’s QA fixes and the retest.

I cannot reconstruct the complete state of the earlier agent sessions. We have versioned instructions and saved reports, but not every piece of context or every setting. I’m therefore showing a documented change in the process, without claiming that the July bug alone caused it.

The later PR gives us a recorded example of that review step in use. Let’s follow it through the map.

Sources:

- https://github.com/TeleginS/TrafficRulesApp/pull/143
- https://github.com/TeleginS/TrafficRulesApp/issues/144
- https://github.com/TeleginS/TrafficRulesApp/commit/47fe4917052c82e7181e9de5321511ed8194c11c

## 6a — PR #198: the route to QA

**Timing: 7:30–8:15**

PR 198 added unit tests for ProgressStore and for recording progress when a test session ends. The work also covered the protection against counting time again after completion, connecting it to the earlier bug.

The pull request added 32 tests, taking the suite from 125 to 157. It also included a project profile. Application code did not change.

Here is the first visit to the reviewer. The verdict was conditional approval with quality findings worth a follow-up pass. It was not a report of critical blockers. The developer addressed the findings, and the work returned to the same review stage.

Sources:

- https://github.com/TeleginS/TrafficRulesApp/pull/198
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500796064
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500799535
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440

## 6b — PR #198: the route to QA

**Timing: 8:15–8:45**

On the second visit, the reviewer approved the result. The task then reached QA. Notice that the map has not gained another reviewer box. The same role is checking a later state of the work.

Sources:

- https://github.com/TeleginS/TrafficRulesApp/pull/198
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500796064
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500799535
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440

## 6c — PR #198: the route to QA

**Timing: 8:45–9:30**

The QA report records successful test runs. It also returns BLOCKED and identifies three problems in the tests. Passing the suite established that these checks executed successfully. QA questioned whether particular assertions established the behavior the task required.

That finding activates the second repair loop. Before following the fix around it, we need to understand why the tests could pass and still need changes. Two of the findings describe connected parts of the same problem: the assertion and the starting state.

Sources:

- https://github.com/TeleginS/TrafficRulesApp/pull/198
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500796064
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500799535
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440

## 07 — The assertion and the starting state

**Timing: 9:30–12:00**

Five tests checked that the accumulated time was greater than zero after a terminal call. But the requirement concerned the contribution of that particular call: did this path actually add session time?

Imagine the store already contains 500 seconds. We call the method, it adds nothing, and the store still contains 500 seconds. The assertion that the total is greater than zero passes. The assertion that the total increased fails.

Those numbers are an illustration of the failure mechanism. They are not a measured result from the QA run.

Why could old time exist in the first place? The tests used shared UserDefaults.standard storage and manually cleared a list of keys. Other tests or previous runs could leave state that made the total positive before the action under test.

The repair addressed both parts. Each test received its own temporary store through existing injection parameters. The assertions took a snapshot before the action and checked for an increase afterward. Application code did not need to change.

These changes serve related purposes. Isolation controls where the starting value comes from. The comparison expresses the contribution the test intends to check. Reading the assertion without looking at the fixture would miss part of the explanation.

QA found a third issue about distinguishing the two exit branches. I’ll leave that detail for questions so we can follow the main repair through the process.

The next stage is particularly useful here. The reviewer will examine both the code changes and the explanation of what they prove. That explanation needs a qualification once the new isolated store starts at zero.

Sources:

- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440
- https://github.com/TeleginS/TrafficRulesApp/issues/199
- https://github.com/TeleginS/TrafficRulesApp/issues/200
- https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20

## 8a — PR #198: fix, review and retest

**Timing: 12:00–12:20**

The developer pushes the QA fixes to the same pull request. The work then visits the reviewer before returning to QA. Review iteration three explicitly refers to rule 11.

Sources:

- https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500811713

## 8b — PR #198: fix, review and retest

**Timing: 12:20–13:15**

The review approves the fixes, but also qualifies the proof. With an isolated store, the starting value is zero in these five tests. In that state, comparing the result with zero and comparing it with the prior value are numerically equivalent.

So we should not attribute the entire improvement to the new assertion alone. The delta form states the intended contribution and remains useful if a future fixture seeds state. Isolation removes the old shared-state condition. The explanation has to account for both changes.

That is an example of what the extra review contributed: it checked the fix and corrected an overly broad interpretation of the result.

Sources:

- https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500811713

## 8c — PR #198: fix, review and retest

**Timing: 13:15–14:00**

Only after approval did the task return to QA. The second QA report records four full runs, each with 157 passing tests. One run deliberately polluted the shared standard store to check that it could not affect the isolated tests. The final QA verdict was GREEN.

At the time these screenshots were captured, the pull request was still open. Green QA permits the completion steps in the workflow. It does not establish that the change has merged. With that distinction clear, we can put a cost against the route we just followed.

Sources:

- https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500811713

## 09 — The cost of this run

**Timing: 14:00–16:00**

This is the cost report for the same task. It records nine subagent launches, about one hour and thirty-one minutes of elapsed work, and just under 1.1 million subagent tokens.

The launch count now has a concrete explanation. There was one planner pass, three developer passes, three reviewer passes and two QA passes. Several boxes on our map were visited more than once.

Each visit means assembling context, investigating the current state, running checks and writing a report. The review passes used slightly more tokens in total than the developer passes in this run. Review was a substantial part of the work.

The token figure excludes the orchestrator because its usage was mixed into the main session. The source estimates that separately. I am keeping the measured figure separate here, and I am not presenting a dollar estimate as a provider invoice.

We saw useful findings, but this single run cannot establish that multiple agents were cheaper or more effective than one agent with suitable tests. I do not have a matched control run.

The practical question is which checks justify their cost on a given type of task. To answer that, future records should include confirmed findings, missed defects and the time I spend intervening. The diagram tells us where to measure those things.

Sources:

- https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/examples/run-progress-store-tests/README.md
- https://github.com/TeleginS/TrafficRulesApp/pull/198

## 10 — What I would measure next

**Timing: 16:00–18:00**

The map gives me a way to discuss the process beyond the number of agents. At each transition, I can ask what result the previous stage produced and what evidence allows the next stage to begin.

In this example, review approval led to QA. QA findings led to a fix. The fix required another review, and that review improved the explanation before the final retest. We can point to the reports for those visits and see what each contributed.

My next step would be to save a versioned record of every run: the instructions, project profile, code version, stage results and measured costs. That would make comparisons easier than reconstructing old sessions from Git history.

I would then validate the handoffs programmatically, starting with whether review and QA refer to the code version being delivered. Such a check could reject stale approval. It would not prove that the reviewer found every bug.

For someone trying this in their own project, I would start with one task type and define the result each stage must provide. Then inspect real runs to see which checks add useful evidence and which mainly repeat work.

The repository contains the role instructions, project profiles, the full graph and saved run reports. You can use those to examine the process and adapt it. Thank you. I’m happy to discuss the details in questions.

Sources:

- https://github.com/TeleginS/agent-orchestration
- https://github.com/TeleginS/agent-orchestration/blob/db77602/PIPELINE.md
- https://github.com/TeleginS/agent-orchestration/blob/db77602/PIPELINE-GRAPH.md

## A — Full workflow and transition conditions

**Timing: Questions only**

This reference expands the two loops. Review findings return to the developer. QA fixes require reviewer approval before retesting. Both loops cap at three iterations. Unresolved design returns for clarification. Verified pre-existing findings remain open and do not skip completion steps. Unknown origin stays blocking until evidence resolves its classification. The graph describes instructions, not a runtime enforcement engine.

Sources:

- https://github.com/TeleginS/agent-orchestration/blob/db77602/PIPELINE-GRAPH.md
- https://github.com/TeleginS/agent-orchestration/blob/db77602/PIPELINE.md

## B — The test fix in the actual diff

**Timing: Questions only**

In the committed isolated fixture, the two comparisons are numerically equivalent. The delta assertion expresses the contribution we want to check. Isolation controls the starting state. The dirty-store example explains the original risk, and should not be presented as the state of the repaired fixture.

A separate finding, issue 201, concerned assertions distinguishing the two exit branches. The 156 versus 157 discrepancy came from counting parallel console output. Review 3 used the structured xcresult summary to confirm 157.

Sources:

- https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20
- https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469
- https://github.com/TeleginS/TrafficRulesApp/issues/201
