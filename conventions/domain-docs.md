# Convention: Domain Documentation

Where the durable design artifacts live. Step 0 of [`PIPELINE.md`](../PIPELINE.md)
checks for these; every role reads them when they cover the area being worked on.

## The two artifacts

- **`CONTEXT.md`** at the repository root — the domain glossary, the project's
  ubiquitous language.
- **`docs/adr/`** — architecture decision records, one per decision, numbered.

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0000-architecture-overview.md
│   ├── 0001-<decision>.md
│   └── ...
└── <source>/
```

For a monorepo with several bounded contexts: a `CONTEXT-MAP.md` at the root pointing
at per-context `CONTEXT.md` files, with context-scoped ADRs under
`src/<context>/docs/adr/`.

## If they don't exist

**Proceed silently.** Don't flag their absence and don't propose creating them upfront.
They are written lazily, when a term or a decision actually needs resolving — a glossary
authored speculatively documents vocabulary nobody has committed to yet.

Step 0 has exactly one case where their absence stops the pipeline: a task that requires
genuine product or design decisions. That stop is not "the docs are missing"; it is
"nobody has decided this yet, and four agents are about to each decide it differently."

## Using the glossary

When your output names a domain concept — an issue title, a refactor proposal, a
hypothesis, a test name — use the term as `CONTEXT.md` defines it. Don't drift to
synonyms the glossary explicitly rejects.

If the concept you need isn't in the glossary, that's a signal. Either you're inventing
language the project doesn't use — reconsider — or there's a real gap worth noting.

## Conflicting with an ADR

Surface it. Don't silently override:

> _Contradicts ADR-0002 (tab-bar navigation), but worth reopening because…_

An ADR is a record of a decision, not a law. Reopening one is legitimate; doing it
without saying so is how a codebase ends up with two contradictory decisions and no
record of which won.
