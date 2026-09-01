# Convention: Triage Labels

Canonical triage vocabulary, mapped to whatever your tracker actually uses. Roles and
skills speak in terms of the role; this table resolves it to a string.

| Canonical role | Label in this tracker | Meaning |
|---|---|---|
| `needs-triage` | `needs-triage` | A maintainer needs to evaluate this |
| `needs-info` | `needs-info` | Waiting on the reporter |
| `ready-for-agent` | `ready-for-agent` | Fully specified — an unattended agent can take it |
| `ready-for-human` | `ready-for-human` | Requires human judgment to implement |
| `wontfix` | `wontfix` | Will not be actioned |

Edit the right-hand column to match your own vocabulary. When a role says "apply the
agent-ready triage label", it means the string in that column.

Labels are created on first use if they don't exist.

## Relationship to the pipeline labels

These are orthogonal to the labels in [`issue-tracker.md`](issue-tracker.md). Those
(`bug`, `pre-existing`, `size:*`, `severity:*`) are set by the pipeline as it runs and
read back by later steps. These are for humans deciding what enters a pipeline in the
first place.

`ready-for-agent` is the useful one: it marks an issue whose acceptance criteria are
concrete enough that Step 0 can skip the design gate and go straight to planning.
