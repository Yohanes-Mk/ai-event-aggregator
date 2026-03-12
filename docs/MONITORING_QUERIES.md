# Monitoring Queries

This document describes the supported monitoring analytics surface, the equivalent SQL reference for direct database inspection, and the tradeoffs behind the current design.

## Design Intent

- Primary interface: Python query helpers in `app/monitoring/queries.py`
- Secondary interface: terminal analytics via `scripts/monitoring_report.py`
- SQL in this doc is reference material, not the primary integration surface
- Queries are parameterized by time window and avoid hardcoded stage names where possible

## Supported Named Queries

### Run health
- `get_recent_runs(limit=10)`
- `get_overall_health(days=30)`
- `get_success_rate_trend(days=30)`
- `get_run_duration_trend(days=30)`
- `get_slowest_runs(limit=10, days=None)`
- `get_incomplete_runs(days=30)`

### Stage performance
- `get_stage_performance(days=30)`
- `get_stage_efficiency(days=30)`
- `get_stage_variance(days=30)`
- `get_stage_status_distribution(days=30)`
- `get_stage_volume_trend(days=30)`
- `compare_periods(before_start, before_end, after_start, after_end)`
- `compare_stage_efficiency_periods(before_start, before_end, after_start, after_end)`

### Failure analysis
- `get_error_frequency(days=30)`
- `get_stage_failure_rates(days=30)`
- `get_error_prone_stages(days=30)`
- `get_persistent_failing_items(days=30, min_failures=2, limit=20)`
- `get_recent_errors(days=7, limit=20)`
- `get_top_failed_runs(days=30, limit=10)`

### Throughput and workload
- `get_throughput_trend(days=30)`
- `get_ai_workload(days=30)`

## CLI Surface

Run via `uv run scripts/monitoring_report.py <command>`.

Available commands:
- `recent-runs --limit 10`
- `health --days 30 --limit 10`
- `stage-performance --days 30`
- `failures --days 30 --limit 20`
- `throughput --days 30`
- `summary --days 7`
- `compare --before-start 2026-03-01 --before-end 2026-03-10 --after-start 2026-03-11 --after-end 2026-03-20`

If no command is supplied, the CLI defaults to `recent-runs`.

## SQL Reference

### Average Duration Per Stage

```sql
SELECT
  stage,
  COUNT(*) AS num_runs,
  ROUND(AVG(duration_seconds)::numeric, 1) AS avg_seconds,
  ROUND(MIN(duration_seconds)::numeric, 1) AS min_seconds,
  ROUND(MAX(duration_seconds)::numeric, 1) AS max_seconds
FROM pipeline_stage_metrics
GROUP BY stage
ORDER BY avg_seconds DESC;
```

### Slowest Runs

```sql
SELECT
  pr.id,
  DATE(pr.started_at) AS run_date,
  ROUND(EXTRACT(EPOCH FROM (pr.ended_at - pr.started_at))::numeric / 60, 1) AS duration_minutes,
  pr.status,
  COUNT(psm.id) AS stage_count
FROM pipeline_runs pr
LEFT JOIN pipeline_stage_metrics psm ON psm.run_id = pr.id
WHERE pr.ended_at IS NOT NULL
GROUP BY pr.id, DATE(pr.started_at), pr.ended_at, pr.started_at, pr.status
ORDER BY EXTRACT(EPOCH FROM (pr.ended_at - pr.started_at)) DESC
LIMIT 10;
```

### Performance Trend

```sql
SELECT
  DATE(started_at) AS run_date,
  COUNT(*) AS num_runs,
  ROUND(AVG(EXTRACT(EPOCH FROM (ended_at - started_at)))::numeric / 60, 1) AS avg_duration_minutes
FROM pipeline_runs
WHERE started_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(started_at)
ORDER BY run_date DESC;
```

### Stage Duration Variance

```sql
SELECT
  stage,
  ROUND(AVG(duration_seconds)::numeric, 1) AS avg_seconds,
  ROUND(STDDEV(duration_seconds)::numeric, 1) AS stddev_seconds,
  ROUND((STDDEV(duration_seconds) / NULLIF(AVG(duration_seconds), 0) * 100)::numeric, 1) AS variance_percent
FROM pipeline_stage_metrics
GROUP BY stage
ORDER BY variance_percent DESC;
```

### Normalized Stage Efficiency

```sql
SELECT
  stage,
  COUNT(*) AS stage_run_count,
  SUM(items_attempted) AS items_attempted,
  SUM(items_succeeded) AS items_succeeded,
  SUM(items_failed) AS items_failed,
  ROUND(AVG(duration_seconds)::numeric, 1) AS avg_duration_seconds,
  ROUND(SUM(duration_seconds)::numeric / NULLIF(SUM(items_attempted), 0), 2) AS seconds_per_item,
  ROUND(SUM(items_attempted)::numeric / NULLIF(SUM(duration_seconds) / 60.0, 0), 2) AS items_per_minute
FROM pipeline_stage_metrics
WHERE started_at > NOW() - INTERVAL '30 days'
GROUP BY stage
ORDER BY seconds_per_item DESC NULLS LAST, avg_duration_seconds DESC;
```

### Error Types and Frequency

```sql
SELECT
  error_type,
  stage,
  COUNT(*) AS count,
  ROUND(
    100.0 * COUNT(*) / NULLIF(
      (SELECT COUNT(*) FROM pipeline_errors WHERE occurred_at > NOW() - INTERVAL '30 days'),
      0
    ),
    1
  ) AS percent_of_all_errors
FROM pipeline_errors
WHERE occurred_at > NOW() - INTERVAL '30 days'
GROUP BY error_type, stage
ORDER BY count DESC;
```

### Failure Rate By Stage

```sql
SELECT
  stage,
  SUM(items_attempted) AS items_attempted,
  SUM(items_failed) AS items_failed,
  ROUND(100.0 * SUM(items_failed) / NULLIF(SUM(items_attempted), 0), 1) AS failure_rate_percent
FROM pipeline_stage_metrics
WHERE started_at > NOW() - INTERVAL '30 days'
GROUP BY stage
ORDER BY failure_rate_percent DESC;
```

### Persistent Failing Items

```sql
SELECT
  item_id,
  COUNT(*) AS failure_count,
  ARRAY_AGG(DISTINCT error_type) AS error_types,
  MAX(occurred_at) AS last_failure
FROM pipeline_errors
WHERE occurred_at > NOW() - INTERVAL '30 days'
  AND item_id IS NOT NULL
  AND item_id <> ''
GROUP BY item_id
HAVING COUNT(*) >= 2
ORDER BY failure_count DESC, last_failure DESC
LIMIT 20;
```

### Success Rate Trend

```sql
SELECT
  DATE(started_at) AS run_date,
  COUNT(*) AS total_runs,
  SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_runs,
  SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) AS partial_runs,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_runs,
  ROUND(
    100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
    1
  ) AS success_rate_percent
FROM pipeline_runs
WHERE started_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(started_at)
ORDER BY run_date DESC;
```

### Overall Pipeline Health

```sql
SELECT
  COUNT(*) AS total_runs,
  SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful,
  SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) AS partial,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
  ROUND(
    100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
    1
  ) AS success_rate,
  ROUND(AVG(EXTRACT(EPOCH FROM (ended_at - started_at)))::numeric / 60, 1) AS avg_duration_minutes,
  (
    SELECT COUNT(*)
    FROM pipeline_errors
    WHERE occurred_at > NOW() - INTERVAL '24 hours'
  ) AS errors_last_24h
FROM pipeline_runs
WHERE started_at > NOW() - INTERVAL '30 days';
```

### Throughput Trend

```sql
SELECT
  DATE(started_at) AS run_date,
  SUM(items_attempted) AS items_attempted,
  SUM(items_succeeded) AS items_succeeded,
  SUM(items_failed) AS items_failed,
  ROUND(100.0 * SUM(items_succeeded) / NULLIF(SUM(items_attempted), 0), 1) AS success_rate_percent
FROM pipeline_stage_metrics
WHERE started_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(started_at)
ORDER BY run_date DESC;
```

### Recent Errors With Full Context

```sql
SELECT
  pe.id,
  pr.id AS run_id,
  pe.stage,
  pe.item_id,
  pe.error_type,
  pe.error_message,
  pe.occurred_at,
  pr.status AS run_status
FROM pipeline_errors pe
JOIN pipeline_runs pr ON pe.run_id = pr.id
WHERE pe.occurred_at > NOW() - INTERVAL '7 days'
ORDER BY pe.occurred_at DESC
LIMIT 20;
```

### Before and After Comparison

```sql
WITH before_window AS (
  SELECT
    stage,
    AVG(duration_seconds) AS avg_before
  FROM pipeline_stage_metrics
  WHERE started_at >= :before_start
    AND started_at <= :before_end
  GROUP BY stage
),
after_window AS (
  SELECT
    stage,
    AVG(duration_seconds) AS avg_after
  FROM pipeline_stage_metrics
  WHERE started_at >= :after_start
    AND started_at <= :after_end
  GROUP BY stage
)
SELECT
  COALESCE(b.stage, a.stage) AS stage,
  ROUND(b.avg_before::numeric, 1) AS before_seconds,
  ROUND(a.avg_after::numeric, 1) AS after_seconds,
  ROUND((a.avg_after - b.avg_before)::numeric, 1) AS change_seconds,
  ROUND(100.0 * (a.avg_after - b.avg_before) / NULLIF(b.avg_before, 0), 1) AS change_percent
FROM before_window b
FULL OUTER JOIN after_window a ON b.stage = a.stage
ORDER BY change_percent DESC NULLS LAST;
```

### Normalized Efficiency Comparison

```sql
WITH before_window AS (
  SELECT
    stage,
    SUM(items_attempted) AS items_attempted,
    SUM(duration_seconds) AS total_duration_seconds
  FROM pipeline_stage_metrics
  WHERE started_at >= :before_start
    AND started_at <= :before_end
  GROUP BY stage
),
after_window AS (
  SELECT
    stage,
    SUM(items_attempted) AS items_attempted,
    SUM(duration_seconds) AS total_duration_seconds
  FROM pipeline_stage_metrics
  WHERE started_at >= :after_start
    AND started_at <= :after_end
  GROUP BY stage
)
SELECT
  COALESCE(b.stage, a.stage) AS stage,
  ROUND(b.total_duration_seconds::numeric / NULLIF(b.items_attempted, 0), 2) AS before_seconds_per_item,
  ROUND(a.total_duration_seconds::numeric / NULLIF(a.items_attempted, 0), 2) AS after_seconds_per_item,
  ROUND(b.items_attempted::numeric / NULLIF(b.total_duration_seconds / 60.0, 0), 2) AS before_items_per_minute,
  ROUND(a.items_attempted::numeric / NULLIF(a.total_duration_seconds / 60.0, 0), 2) AS after_items_per_minute,
  ROUND(
    100.0 * (
      (a.total_duration_seconds / NULLIF(a.items_attempted, 0)) -
      (b.total_duration_seconds / NULLIF(b.items_attempted, 0))
    ) / NULLIF((b.total_duration_seconds / NULLIF(b.items_attempted, 0)), 0),
    1
  ) AS change_percent
FROM before_window b
FULL OUTER JOIN after_window a ON b.stage = a.stage
ORDER BY change_percent DESC NULLS LAST;
```

## Interpretation Notes

- `success` vs `partial` vs `failed` lives at both run and stage level; they answer different questions.
- `duration_seconds` is useful for performance, not cost.
- `items_attempted/succeeded/failed` are stage-level counters; they are meaningful only for stages that actually count items.
- `seconds_per_item` and `items_per_minute` are the better optimization metrics when stage volume changes between runs.
- `item_id` can reveal persistent bad inputs or recurring upstream data issues.
- Stage grouping in Python is a derived view only. Unknown future stages fall into `unknown` rather than breaking the analytics surface.

## Known Caveats

- Current schema is enough for operational analytics, but not for real cost analysis.
- `get_ai_workload()` is a workload view, not a billing view.
- If a run aborts before any stage metric is recorded, it will appear in incomplete-observability queries.
- Stage-group taxonomy is code-level today; if external tools need to query by group directly, it may later need promotion into schema or exposed API fields.

## Next Telemetry Extensions

These are intentionally deferred until needed:
- `provider`
- `model`
- `input_tokens`
- `output_tokens`
- `estimated_cost_usd`

Only after these exist should true cost analytics be added.
