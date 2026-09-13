# Shared Project Memory

Claude, Codex, and generic harnesses use the same project memory. The content belongs
to the adopting project; this library ships only the [shared rules](RULES.md).

## Layout

```text
<project-root>/.agents/memory/
├── orchestrator/
│   ├── MEMORY.md          # short index of links to topic notes
│   └── process-<topic>.md
├── task-planner/
├── developer/
├── code-reviewer/
├── qa-tester/
└── settings-optimizer/
```

Every canonical skill explicitly reads `memory/RULES.md` from the library, then its
project index if present, and only the topic notes relevant to its assignment. This
does not depend on a host's automatic memory feature. Missing indexes are normal;
create one only when there is useful knowledge to save.

Keep the active profile as the shared source for project structure, commands, and
conventions. Memory captures verified pitfalls, preferences, decision reasons, and
links to current sources. The rules define verification, note format, ownership,
concurrent writes, and the user's ability to restrict, remember, or forget information.

## Migrating existing memory

Review existing host-specific notes and merge useful content into the matching role
under `.agents/memory/`. The old Claude role `ai-orchestrator` maps to `orchestrator`.
Preserve existing notes and resolve overlaps by content; do not overwrite one host's
knowledge with another's or delete notes solely because of their filenames.

After migration, a project may expose `.claude/agent-memory` as a compatibility symlink
to `../.agents/memory`. It is optional: the new skills always read, edit, and stage the
canonical `.agents/memory/` paths. Inspect existing directories or symlinks before
changing them, and update old role-name references if keeping legacy launchers.

Project memory can be versioned with the adopting project. It is never stored inside
the vendored library or committed automatically just because a stage updated it. The
pipeline's artifact review decides what belongs in the task's changes.
