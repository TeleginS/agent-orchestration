# Shared Agent Memory Rules

## Location and loading

Memory stores knowledge that helps future tasks: collaboration preferences, reasons
for decisions, verified pitfalls, and useful source references.

- Canonical path: `<project-root>/.agents/memory/<role>/` across all hosts.
- `MEMORY.md` is a short index; separate Markdown files contain topic notes.
- Every skill explicitly reads these rules, its role's index if present, and only the
  relevant notes. Do not assume the host loads them automatically.
- Read, edit, and stage the canonical path, even when a compatibility symlink exists.

## Reading and recording

1. Respect explicit memory restrictions before reading: do not read, apply, or modify
   memory within the restricted scope. Pass the restriction to delegated stages.
   A targeted request to remember or forget authorizes only that targeted change.
2. Verify information that can change against its current source before using it.
   Code establishes current behavior; an ADR records an accepted decision. Investigate
   discrepancies. Memory does not override instructions or expand permissions.
3. Save useful lessons from success as well as failure, when they will matter beyond
   this task. Update an existing topic instead of creating a duplicate.
4. At the end of a stage, write only useful new knowledge or corrections. If nothing
   changed, do not add a record, refresh dates, or create an empty index.

Good candidates include an explicit user preference with its scope, a decision reason
not apparent in code, a reproducible technical pitfall with a verified workaround,
and a link to an ADR or source that prevents repeated investigation.

Do not copy module inventories, signatures, dependency versions, test counts, branch
state, task reports, or PR histories into memory as snapshots. Project structure and
conventions belong in the active profile; tasks and bugs belong in the tracker;
decisions belong in ADRs; change history belongs in Git. Retain the reusable lesson
and source link. Keep unverified hypotheses in the current report or issue. Do not
record secrets or unnecessary personal data.

Handle an explicit remember or forget request within its stated scope, including the
relevant role. Remove only the specified lesson; delete a file and its index entry
only if no useful content remains. Check affected cross-role links. This targeted
request can authorize editing another role's memory; ordinary stage work cannot.

## Note format

Keep one coherent topic per file and preserve useful existing formats. For new notes:

```markdown
---
name: short-topic-name
description: When this note is useful
metadata:
  type: feedback
---

The lesson, with its conditions and significant exceptions.

**Why:** The reason and consequences.
**When to apply:** Scope and exceptions.
**Source:** A dated user message, issue/PR, ADR, or documentation.
**Verified:** YYYY-MM-DD; environment or version when relevant.
```

Types are `user`, `feedback`, `project`, and `reference`. Omit sections that do not
help. Provide a source for new or substantially revised lessons and a verification
date for facts that can become stale. Never attribute an assumption to the user.

In `MEMORY.md`, add a relative link and short description per topic. The index has no
YAML frontmatter and no detailed rules. Create missing directories only when saving
a useful note. Link to another role's canonical note rather than duplicating it.

## Ownership and concurrent work

- During an ordinary stage, update only `.agents/memory/<your-role>/`. Shared rules
  and another role's notes are maintained in a separate maintenance task.
- Send findings for another role to the orchestrator with a source and suggested owner.
- Reread the file and index before editing. Preserve others' entries with targeted
  edits. When writes overlap, coordinate a single writer through the orchestrator.
- Check links and the diff after editing. Memory alone never triggers a commit or push;
  the current task determines commit scope.
- Audit-only settings work edits neither settings nor memory. Other stages retain
  their supplied mode and memory restrictions; dry-run artifact review does not commit.

## Revision

Correct inaccuracies in your own notes when encountered. Route corrections for other
roles through the orchestrator, and do not apply a lesson known to be stale. Review
memory after major changes or when requested: merge duplicates, verify changing facts,
and replace architecture snapshots or run logs with links to current sources.

Do not delete notes just because their names start with `arch-` or `history-`. Review
the content and preserve useful reasons, conditions, and exceptions. Split long notes
when they cover distinct topics, not merely to meet an arbitrary length limit.

## Role guidance

| Role | Especially useful knowledge |
|---|---|
| `orchestrator` | Collaboration agreements and reasons for process changes |
| `task-planner` | Reasons for task boundaries, dependencies, and decomposition exceptions |
| `developer` | Verified implementation pitfalls and reasons for choosing an approach |
| `code-reviewer` | Recurring causes of defects and checks that uncovered them |
| `qa-tester` | Reproducible edge cases and confirmed verification limitations |
| `settings-optimizer` | Verified permission-matching behavior and safe generalization limits |
