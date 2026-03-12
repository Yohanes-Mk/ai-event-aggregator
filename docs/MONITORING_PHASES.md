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
- [ ] Persist prompt/model metadata for ranking and enrichment work

### Notes
- 2026-03-12: `git_sha` and `config_version` were added to `pipeline_runs`. Prompt/model metadata is deferred until ranking history and richer stage telemetry land.

## Phase 1 — Core Performance Analytics

- [x] Add normalized efficiency analytics (`seconds_per_item`, `items_per_minute`)
- [x] Add normalized before/after comparison support
- [x] Include normalized efficiency in stage-performance reporting
- [x] Keep raw duration analytics alongside normalized metrics
- [ ] Add p95/p99 latency analytics once enough run history exists

### Notes
- 2026-03-12: Normalized efficiency is now available through the Python query layer, compare reports, and CLI surfaces.

## Phase 2 — Ranking History Persistence

- [ ] Add `curator_runs` table
- [ ] Add `curator_rankings` table
- [ ] Persist score, rank position, ranking reason, prompt version, and model name per ranking run
- [ ] Add score drift and rank volatility queries
- [ ] Expose ranking drift through CLI/Makefile

## Phase 3 — Digest Freshness and Versioning

- [ ] Add `digest_version`
- [ ] Add `digest_generated_at`
- [ ] Add `source_updated_at` or `content_last_seen_at`
- [ ] Distinguish stale digests from fresh digests in monitoring
- [ ] Add stale-digest and mixed-version queries

## Phase 4 — Batching, Retry, and Optimization Telemetry

- [ ] Track batch size for API-heavy stages
- [ ] Track total batches per stage run
- [ ] Track retry/backoff counts
- [ ] Track concurrency level where applicable
- [ ] Add batch-performance and retry-summary queries

## Phase 5 — Rule-Based Summary Layer

- [x] Add deterministic monitoring summary logic
- [x] Emit focus areas with recommended actions
- [x] Expose summary through CLI and Makefile
- [ ] Add regression severity scoring based on stronger baselines
- [ ] Add freshness/ranking warnings once Phases 2 and 3 ship

### Notes
- 2026-03-12: Initial summary rules cover bottlenecks, regressions, instability, reliability issues, incomplete observability, and recent errors.

## Phase 6 — Score and Ranking Concerns

- [ ] Track score drift over time
- [ ] Track ranking stability for existing items
- [ ] Distinguish new-digest ranking from re-ranking of existing digests
- [ ] Detect when stale digests dominate top-ranked results

## Phase 7 — Query Surface Expansion

- [ ] Add digest freshness queries
- [ ] Add ranking drift queries
- [ ] Add batch/retry telemetry queries
- [ ] Add top-focus-area helper query outputs for summary rendering

## Phase 8 — Operator Surface

- [x] Add Makefile shortcuts for common monitoring commands
- [x] Add `monitoring-summary`
- [ ] Add ranking drift Make targets
- [ ] Add digest freshness Make targets
- [ ] Add `make help` if command discovery becomes friction

## Phase 9 — Timelessness and Schema Discipline

- [ ] Keep stage grouping code-level unless schema pressure justifies promotion
- [ ] Avoid stage-name-specific query assumptions
- [ ] Only add telemetry fields when they unlock truthful analysis
- [ ] Reuse monitoring query helpers across CLI, dashboard, API, and MCP surfaces

---

## Next Recommended Build Order

1. Ranking history persistence
2. Digest freshness/version tracking
3. Batch/retry telemetry
4. Summary-layer expansion over the new telemetry
