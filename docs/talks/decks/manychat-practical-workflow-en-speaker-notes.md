# Practical workflow — English speaker notes

14 main pages + 2 backup pages. Page numbers 1–16 match the scenario and the deck.
Main speech: approximately 1948 words. Planned duration: 18 minutes, with
18:00–20:00 reserved for pauses and overruns. Questions follow the talk.

Timing is a plan, not a measured rehearsal. Sources and presentation directions are in
[the scenario](../manychat-meetup-agent-orchestration-talk-practical.md).

## Page 1. Agent Orchestration

TIMING: 0:00–0:15.

Hi, I’m Sergei Telegin. I’ll show you one real task from my AI development workflow: what the agents checked, why the work came back, and what those extra passes cost.

## Page 2. 157 tests passed. QA blocked the PR.

TIMING: 0:15–1:00.

TrafficRulesApp is my personal iOS app for the Spanish driving theory exam. In this task, agents were adding tests. The reviewer approved the change. All 157 tests passed. QA still blocked the pull request.

The problem was in what some of those tests could prove. We’ll follow the task through one map, see the finding and its repair, and look at the cost. The question to keep in mind is: what evidence should one stage give the next?

SOURCES

- [Source 1](https://github.com/TeleginS/TrafficRulesApp/pull/198)
- [Source 2](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440)
- [Source 3](https://github.com/TeleginS/TrafficRulesApp/issues/199)
- [Source 4](https://github.com/TeleginS/TrafficRulesApp/issues/200)
- [Source 5](https://github.com/TeleginS/TrafficRulesApp/issues/201)

## Page 3. An agent is a loop

TIMING: 1:00–2:00.

An agent works through a loop. The model receives context and chooses an action. A tool reads a file, edits code, or runs a test. The execution environment, often called a harness, performs that action and returns the result.

The model can then choose another action. A developer might inspect code, make a change, read a test failure and try again.

For this talk, that is enough theory. The next question is how several such loops work together. Someone must provide the task and decide what result allows the next role to begin. My orchestrator coordinates that through written instructions. The diagram we’ll use describes those instructions; it does not enforce them.

SOURCES

- [docs/talks/resources/transcripts/ai-agents-harness.md](/Users/sergei/Developer/agent-orchestration/docs/talks/resources/transcripts/ai-agents-harness.md)
- [docs/talks/manychat-meetup-agent-orchestration-talk-graph-walkthrough.md](/Users/sergei/Developer/agent-orchestration/docs/talks/manychat-meetup-agent-orchestration-talk-graph-walkthrough.md)

## Page 4. One map, four responsibilities

TIMING: 2:00–3:30.

Here is the map we’ll keep using. Four responsibilities: planning, implementation, review and QA.

The planner turns the request into acceptance criteria and work items. The developer implements those requirements and supplies the change and its checks. The reviewer examines the actual diff against the task. QA runs the suite and checks the acceptance criteria and relevant behavior.

These responsibilities overlap. Separate contexts do not make the agents statistically independent: they can share a model and repeat an assumption. The useful distinction is the additional check each role is asked to perform.

The orchestrator coordinates the whole route. It carries the task, the project profile and previous results between stages. It also handles preparation and completion: clarification, branch hygiene, artifact review and issue cleanup. We’ll keep those details on a backup slide.

Notice the labels between the boxes. A stage hands over something another stage can inspect. A message saying “done” is not enough to explain why the task should move forward.

SOURCES

- [README.md](/Users/sergei/Developer/agent-orchestration/README.md)
- [PIPELINE.md](/Users/sergei/Developer/agent-orchestration/PIPELINE.md)
- [PIPELINE-GRAPH.md](/Users/sergei/Developer/agent-orchestration/PIPELINE-GRAPH.md)
- [skills/README.md](/Users/sergei/Developer/agent-orchestration/skills/README.md)
- [adapters/README.md](/Users/sergei/Developer/agent-orchestration/adapters/README.md)
- [adapters/codex/README.md](/Users/sergei/Developer/agent-orchestration/adapters/codex/README.md)
- [memory/RULES.md](/Users/sergei/Developer/agent-orchestration/memory/RULES.md)

## Page 5. Changed code needs fresh evidence

TIMING: 3:30–5:00.

There are two ways back. Review findings can send the patch to the developer. QA findings can also send it back, but a QA fix goes through review before QA tests it again.

The reason is simple: the fix changes the code. Approval of an earlier version does not cover that change automatically.

There is a short history behind this rule. In July, QA found double-counted session time after a reviewer had approved PR 143. On August 26, a versioned change explicitly added review of QA fixes to the instructions: rule eleven.

That establishes a documented process change. It does not establish that the July bug was its only cause, or reconstruct every setting in the old sessions.

Today, both repair loops have a three-iteration limit, then escalation with the remaining blockers. Those limits and transitions are instructions the orchestrator must follow. Now we can look at a later run where the additional review is visible in the reports.

SOURCES

- [Source 1](https://github.com/TeleginS/TrafficRulesApp/pull/143)
- [Source 2](https://github.com/TeleginS/TrafficRulesApp/issues/144)
- [Source 3](https://github.com/TeleginS/TrafficRulesApp/commit/47fe4917052c82e7181e9de5321511ed8194c11c)
- [README.md](/Users/sergei/Developer/agent-orchestration/README.md)
- [PIPELINE.md](/Users/sergei/Developer/agent-orchestration/PIPELINE.md)
- [PIPELINE-GRAPH.md](/Users/sergei/Developer/agent-orchestration/PIPELINE-GRAPH.md)
- [skills/README.md](/Users/sergei/Developer/agent-orchestration/skills/README.md)
- [adapters/README.md](/Users/sergei/Developer/agent-orchestration/adapters/README.md)
- [adapters/codex/README.md](/Users/sergei/Developer/agent-orchestration/adapters/codex/README.md)
- [memory/RULES.md](/Users/sergei/Developer/agent-orchestration/memory/RULES.md)

## Page 6. 32 new tests. One delivery route.

TIMING: 5:00–6:30.

The task in PR 198 was to add unit tests for ProgressStore and for recording progress when a test session ends. That included the protection against counting time twice after completion, connecting this work to the earlier bug.

The final change contained 32 new tests. The suite grew from 125 to 157. It also added a project profile, with commands and project-specific constraints. Application code did not need to change.

We are looking at saved reports and screenshots from that run, not a new test session performed for this presentation. The map is our guide to the intended route; the reports show the visits we can actually trace.

Keep the task’s goal in mind: useful tests of existing behavior. Success required more than increasing the test count. A test needed to fail when the behavior it claimed to protect was broken. That is where both review and QA had work to do.

SOURCES

- [Source 1](https://github.com/TeleginS/TrafficRulesApp/pull/198)
- [Source 2](https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/examples/run-progress-store-tests/README.md#measured-subagent-tokens)
- [Source 3](https://github.com/TeleginS/TrafficRulesApp/commit/9a26da875489315c3164ebeb14e1b8af7c57b177)

## Page 7. Review improved the patch

TIMING: 6:30–7:30.

The first review gave conditional approval with quality findings. It did not report critical blockers. Two findings were worth a short follow-up: a missing integration check for an important progress rule, and a check connecting the expected theme count to the bundled data.

The developer addressed them. The second review approved the patch after examining those changes and running the suite.

That was useful work. The point of the next finding is not that review did nothing. It improved the patch, and QA then found a different weakness.

On our map, we have visited the same reviewer twice. Each visit concerns a different state of the code. The second approval is what takes this task into QA.

SOURCES

- [Source 1](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500796064)
- [Source 2](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500799535)

## Page 8. Green tests. Weak evidence.

TIMING: 7:30–9:00.

The QA report records successful runs on two simulator destinations, including a full run with parallel testing disabled. It also says BLOCKED, with three in-scope findings.

Two findings belong together. Five tests asserted that accumulated session time was greater than zero. The tests also used shared storage and manually cleared a list of keys.

The task required each terminal action to contribute time. A positive total did not necessarily show that this particular action had contributed anything. Old values could make the assertion pass.

The third finding concerned distinguishing two exit branches. We’ll leave its details for questions.

This does not make all 157 tests useless. QA specifically identified the affected checks and acknowledged checks that were sound. The useful distinction is between a test executing successfully and the test establishing the behavior its name and acceptance criterion promise. Let’s make that distinction concrete.

SOURCES

- [Source 1](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440)
- [Source 2](https://github.com/TeleginS/TrafficRulesApp/issues/199)
- [Source 3](https://github.com/TeleginS/TrafficRulesApp/issues/200)
- [Source 4](https://github.com/TeleginS/TrafficRulesApp/issues/201)

## Page 9. Prove the change, isolate the state

TIMING: 9:00–11:00.

Imagine the store contains 500 seconds before the call. The call adds nothing. Afterward, the store still contains 500 seconds.

“Is the total greater than zero?” passes. “Did the total increase after this call?” fails. Pause on those two questions: they establish different things. Five hundred is an illustrative value, not a measurement from this QA run.

Why could there be an old value? These tests used UserDefaults.standard, shared application storage. They cleared a known list of keys, but that did not give each test control over every possible source of starting state. The saved findings describe contamination encountered during implementation.

The repair had two parts. Each test received its own temporary storage suite through injection points already present in the application. The assertions captured the value just before the terminal call and checked for an increase afterward.

Isolation controls the starting state. The comparison expresses the contribution of the action under test. Both matter to the explanation; we should examine the fixture and the assertion together.

There is a qualification: in the repaired isolated fixture, the starting value is zero. The two comparisons are numerically equivalent there. We should not credit the whole improvement to the new assertion alone.

The developer made these changes in the test files without changing production code. But the work is not finished when the developer reports the fix. We have changed the patch, so we need fresh review evidence before another QA verdict.

SOURCES

- [Source 1](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440)
- [Source 2](https://github.com/TeleginS/TrafficRulesApp/issues/199)
- [Source 3](https://github.com/TeleginS/TrafficRulesApp/issues/200)
- [Source 4](https://github.com/TeleginS/TrafficRulesApp/issues/201)
- [Source 5](https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20)
- [Source 6](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469)

## Page 10. Fix → review → QA

TIMING: 11:00–12:30.

The developer pushed the fixes to the same pull request. Review iteration three explicitly invoked rule eleven and checked the QA fixes before the work returned to QA.

The reviewer approved and explicitly made the qualification we just discussed: in the isolated fixture, “before” is zero. The explanation must account for both changes. The delta form expresses the requirement; isolation removes the shared-state problem.

That is useful scrutiny of both the patch and the explanation of what it proves.

QA then returned GREEN. Its report records four full runs with 157 passing tests each, including a deliberately polluted shared store to test the isolation.

At the September 6 screenshot capture, the PR was still open. We have a recorded approval and green QA, not evidence of a merge. Completion work still follows on the map. Now let’s attach costs to the visits we just saw.

SOURCES

- [Source 1](https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20)
- [Source 2](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469)
- [Source 3](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500811713)

## Page 11. The observed cost

TIMING: 12:30–14:00.

The saved report gives us nine subagent launches and 1,097,667 subagent tokens. The recorded stage wall times add up to about one hour and thirty-one minutes. That is the sum of those stage durations, not a separate measurement of my total time on the task.

The visits explain the count: one planner, three developer passes, three reviews and two QA passes. Review used slightly more tokens than implementation in this run.

Orchestrator tokens were mixed into the main conversation and estimated separately, so they are excluded here. I’m also keeping estimated dollar costs off this slide.

For 32 new tests, these are substantial coordination costs. We saw useful findings, but there was no matched single-agent run. This example does not establish a general quality or cost advantage.

What I would measure next is confirmed findings, missed defects and human intervention time, alongside tokens and duration. That would help decide which checks are worth retaining for this kind of task.

SOURCES

- [Source 1](https://github.com/TeleginS/agent-orchestration/blob/693c5cd291e35d773c9f68f99888ca420dbbf30a/examples/run-progress-store-tests/README.md#measured-subagent-tokens)

## Page 12. How the repository works today

TIMING: 14:00–15:00.

The repository has since changed its packaging. The reusable procedures now live in canonical skills. The orchestrator stays in the main conversation, where it can clarify requirements, and delegates the stages to separate agents.

Thin host adapters provide launch behavior and model configuration. Model and reasoning choices can be configured per role where the host supports them; otherwise its defaults apply. A skill contains instructions. Loading it alone does not create an independent agent.

The project profile supplies commands and constraints. Each role explicitly reads relevant shared project memory under common rules.

These changes make the responsibilities of the files clearer. The historical run we just examined predates this packaging. I am not claiming measured improvements in cost or quality from the migration.

SOURCES

- [README.md](/Users/sergei/Developer/agent-orchestration/README.md)
- [PIPELINE.md](/Users/sergei/Developer/agent-orchestration/PIPELINE.md)
- [PIPELINE-GRAPH.md](/Users/sergei/Developer/agent-orchestration/PIPELINE-GRAPH.md)
- [skills/README.md](/Users/sergei/Developer/agent-orchestration/skills/README.md)
- [adapters/README.md](/Users/sergei/Developer/agent-orchestration/adapters/README.md)
- [adapters/codex/README.md](/Users/sergei/Developer/agent-orchestration/adapters/codex/README.md)
- [memory/RULES.md](/Users/sergei/Developer/agent-orchestration/memory/RULES.md)

## Page 13. Define what each stage hands over

TIMING: 15:00–17:00.

Here is the part you can apply without copying my entire workflow: define what each stage hands over.

For the planner, I want criteria someone can actually check, dependencies and linked work items with a clear scope. The developer needs those criteria, project context and execution constraints. It returns a pull request and diff, the version it changed, and what it built or tested.

The reviewer needs the actual diff and requirements, not only the developer’s summary. Its report should identify the reviewed version, prioritized findings or explicit approval. After a fix, the next reviewer also needs the previous findings so it can establish what changed.

QA needs the same requirements and current change. It returns evidence for acceptance criteria, test results, classified bugs and an explicit GREEN or BLOCKED verdict. Calling a bug pre-existing needs evidence from the base version; uncertainty is not a reason to mark the work green.

The orchestrator carries these results onward while preserving the task’s constraints. That includes the branch, ownership, mode and any limits on writes. In a dry run, local plans, diffs and findings replace tracker and PR artifacts.

Today this is largely an instruction contract. A future controller could check that required artifacts exist and refer to the current version. It could reject stale approval. It would still not prove that the review itself was correct.

SOURCES

- [README.md](/Users/sergei/Developer/agent-orchestration/README.md)
- [PIPELINE.md](/Users/sergei/Developer/agent-orchestration/PIPELINE.md)
- [PIPELINE-GRAPH.md](/Users/sergei/Developer/agent-orchestration/PIPELINE-GRAPH.md)
- [skills/README.md](/Users/sergei/Developer/agent-orchestration/skills/README.md)
- [adapters/README.md](/Users/sergei/Developer/agent-orchestration/adapters/README.md)
- [adapters/codex/README.md](/Users/sergei/Developer/agent-orchestration/adapters/codex/README.md)
- [memory/RULES.md](/Users/sergei/Developer/agent-orchestration/memory/RULES.md)

## Page 14. Three things to take back

TIMING: 17:00–18:00.

Three things to take back.

First, define the output of each stage. Say what it must deliver and what permits the next stage to begin.

Second, pass artifacts that others can verify: requirements, the actual diff, findings and test results. Give the next role something it can inspect.

Third, repeat verification after code changes. A fix needs evidence for the new version, including review before fresh QA.

Start with one type of task and inspect the handoffs in real runs. The repository includes the skills, profiles, workflow and saved examples we discussed. Thank you. I’m happy to take questions after the talk.

SOURCES

- [README.md](/Users/sergei/Developer/agent-orchestration/README.md)
- [PIPELINE.md](/Users/sergei/Developer/agent-orchestration/PIPELINE.md)
- [PIPELINE-GRAPH.md](/Users/sergei/Developer/agent-orchestration/PIPELINE-GRAPH.md)
- [skills/README.md](/Users/sergei/Developer/agent-orchestration/skills/README.md)
- [adapters/README.md](/Users/sergei/Developer/agent-orchestration/adapters/README.md)
- [adapters/codex/README.md](/Users/sergei/Developer/agent-orchestration/adapters/codex/README.md)
- [memory/RULES.md](/Users/sergei/Developer/agent-orchestration/memory/RULES.md)

## Page 15. Full workflow and transition conditions

TIMING: Backup — questions only.

This is the complete documented workflow. The main conversation first resolves project context and any missing product decisions. Planning establishes the work, branch preparation protects unrelated changes, and the developer produces the patch.

The review loop permits up to three completed verdicts, counting the initial review. The QA repair loop counts each developer fix and its review as an iteration, even if review blocks a return to QA. Moving between roles does not reset that counter.

A verified pre-existing bug is recorded as separate work and does not block this change. Its classification needs comparable base-version evidence. An unconfirmed origin remains a blocker until classified.

After green QA, artifact review, issue cleanup and any applicable settings work still happen. Unmerged work keeps its issue references and stays open. In dry-run mode, planning and findings stay local and the workflow writes neither to the tracker nor the remote.

The diagram documents these transitions. It is not an executable controller and does not provide automatic recovery.

SOURCES

- [README.md](/Users/sergei/Developer/agent-orchestration/README.md)
- [PIPELINE.md](/Users/sergei/Developer/agent-orchestration/PIPELINE.md)
- [PIPELINE-GRAPH.md](/Users/sergei/Developer/agent-orchestration/PIPELINE-GRAPH.md)
- [skills/README.md](/Users/sergei/Developer/agent-orchestration/skills/README.md)
- [adapters/README.md](/Users/sergei/Developer/agent-orchestration/adapters/README.md)
- [adapters/codex/README.md](/Users/sergei/Developer/agent-orchestration/adapters/codex/README.md)
- [memory/RULES.md](/Users/sergei/Developer/agent-orchestration/memory/RULES.md)

## Page 16. The zero-baseline caveat

TIMING: Backup — questions only.

The dirty-store example explains the original risk. If the store was already positive, an assertion on the absolute total could pass when the terminal action added nothing.

The repair also changed the fixture. In the committed isolated tests, the initial value is zero. Therefore greater than zero and greater than the prior value are numerically equivalent in that fixture. The reviewer explicitly pointed this out.

The delta form states the intended contribution and remains useful if a future fixture starts with seeded progress. Isolation removes dependence on shared old values. Both changes are reasonable, but the mutation demonstration with a dirty store should not be presented as the starting state of the repaired suite.

The third finding added checks distinguishing the two exit branches. If you want the full discussion, the saved issues and the final review and QA reports contain the details.

SOURCES

- [Source 1](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500803440)
- [Source 2](https://github.com/TeleginS/TrafficRulesApp/issues/199)
- [Source 3](https://github.com/TeleginS/TrafficRulesApp/issues/200)
- [Source 4](https://github.com/TeleginS/TrafficRulesApp/issues/201)
- [Source 5](https://github.com/TeleginS/TrafficRulesApp/commit/114cb54a883fcfed25f98e08c97d9d3ff9407e20)
- [Source 6](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500807469)
- [Source 7](https://github.com/TeleginS/TrafficRulesApp/pull/198#issuecomment-5500811713)
