# Harness Adapters

Three ways to run the same pipeline. Every adapter is **thin**: it carries the
harness-specific wiring — registration format, model selection, launch mechanics — and
points at the canonical role prompt in [`../agents/`](../agents/). None of them
duplicates a role body.

That is deliberate. The moment an adapter contains a copy of a prompt, the copies drift,
and the pipeline behaves differently depending on which harness you ran it from. A
pointer cannot drift.

| Adapter | For | Registration |
|---|---|---|
| [`claude-code/`](claude-code/) | Claude Code | `.claude/agents/*.md` with frontmatter, auto-discovered |
| [`codex/`](codex/) | Codex | `.codex/agents/*.toml` |
| [`generic-harness/`](generic-harness/) | Any harness with a subagent primitive but no agent registry | Manual prompt assembly at launch |

## Installation

Vendor this repository into your project — submodule, subtree, or a plain copy — at
`<project-root>/agent-orchestration/`, then install the adapter you need. Each adapter's
README has the exact steps.

If you vendor it somewhere else, update the prompt paths inside the adapter files. They
are relative to the project root, and they are the only place the location appears.

## Choosing one

Use `claude-code/` if you're on Claude Code — it has a real subagent registry, so the
orchestrator can delegate by name and the harness handles model selection and memory.

Use `generic-harness/` for anything with a `subagent`-style primitive but no registry.
It is the most portable and the most explicit: the orchestrator assembles each prompt by
hand from a shim, the role file, and the step context. Its runbook also carries the
iteration guardrails as explicit counters, since there's no framework enforcing them.

Use `codex/` alongside either. Note that maintaining a third registration format for the
same six roles is real overhead — skip it unless you actually run the pipeline there.

## Adding an adapter

1. Create `adapters/<harness>/` with a README covering installation and launch.
2. For each role, write the harness's registration artifact with: the role name, a
   description good enough for delegation, model selection if the harness supports it,
   and a body that instructs the agent to read `agent-orchestration/agents/<role>.md`
   plus the active profile.
3. Do not paste role content. If the harness cannot read a file at runtime, generate the
   adapter from `agents/` in a build step rather than maintaining a copy by hand.
4. Note in the README how the harness handles the pieces the pipeline assumes: subagent
   launching, persistent memory, and whether it has a local permission config (which
   decides whether Step 9 applies).
