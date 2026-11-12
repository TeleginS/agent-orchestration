---
name: save-session-log
description: "Manual run: save or refresh the current Claude Code conversation as a Markdown log in docs/ai-logs/."
argument-hint: "[slug for a new log]"
disable-model-invocation: true
---

Resolve the target project root from the invocation context, or the main session's
repository root for a direct invocation. Use the supplied absolute library root, or
resolve `<project-root>/agent-orchestration` physically, following symlinks.

Read `<library-root>/skills/save-session-log/SKILL.md` and apply that skill to this
invocation with `--host claude`. The current session id is `${CLAUDE_SESSION_ID}`;
pass it as `--session` unless it is empty or unexpanded. Use the slug from the
arguments below when creating a log:

$ARGUMENTS
