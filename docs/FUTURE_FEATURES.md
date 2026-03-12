# Future Features Log

This file tracks future features, enhancements, and follow-up ideas that come up during work.

> **Convention:** Update this file whenever a future feature, enhancement, extension, or follow-up idea is mentioned.
> Keep the **Current Backlog** section up to date so another agent can act on it quickly.
> Keep the **Implemented Features** section up to date so another agent can see what already exists.
> Append new dated entries at the bottom only. Never delete earlier entries.
> If an idea is implemented, cancelled, or replaced, update the top sections and note the change in a new dated entry instead of rewriting history.

---

## Implemented Features

| Feature | Shipped | Notes | Source |
|---|---|---|---|
| YouTube Scraper Pipeline | 2026-03-10 | RSS-based YouTube scraper with transcript support and Shorts filtering. | Initial scraper sessions |
| Event Scraper Pipeline | 2026-03-10 | iCal event scraping with 25 feeds, deduplication, and feed-level resilience. | Event scraper sessions |
| Postgres Persistence Layer | 2026-03-10 | SQLAlchemy models, repository functions, and table bootstrap script. | DB layer + cleanup session |
| AI Digest Generation | 2026-03-11 | OpenAI-powered YouTube digests stored in `digests`. | Digest infrastructure session |
| Event AI Enrichment | 2026-03-11 | Events get inline AI summary and relevance score on the `events` row. | Curator refactor session |
| Curator Ranking | 2026-03-11 | Personalized ranking over recent digests using user context. | Curator agent session |
| Email Digest Delivery | 2026-03-11 | Gmail-based YouTube and events digest emails with HTML rendering. | Email agents session |
| Dashboard Mock UI | 2026-03-11 | Standalone HTML dashboard with mock data and expandable event list. | HTML dashboard session |
| Pipeline Monitoring Foundation | 2026-03-12 | Structured logging, run/stage/error tracking, and monitoring CLI report. | Monitoring foundation session |
| Monitoring Query Layer | 2026-03-12 | Reusable analytics helpers, richer monitoring CLI modes, and SQL reference docs. | Monitoring query layer session |
| Rule-Based Monitoring Summary | 2026-03-12 | Deterministic focus-area summary over monitoring analytics with direct operator recommendations. | Monitoring phases session |
| Ranking History Persistence | 2026-03-12 | Curator runs and per-item rankings are now stored so score drift and ranking stability can be analyzed. | Monitoring phases session |
| Digest Freshness and Versioning | 2026-03-12 | Digests now track generation/version/freshness metadata for stale-content analysis. | Monitoring phases session |
| Batch/Retry Telemetry | 2026-03-12 | Stage metrics now record batch, retry, backoff, concurrency, model, and prompt telemetry for API-heavy stages. | Monitoring completion session |
| YouTube Shorts Classification Cache | 2026-03-12 | Shorts checks now use a persisted classification cache plus scrape telemetry for cache hits, network calls, and filtered Shorts. | Shorts optimization session |

## Current Backlog

| Feature | Status | Why it exists | Source |
|---|---|---|---|
| Slack Alert Handler | Proposed | Send pipeline completion and error alerts through the monitoring `AlertHandler` interface without changing pipeline code. | Monitoring planning + implementation |
| APScheduler Pipeline Runner | Proposed | Run the full pipeline on a schedule instead of only manual `main.py` execution. | Repeated `What's next` backlog |
| FastAPI Digest API | Proposed | Serve digests, events, monitoring data, and dashboard content from a real API layer. | Repeated `What's next` backlog |
| Live Dashboard Data Wiring | Proposed | Replace dashboard mock data with API-backed content. | Dashboard session backlog |
| Monitoring HTML Report | Proposed | Add a richer visual run report using monitoring data and existing templates. | Monitoring evolution path |
| Metrics Export / Prometheus Adapter | Proposed | Export stage timing and failure data to external metrics systems without changing stage tracking. | Monitoring evolution path |
| Monitoring Telemetry Extension | Proposed | Add provider/model/token/cost telemetry so future analytics can answer billing and model-usage questions honestly. | Monitoring query layer next track |
| Pipeline Error Retention Automation | Proposed | Automate cleanup of old `pipeline_errors` rows instead of relying on manual SQL. | Monitoring implementation follow-up |
| Slack Digest Delivery | Proposed | Deliver curated content through Slack in addition to email. | Earlier notification backlog |
| Interactive Channel Selector Wiring | Proposed | Wire `app/scrapers/youtube/selector.py` into the main workflow when interactive channel picking is needed. | 2026-03-11 selector session |
| YouTube Email Channel Metadata Hardening | Proposed | Fix incomplete channel/source metadata so email rendering never shows unknown channel values. | 2026-03-11 email session |

---

## 2026-03-12 — Future feature log initialized

### What was added
- Created this append-only future feature tracker so product and infrastructure ideas do not get lost across chats or agents.
- Added a current backlog seeded from existing project history and recent monitoring design work.

### Initial backlog sources
- Repeated project backlog items from `docs/PROJECT_STATUS.md`: scheduler, API layer, dashboard wiring, Slack/delivery expansion.
- Monitoring follow-ups from recent design/implementation work: Slack alerts, HTML report, metrics export, automated error retention.
- Previously shelved workflow ideas already mentioned in project history: interactive channel selector wiring and YouTube email metadata hardening.

### Notes
- `Implemented Features` is the quick shipped-capabilities summary.
- `Current Backlog` is the quick future-work summary.
- Detailed completed work history still lives in `docs/PROJECT_STATUS.md`.
- If a future feature becomes active implementation work, keep it in the backlog until it is actually shipped, then move it into `Implemented Features` and record the shipped work in `docs/PROJECT_STATUS.md`.

---

## 2026-03-12 — Implemented features section added

### What was added
- Added a top-level `Implemented Features` section so the feature log shows both future work and shipped capabilities.
- Seeded the section with major capabilities already built, using `docs/PROJECT_STATUS.md` as the source of truth.

### Why this changed
- The backlog alone did not answer “what do we already have?”
- Agents should be able to see both current capabilities and future plans from the same document.

---

## 2026-03-12 — Monitoring query layer added to capability summary

### What changed
- Added `Monitoring Query Layer` to `Implemented Features`.
- Added `Monitoring Telemetry Extension` to `Current Backlog` as the next-step follow-up for truthful future cost and model-usage analytics.

### Why this changed
- The monitoring system now has a reusable analytics layer, not just raw tables plus one terminal report.
- True cost analysis still needs telemetry that does not exist yet, so it remains future work.

---

## 2026-03-12 — Monitoring phases checklist + next telemetry backlog

### What changed
- Added `Rule-Based Monitoring Summary` to `Implemented Features`.
- Added new backlog items for:
  - `Ranking History Persistence`
  - `Digest Freshness and Versioning`
  - `Batch/Retry Telemetry`
- Added `docs/MONITORING_PHASES.md` as the checklist another agent can use to continue monitoring work without re-reading chat history.

### Why this changed
- Monitoring now has an operator-facing summary layer, not just raw reports.
- The next meaningful monitoring work is no longer generic; it is specifically ranking history, digest freshness, and optimization telemetry.

---

## 2026-03-12 — Ranking history + digest freshness shipped

### What changed
- Moved `Ranking History Persistence` into `Implemented Features`.
- Moved `Digest Freshness and Versioning` into `Implemented Features`.
- Kept `Batch/Retry Telemetry` in `Current Backlog`.

### Why this changed
- Curator runs and per-item rankings are now stored, which makes score drift measurable.
- Digests now carry version and freshness metadata, which makes stale-content analysis possible.
- The next monitoring gap is optimization telemetry, not ranking/freshness persistence.

---

## 2026-03-12 — Batch/retry telemetry + operator completion

### What changed
- Moved `Batch/Retry Telemetry` into `Implemented Features`.
- Left `Monitoring Telemetry Extension` in `Current Backlog` for future provider/token/cost-level telemetry.

### Why this changed
- Monitoring now records operational optimization telemetry at the stage level.
- The remaining telemetry work is the higher-cost, more specialized provider/token/cost layer rather than basic retry/batch observability.
