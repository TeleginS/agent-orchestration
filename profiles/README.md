# Profiles

A **profile** is everything the roles need to know about *your* project. It is the only
file you have to write to adopt this pipeline.

The role prompts in `agents/` are deliberately stack-neutral. They describe how a
reviewer reviews, not what a Swift reviewer checks. The profile supplies the second
half: build commands, module names, architecture invariants, release gates,
stack-specific checklist items.

## Resolution

The orchestrator resolves the active profile before Step 0 and passes its path into
every subagent launch:

1. A path given explicitly by the user or the launching context
2. `profiles/active.md`
3. The only file in `profiles/` that is not `README.md` or `_template.md`

No profile resolves → the orchestrator stops and asks. A run without a profile produces
confident work against invented conventions, which is worse than no work.

## Creating one

Copy `_template.md`, fill in every section, and either name it `active.md` or point at
it explicitly. `example-mobile-app.md` is a filled-in profile for a subscription mobile
app — read it to see the level of detail that actually helps.

## The contract

Every section in `_template.md` is required. Roles reference them by name:

| Section | Read by |
|---|---|
| Identity | all |
| Stack | all |
| Layout | developer, code-reviewer, qa-tester |
| Commands | developer, qa-tester, orchestrator |
| Architecture invariants | all |
| Critical flags and release gates | developer, code-reviewer, qa-tester |
| Review checklist additions | code-reviewer |
| Anti-patterns | developer, code-reviewer |
| Known risk areas | qa-tester |
| Output language | task-planner, qa-tester, developer |
| Harness settings | settings-optimizer, orchestrator |

Leaving a section empty is fine when it genuinely doesn't apply — say so explicitly
(`None — this project has no localization layer`) rather than deleting the heading. A
missing heading reads as an oversight; an explicit "none" reads as a decision.

## Keeping it honest

**Precedence is: observed code > profile > role prompt.** Roles are instructed to
follow the code when the profile contradicts it, and to report the drift. Those reports
surface in the orchestrator's final summary — use them to correct the profile.

The section most worth maintaining is **Architecture invariants**, and specifically its
*what does not exist* list. Naming the modules that were renamed or removed stops agents
from confidently writing code against them, which is the single most common way a stale
profile turns into wasted review cycles.
