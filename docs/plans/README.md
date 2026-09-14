# Execution Plans

Execution plans are Git-native working memory for complex tasks. They preserve
enough context for another agent or human to resume work without reconstructing
intent from chat history or a partial diff.

## When To Create A Plan

Use an ephemeral plan for bounded, single-session work.

Create one durable plan when work spans sessions, coordinates contributors, has
meaningful dependencies or ordering, requires recovery steps, or would be unsafe
to resume from the diff alone.

Use `docs/templates/exec-plan.md` and place the file under `active/`.
For an explicitly authorized baseline-to-rerun Harness experiment, use
`docs/templates/harness-improvement.md` instead.

## Lifecycle

```text
docs/plans/active/<slug>.md
  -> update progress and decisions during implementation
  -> record final validation and result
  -> move to docs/plans/completed/<slug>.md
```

The plan is the primary task artifact. Promote a lasting product or architecture
decision into `docs/decisions/`; keep task-local choices in the plan.

## Active Plans

- [`active/master-plan.md`](active/master-plan.md) — thesis timeline and project
  progress; the source of truth for status.
- [`active/backfill-corpus-v2.md`](active/backfill-corpus-v2.md) — backfill,
  scope rules and snapshot v2 before M1 (master plan P2.7–P2.12).

## Completed Plans

- [`completed/2026-09-04-truoc-stage-6.md`](completed/2026-09-04-truoc-stage-6.md)
  — status-code table, Stage 5b text attachment, delta crawl.
