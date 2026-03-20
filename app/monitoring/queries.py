from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from math import floor, ceil

from sqlalchemy import Date, case, cast, func
from sqlalchemy.orm import Session

from app.db.models import CuratorRanking, CuratorRun, Digest
from app.monitoring.models import PipelineError, PipelineRun, PipelineStageMetric, RunStatus

RUNNING_AI_STAGE_GROUPS = {"enrichment", "ranking"}

STAGE_GROUPS = {
    "youtube_scrape": "scrape",
    "youtube_short_checks": "scrape",
    "events_scrape": "scrape",
    "digest_videos": "enrichment",
    "events_enrichment": "enrichment",
    "curator": "ranking",
    "youtube_email": "delivery",
    "events_email": "delivery",
    "dashboard_render": "delivery",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_stage_group(stage: str) -> str:
    return STAGE_GROUPS.get(stage, "unknown")


def _coalesce_int(value: int | None) -> int:
    return int(value or 0)


def _coalesce_float(value: float | None) -> float:
    return float(value or 0.0)


def _compute_percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    sorted_values = sorted(values)
    position = (len(sorted_values) - 1) * percentile
    lower = floor(position)
    upper = ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _window_bounds(
    *,
    days: int | None = None,
    hours: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[datetime | None, datetime]:
    window_end = end or utc_now()
    window_start = start
    if window_start is None and days is not None:
        window_start = window_end - timedelta(days=days)
    if window_start is None and hours is not None:
        window_start = window_end - timedelta(hours=hours)
    return window_start, window_end


def _apply_started_window(query, column, start: datetime | None, end: datetime | None):
    if start is not None:
        query = query.filter(column >= start)
    if end is not None:
        query = query.filter(column <= end)
    return query


def _apply_occurred_window(query, column, start: datetime | None, end: datetime | None):
    if start is not None:
        query = query.filter(column >= start)
    if end is not None:
        query = query.filter(column <= end)
    return query


@dataclass(slots=True)
class RunStageSummary:
    stage: str
    stage_group: str
    status: str
    duration_seconds: float
    items_attempted: int
    items_succeeded: int
    items_failed: int
    items_skipped: int
    cache_hit_count: int
    network_call_count: int
    batch_size: int | None
    total_batches: int | None
    retry_count: int
    backoff_count: int
    concurrency_level: int | None
    model_name: str | None
    prompt_version: str | None
    started_at: datetime


@dataclass(slots=True)
class RecentRun:
    run_id: int
    started_at: datetime
    ended_at: datetime | None
    status: str
    trigger: str
    git_sha: str | None
    config_version: str | None
    duration_seconds: float | None
    stage_count: int
    error_count: int
    total_items_failed: int
    notes: str | None
    stages: list[RunStageSummary]


@dataclass(slots=True)
class OverallHealth:
    total_runs: int
    successful_runs: int
    partial_runs: int
    failed_runs: int
    success_rate_percent: float
    avg_duration_minutes: float
    errors_last_24h: int


@dataclass(slots=True)
class DailySuccessRate:
    run_date: date
    total_runs: int
    successful_runs: int
    partial_runs: int
    failed_runs: int
    success_rate_percent: float


@dataclass(slots=True)
class DailyRunDuration:
    run_date: date
    num_runs: int
    avg_duration_minutes: float


@dataclass(slots=True)
class SlowRun:
    run_id: int
    run_date: date
    duration_minutes: float
    status: str
    stage_count: int


@dataclass(slots=True)
class StagePerformance:
    stage: str
    stage_group: str
    num_runs: int
    avg_seconds: float
    min_seconds: float
    max_seconds: float


@dataclass(slots=True)
class StageEfficiency:
    stage: str
    stage_group: str
    stage_run_count: int
    items_attempted: int
    items_succeeded: int
    items_failed: int
    avg_duration_seconds: float
    seconds_per_item: float
    items_per_minute: float
    avg_items_attempted_per_run: float


@dataclass(slots=True)
class StageEfficiencyComparison:
    stage: str
    stage_group: str
    before_seconds_per_item: float | None
    after_seconds_per_item: float | None
    before_items_per_minute: float | None
    after_items_per_minute: float | None
    change_percent: float | None


@dataclass(slots=True)
class StageVariance:
    stage: str
    stage_group: str
    avg_seconds: float
    stddev_seconds: float
    variance_percent: float


@dataclass(slots=True)
class StageLatencyPercentiles:
    stage: str
    stage_group: str
    p95_seconds: float
    p99_seconds: float
    sample_count: int


@dataclass(slots=True)
class StageFailureRate:
    stage: str
    stage_group: str
    items_attempted: int
    items_failed: int
    failure_rate_percent: float
    stage_run_count: int


@dataclass(slots=True)
class ErrorFrequency:
    error_type: str
    stage: str
    stage_group: str
    count: int
    percent_of_all_errors: float


@dataclass(slots=True)
class PersistentFailingItem:
    item_id: str
    failure_count: int
    error_types: list[str]
    last_failure: datetime


@dataclass(slots=True)
class RecentError:
    error_id: int
    run_id: int
    stage: str
    stage_group: str
    item_id: str | None
    error_type: str
    error_message: str
    occurred_at: datetime
    run_status: str


@dataclass(slots=True)
class DailyThroughput:
    run_date: date
    items_attempted: int
    items_succeeded: int
    items_failed: int
    success_rate_percent: float


@dataclass(slots=True)
class StageStatusDistribution:
    stage: str
    stage_group: str
    success_count: int
    partial_count: int
    failed_count: int


@dataclass(slots=True)
class ErrorProneStage:
    stage: str
    stage_group: str
    error_count: int
    distinct_runs: int


@dataclass(slots=True)
class IncompleteRun:
    run_id: int
    started_at: datetime
    status: str
    stage_count: int
    error_count: int


@dataclass(slots=True)
class FailedRun:
    run_id: int
    started_at: datetime
    status: str
    total_failed_items: int
    error_count: int


@dataclass(slots=True)
class StageVolumePoint:
    run_date: date
    stage: str
    stage_group: str
    items_attempted: int


@dataclass(slots=True)
class AIWorkload:
    stage: str
    stage_group: str
    num_stage_runs: int
    items_processed: int
    avg_duration_seconds: float


@dataclass(slots=True)
class BatchTelemetry:
    stage: str
    stage_group: str
    stage_run_count: int
    avg_batch_size: float
    avg_total_batches: float
    avg_seconds_per_batch: float
    avg_retry_count: float
    avg_backoff_count: float
    avg_concurrency_level: float
    avg_items_skipped: float
    avg_cache_hits: float
    avg_network_calls: float
    model_names: list[str]
    prompt_versions: list[str]


@dataclass(slots=True)
class RetrySummary:
    stage: str
    stage_group: str
    total_retries: int
    total_backoffs: int
    affected_runs: int
    retry_rate_percent: float


@dataclass(slots=True)
class RankingDrift:
    article_id: str
    article_type: str
    title: str
    run_count: int
    min_score: int
    max_score: int
    score_delta: int
    latest_ranked_at: datetime


@dataclass(slots=True)
class DigestFreshness:
    article_id: str
    article_type: str
    title: str
    digest_version: int
    digest_generated_at: datetime
    source_updated_at: datetime | None
    content_last_seen_at: datetime | None
    digest_age_days: float
    ranking_count_recent: int
    latest_ranked_at: datetime | None
    is_stale: bool


@dataclass(slots=True)
class StaleTopRankDominance:
    curator_run_id: int | None
    ranked_items: int
    stale_ranked_items: int
    stale_share_percent: float


@dataclass(slots=True)
class FocusSignalSnapshot:
    bottleneck_stage: str | None
    bottleneck_seconds_per_item: float
    regression_stage: str | None
    regression_change_percent: float | None
    unstable_stage: str | None
    unstable_variance_percent: float
    failure_stage: str | None
    failure_rate_percent: float
    stale_top_rank_share_percent: float


@dataclass(slots=True)
class StagePeriodComparison:
    stage: str
    stage_group: str
    before_seconds: float | None
    after_seconds: float | None
    change_seconds: float | None
    change_percent: float | None


def get_run_stage_metrics(db: Session, run_id: int) -> list[RunStageSummary]:
    rows = (
        db.query(PipelineStageMetric)
        .filter(PipelineStageMetric.run_id == run_id)
        .order_by(PipelineStageMetric.started_at.asc())
        .all()
    )
    return [
        RunStageSummary(
            stage=row.stage,
            stage_group=get_stage_group(row.stage),
            status=row.status.value,
            duration_seconds=_coalesce_float(row.duration_seconds),
            items_attempted=_coalesce_int(row.items_attempted),
            items_succeeded=_coalesce_int(row.items_succeeded),
            items_failed=_coalesce_int(row.items_failed),
            items_skipped=_coalesce_int(row.items_skipped),
            cache_hit_count=_coalesce_int(row.cache_hit_count),
            network_call_count=_coalesce_int(row.network_call_count),
            batch_size=row.batch_size,
            total_batches=row.total_batches,
            retry_count=_coalesce_int(row.retry_count),
            backoff_count=_coalesce_int(row.backoff_count),
            concurrency_level=row.concurrency_level,
            model_name=row.model_name,
            prompt_version=row.prompt_version,
            started_at=row.started_at,
        )
        for row in rows
    ]


def get_recent_runs(db: Session, limit: int = 10) -> list[RecentRun]:
    stage_counts_sq = (
        db.query(
            PipelineStageMetric.run_id.label("run_id"),
            func.count(PipelineStageMetric.id).label("stage_count"),
            func.coalesce(func.sum(PipelineStageMetric.items_failed), 0).label("total_items_failed"),
        )
        .group_by(PipelineStageMetric.run_id)
        .subquery()
    )
    error_counts_sq = (
        db.query(
            PipelineError.run_id.label("run_id"),
            func.count(PipelineError.id).label("error_count"),
        )
        .group_by(PipelineError.run_id)
        .subquery()
    )

    rows = (
        db.query(PipelineRun, stage_counts_sq.c.stage_count, stage_counts_sq.c.total_items_failed, error_counts_sq.c.error_count)
        .outerjoin(stage_counts_sq, PipelineRun.id == stage_counts_sq.c.run_id)
        .outerjoin(error_counts_sq, PipelineRun.id == error_counts_sq.c.run_id)
        .order_by(PipelineRun.started_at.desc())
        .limit(limit)
        .all()
    )

    run_ids = [run.id for run, _, _, _ in rows]
    stages_by_run: dict[int, list[RunStageSummary]] = defaultdict(list)
    if run_ids:
        stage_rows = (
            db.query(PipelineStageMetric)
            .filter(PipelineStageMetric.run_id.in_(run_ids))
            .order_by(PipelineStageMetric.run_id.asc(), PipelineStageMetric.started_at.asc())
            .all()
        )
        for row in stage_rows:
            stages_by_run[row.run_id].append(
                RunStageSummary(
                    stage=row.stage,
                    stage_group=get_stage_group(row.stage),
                    status=row.status.value,
                    duration_seconds=_coalesce_float(row.duration_seconds),
                    items_attempted=_coalesce_int(row.items_attempted),
                    items_succeeded=_coalesce_int(row.items_succeeded),
                    items_failed=_coalesce_int(row.items_failed),
                    items_skipped=_coalesce_int(row.items_skipped),
                    cache_hit_count=_coalesce_int(row.cache_hit_count),
                    network_call_count=_coalesce_int(row.network_call_count),
                    batch_size=row.batch_size,
                    total_batches=row.total_batches,
                    retry_count=_coalesce_int(row.retry_count),
                    backoff_count=_coalesce_int(row.backoff_count),
                    concurrency_level=row.concurrency_level,
                    model_name=row.model_name,
                    prompt_version=row.prompt_version,
                    started_at=row.started_at,
                )
            )

    results: list[RecentRun] = []
    for run, stage_count, total_items_failed, error_count in rows:
        duration_seconds = None
        if run.ended_at is not None:
            duration_seconds = max((run.ended_at - run.started_at).total_seconds(), 0.0)
        results.append(
            RecentRun(
                run_id=run.id,
                started_at=run.started_at,
                ended_at=run.ended_at,
                status=run.status.value,
                trigger=run.trigger,
                git_sha=run.git_sha,
                config_version=run.config_version,
                duration_seconds=duration_seconds,
                stage_count=_coalesce_int(stage_count),
                error_count=_coalesce_int(error_count),
                total_items_failed=_coalesce_int(total_items_failed),
                notes=run.notes,
                stages=stages_by_run.get(run.id, []),
            )
        )
    return results


def get_overall_health(db: Session, days: int = 30) -> OverallHealth:
    start, end = _window_bounds(days=days)
    success_case = case((PipelineRun.status == RunStatus.success, 1), else_=0)
    partial_case = case((PipelineRun.status == RunStatus.partial, 1), else_=0)
    failed_case = case((PipelineRun.status == RunStatus.failed, 1), else_=0)

    query = db.query(
        func.count(PipelineRun.id),
        func.sum(success_case),
        func.sum(partial_case),
        func.sum(failed_case),
        func.avg(func.extract("epoch", PipelineRun.ended_at - PipelineRun.started_at)),
    )
    query = _apply_started_window(query, PipelineRun.started_at, start, end)
    total_runs, successful_runs, partial_runs, failed_runs, avg_duration_seconds = query.one()

    error_start, error_end = _window_bounds(hours=24)
    error_query = db.query(func.count(PipelineError.id))
    error_query = _apply_occurred_window(error_query, PipelineError.occurred_at, error_start, error_end)
    errors_last_24h = error_query.scalar() or 0

    total_runs = _coalesce_int(total_runs)
    successful_runs = _coalesce_int(successful_runs)
    partial_runs = _coalesce_int(partial_runs)
    failed_runs = _coalesce_int(failed_runs)
    success_rate_percent = round((100.0 * successful_runs / total_runs), 1) if total_runs else 0.0

    return OverallHealth(
        total_runs=total_runs,
        successful_runs=successful_runs,
        partial_runs=partial_runs,
        failed_runs=failed_runs,
        success_rate_percent=success_rate_percent,
        avg_duration_minutes=round(_coalesce_float(avg_duration_seconds) / 60.0, 1),
        errors_last_24h=_coalesce_int(errors_last_24h),
    )


def get_success_rate_trend(db: Session, days: int = 30) -> list[DailySuccessRate]:
    start, end = _window_bounds(days=days)
    day_col = cast(PipelineRun.started_at, Date)
    rows = (
        _apply_started_window(
            db.query(
                day_col.label("run_date"),
                func.count(PipelineRun.id).label("total_runs"),
                func.sum(case((PipelineRun.status == RunStatus.success, 1), else_=0)).label("successful_runs"),
                func.sum(case((PipelineRun.status == RunStatus.partial, 1), else_=0)).label("partial_runs"),
                func.sum(case((PipelineRun.status == RunStatus.failed, 1), else_=0)).label("failed_runs"),
            ),
            PipelineRun.started_at,
            start,
            end,
        )
        .group_by(day_col)
        .order_by(day_col.desc())
        .all()
    )

    return [
        DailySuccessRate(
            run_date=row.run_date,
            total_runs=_coalesce_int(row.total_runs),
            successful_runs=_coalesce_int(row.successful_runs),
            partial_runs=_coalesce_int(row.partial_runs),
            failed_runs=_coalesce_int(row.failed_runs),
            success_rate_percent=round(
                (100.0 * _coalesce_int(row.successful_runs) / _coalesce_int(row.total_runs)),
                1,
            )
            if _coalesce_int(row.total_runs)
            else 0.0,
        )
        for row in rows
    ]


def get_run_duration_trend(db: Session, days: int = 30) -> list[DailyRunDuration]:
    start, end = _window_bounds(days=days)
    day_col = cast(PipelineRun.started_at, Date)
    rows = (
        _apply_started_window(
            db.query(
                day_col.label("run_date"),
                func.count(PipelineRun.id).label("num_runs"),
                func.avg(func.extract("epoch", PipelineRun.ended_at - PipelineRun.started_at)).label("avg_duration_seconds"),
            ),
            PipelineRun.started_at,
            start,
            end,
        )
        .group_by(day_col)
        .order_by(day_col.desc())
        .all()
    )

    return [
        DailyRunDuration(
            run_date=row.run_date,
            num_runs=_coalesce_int(row.num_runs),
            avg_duration_minutes=round(_coalesce_float(row.avg_duration_seconds) / 60.0, 1),
        )
        for row in rows
    ]


def get_slowest_runs(db: Session, limit: int = 10, days: int | None = None) -> list[SlowRun]:
    start, end = _window_bounds(days=days) if days is not None else (None, None)
    stage_counts_sq = (
        db.query(
            PipelineStageMetric.run_id.label("run_id"),
            func.count(PipelineStageMetric.id).label("stage_count"),
        )
        .group_by(PipelineStageMetric.run_id)
        .subquery()
    )
    duration_seconds = func.extract("epoch", PipelineRun.ended_at - PipelineRun.started_at)

    query = db.query(
        PipelineRun.id,
        cast(PipelineRun.started_at, Date).label("run_date"),
        duration_seconds.label("duration_seconds"),
        PipelineRun.status,
        stage_counts_sq.c.stage_count,
    )
    query = query.outerjoin(stage_counts_sq, PipelineRun.id == stage_counts_sq.c.run_id)
    query = query.filter(PipelineRun.ended_at.is_not(None))
    query = _apply_started_window(query, PipelineRun.started_at, start, end)
    rows = query.order_by(duration_seconds.desc()).limit(limit).all()

    return [
        SlowRun(
            run_id=row.id,
            run_date=row.run_date,
            duration_minutes=round(_coalesce_float(row.duration_seconds) / 60.0, 1),
            status=row.status.value,
            stage_count=_coalesce_int(row.stage_count),
        )
        for row in rows
    ]


def get_stage_performance(db: Session, days: int = 30) -> list[StagePerformance]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_started_window(
            db.query(
                PipelineStageMetric.stage,
                func.count(PipelineStageMetric.id).label("num_runs"),
                func.avg(PipelineStageMetric.duration_seconds).label("avg_seconds"),
                func.min(PipelineStageMetric.duration_seconds).label("min_seconds"),
                func.max(PipelineStageMetric.duration_seconds).label("max_seconds"),
            ),
            PipelineStageMetric.started_at,
            start,
            end,
        )
        .group_by(PipelineStageMetric.stage)
        .order_by(func.avg(PipelineStageMetric.duration_seconds).desc())
        .all()
    )

    return [
        StagePerformance(
            stage=row.stage,
            stage_group=get_stage_group(row.stage),
            num_runs=_coalesce_int(row.num_runs),
            avg_seconds=round(_coalesce_float(row.avg_seconds), 1),
            min_seconds=round(_coalesce_float(row.min_seconds), 1),
            max_seconds=round(_coalesce_float(row.max_seconds), 1),
        )
        for row in rows
    ]


def get_stage_efficiency(db: Session, days: int = 30) -> list[StageEfficiency]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_started_window(
            db.query(
                PipelineStageMetric.stage,
                func.count(PipelineStageMetric.id).label("stage_run_count"),
                func.sum(PipelineStageMetric.items_attempted).label("items_attempted"),
                func.sum(PipelineStageMetric.items_succeeded).label("items_succeeded"),
                func.sum(PipelineStageMetric.items_failed).label("items_failed"),
                func.avg(PipelineStageMetric.duration_seconds).label("avg_duration_seconds"),
                func.sum(PipelineStageMetric.duration_seconds).label("total_duration_seconds"),
            ),
            PipelineStageMetric.started_at,
            start,
            end,
        )
        .group_by(PipelineStageMetric.stage)
        .all()
    )

    results: list[StageEfficiency] = []
    for row in rows:
        items_attempted = _coalesce_int(row.items_attempted)
        items_succeeded = _coalesce_int(row.items_succeeded)
        items_failed = _coalesce_int(row.items_failed)
        stage_run_count = _coalesce_int(row.stage_run_count)
        avg_duration_seconds = round(_coalesce_float(row.avg_duration_seconds), 1)
        total_duration_seconds = _coalesce_float(row.total_duration_seconds)
        seconds_per_item = round((total_duration_seconds / items_attempted), 2) if items_attempted else 0.0
        items_per_minute = round((items_attempted / (total_duration_seconds / 60.0)), 2) if total_duration_seconds else 0.0
        avg_items_attempted_per_run = round((items_attempted / stage_run_count), 2) if stage_run_count else 0.0
        results.append(
            StageEfficiency(
                stage=row.stage,
                stage_group=get_stage_group(row.stage),
                stage_run_count=stage_run_count,
                items_attempted=items_attempted,
                items_succeeded=items_succeeded,
                items_failed=items_failed,
                avg_duration_seconds=avg_duration_seconds,
                seconds_per_item=seconds_per_item,
                items_per_minute=items_per_minute,
                avg_items_attempted_per_run=avg_items_attempted_per_run,
            )
        )
    return sorted(
        results,
        key=lambda row: (row.seconds_per_item, row.avg_duration_seconds, row.items_attempted),
        reverse=True,
    )


def get_stage_variance(db: Session, days: int = 30) -> list[StageVariance]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_started_window(
            db.query(
                PipelineStageMetric.stage,
                func.avg(PipelineStageMetric.duration_seconds).label("avg_seconds"),
                func.stddev(PipelineStageMetric.duration_seconds).label("stddev_seconds"),
            ),
            PipelineStageMetric.started_at,
            start,
            end,
        )
        .group_by(PipelineStageMetric.stage)
        .all()
    )

    results: list[StageVariance] = []
    for row in rows:
        avg_seconds = _coalesce_float(row.avg_seconds)
        stddev_seconds = _coalesce_float(row.stddev_seconds)
        variance_percent = round((stddev_seconds / avg_seconds * 100.0), 1) if avg_seconds else 0.0
        results.append(
            StageVariance(
                stage=row.stage,
                stage_group=get_stage_group(row.stage),
                avg_seconds=round(avg_seconds, 1),
                stddev_seconds=round(stddev_seconds, 1),
                variance_percent=variance_percent,
            )
        )
    return sorted(results, key=lambda row: row.variance_percent, reverse=True)


def get_stage_latency_percentiles(db: Session, days: int = 30) -> list[StageLatencyPercentiles]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_started_window(
            db.query(
                PipelineStageMetric.stage,
                PipelineStageMetric.duration_seconds,
            ),
            PipelineStageMetric.started_at,
            start,
            end,
        )
        .order_by(PipelineStageMetric.stage.asc(), PipelineStageMetric.duration_seconds.asc())
        .all()
    )

    durations_by_stage: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        durations_by_stage[row.stage].append(_coalesce_float(row.duration_seconds))

    results: list[StageLatencyPercentiles] = []
    for stage, values in durations_by_stage.items():
        results.append(
            StageLatencyPercentiles(
                stage=stage,
                stage_group=get_stage_group(stage),
                p95_seconds=round(_compute_percentile(values, 0.95), 1),
                p99_seconds=round(_compute_percentile(values, 0.99), 1),
                sample_count=len(values),
            )
        )
    return sorted(results, key=lambda row: row.p95_seconds, reverse=True)


def get_stage_failure_rates(db: Session, days: int = 30) -> list[StageFailureRate]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_started_window(
            db.query(
                PipelineStageMetric.stage,
                func.sum(PipelineStageMetric.items_attempted).label("items_attempted"),
                func.sum(PipelineStageMetric.items_failed).label("items_failed"),
                func.count(PipelineStageMetric.id).label("stage_run_count"),
            ),
            PipelineStageMetric.started_at,
            start,
            end,
        )
        .group_by(PipelineStageMetric.stage)
        .all()
    )

    results: list[StageFailureRate] = []
    for row in rows:
        items_attempted = _coalesce_int(row.items_attempted)
        items_failed = _coalesce_int(row.items_failed)
        failure_rate_percent = round((100.0 * items_failed / items_attempted), 1) if items_attempted else 0.0
        results.append(
            StageFailureRate(
                stage=row.stage,
                stage_group=get_stage_group(row.stage),
                items_attempted=items_attempted,
                items_failed=items_failed,
                failure_rate_percent=failure_rate_percent,
                stage_run_count=_coalesce_int(row.stage_run_count),
            )
        )
    return sorted(results, key=lambda row: row.failure_rate_percent, reverse=True)


def get_error_frequency(db: Session, days: int = 30) -> list[ErrorFrequency]:
    start, end = _window_bounds(days=days)
    total_query = db.query(func.count(PipelineError.id))
    total_query = _apply_occurred_window(total_query, PipelineError.occurred_at, start, end)
    total_errors = _coalesce_int(total_query.scalar())

    rows = (
        _apply_occurred_window(
            db.query(
                PipelineError.error_type,
                PipelineError.stage,
                func.count(PipelineError.id).label("error_count"),
            ),
            PipelineError.occurred_at,
            start,
            end,
        )
        .group_by(PipelineError.error_type, PipelineError.stage)
        .order_by(func.count(PipelineError.id).desc())
        .all()
    )

    return [
        ErrorFrequency(
            error_type=row.error_type,
            stage=row.stage,
            stage_group=get_stage_group(row.stage),
            count=_coalesce_int(row.error_count),
            percent_of_all_errors=round((100.0 * _coalesce_int(row.error_count) / total_errors), 1)
            if total_errors
            else 0.0,
        )
        for row in rows
    ]


def get_persistent_failing_items(
    db: Session,
    days: int = 30,
    min_failures: int = 2,
    limit: int = 20,
) -> list[PersistentFailingItem]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_occurred_window(
            db.query(
                PipelineError.item_id,
                func.count(PipelineError.id).label("failure_count"),
                func.array_agg(func.distinct(PipelineError.error_type)).label("error_types"),
                func.max(PipelineError.occurred_at).label("last_failure"),
            ),
            PipelineError.occurred_at,
            start,
            end,
        )
        .filter(PipelineError.item_id.is_not(None))
        .filter(PipelineError.item_id != "")
        .group_by(PipelineError.item_id)
        .having(func.count(PipelineError.id) >= min_failures)
        .order_by(func.count(PipelineError.id).desc(), func.max(PipelineError.occurred_at).desc())
        .limit(limit)
        .all()
    )

    return [
        PersistentFailingItem(
            item_id=row.item_id,
            failure_count=_coalesce_int(row.failure_count),
            error_types=sorted(error_type for error_type in (row.error_types or []) if error_type),
            last_failure=row.last_failure,
        )
        for row in rows
    ]


def get_recent_errors(db: Session, days: int = 7, limit: int = 20) -> list[RecentError]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_occurred_window(
            db.query(
                PipelineError.id.label("error_id"),
                PipelineRun.id.label("run_id"),
                PipelineError.stage,
                PipelineError.item_id,
                PipelineError.error_type,
                PipelineError.error_message,
                PipelineError.occurred_at,
                PipelineRun.status.label("run_status"),
            )
            .join(PipelineRun, PipelineError.run_id == PipelineRun.id),
            PipelineError.occurred_at,
            start,
            end,
        )
        .order_by(PipelineError.occurred_at.desc())
        .limit(limit)
        .all()
    )

    return [
        RecentError(
            error_id=row.error_id,
            run_id=row.run_id,
            stage=row.stage,
            stage_group=get_stage_group(row.stage),
            item_id=row.item_id,
            error_type=row.error_type,
            error_message=row.error_message,
            occurred_at=row.occurred_at,
            run_status=row.run_status.value,
        )
        for row in rows
    ]


def get_throughput_trend(db: Session, days: int = 30) -> list[DailyThroughput]:
    start, end = _window_bounds(days=days)
    day_col = cast(PipelineStageMetric.started_at, Date)
    rows = (
        _apply_started_window(
            db.query(
                day_col.label("run_date"),
                func.sum(PipelineStageMetric.items_attempted).label("items_attempted"),
                func.sum(PipelineStageMetric.items_succeeded).label("items_succeeded"),
                func.sum(PipelineStageMetric.items_failed).label("items_failed"),
            ),
            PipelineStageMetric.started_at,
            start,
            end,
        )
        .group_by(day_col)
        .order_by(day_col.desc())
        .all()
    )

    results: list[DailyThroughput] = []
    for row in rows:
        items_attempted = _coalesce_int(row.items_attempted)
        items_succeeded = _coalesce_int(row.items_succeeded)
        items_failed = _coalesce_int(row.items_failed)
        success_rate_percent = round((100.0 * items_succeeded / items_attempted), 1) if items_attempted else 0.0
        results.append(
            DailyThroughput(
                run_date=row.run_date,
                items_attempted=items_attempted,
                items_succeeded=items_succeeded,
                items_failed=items_failed,
                success_rate_percent=success_rate_percent,
            )
        )
    return results


def get_stage_status_distribution(db: Session, days: int = 30) -> list[StageStatusDistribution]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_started_window(
            db.query(
                PipelineStageMetric.stage,
                func.sum(case((PipelineStageMetric.status == RunStatus.success, 1), else_=0)).label("success_count"),
                func.sum(case((PipelineStageMetric.status == RunStatus.partial, 1), else_=0)).label("partial_count"),
                func.sum(case((PipelineStageMetric.status == RunStatus.failed, 1), else_=0)).label("failed_count"),
            ),
            PipelineStageMetric.started_at,
            start,
            end,
        )
        .group_by(PipelineStageMetric.stage)
        .order_by(PipelineStageMetric.stage.asc())
        .all()
    )

    return [
        StageStatusDistribution(
            stage=row.stage,
            stage_group=get_stage_group(row.stage),
            success_count=_coalesce_int(row.success_count),
            partial_count=_coalesce_int(row.partial_count),
            failed_count=_coalesce_int(row.failed_count),
        )
        for row in rows
    ]


def get_error_prone_stages(db: Session, days: int = 30) -> list[ErrorProneStage]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_occurred_window(
            db.query(
                PipelineError.stage,
                func.count(PipelineError.id).label("error_count"),
                func.count(func.distinct(PipelineError.run_id)).label("distinct_runs"),
            ),
            PipelineError.occurred_at,
            start,
            end,
        )
        .group_by(PipelineError.stage)
        .order_by(func.count(PipelineError.id).desc())
        .all()
    )

    return [
        ErrorProneStage(
            stage=row.stage,
            stage_group=get_stage_group(row.stage),
            error_count=_coalesce_int(row.error_count),
            distinct_runs=_coalesce_int(row.distinct_runs),
        )
        for row in rows
    ]


def get_incomplete_runs(db: Session, days: int = 30) -> list[IncompleteRun]:
    start, end = _window_bounds(days=days)
    stage_counts_sq = (
        db.query(
            PipelineStageMetric.run_id.label("run_id"),
            func.count(PipelineStageMetric.id).label("stage_count"),
        )
        .group_by(PipelineStageMetric.run_id)
        .subquery()
    )
    error_counts_sq = (
        db.query(
            PipelineError.run_id.label("run_id"),
            func.count(PipelineError.id).label("error_count"),
        )
        .group_by(PipelineError.run_id)
        .subquery()
    )

    rows = (
        _apply_started_window(
            db.query(
                PipelineRun.id,
                PipelineRun.started_at,
                PipelineRun.status,
                stage_counts_sq.c.stage_count,
                error_counts_sq.c.error_count,
            )
            .outerjoin(stage_counts_sq, PipelineRun.id == stage_counts_sq.c.run_id)
            .outerjoin(error_counts_sq, PipelineRun.id == error_counts_sq.c.run_id),
            PipelineRun.started_at,
            start,
            end,
        )
        .filter(func.coalesce(stage_counts_sq.c.stage_count, 0) == 0)
        .order_by(PipelineRun.started_at.desc())
        .all()
    )

    return [
        IncompleteRun(
            run_id=row.id,
            started_at=row.started_at,
            status=row.status.value,
            stage_count=_coalesce_int(row.stage_count),
            error_count=_coalesce_int(row.error_count),
        )
        for row in rows
    ]


def get_top_failed_runs(db: Session, days: int = 30, limit: int = 10) -> list[FailedRun]:
    start, end = _window_bounds(days=days)
    failed_items_sq = (
        db.query(
            PipelineStageMetric.run_id.label("run_id"),
            func.coalesce(func.sum(PipelineStageMetric.items_failed), 0).label("total_failed_items"),
        )
        .group_by(PipelineStageMetric.run_id)
        .subquery()
    )
    error_counts_sq = (
        db.query(
            PipelineError.run_id.label("run_id"),
            func.count(PipelineError.id).label("error_count"),
        )
        .group_by(PipelineError.run_id)
        .subquery()
    )

    rows = (
        _apply_started_window(
            db.query(
                PipelineRun.id,
                PipelineRun.started_at,
                PipelineRun.status,
                failed_items_sq.c.total_failed_items,
                error_counts_sq.c.error_count,
            )
            .outerjoin(failed_items_sq, PipelineRun.id == failed_items_sq.c.run_id)
            .outerjoin(error_counts_sq, PipelineRun.id == error_counts_sq.c.run_id),
            PipelineRun.started_at,
            start,
            end,
        )
        .order_by(func.coalesce(failed_items_sq.c.total_failed_items, 0).desc(), PipelineRun.started_at.desc())
        .limit(limit)
        .all()
    )

    return [
        FailedRun(
            run_id=row.id,
            started_at=row.started_at,
            status=row.status.value,
            total_failed_items=_coalesce_int(row.total_failed_items),
            error_count=_coalesce_int(row.error_count),
        )
        for row in rows
    ]


def get_stage_volume_trend(db: Session, days: int = 30) -> list[StageVolumePoint]:
    start, end = _window_bounds(days=days)
    day_col = cast(PipelineStageMetric.started_at, Date)
    rows = (
        _apply_started_window(
            db.query(
                day_col.label("run_date"),
                PipelineStageMetric.stage,
                func.sum(PipelineStageMetric.items_attempted).label("items_attempted"),
            ),
            PipelineStageMetric.started_at,
            start,
            end,
        )
        .group_by(day_col, PipelineStageMetric.stage)
        .order_by(day_col.desc(), PipelineStageMetric.stage.asc())
        .all()
    )

    return [
        StageVolumePoint(
            run_date=row.run_date,
            stage=row.stage,
            stage_group=get_stage_group(row.stage),
            items_attempted=_coalesce_int(row.items_attempted),
        )
        for row in rows
    ]


def get_ai_workload(db: Session, days: int = 30) -> list[AIWorkload]:
    stage_rows = get_stage_performance(db, days=days)
    stage_failure_rows = {row.stage: row for row in get_stage_failure_rates(db, days=days)}

    workload: list[AIWorkload] = []
    for row in stage_rows:
        if row.stage_group not in RUNNING_AI_STAGE_GROUPS:
            continue
        failure_row = stage_failure_rows.get(row.stage)
        items_processed = failure_row.items_attempted if failure_row else 0
        workload.append(
            AIWorkload(
                stage=row.stage,
                stage_group=row.stage_group,
                num_stage_runs=row.num_runs,
                items_processed=items_processed,
                avg_duration_seconds=row.avg_seconds,
            )
        )
    return sorted(workload, key=lambda item: (item.stage_group, item.stage))


def get_batch_telemetry(db: Session, days: int = 30) -> list[BatchTelemetry]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_started_window(
            db.query(
                PipelineStageMetric.stage,
                func.count(PipelineStageMetric.id).label("stage_run_count"),
                func.avg(PipelineStageMetric.batch_size).label("avg_batch_size"),
                func.avg(PipelineStageMetric.total_batches).label("avg_total_batches"),
                func.avg(PipelineStageMetric.retry_count).label("avg_retry_count"),
                func.avg(PipelineStageMetric.backoff_count).label("avg_backoff_count"),
                func.avg(PipelineStageMetric.concurrency_level).label("avg_concurrency_level"),
                func.avg(PipelineStageMetric.items_skipped).label("avg_items_skipped"),
                func.avg(PipelineStageMetric.cache_hit_count).label("avg_cache_hits"),
                func.avg(PipelineStageMetric.network_call_count).label("avg_network_calls"),
                func.avg(
                    case(
                        (
                            PipelineStageMetric.total_batches.is_not(None),
                            PipelineStageMetric.duration_seconds / func.nullif(PipelineStageMetric.total_batches, 0),
                        ),
                        else_=None,
                    )
                ).label("avg_seconds_per_batch"),
                func.array_agg(func.distinct(PipelineStageMetric.model_name)).label("model_names"),
                func.array_agg(func.distinct(PipelineStageMetric.prompt_version)).label("prompt_versions"),
            ),
            PipelineStageMetric.started_at,
            start,
            end,
        )
        .group_by(PipelineStageMetric.stage)
        .order_by(func.avg(PipelineStageMetric.retry_count).desc(), func.avg(PipelineStageMetric.batch_size).desc())
        .all()
    )

    return [
        BatchTelemetry(
            stage=row.stage,
            stage_group=get_stage_group(row.stage),
            stage_run_count=_coalesce_int(row.stage_run_count),
            avg_batch_size=round(_coalesce_float(row.avg_batch_size), 2),
            avg_total_batches=round(_coalesce_float(row.avg_total_batches), 2),
            avg_seconds_per_batch=round(_coalesce_float(row.avg_seconds_per_batch), 2),
            avg_retry_count=round(_coalesce_float(row.avg_retry_count), 2),
            avg_backoff_count=round(_coalesce_float(row.avg_backoff_count), 2),
            avg_concurrency_level=round(_coalesce_float(row.avg_concurrency_level), 2),
            avg_items_skipped=round(_coalesce_float(row.avg_items_skipped), 2),
            avg_cache_hits=round(_coalesce_float(row.avg_cache_hits), 2),
            avg_network_calls=round(_coalesce_float(row.avg_network_calls), 2),
            model_names=sorted(name for name in (row.model_names or []) if name),
            prompt_versions=sorted(version for version in (row.prompt_versions or []) if version),
        )
        for row in rows
    ]


def get_retry_summary(db: Session, days: int = 30) -> list[RetrySummary]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_started_window(
            db.query(
                PipelineStageMetric.stage,
                func.sum(PipelineStageMetric.retry_count).label("total_retries"),
                func.sum(PipelineStageMetric.backoff_count).label("total_backoffs"),
                func.sum(case((PipelineStageMetric.retry_count > 0, 1), else_=0)).label("affected_runs"),
                func.count(PipelineStageMetric.id).label("stage_run_count"),
            ),
            PipelineStageMetric.started_at,
            start,
            end,
        )
        .group_by(PipelineStageMetric.stage)
        .order_by(func.sum(PipelineStageMetric.retry_count).desc(), PipelineStageMetric.stage.asc())
        .all()
    )

    results: list[RetrySummary] = []
    for row in rows:
        stage_run_count = _coalesce_int(row.stage_run_count)
        affected_runs = _coalesce_int(row.affected_runs)
        results.append(
            RetrySummary(
                stage=row.stage,
                stage_group=get_stage_group(row.stage),
                total_retries=_coalesce_int(row.total_retries),
                total_backoffs=_coalesce_int(row.total_backoffs),
                affected_runs=affected_runs,
                retry_rate_percent=round((100.0 * affected_runs / stage_run_count), 1) if stage_run_count else 0.0,
            )
        )
    return results


def get_ranking_drift(
    db: Session,
    days: int = 30,
    min_score_delta: int = 10,
    limit: int = 20,
) -> list[RankingDrift]:
    start, end = _window_bounds(days=days)
    rows = (
        _apply_started_window(
            db.query(
                CuratorRanking.article_id,
                CuratorRanking.article_type,
                CuratorRanking.title,
                func.count(func.distinct(CuratorRanking.curator_run_id)).label("run_count"),
                func.min(CuratorRanking.score).label("min_score"),
                func.max(CuratorRanking.score).label("max_score"),
                func.max(CuratorRun.started_at).label("latest_ranked_at"),
            ).join(CuratorRun, CuratorRanking.curator_run_id == CuratorRun.id),
            CuratorRun.started_at,
            start,
            end,
        )
        .group_by(CuratorRanking.article_id, CuratorRanking.article_type, CuratorRanking.title)
        .having((func.max(CuratorRanking.score) - func.min(CuratorRanking.score)) >= min_score_delta)
        .order_by((func.max(CuratorRanking.score) - func.min(CuratorRanking.score)).desc(), func.max(CuratorRun.started_at).desc())
        .limit(limit)
        .all()
    )

    return [
        RankingDrift(
            article_id=row.article_id,
            article_type=row.article_type,
            title=row.title,
            run_count=_coalesce_int(row.run_count),
            min_score=_coalesce_int(row.min_score),
            max_score=_coalesce_int(row.max_score),
            score_delta=_coalesce_int(row.max_score) - _coalesce_int(row.min_score),
            latest_ranked_at=row.latest_ranked_at,
        )
        for row in rows
    ]


def get_digest_freshness(
    db: Session,
    days: int = 30,
    stale_after_days: int = 7,
    limit: int = 20,
) -> list[DigestFreshness]:
    start, end = _window_bounds(days=days)
    ranking_stats_sq = (
        _apply_started_window(
            db.query(
                CuratorRanking.article_id.label("article_id"),
                CuratorRanking.article_type.label("article_type"),
                func.count(CuratorRanking.id).label("ranking_count_recent"),
                func.max(CuratorRun.started_at).label("latest_ranked_at"),
            ).join(CuratorRun, CuratorRanking.curator_run_id == CuratorRun.id),
            CuratorRun.started_at,
            start,
            end,
        )
        .group_by(CuratorRanking.article_id, CuratorRanking.article_type)
        .subquery()
    )

    rows = (
        db.query(
            Digest.article_id,
            Digest.article_type,
            Digest.title,
            Digest.digest_version,
            Digest.digest_generated_at,
            Digest.source_updated_at,
            Digest.content_last_seen_at,
            ranking_stats_sq.c.ranking_count_recent,
            ranking_stats_sq.c.latest_ranked_at,
        )
        .outerjoin(
            ranking_stats_sq,
            (Digest.article_id == ranking_stats_sq.c.article_id)
            & (Digest.article_type == ranking_stats_sq.c.article_type),
        )
        .order_by(Digest.digest_generated_at.asc())
        .limit(limit)
        .all()
    )

    now = utc_now()
    results: list[DigestFreshness] = []
    for row in rows:
        digest_age_days = round(max((now - row.digest_generated_at).total_seconds(), 0.0) / 86400.0, 1)
        ranking_count_recent = _coalesce_int(row.ranking_count_recent)
        results.append(
            DigestFreshness(
                article_id=row.article_id,
                article_type=row.article_type,
                title=row.title,
                digest_version=_coalesce_int(row.digest_version),
                digest_generated_at=row.digest_generated_at,
                source_updated_at=row.source_updated_at,
                content_last_seen_at=row.content_last_seen_at,
                digest_age_days=digest_age_days,
                ranking_count_recent=ranking_count_recent,
                latest_ranked_at=row.latest_ranked_at,
                is_stale=digest_age_days >= stale_after_days,
            )
        )
    return sorted(
        results,
        key=lambda row: (row.is_stale, row.ranking_count_recent, row.digest_age_days),
        reverse=True,
    )


def get_stale_top_rank_dominance(
    db: Session,
    days: int = 30,
    stale_after_days: int = 7,
    top_n: int = 10,
) -> StaleTopRankDominance:
    start, end = _window_bounds(days=days)
    latest_run = (
        _apply_started_window(
            db.query(CuratorRun),
            CuratorRun.started_at,
            start,
            end,
        )
        .order_by(CuratorRun.started_at.desc())
        .first()
    )
    if latest_run is None:
        return StaleTopRankDominance(
            curator_run_id=None,
            ranked_items=0,
            stale_ranked_items=0,
            stale_share_percent=0.0,
        )

    ranking_rows = (
        db.query(CuratorRanking, Digest)
        .join(
            Digest,
            (CuratorRanking.article_id == Digest.article_id)
            & (CuratorRanking.article_type == Digest.article_type),
        )
        .filter(CuratorRanking.curator_run_id == latest_run.id)
        .order_by(CuratorRanking.rank_position.asc())
        .limit(top_n)
        .all()
    )
    if not ranking_rows:
        return StaleTopRankDominance(
            curator_run_id=latest_run.id,
            ranked_items=0,
            stale_ranked_items=0,
            stale_share_percent=0.0,
        )

    now = utc_now()
    stale_ranked_items = 0
    for _ranking, digest in ranking_rows:
        digest_age_days = max((now - digest.digest_generated_at).total_seconds(), 0.0) / 86400.0
        if digest_age_days >= stale_after_days:
            stale_ranked_items += 1

    ranked_items = len(ranking_rows)
    return StaleTopRankDominance(
        curator_run_id=latest_run.id,
        ranked_items=ranked_items,
        stale_ranked_items=stale_ranked_items,
        stale_share_percent=round((100.0 * stale_ranked_items / ranked_items), 1) if ranked_items else 0.0,
    )


def get_focus_signal_snapshot(db: Session, days: int = 7) -> FocusSignalSnapshot:
    efficiency = get_stage_efficiency(db, days=days)
    variance = get_stage_variance(db, days=days)
    failure_rates = get_stage_failure_rates(db, days=days)
    current_end = utc_now()
    current_start = current_end - timedelta(days=days)
    previous_end = current_start
    previous_start = previous_end - timedelta(days=days)
    regressions = compare_stage_efficiency_periods(
        db,
        before_start=previous_start,
        before_end=previous_end,
        after_start=current_start,
        after_end=current_end,
    )
    stale_top_rank = get_stale_top_rank_dominance(db, days=max(days, 30), stale_after_days=7, top_n=10)

    bottleneck = efficiency[0] if efficiency else None
    regression = next((row for row in regressions if row.change_percent is not None), None)
    unstable = variance[0] if variance else None
    failure = failure_rates[0] if failure_rates else None
    return FocusSignalSnapshot(
        bottleneck_stage=bottleneck.stage if bottleneck else None,
        bottleneck_seconds_per_item=bottleneck.seconds_per_item if bottleneck else 0.0,
        regression_stage=regression.stage if regression else None,
        regression_change_percent=regression.change_percent if regression else None,
        unstable_stage=unstable.stage if unstable else None,
        unstable_variance_percent=unstable.variance_percent if unstable else 0.0,
        failure_stage=failure.stage if failure else None,
        failure_rate_percent=failure.failure_rate_percent if failure else 0.0,
        stale_top_rank_share_percent=stale_top_rank.stale_share_percent,
    )


def compare_periods(
    db: Session,
    before_start: datetime,
    before_end: datetime,
    after_start: datetime,
    after_end: datetime,
) -> list[StagePeriodComparison]:
    before_rows = (
        _apply_started_window(
            db.query(
                PipelineStageMetric.stage,
                func.avg(PipelineStageMetric.duration_seconds).label("avg_seconds"),
            ),
            PipelineStageMetric.started_at,
            before_start,
            before_end,
        )
        .group_by(PipelineStageMetric.stage)
        .all()
    )
    after_rows = (
        _apply_started_window(
            db.query(
                PipelineStageMetric.stage,
                func.avg(PipelineStageMetric.duration_seconds).label("avg_seconds"),
            ),
            PipelineStageMetric.started_at,
            after_start,
            after_end,
        )
        .group_by(PipelineStageMetric.stage)
        .all()
    )

    before_map = {row.stage: _coalesce_float(row.avg_seconds) for row in before_rows}
    after_map = {row.stage: _coalesce_float(row.avg_seconds) for row in after_rows}
    stages = sorted(set(before_map) | set(after_map))

    results: list[StagePeriodComparison] = []
    for stage in stages:
        before_seconds = before_map.get(stage)
        after_seconds = after_map.get(stage)
        change_seconds = None
        change_percent = None
        if before_seconds is not None and after_seconds is not None:
            change_seconds = round(after_seconds - before_seconds, 1)
            if before_seconds:
                change_percent = round((after_seconds - before_seconds) / before_seconds * 100.0, 1)

        results.append(
            StagePeriodComparison(
                stage=stage,
                stage_group=get_stage_group(stage),
                before_seconds=round(before_seconds, 1) if before_seconds is not None else None,
                after_seconds=round(after_seconds, 1) if after_seconds is not None else None,
                change_seconds=change_seconds,
                change_percent=change_percent,
            )
        )
    return sorted(
        results,
        key=lambda row: row.change_percent if row.change_percent is not None else float("-inf"),
        reverse=True,
    )


def compare_stage_efficiency_periods(
    db: Session,
    before_start: datetime,
    before_end: datetime,
    after_start: datetime,
    after_end: datetime,
) -> list[StageEfficiencyComparison]:
    def _period_map(start: datetime, end: datetime) -> dict[str, tuple[float | None, float | None]]:
        rows = (
            _apply_started_window(
                db.query(
                    PipelineStageMetric.stage,
                    func.sum(PipelineStageMetric.items_attempted).label("items_attempted"),
                    func.sum(PipelineStageMetric.duration_seconds).label("total_duration_seconds"),
                ),
                PipelineStageMetric.started_at,
                start,
                end,
            )
            .group_by(PipelineStageMetric.stage)
            .all()
        )

        values: dict[str, tuple[float | None, float | None]] = {}
        for row in rows:
            items_attempted = _coalesce_int(row.items_attempted)
            total_duration_seconds = _coalesce_float(row.total_duration_seconds)
            if not items_attempted or not total_duration_seconds:
                values[row.stage] = (None, None)
                continue
            seconds_per_item = round(total_duration_seconds / items_attempted, 2)
            items_per_minute = round(items_attempted / (total_duration_seconds / 60.0), 2)
            values[row.stage] = (seconds_per_item, items_per_minute)
        return values

    before_map = _period_map(before_start, before_end)
    after_map = _period_map(after_start, after_end)
    stages = sorted(set(before_map) | set(after_map))

    results: list[StageEfficiencyComparison] = []
    for stage in stages:
        before_seconds_per_item, before_items_per_minute = before_map.get(stage, (None, None))
        after_seconds_per_item, after_items_per_minute = after_map.get(stage, (None, None))
        change_percent = None
        if before_seconds_per_item and after_seconds_per_item:
            change_percent = round(
                ((after_seconds_per_item - before_seconds_per_item) / before_seconds_per_item) * 100.0,
                1,
            )

        results.append(
            StageEfficiencyComparison(
                stage=stage,
                stage_group=get_stage_group(stage),
                before_seconds_per_item=before_seconds_per_item,
                after_seconds_per_item=after_seconds_per_item,
                before_items_per_minute=before_items_per_minute,
                after_items_per_minute=after_items_per_minute,
                change_percent=change_percent,
            )
        )
    return sorted(
        results,
        key=lambda row: row.change_percent if row.change_percent is not None else float("-inf"),
        reverse=True,
    )
