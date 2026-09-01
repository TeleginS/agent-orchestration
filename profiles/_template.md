# Profile: <PROJECT NAME>

> Copy this file, fill in every section, and name it `active.md` (or point the
> orchestrator at it explicitly). Keep every heading — write an explicit "None" where a
> section genuinely does not apply.
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

## Commands

Exact, copy-pasteable, including any prefix this machine requires.

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
`agents/code-reviewer.md`, grouped by its severity headings.

- 🔴 **Critical**: <...>
- 🟠 **Architectural**: <...>
- 🟡 **Correctness**: <...>
- 🟢 **Quality**: <...>

## Anti-patterns

Code smells specific to this stack, beyond the universal list in `agents/developer.md`.

- <...>

## Known risk areas

Where bugs keep coming from. QA starts here.

- <component> — <the failure mode it has a history of>

## Output language

- **Tracker issues and PR text**: <language>
- **Code, identifiers, commit messages**: <language>
- **Technical terms**: keep in their original form regardless

## Harness settings

- **Local permission config**: <path, or "none — skip Step 9">
- **Habitual command prefixes** the optimizer must preserve in generalized patterns:
  <...>
