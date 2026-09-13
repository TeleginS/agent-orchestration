# Canonical pipeline skills

These six skills are the single source of truth for role behavior. The
[pipeline](../PIPELINE.md) defines stage order, gates, loops, modes, and housekeeping;
skills carry each role's engineering checks and report contract.

| Skill | Responsibility |
|---|---|
| [orchestrator](orchestrator/SKILL.md) | Coordinate the whole run from the main conversation |
| [task-planner](task-planner/SKILL.md) | Produce planning issues and acceptance criteria |
| [developer](developer/SKILL.md) | Implement and address review/QA findings |
| [code-reviewer](code-reviewer/SKILL.md) | Review independently and return findings or `✅ APPROVAL` |
| [qa-tester](qa-tester/SKILL.md) | Run tests, verify criteria, classify and report bugs |
| [settings-optimizer](settings-optimizer/SKILL.md) | Optional permission housekeeping or a standalone audit |

Canonical frontmatter contains only `name` and `description`. Runtime-specific
discovery, model choices, and subagent launching live in the
[adapters](../adapters/README.md), including Claude wrappers that configure foreground
forked stages. Loading a canonical skill alone does not select a model or create an
independent agent. Historical [agents/](../agents/README.md) entries are compatibility
pointers to these files.

Each stage receives the original task, an absolute active profile path, design
artifacts, mode, branch/PR, ownership, constraints, and the inputs for its current pass.
It completes that stage and returns the defined result to its caller; it does not
start the full pipeline recursively. Stage-specific requests can use the same skills
without launching the whole pipeline, while preserving each stage's prerequisites.

## Paths and project context

Resolve symlinks first. From the physical `skills/<role>/` directory, `../..` is the
library root. Resolve pipeline, convention, profile-resolution, memory-policy, and
adapter links from that library. Resolve app files, settings, local run plans, and
`.agents/memory/<role>/` from the target project root supplied in the handoff. The
default installation can be `<project>/agent-orchestration/`; the library root and
project root are distinct even in that layout.

Keep stack and project details in the [active profile](../profiles/README.md): build
commands, modules, framework rules, release gates, and output language. Use current
code to verify factual claims in the profile, report drift, and preserve the task's
intended behavior rather than treating an existing bug as the requirement.

## Memory and maintenance

Every stage explicitly reads [memory/RULES.md](../memory/RULES.md), its project role
index, and only relevant notes, unless the user restricts memory use. Save useful,
sourced lessons rather than snapshots or completion logs. Keep role ownership and
coordinate concurrent changes under the shared rules.

Keep report contracts stable: issue/PR identifiers, the explicit reviewer verdict,
and QA's separate blocking and verified pre-existing lists. Put cross-stage rules in
`PIPELINE.md` and host-specific behavior in adapters so there is one place to change
each concern.
