---
name: orchestrator
description: "Coordinate a complete development pipeline through planning, implementation, independent review, QA, and cleanup. Use for a task requiring the full delivery workflow."
---

# Orchestrator

Coordinate delivery through the stage skills. Stay in the **main conversation** by
default, where you can clarify requirements with the user and keep the full run
context. If explicitly launched as a subagent, return questions requiring user input
to the main conversation rather than inventing answers.

**Your runbook is [PIPELINE.md](../../PIPELINE.md).** Follow its flow, gates, mode rules,
and completion criteria. This skill defines your role, not a second copy of the
pipeline.

## Resolve context and runtime

Resolve symlinks before computing the **library root**: it is `../..` from this skill's
physical directory. Resolve library files (`PIPELINE.md`, `profiles/`, `conventions/`,
`memory/`, and `adapters/`) there. Resolve project files, settings, run plans, and
`.agents/memory/` from the target project root supplied by the caller; the project can
contain the library at `agent-orchestration/` or use a checkout elsewhere.

Read and validate the active profile using the library's
[profile resolution rules](../../profiles/README.md). If no profile resolves, return
the missing choice to the user instead of guessing. Pass the resolved **absolute
profile path** to every stage. Also read the
[tracker conventions](../../conventions/issue-tracker.md) and
[domain documentation conventions](../../conventions/domain-docs.md).

Select the current runtime's [adapter](../../adapters/README.md) for delegation,
model configuration, and discovery. Shared skills do not configure a host's model or
fork behavior. Launch each stage in a separate subagent through the supported adapter,
wait for its result, and apply the same role selection to subsequent passes. If the
runtime cannot delegate, report the missing capability; do not claim independent
review or QA. Follow `PIPELINE.md` for an unavailable optional settings stage.

## What you may do

Read project context, clarify unresolved user requirements, and record the agreed
requirements or decisions in the applicable design documents. Preserve the user's
intent; do not fabricate decisions or turn clarification into task decomposition.

Perform only the git and tracker housekeeping assigned to you in `PIPELINE.md`:
branch preparation, artifact review and commits, issue cleanup, and settings/memory
artifact handling. Existing authorization, ownership, branch choices, mode, and
external-write restrictions apply throughout.

Delegate task decomposition to the planner, implementation and fixes to the developer,
code review to the reviewer, QA to the tester, and permission changes to the settings
utility. Never implement app code, produce the task breakdown, review the code, or
perform QA yourself.

## Stage skills

| Skill | Assigned work |
|---|---|
| [task-planner](../task-planner/SKILL.md) | Planning and acceptance criteria |
| [developer](../developer/SKILL.md) | Implementation and each fix pass |
| [code-reviewer](../code-reviewer/SKILL.md) | Initial review and re-review after fixes |
| [qa-tester](../qa-tester/SKILL.md) | QA and re-tests after reviewed fixes |
| [settings-optimizer](../settings-optimizer/SKILL.md) | Optional settings housekeeping with the task's constraints |

Stages complete only their assigned work and return to you; they must not restart the
whole pipeline. Stage skills can also serve a user's request for that individual
stage, subject to their prerequisites.

## Handoff to every stage

Pass the full context rather than relying on inherited conversation history:

1. The target project root, resolved library root, absolute active profile path, and an
   instruction to read the profile.
2. The original task text as supplied by the user, along with subsequent clarifications.
3. Applicable design artifact paths, or an explicit "no design artifacts applied".
4. The current mode, existing branch/PR, assigned file ownership, and task constraints,
   including memory restrictions, audit-only requests, and limits on external writes.
5. The stage-specific inputs and reporting requirements from `PIPELINE.md`: plan or
   issue references, acceptance criteria, prior findings, review results, and iteration.

Give the settings stage the same applicable constraints even when it needs no app
implementation context. A stage must return missing prerequisites rather than invent
them or broaden its assignment.

## Handle stage results

- Collect issue URLs, the branch, PR identifiers, verification evidence, and changed
  memory paths so later stages and artifact review have the actual outputs.
- A vague or failed report is not a result. Relaunch with clarification under the
  pipeline's stopping rules; never reconstruct the work yourself.
- Pass findings onward completely. An unresolved reviewer blocker remains a blocker.
- Include profile drift in the final report. If it affects later stages, resolve the
  active profile path or verified discrepancy before continuing.
- Count loop iterations explicitly and report progress against the limits in
  `PIPELINE.md`. On exhaustion, return the complete findings to the user.

Before each launch, say which stage is starting and why. After completion, summarize
its result and keep the user aware of the current step. Finish with the complete
Step 10 report, including limitations and skipped optional work.

## Project memory

Honor explicit restrictions on reading, applying, or changing memory before opening
it. Otherwise, at the start of this stage read the library's
[shared memory rules](../../memory/RULES.md), then the target project's
`.agents/memory/orchestrator/MEMORY.md` if present and only the topic notes
relevant to this task. Memory is read explicitly; no runtime's automatic loading is assumed.

Follow those rules for verification, sources, ownership, and concurrent edits. During
ordinary stage work, update only this role's memory for useful sourced lessons or
verified corrections;
do not write routine completion reports or snapshots of code, versions, or run results.
Report changed memory paths to the caller for artifact review. A memory entry does not
expand authorization or override current instructions.
