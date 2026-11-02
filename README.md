# agent-orchestration

A delivery pipeline built from reusable skills that you can point at any codebase.
One task in, one reviewed and QA'd pull request out.

Six pipeline skills, eleven steps, two loops with guardrails, three human gates — plus a
standalone triage skill that feeds production errors back into the tracker. The orchestrator stays
in the main conversation, clarifies requirements with you, and delegates planning,
implementation, review, and QA to separate subagents.

```
task → plan → branch → implement → review ⇄ fix → QA → fix ⇄ review ⇄ retest → cleanup → report
                                    (×3 max)          (×3 max)
```

## What 20 real runs look like

Most published agent pipelines are a diagram and a promise. This one has outcomes.

| | |
|---|---|
| Orchestrated runs | 20 |
| Merged | 19 |
| Closed without merging | 1 |
| Runs where **review** sent work back | 2 |
| Runs where **QA** filed bugs | 8 |
| Times either loop hit its 3-iteration cap | 0 |

The interesting number is the gap between the last two. Review sends work back 10% of the
time; QA finds bugs 40% of the time — on code a reviewer just approved. That ratio is the
entire argument for keeping them as separate steps, and for running QA second.

Here is one of those eight, in full:

> The reviewer read every terminal code path and proved a true statement — no path
> double-counts session time — and approved. QA then found time being double-counted, via
> a race between a countdown timer and a modal dialog that no reading of the diff could
> reveal.

Nobody was careless, and the approval was correct. **A reviewer reads the change; QA runs
the program and asks what else can happen.** Merging the two steps — the obvious
efficiency — deletes the one that catches this.

[`examples/run-cumulative-stats/`](examples/run-cumulative-stats/) has that run end to end,
with the artifacts the pipeline actually wrote: epic, child issues, PR, review comment, bug
report, fix, re-review, re-test. [`examples/`](examples/) also covers the two send-backs —
one where the pipeline caught its own agents writing a deleted symbol back into the
repository, and one that shipped nothing at all.

For what a run **costs**, the measured numbers are in
[`examples/run-progress-store-tests/`](examples/run-progress-store-tests/): 1,097,667
subagent tokens across 9 launches, 302 tool calls, 1h 31m wall clock, broken down per step
and per role — plus a costed estimate and an honest argument about whether it was worth it.

### Status, stated plainly

Those 20 runs were produced by the **ancestor** of this repository: one project, one
stack, prompts with the project fused into them. What is published here is a
restructuring — same flow, same guardrails, rewritten role prompts, and a profile
indirection the original did not have.

The restructured version has now been run end to end **once**, on a real task in a real
repository: [`examples/run-progress-store-tests/`](examples/run-progress-store-tests/).
Every guardrail behaved as designed, the profile seam held, and the precedence rule caught
three stale facts in the profile on its first outing. That run has measured token counts,
wall clock and a costed estimate — **≈1.7M tokens, ~$10, 1.5 hours** for a task a
competent engineer would scope at half a day. Whether that trade is worth it is argued
honestly in the report rather than assumed.

That measured run predates the skill packaging and shared memory migration. It is
evidence for the pipeline, not an end-to-end validation of the new host launchers.

One run is not twenty. Point it at something real in
[dry-run](PIPELINE.md#dry-run-mode) first — it touches neither your tracker nor your
remote — and treat your first live run as a shakedown.

## Map

- **[examples/](examples/)** — what the pipeline produces, and what 20 runs look like
  - **[run-cumulative-stats/](examples/run-cumulative-stats/)** — one complete run, every
    artifact, including the bug-fix loop
  - **[run-progress-store-tests/](examples/run-progress-store-tests/)** — the first live
    run of this version: measured tokens, wall clock, cost, and what it found
  - **[artifacts/](examples/artifacts/)** — the output contracts the orchestrator parses
- **[PIPELINE.md](PIPELINE.md)** — the runbook: every step, its transition criterion,
  the strict rules
- **[PIPELINE-GRAPH.md](PIPELINE-GRAPH.md)** — the same thing as a state diagram
- **[skills/](skills/)** — the six pipeline skills and the standalone `production-triage`
- **[gates/](gates/)** — hooks that enforce the owner's merge and release gates
- **[profiles/](profiles/)** — the one file you write to adopt this
- **[adapters/](adapters/)** — Claude Code, Codex, generic harness

## The idea

The natural way to write agent prompts is to bake the project into them: this reviewer
knows the framework and checks the billing SDK's entitlement flag, this developer knows
the module layout. It works, and it produces six files that must each be rewritten for
the next project and that quietly rot as this one moves.

So the prompts here are split along that seam:

- **`skills/<role>/SKILL.md`** — how a reviewer reviews, how a planner decomposes, what a QA
  verdict requires. Stack-neutral, and true regardless of what the project is written
  in.
- **`profiles/<project>.md`** — build and test commands, module names, architecture
  invariants, release gates, the stack-specific checklist entries.

The orchestrator resolves the active profile once and passes its path into every
subagent launch. Adopting the pipeline for a new project means writing one profile.
Host adapters control invocation and models; the skill bodies remain shared. Each
stage completes its assignment and returns to the orchestrator without restarting
the pipeline.

**Precedence is: observed code > profile > role prompt.** Profiles are written by hand
and go stale; roles are told to follow the code when the two disagree and to report the
drift, which surfaces in the final report so the profile can be fixed.

## Install in a project

Run everything below from the adopting project's root. Claude Code is shown in full;
the Codex differences are one line each, and the [generic harness](adapters/generic-harness/README.md)
needs only steps 1, 2 and 7. The adapter and gate READMEs hold the details and the
migration paths for projects that already have skills, hooks or an older install.

**1. Vendor the library and write the profile.**

```bash
git submodule add <this-repo> agent-orchestration
mkdir -p .agents
cp agent-orchestration/profiles/_template.md .agents/profile.md
```

Fill in every section of `.agents/profile.md`; [`example-mobile-app.md`](profiles/example-mobile-app.md)
shows the useful level of detail, and the **Verification command** and **Human gates**
sections are the ones the rest of this list depends on. The profile lives in your
project, next to `.agents/skills/` and `.agents/memory/`, so it is versioned with the
code it describes and the orchestrator finds it without an explicit path.

**2. Link the canonical skills.** Skip any role that already exists and inspect it; if
`.agents/skills` is itself a symlink, read [adapters/README.md](adapters/README.md#shared-installation) first.

```bash
mkdir -p .agents/skills
for role in orchestrator task-planner developer code-reviewer qa-tester settings-optimizer production-triage; do
  [ -e ".agents/skills/$role" ] || ln -s "../../agent-orchestration/skills/$role" ".agents/skills/$role"
done
```

**3. Install the host launchers.** They carry the model and fork settings; the skill
bodies stay in the library.

```bash
# Claude Code: thin wrappers in .claude/skills/
mkdir -p .claude/skills
for role in orchestrator task-planner developer code-reviewer qa-tester settings-optimizer production-triage; do
  [ -e ".claude/skills/$role" ] || cp -R "agent-orchestration/adapters/claude-code/skills/$role" ".claude/skills/$role"
done
```

Codex: copy `agent-orchestration/adapters/codex/agents/<role>.toml` into `.codex/agents/`
for the five stage roles instead; see [adapters/codex/README.md](adapters/codex/README.md#install).

**4. Install the gate hooks and their configuration.**

```bash
mkdir -p .claude/hooks
cp agent-orchestration/gates/hooks/*.py .claude/hooks/
cp -n agent-orchestration/gates/hooks/gates.example.json .claude/hooks/gates.json
```

Edit `.claude/hooks/gates.json` from the profile's Human gates section: protected
branches, the files agents may not open, every command that publishes a release. With
no release rules the release gate blocks nothing. Codex: the same files go to
`.codex/hooks/`.

**5. Run the self-test before wiring anything.** A broken `PreToolUse` hook blocks every
later tool call, so this step is not optional.

```bash
python3 .claude/hooks/selftest.py        # must end with "0 failed"
```

**6. Wire the hooks into the host.** Merge the `hooks` block from
[`adapters/claude-code/hooks/settings.example.json`](adapters/claude-code/hooks/settings.example.json)
into the tracked `.claude/settings.json`. Codex: merge
[`adapters/codex/hooks.example.json`](adapters/codex/hooks.example.json) into
`.codex/hooks.json`, then review and trust the hooks with `/hooks`; an untrusted hook is
silently skipped.

**7. Install the git `pre-push` hook.** It sees the real push from any tool and is the
second layer behind the command parsers.

```bash
mkdir -p .githooks
cp agent-orchestration/gates/git/pre-push .githooks/pre-push
chmod +x .githooks/pre-push
git config core.hooksPath .githooks              # the owner runs this, once per clone
# git config --add agent-gates.protectedBranch develop   # if the base branch is not main/master
```

Run that `git config` yourself: `merge-gate.py` blocks every change to `core.hooksPath`
so that an agent cannot switch the hook off later. Where the hosting plan allows it, add
a server-side branch rule as well; a local hook cannot stop a merge made through the web
UI with your credentials.

**8. Commit the installation.** `.gitmodules` and the submodule pointer,
`.agents/profile.md`, the `.agents/skills/*` links, `.claude/skills/*`,
`.claude/hooks/*` including `gates.json`, `.claude/settings.json` and
`.githooks/pre-push`. Leave `.claude/settings.local.json` untracked, and let
`.agents/memory/` appear through a pipeline run rather than an empty directory.

**9. Check that the gates are live, then do a dry-run.**

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main"},"cwd":"'"$PWD"'"}' \
  | python3 .claude/hooks/merge-gate.py; echo "exit $?"     # expect "Blocked by merge-gate" and exit 2
```

Then, in Claude, run `/orchestrator Task: <a small real task>. Mode: dry-run.` It touches
neither your tracker nor your remote (see [Dry-run](#dry-run)). Confirm that each stage
ran as a separate subagent rather than inline, that the planner read your profile, and
that the final report names the verification command. Record what is actually enforced
in the profile's **Enforcement installed** field; the pipeline reports gaps from there.

Codex discovers the canonical packages through per-role links in the adopting project's
`.agents/skills/`. Claude uses thin skill launchers in `.claude/skills/` to supply its
model and fork settings. Install only these roles and preserve unrelated skills.

In Claude, invoke `/orchestrator <task>`; in Codex, invoke `$orchestrator` with the task.
The orchestrator stays in your conversation while each stage runs separately. You can
also invoke a stage skill directly when you want only that stage. Skills respect the
scope and mode you supplied; selecting a stage does not start the full pipeline.

## The roles

| Role | Owns | Never does |
|---|---|---|
| `orchestrator` | Requirement clarification, sequencing, git hygiene, issue cleanup, the final report | Writes code. Decomposes. Reviews. |
| `task-planner` | Decomposition into tracker issues with acceptance criteria | Implements |
| `developer` | Implementation, fix passes, the PR | Reviews its own work |
| `code-reviewer` | Reviewing the diff, blocking or approving | Fixes what it reviews |
| `qa-tester` | Acceptance criteria, the test suite, filing bugs | Fixes bugs |
| `settings-optimizer` | Consolidating the harness's permission config | Touches code or git |
| `production-triage` | Filing production errors as `needs-triage` issues (standalone, manual) | Touches code. Fixes anything. |

## Rules worth knowing before you run it

A handful of these exist because the obvious behaviour is the wrong one:

**Every code change made after QA begins passes review before QA can be called green.**
QA bug fixes are code. Skipping the review on them is how an unreviewed change ships
under a green verdict.

**You hold three gates; agents hold everything between them.** Accepting a design
decision, merging the PR, and publishing a release are yours. The rest runs without
you. Instructions alone are advisory, so the merge and release gates are also enforced
by hooks ([`gates/`](gates/)) — an agent that tries to merge is stopped, not trusted.

**One command defines "done".** The profile names a verification command — build,
tests, cheap static checks, a short summary. The developer runs it before reporting,
QA runs its fullest variant, and the reviewer doesn't re-report what it enforces.

**Review checks the change against what was asked.** A compliance pass compares the
PR with its decision records and issue criteria, both ways: missing work and work
nobody asked for. Findings are Important (blocking) or Nits (at most five, never
blocking). Bug fixes start from a failing test committed before the fix.

**Loops cap at three iterations, then stop and escalate.** A review loop that hasn't
converged in three passes is telling you the task is under-specified or the finding is
wrong. A fourth pass doesn't discover that.

**Bugs found outside the current change are filed but never block it.** QA labels them
`pre-existing`; Step 6 skips them and Step 8 refuses to close them. Filing everything and
scheduling separately beats the alternatives — silently not filing, or blocking a
finished PR on unrelated debt.

**Unmerged work is not closed.** Issues get a PR reference comment and stay open until
merge is confirmed. Closing the wrong one erases a tracked task.

**No blanket `git add .`.** Only durable artifacts, path by path. Anything uncertain goes
in the report for a human to decide.

**Step 0 resolves missing product decisions before planning.** The orchestrator can
clarify them with you in the main conversation and record the agreed design artifacts.
Small operational tasks can proceed without design documents. This keeps the stages
working from the same decisions.

## Harness support

| | Claude Code | Codex | Generic |
|---|---|---|---|
| Main entry point | `/orchestrator` skill | `$orchestrator` skill | Main-session runbook |
| Stage execution | Forked skills | Role TOMLs or explicit spawn configuration | Subagent with assembled context |
| Per-role model selection | Skill launcher frontmatter | Host configuration / role TOMLs | Host capability |
| Shared project memory | Explicit skill reads | Explicit skill reads | Explicit skill reads |
| Step 9 (settings) | ✅ applies | ⊘ no permission config | ⊘ usually none |
| Loop guardrails | orchestrator | orchestrator | orchestrator |

Each Codex role TOML includes commented `model` and `model_reasoning_effort` examples.
Uncomment them in the installed `.codex/agents/<role>.toml` to configure that role;
otherwise host defaults apply. See [Codex model configuration](adapters/codex/README.md#models-and-runtime-capabilities).

Every adapter is a **pointer** to `skills/<role>/SKILL.md`. Runtime files explain
launching and model selection; `PIPELINE.md` remains the shared workflow. All hosts
use `.agents/memory/<role>/` in the adopting project and explicitly load the
[shared memory rules](memory/RULES.md).

Existing `agents/<role>.md` paths remain compatibility pointers for earlier loaders
and historical references. For existing installations, follow the adapter's migration
instructions to switch orchestration into the main conversation and retire old Claude
agent registrations. In particular, do not copy Claude launchers through a
`.claude/skills` symlink into the canonical skill directory.

## Also here

- **[conventions/](conventions/)** — swappable repo conventions the roles reference:
  the issue tracker (GitHub `gh` by default), triage labels, and where domain docs live
- **[memory/](memory/)** — the agent memory layout, and the rule that keeps it from
  becoming a second, stale copy of the profile

## Dry-run

The whole pipeline with no writes to the tracker or the remote — plan to markdown, local
branch, no PR, bugs as a list. Useful for evaluating it on a new project before pointing
it at anything real. See the table at the end of [PIPELINE.md](PIPELINE.md).
