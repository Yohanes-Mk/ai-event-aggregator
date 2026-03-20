# Monitoring Phases Checklist

This file tracks the monitoring roadmap as a checklist another coding agent can continue without reconstructing context from chat history.

> **Convention:** Update this file whenever monitoring/analytics work advances.
> Mark checklist items as done only when the code is shipped in this repo.
> Add short dated notes under the relevant phase when scope changes, tradeoffs are decided, or implementation is partially complete.

---

## Phase 0 — Prerequisites

- [x] Persist run attribution metadata on `pipeline_runs`
- [x] Capture `git_sha` automatically at pipeline start
- [x] Support optional `PIPELINE_CONFIG_VERSION`
- [x] Surface run metadata in the recent-runs report
- [x] Update bootstrap script so existing Postgres tables gain the new columns
- [x] Persist prompt/model metadata for ranking and enrichment work

### Notes
- 2026-03-12: `git_sha` and `config_version` were added to `pipeline_runs`. Prompt/model metadata is deferred until ranking history and richer stage telemetry land.
- 2026-03-12: Stage metrics now also carry `model_name` and `prompt_version` for API-heavy stages.

## Phase 1 — Core Performance Analytics

- [x] Add normalized efficiency analytics (`seconds_per_item`, `items_per_minute`)
- [x] Add normalized before/after comparison support
- [x] Include normalized efficiency in stage-performance reporting
- [x] Keep raw duration analytics alongside normalized metrics
- [x] Add p95/p99 latency analytics once enough run history exists

### Notes
- 2026-03-12: Normalized efficiency is now available through the Python query layer, compare reports, and CLI surfaces.
- 2026-03-12: P95/P99 latency analytics were added with a Python percentile implementation so they work without Postgres-only SQL functions.

## Phase 2 — Ranking History Persistence

- [x] Add `curator_runs` table
- [x] Add `curator_rankings` table
- [x] Persist score, rank position, ranking reason, prompt version, and model name per ranking run
- [x] Add score drift and rank volatility queries
- [x] Expose ranking drift through CLI/Makefile

### Notes
- 2026-03-12: Curator runs and per-item rankings are now persisted. `process_curator()` ranks the last 7 days of digests instead of only same-day new digests, so ranking history can accumulate across runs.

## Phase 3 — Digest Freshness and Versioning

- [x] Add `digest_version`
- [x] Add `digest_generated_at`
- [x] Add `source_updated_at` or `content_last_seen_at`
- [x] Distinguish stale digests from fresh digests in monitoring
- [x] Add stale-digest and mixed-version queries

### Notes
- 2026-03-12: Existing digests are backfilled with version/freshness defaults through `scripts/create_tables.py`, and existing digests are now `touch`ed when seen again so freshness can diverge from generation time.

## Phase 4 — Batching, Retry, and Optimization Telemetry

- [x] Track batch size for API-heavy stages
- [x] Track total batches per stage run
- [x] Track retry/backoff counts
- [x] Track concurrency level where applicable
- [x] Add batch-performance and retry-summary queries

### Notes
- 2026-03-12: Batch/retry telemetry is now recorded on stage metrics. Existing historical runs predate the new columns, so the telemetry reports will show meaningful values only after fresh runs occur.
- 2026-03-12: Added persisted YouTube Shorts classification caching plus scrape telemetry for `youtube_short_checks`. Stage metrics now capture skipped items, cache hits, and network calls so Shorts filtering can be optimized with evidence instead of guesswork.

## Phase 5 — Rule-Based Summary Layer

- [x] Add deterministic monitoring summary logic
- [x] Emit focus areas with recommended actions
- [x] Expose summary through CLI and Makefile
- [x] Add regression severity scoring based on stronger baselines
- [x] Add freshness/ranking warnings once Phases 2 and 3 ship

### Notes
- 2026-03-12: Initial summary rules cover bottlenecks, regressions, instability, reliability issues, incomplete observability, and recent errors.
- 2026-03-12: Ranking-drift and stale-ranked-digest warnings are now included when the underlying data exists.
- 2026-03-12: Regression severity is now scored using both percentage change and absolute seconds-per-item increase.

## Phase 6 — Score and Ranking Concerns

- [x] Track score drift over time
- [x] Track ranking stability for existing items
- [x] Distinguish new-digest ranking from re-ranking of existing digests
- [x] Detect when stale digests dominate top-ranked results

## Phase 7 — Query Surface Expansion

- [x] Add digest freshness queries
- [x] Add ranking drift queries
- [x] Add batch/retry telemetry queries
- [x] Add top-focus-area helper query outputs for summary rendering

## Phase 8 — Operator Surface

- [x] Add Makefile shortcuts for common monitoring commands
- [x] Add `monitoring-summary`
- [x] Add ranking drift Make targets
- [x] Add digest freshness Make targets
- [x] Add `make help` if command discovery becomes friction

## Phase 9 — Timelessness and Schema Discipline

- [x] Keep stage grouping code-level unless schema pressure justifies promotion
- [x] Avoid stage-name-specific query assumptions
- [x] Only add telemetry fields when they unlock truthful analysis
- [ ] Reuse monitoring query helpers across CLI, dashboard, API, and MCP surfaces

---

## Next Recommended Build Order

1. Ranking history persistence
2. Reuse monitoring query helpers in future API/dashboard/MCP surfaces
3. Add provider/token/cost telemetry only when truthful cost analytics are needed
