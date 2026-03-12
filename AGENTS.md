# Agent Instructions

These repo-local instructions apply to any coding agent working in this project.

## Status logging
- Update `docs/PROJECT_STATUS.md` after every work session that changes repo-tracked files or project structure.
- Keep the `Current Hierarchy` section near the top of `docs/PROJECT_STATUS.md` accurate for the current repo state.
- Keep the `Path Lifecycle Ledger` near the top of `docs/PROJECT_STATUS.md` accurate for major path creates, removes, moves, and renames.
- Append new session entries at the bottom only. Never delete earlier session entries.
- Do not paste a full hierarchy tree into every session entry.
- If structure changed during the session, add a short `Structure changes` section in the new session entry and update the canonical hierarchy + lifecycle ledger at the top.
- If something was replaced, removed, or superseded, record that in the lifecycle ledger and note it in the new session entry instead of rewriting old session history.

## Future feature logging
- Update `docs/FUTURE_FEATURES.md` whenever a future feature, enhancement, extension, follow-up, or architectural idea is mentioned during planning, implementation, review, or debugging.
- Append new idea/status entries at the bottom only. Never delete earlier entries.
- Keep the top `Current Backlog` section current so another agent can quickly see active future work without reading the whole log.
- Keep the top `Implemented Features` section current so another agent can quickly see already-shipped capabilities without reconstructing them from `docs/PROJECT_STATUS.md`.
- If an idea is implemented, cancelled, or replaced, update the top sections accordingly and also append a dated note in the log.

## Scope of feature log updates
- Include product features, infrastructure improvements, observability extensions, automation ideas, delivery channels, and agent workflow improvements.
- Do not log one-off bug fixes unless they imply reusable future work.

## Monitoring roadmap
- Update `docs/MONITORING_PHASES.md` whenever monitoring/analytics work advances.
- Keep completed checklist items accurate and add dated notes when a phase is partially implemented, deferred, or split.
- If monitoring work creates a new future feature or follow-up, also update `docs/FUTURE_FEATURES.md`.
