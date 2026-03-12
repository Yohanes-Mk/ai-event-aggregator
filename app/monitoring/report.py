from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.monitoring.queries import (
    compare_periods,
    compare_stage_efficiency_periods,
    get_ai_workload,
    get_error_frequency,
    get_error_prone_stages,
    get_incomplete_runs,
    get_overall_health,
    get_persistent_failing_items,
    get_recent_errors,
    get_recent_runs,
    get_run_duration_trend,
    get_slowest_runs,
    get_stage_efficiency,
    get_stage_failure_rates,
    get_stage_performance,
    get_stage_status_distribution,
    get_stage_variance,
    get_stage_volume_trend,
    get_success_rate_trend,
    get_throughput_trend,
    get_top_failed_runs,
)
from app.monitoring.summary import build_monitoring_summary, render_monitoring_summary


def _format_dt(value: datetime | None) -> str:
    return value.isoformat(timespec="seconds") if value else "-"


def _format_duration_seconds(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f}s"


def _format_minutes(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f}m"


def _section(title: str) -> list[str]:
    return [title, "-" * len(title)]


def generate_recent_runs_report(db: Session, limit: int = 10) -> str:
    runs = get_recent_runs(db, limit=limit)
    if not runs:
        return "No pipeline runs found."

    lines: list[str] = [f"Pipeline Monitoring Report (last {len(runs)} runs)"]
    for run in runs:
        lines.append(
            f"Run #{run.run_id} | status={run.status} | trigger={run.trigger} | "
            f"started={_format_dt(run.started_at)} | ended={_format_dt(run.ended_at)} | "
            f"duration={_format_duration_seconds(run.duration_seconds)} | "
            f"stages={run.stage_count} | errors={run.error_count} | failed_items={run.total_items_failed}"
        )
        lines.append(f"  git_sha={run.git_sha or '-'} config_version={run.config_version or '-'}")
        if not run.stages:
            lines.append("  stages: none")
        else:
            for stage in run.stages:
                lines.append(
                    "  stage="
                    f"{stage.stage} group={stage.stage_group} status={stage.status} "
                    f"duration={stage.duration_seconds:.1f}s attempted={stage.items_attempted} "
                    f"succeeded={stage.items_succeeded} failed={stage.items_failed}"
                )
        if run.notes:
            lines.append(f"  notes={run.notes}")
    return "\n".join(lines)


def generate_health_report(db: Session, days: int = 30, slowest_limit: int = 10) -> str:
    health = get_overall_health(db, days=days)
    success_trend = get_success_rate_trend(db, days=days)
    duration_trend = get_run_duration_trend(db, days=days)
    slowest_runs = get_slowest_runs(db, limit=slowest_limit, days=days)
    incomplete_runs = get_incomplete_runs(db, days=days)

    lines: list[str] = _section(f"Pipeline Health ({days}d)")
    lines.append(
        f"runs={health.total_runs} success={health.successful_runs} partial={health.partial_runs} "
        f"failed={health.failed_runs} success_rate={health.success_rate_percent:.1f}% "
        f"avg_duration={health.avg_duration_minutes:.1f}m errors_last_24h={health.errors_last_24h}"
    )

    lines.extend(_section("Success Rate Trend"))
    if not success_trend:
        lines.append("No runs found.")
    else:
        for row in success_trend:
            lines.append(
                f"{row.run_date}: total={row.total_runs} success={row.successful_runs} "
                f"partial={row.partial_runs} failed={row.failed_runs} rate={row.success_rate_percent:.1f}%"
            )

    lines.extend(_section("Run Duration Trend"))
    if not duration_trend:
        lines.append("No duration data found.")
    else:
        for row in duration_trend:
            lines.append(f"{row.run_date}: runs={row.num_runs} avg_duration={row.avg_duration_minutes:.1f}m")

    lines.extend(_section("Slowest Runs"))
    if not slowest_runs:
        lines.append("No completed runs found.")
    else:
        for run in slowest_runs:
            lines.append(
                f"run={run.run_id} date={run.run_date} duration={run.duration_minutes:.1f}m "
                f"status={run.status} stages={run.stage_count}"
            )

    lines.extend(_section("Incomplete Observability"))
    if not incomplete_runs:
        lines.append("No runs missing stage metrics.")
    else:
        for run in incomplete_runs:
            lines.append(
                f"run={run.run_id} started={_format_dt(run.started_at)} status={run.status} "
                f"stages={run.stage_count} errors={run.error_count}"
            )

    return "\n".join(lines)


def generate_stage_performance_report(db: Session, days: int = 30) -> str:
    performance = get_stage_performance(db, days=days)
    efficiency = get_stage_efficiency(db, days=days)
    variance = get_stage_variance(db, days=days)
    status_distribution = get_stage_status_distribution(db, days=days)
    stage_volume = get_stage_volume_trend(db, days=days)
    ai_workload = get_ai_workload(db, days=days)

    lines: list[str] = _section(f"Stage Performance ({days}d)")

    lines.extend(_section("Average Duration Per Stage"))
    if not performance:
        lines.append("No stage metrics found.")
    else:
        for row in performance:
            lines.append(
                f"{row.stage} [{row.stage_group}]: runs={row.num_runs} avg={row.avg_seconds:.1f}s "
                f"min={row.min_seconds:.1f}s max={row.max_seconds:.1f}s"
            )

    lines.extend(_section("Normalized Stage Efficiency"))
    if not efficiency:
        lines.append("No efficiency data found.")
    else:
        for row in efficiency:
            lines.append(
                f"{row.stage} [{row.stage_group}]: runs={row.stage_run_count} attempted={row.items_attempted} "
                f"avg_duration={row.avg_duration_seconds:.1f}s seconds_per_item={row.seconds_per_item:.2f} "
                f"items_per_minute={row.items_per_minute:.2f} avg_items_per_run={row.avg_items_attempted_per_run:.2f}"
            )

    lines.extend(_section("Stage Duration Variance"))
    if not variance:
        lines.append("No stage variance data found.")
    else:
        for row in variance:
            lines.append(
                f"{row.stage} [{row.stage_group}]: avg={row.avg_seconds:.1f}s "
                f"stddev={row.stddev_seconds:.1f}s variance={row.variance_percent:.1f}%"
            )

    lines.extend(_section("Stage Status Distribution"))
    if not status_distribution:
        lines.append("No stage status data found.")
    else:
        for row in status_distribution:
            lines.append(
                f"{row.stage} [{row.stage_group}]: success={row.success_count} "
                f"partial={row.partial_count} failed={row.failed_count}"
            )

    lines.extend(_section("Stage Volume Trend"))
    if not stage_volume:
        lines.append("No stage volume data found.")
    else:
        for row in stage_volume:
            lines.append(f"{row.run_date}: {row.stage} [{row.stage_group}] attempted={row.items_attempted}")

    lines.extend(_section("AI Workload"))
    if not ai_workload:
        lines.append("No AI-heavy stage workload found.")
    else:
        for row in ai_workload:
            lines.append(
                f"{row.stage} [{row.stage_group}]: runs={row.num_stage_runs} "
                f"items={row.items_processed} avg_duration={row.avg_duration_seconds:.1f}s"
            )

    return "\n".join(lines)


def generate_failures_report(db: Session, days: int = 30, limit: int = 20) -> str:
    error_frequency = get_error_frequency(db, days=days)
    failure_rates = get_stage_failure_rates(db, days=days)
    persistent_items = get_persistent_failing_items(db, days=days, limit=limit)
    recent_errors = get_recent_errors(db, days=min(days, 7), limit=limit)
    error_prone_stages = get_error_prone_stages(db, days=days)
    top_failed_runs = get_top_failed_runs(db, days=days, limit=min(limit, 10))

    lines: list[str] = _section(f"Failure Analysis ({days}d)")

    lines.extend(_section("Error Types & Frequency"))
    if not error_frequency:
        lines.append("No errors found.")
    else:
        for row in error_frequency:
            lines.append(
                f"{row.error_type} @ {row.stage} [{row.stage_group}]: "
                f"count={row.count} share={row.percent_of_all_errors:.1f}%"
            )

    lines.extend(_section("Failure Rate By Stage"))
    if not failure_rates:
        lines.append("No failure-rate data found.")
    else:
        for row in failure_rates:
            lines.append(
                f"{row.stage} [{row.stage_group}]: attempted={row.items_attempted} "
                f"failed={row.items_failed} rate={row.failure_rate_percent:.1f}% runs={row.stage_run_count}"
            )

    lines.extend(_section("Most Error-Prone Stages"))
    if not error_prone_stages:
        lines.append("No stage errors found.")
    else:
        for row in error_prone_stages:
            lines.append(
                f"{row.stage} [{row.stage_group}]: errors={row.error_count} affected_runs={row.distinct_runs}"
            )

    lines.extend(_section("Persistent Failing Items"))
    if not persistent_items:
        lines.append("No persistent failing items found.")
    else:
        for row in persistent_items:
            lines.append(
                f"{row.item_id}: failures={row.failure_count} "
                f"types={', '.join(row.error_types)} last={_format_dt(row.last_failure)}"
            )

    lines.extend(_section("Top Failed Runs"))
    if not top_failed_runs:
        lines.append("No failed-item aggregates found.")
    else:
        for row in top_failed_runs:
            lines.append(
                f"run={row.run_id} started={_format_dt(row.started_at)} status={row.status} "
                f"failed_items={row.total_failed_items} errors={row.error_count}"
            )

    lines.extend(_section("Recent Errors"))
    if not recent_errors:
        lines.append("No recent errors found.")
    else:
        for row in recent_errors:
            lines.append(
                f"error={row.error_id} run={row.run_id} stage={row.stage} [{row.stage_group}] "
                f"item={row.item_id or '-'} type={row.error_type} run_status={row.run_status} "
                f"at={_format_dt(row.occurred_at)} message={row.error_message}"
            )

    return "\n".join(lines)


def generate_throughput_report(db: Session, days: int = 30) -> str:
    throughput = get_throughput_trend(db, days=days)
    stage_volume = get_stage_volume_trend(db, days=days)

    lines: list[str] = _section(f"Throughput ({days}d)")

    lines.extend(_section("Daily Throughput"))
    if not throughput:
        lines.append("No throughput data found.")
    else:
        for row in throughput:
            lines.append(
                f"{row.run_date}: attempted={row.items_attempted} succeeded={row.items_succeeded} "
                f"failed={row.items_failed} success_rate={row.success_rate_percent:.1f}%"
            )

    lines.extend(_section("Stage Volume Trend"))
    if not stage_volume:
        lines.append("No stage volume data found.")
    else:
        for row in stage_volume:
            lines.append(f"{row.run_date}: {row.stage} [{row.stage_group}] attempted={row.items_attempted}")

    return "\n".join(lines)


def generate_compare_report(
    db: Session,
    before_start: datetime,
    before_end: datetime,
    after_start: datetime,
    after_end: datetime,
) -> str:
    comparisons = compare_periods(
        db,
        before_start=before_start,
        before_end=before_end,
        after_start=after_start,
        after_end=after_end,
    )
    efficiency_comparisons = compare_stage_efficiency_periods(
        db,
        before_start=before_start,
        before_end=before_end,
        after_start=after_start,
        after_end=after_end,
    )

    lines: list[str] = _section(
        "Stage Comparison "
        f"(before={_format_dt(before_start)}..{_format_dt(before_end)}, "
        f"after={_format_dt(after_start)}..{_format_dt(after_end)})"
    )
    if not comparisons:
        lines.append("No stage comparison data found.")
        return "\n".join(lines)

    for row in comparisons:
        lines.append(
            f"{row.stage} [{row.stage_group}]: before={_format_duration_seconds(row.before_seconds)} "
            f"after={_format_duration_seconds(row.after_seconds)} "
            f"change={_format_duration_seconds(row.change_seconds) if row.change_seconds is not None else '-'} "
            f"change_percent={f'{row.change_percent:.1f}%' if row.change_percent is not None else '-'}"
        )

    lines.extend(_section("Normalized Efficiency Comparison"))
    if not efficiency_comparisons:
        lines.append("No efficiency comparison data found.")
    else:
        for row in efficiency_comparisons:
            lines.append(
                f"{row.stage} [{row.stage_group}]: before_seconds_per_item="
                f"{f'{row.before_seconds_per_item:.2f}' if row.before_seconds_per_item is not None else '-'} "
                f"after_seconds_per_item="
                f"{f'{row.after_seconds_per_item:.2f}' if row.after_seconds_per_item is not None else '-'} "
                f"before_items_per_minute="
                f"{f'{row.before_items_per_minute:.2f}' if row.before_items_per_minute is not None else '-'} "
                f"after_items_per_minute="
                f"{f'{row.after_items_per_minute:.2f}' if row.after_items_per_minute is not None else '-'} "
                f"change_percent={f'{row.change_percent:.1f}%' if row.change_percent is not None else '-'}"
            )
    return "\n".join(lines)


def generate_summary_report(db: Session, days: int = 7) -> str:
    summary = build_monitoring_summary(db, days=days)
    return render_monitoring_summary(summary)


def generate_terminal_report(db: Session, limit: int = 10) -> str:
    return generate_recent_runs_report(db, limit=limit)
