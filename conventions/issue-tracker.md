# Convention: Issue Tracker

Where issues live and how agents drive them. **Swap this file to change trackers** — the
role prompts only ever say "the tracker", never "GitHub".

Default: **GitHub Issues**, via the `gh` CLI.

## Operations

- **Create**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line
  bodies rather than escaping newlines.
- **Read**: `gh issue view <number> --comments`
- **List**:
  ```bash
  gh issue list --state open --json number,title,body,labels,comments \
    --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'
  ```
  with `--label` and `--state` filters as needed.
- **Comment**: `gh issue comment <number> --body "..."`
- **Label**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Create a label**: `gh label create <name>`
- **Close**: `gh issue close <number> --comment "..."`

The repo is inferred from the git remote — `gh` does this automatically inside a clone.

## Pull requests

- **Create**: `gh pr create --title "..." --body "..." --base <base-branch>`
- **Review with findings**: `gh pr review <number> --request-changes --body "..."`
- **Approve**: `gh pr comment <number> --body "..."` — see the constraint below
- **Comment**: `gh pr comment <number> --body "..."`
- **Diff**: `git fetch origin <base> && git diff origin/<base>...HEAD`

Fetch the base before diffing. A review computed against a stale base reviews changes
that already landed.

### The self-approval constraint

Every agent in the pipeline authenticates as the same user, so the reviewer is the author
of the PR it is reviewing. GitHub rejects that:

```
gh pr review <n> --approve
> Can not approve your own pull request
```

`--request-changes` works fine on your own PR; only `--approve` is blocked. So:

- **Blocking findings** → `gh pr review --request-changes --body "..."`, as normal.
- **Approval** → post the verdict with `gh pr comment`, opening with the literal
  `✅ APPROVAL` (or `**Verdict: ✅ APPROVED**`) so the orchestrator and any human reader
  can find it. Say in the comment that it is posted as a comment because self-approval is
  blocked, so nobody reads the missing green check as an unfinished review.

The orchestrator gates Step 5 on the reviewer's **reported verdict**, not on GitHub's
review state. Do not wait for an approval that cannot be given.

If you run agents under separate accounts or a bot token, this constraint disappears and
`--approve` works — but the verdict string stays mandatory either way, because that is
what the pipeline parses.

## Labels the pipeline relies on

| Label | Set by | Meaning |
|---|---|---|
| `epic` | task-planner | The overview issue |
| `epic:<name>` | task-planner | Groups an epic's children |
| `size:S\|M\|L\|XL` | task-planner | Estimated size |
| `blocked` | task-planner | Has an unmet dependency |
| `bug` | qa-tester | Every filed defect |
| `pre-existing` | qa-tester | Not introduced by this PR — never enters the fix loop, never auto-closed |
| `severity:critical\|high\|medium\|low` | qa-tester | Triage severity |
| `component:<name>` | qa-tester | Module, from the profile's module list |

`pre-existing` is the one with teeth: Step 6 reads it to decide what blocks the run, and
Step 8 reads it to decide what must stay open.

## When a role says…

- **"publish to the tracker"** → create an issue
- **"fetch the relevant ticket"** → `gh issue view <number> --comments`
- **"leave findings on the PR"** → `gh pr review --request-changes`, not only a report
  back to the orchestrator

## Swapping trackers

Rewrite the Operations and Pull requests sections for your tool and keep the label table
semantically intact. The pipeline needs: an issue with a body and labels, comments, a
close operation, and a reviewable change request. Anything providing those works.

If your tracker has no equivalent of a label, encode the same distinctions in a field
the queries in Step 6 and Step 8 can filter on. The pipeline does not care what it is
called; it cares that "pre-existing" is machine-checkable.
