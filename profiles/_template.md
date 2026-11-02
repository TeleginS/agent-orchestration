# Profile: <PROJECT NAME>

> Copy this file to `<project-root>/.agents/profile.md` and fill in every section (or
> keep it elsewhere and point the orchestrator at it explicitly). Keep every heading —
> write an explicit "None" where a section genuinely does not apply.
>
> **Precedence: observed code > this profile > the role prompts.** Agents are told to
> follow the code when this file is wrong, and to report the drift. Fix it when they do.

## Identity

- **Project**: <name and one-line description>
- **Repository root**: <path>
- **Remote / tracker**: <org/repo>
- **Base branch**: <main | master | develop>

## Stack

- **Language / runtime**: <e.g. TypeScript 5.4 on Node 20>
- **Framework**: <e.g. Next.js 14 App Router>
- **Minimum platform / target**: <e.g. Node 20, or iOS 16, or evergreen browsers>
- **Architecture pattern**: <e.g. MVVM, hexagonal, feature-sliced>
- **Key dependencies**: <the two or three that shape the code>

## Layout

Where things live, and the names that mislead.

```
<tree of the directories that matter — source, tests, resources, config>
```

- **Source**: <path>
- **Tests**: <path>
- **Resources / assets**: <path>
- **Naming trap**: <e.g. the directory is `app/` but the module is named `web` — the
  kind of mismatch that costs an agent three wrong greps>

## Verification command

The single definition of "done". The developer runs it before reporting, QA runs the
fullest variant before any verdict, and the reviewer does not re-report what it checks.
It exits non-zero on any failure and prints a short summary, not raw tool logs.

```bash
<script>            # e.g. lint + locale-key parity, build, unit tests
<script> --full     # the slower variant: UI / end-to-end tests
```

- **What it enforces**: <the checks, so the reviewer can exclude them>
- **Healthy output**: <two or three lines of a passing run>
- **Typical duration**: <so agents pick a long enough timeout and run it in the foreground>
- **QA variant**: <the variant QA runs before a verdict — the fullest one unless it is
  impractical on every change, e.g. `<script> --full`, or `<script>` plus the UI tests of
  touched screens>
- **Time budget**: <the longest one QA run may take before QA reports "blocked by
  environment", e.g. 30 minutes>
- **Base-version checks**: <how QA builds and tests the pre-change commit to prove a bug
  pre-existing without a full rebuild — a shared build cache, a reusable worktree path,
  running only the failing tests>
- **Shared resources**: <simulators, devices, ports or databases that one run occupies,
  and what to do when another session holds them>

Write "None — use the build and test commands below" if the project has no such script
yet; adding one is usually the first improvement worth making.

## Commands

Exact, copy-pasteable, including any prefix this machine requires. Use these for
targeted debugging; the verification command above is the definition of "done".

```bash
# Build
<command>

# Test — the mandatory QA gate
<command>

# Lint / format
<command>

# Discover test targets or devices before running (if applicable)
<command>
```

- **Required prefix or environment**: <e.g. an explicit toolchain path this machine
  needs, without which the bare command fails>
- **Known-bad invocations**: <the wrong ones that look right, so agents skip them>

## Architecture invariants

The facts that are always true, and the ones that are always false.

- **Core modules**: <name — path — responsibility, one line each>
- **Single decision points**: <the rule that has exactly one home, and where — e.g.
  "all access-control decisions go through `AccessPolicy`; nothing else decides">
- **State and persistence**: <mechanism, key conventions>
- **Data model layering**: <if raw and resolved forms exist, where conversion happens>
- **Does NOT exist**: <modules that were renamed or removed but still appear in old
  docs, issues or agent memory. This list is the highest-value part of the profile.>

## Critical flags and release gates

Things that must never ship wrong. The reviewer and QA check these every pass.

- `<FLAG>` in `<file>` must be `<value>` in production
- <Placeholder URLs, keys or endpoints that must be real before release>
- <Configuration that must be set in an external dashboard>

## Human gates

What the owner alone does, and how it is enforced. See `gates/README.md` in the library.

- **Merge**: <who merges; protected branch names>
- **Release**: <the commands that publish a build or package, which agents must never
  run — e.g. a store upload tool, `npm publish`, a deploy command>
- **Secrets**: <files agents must never read — e.g. `.env`, a secrets config — and the
  example file they may read instead>
- **Enforcement installed**: <harness hooks, git pre-push via `core.hooksPath`,
  server-side branch rules — or "none yet">
- **Known exceptions**: <e.g. a release script that pushes a version bump straight to
  the base branch, and the allow-script that permits only that>

## Access control / gating rules

The exact limits, if the product has them. Vague gating rules produce vague QA.

- <capability>: <free/paid, quotas, resets>
- <capability>: <...>

## Localization

- **Mechanism**: <how strings are externalized and looked up>
- **Locale files**: <every file that must be updated together>
- **Content vs UI**: <if content strings use a different mechanism, say so>

## Review checklist additions

Stack-specific items the reviewer adds to the universal checklist in
`skills/code-reviewer/SKILL.md`, grouped by its severity headings.

- 🔴 **Critical**: <...>
- 🟠 **Architectural**: <...>
- 🟡 **Correctness**: <...>
- 🟢 **Quality**: <...>

## Review exclusions

Paths and content the reviewer skips: generated code, bulk data or content files,
binary fixtures. Checks enforced by the verification command are excluded already.

- <path or glob> — <why>

## Anti-patterns

Code smells specific to this stack, beyond the universal list in `skills/developer/SKILL.md`.

- <...>

## Known risk areas

Where bugs keep coming from. QA starts here.

- <component> — <the failure mode it has a history of>

## Production error source

Where `production-triage` reads errors. Write "None" if the project has no production
error tracking yet.

- **Tool**: <e.g. an error-tracking MCP server or CLI, and the project/environment id>
- **Window**: <default 7 days>
- **Threshold**: <new in the window, or at least N affected users — default 3>
- **Filters to keep**: <e.g. exclude internal and test accounts>

## Output language

- **Tracker issues and PR text**: <language>
- **Code, identifiers, commit messages**: <language>
- **Technical terms**: keep in their original form regardless

## Harness settings

- **Local permission config**: <path, or "none — skip Step 9">
- **Habitual command prefixes** the optimizer must preserve in generalized patterns:
  <...>
