# Runtime Adapters

The main conversation runs the orchestrator skill. Stage skills supply the procedures;
an adapter supplies the host's launch mechanism, model selection and environment.
The canonical instructions live in [`../skills/`](../skills/) and the state machine
lives in [`../PIPELINE.md`](../PIPELINE.md).

| Adapter | Main conversation | Independent stage execution |
|---|---|---|
| [`claude-code/`](claude-code/) | `/orchestrator` | Native forked skills, with model metadata in thin Claude wrappers |
| [`codex/`](codex/) | `$orchestrator` | Thin TOML loaders when supported, or explicit launch configuration |
| [`generic-harness/`](generic-harness/) | Load the orchestrator skill | Assemble a skill and its handoff into a supported subagent launch |

Skills and subagents serve different purposes: loading a procedure does not create an
independent agent or select a model. Review and QA need separate agents from the
implementer; an adapter must preserve that boundary.

## Shared installation

Vendor this library at `<project-root>/agent-orchestration/`, then create a project
profile following [`../profiles/README.md`](../profiles/README.md). Keep the canonical
skills discoverable through individual links, preserving unrelated project skills:

```bash
if [ -L .agents/skills ]; then
  printf '%s\n' 'Inspect the existing .agents/skills symlink and adapt link targets first.'
else
  mkdir -p .agents/skills
  for role in orchestrator task-planner developer code-reviewer qa-tester settings-optimizer; do
    if [ -e ".agents/skills/$role" ] || [ -L ".agents/skills/$role" ]; then
      printf 'Preserving existing skill: %s\n' "$role"
    else
      ln -s "../../agent-orchestration/skills/$role" ".agents/skills/$role"
    fi
  done
fi
```

Run this from the adopting project root. Inspect any preserved same-name entry before
using it: a different skill is not an installed pipeline role. If `.agents/skills`
itself is a symlink, inspect its destination first and adapt the link targets to that
physical directory; the relative paths above assume a real project directory.

Then follow the chosen adapter's installation instructions. Do not copy Claude-specific
frontmatter into the canonical skills. Resolve skill symlinks to find the physical
library root, and use absolute paths for the target repository, profile, runtime adapter,
skill and design artifacts in every handoff. A vendored library directory is not the
target application's repository root.

All adapters use `<project-root>/.agents/memory/<role>/`. The canonical skills load
[`../memory/RULES.md`](../memory/RULES.md) and the role's index explicitly, respecting
the task's memory restrictions before reading. See
[`../memory/README.md`](../memory/README.md) for migration from host-specific memory.

## Maintaining an adapter

Keep host model defaults and user overrides in host configuration. A loader reads the
canonical skill and passes the complete handoff; it does not repeat the skill's
checklist, report format, pipeline transitions, loop limits or dry-run rules. If a
configured launch option cannot be honored, surface the mismatch before launching;
do not silently run a different model or execute an independent review inline.

Optional settings housekeeping depends on the runtime capability and active profile.
The canonical pipeline owns whether it runs and what dry-run means.
