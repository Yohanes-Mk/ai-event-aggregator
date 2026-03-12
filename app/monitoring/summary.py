from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.monitoring.queries import (
    compare_stage_efficiency_periods,
    get_incomplete_runs,
    get_recent_errors,
    get_stage_efficiency,
    get_stage_failure_rates,
    get_stage_variance,
    utc_now,
)


@dataclass(slots=True)
class MonitoringFocus:
    category: str
    severity: str
    stage: str | None
    stage_group: str | None
    message: str
    recommendation: str


@dataclass(slots=True)
class MonitoringSummary:
    generated_at: datetime
    window_days: int
    focus_areas: list[MonitoringFocus]


def build_monitoring_summary(db: Session, days: int = 7) -> MonitoringSummary:
    generated_at = utc_now()
    focus_areas: list[MonitoringFocus] = []

    efficiency = get_stage_efficiency(db, days=days)
    variance = get_stage_variance(db, days=days)
    failure_rates = get_stage_failure_rates(db, days=days)
    incomplete_runs = get_incomplete_runs(db, days=days)
    recent_errors = get_recent_errors(db, days=min(days, 7), limit=20)

    current_end = generated_at
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

    if efficiency:
        bottleneck = efficiency[0]
        if bottleneck.seconds_per_item > 0:
            focus_areas.append(
                MonitoringFocus(
                    category="bottleneck",
                    severity="high",
                    stage=bottleneck.stage,
                    stage_group=bottleneck.stage_group,
                    message=(
                        f"{bottleneck.stage} is the current bottleneck at "
                        f"{bottleneck.seconds_per_item:.2f}s/item over {bottleneck.items_attempted} items."
                    ),
                    recommendation=_recommendation_for_stage(
                        bottleneck.stage_group,
                        "bottleneck",
                    ),
                )
            )

    regression = next((row for row in regressions if row.change_percent is not None and row.change_percent >= 20.0), None)
    if regression is not None:
        focus_areas.append(
            MonitoringFocus(
                category="regression",
                severity="high",
                stage=regression.stage,
                stage_group=regression.stage_group,
                message=(
                    f"{regression.stage} regressed by {regression.change_percent:.1f}% in seconds/item "
                    f"versus the previous {days}-day window."
                ),
                recommendation=_recommendation_for_stage(regression.stage_group, "regression"),
            )
        )

    unstable_stage = next((row for row in variance if row.variance_percent >= 50.0), None)
    if unstable_stage is not None:
        focus_areas.append(
            MonitoringFocus(
                category="instability",
                severity="medium",
                stage=unstable_stage.stage,
                stage_group=unstable_stage.stage_group,
                message=(
                    f"{unstable_stage.stage} is highly variable at {unstable_stage.variance_percent:.1f}% variance."
                ),
                recommendation=_recommendation_for_stage(unstable_stage.stage_group, "instability"),
            )
        )

    failure_stage = next((row for row in failure_rates if row.failure_rate_percent >= 5.0), None)
    if failure_stage is not None:
        focus_areas.append(
            MonitoringFocus(
                category="reliability",
                severity="high",
                stage=failure_stage.stage,
                stage_group=failure_stage.stage_group,
                message=(
                    f"{failure_stage.stage} has the highest material failure rate at "
                    f"{failure_stage.failure_rate_percent:.1f}%."
                ),
                recommendation=_recommendation_for_stage(failure_stage.stage_group, "reliability"),
            )
        )

    if incomplete_runs:
        focus_areas.append(
            MonitoringFocus(
                category="observability",
                severity="medium",
                stage=None,
                stage_group="monitoring",
                message=f"{len(incomplete_runs)} runs have no recorded stage metrics in the last {days} days.",
                recommendation="Audit stage instrumentation so every pipeline run records its expected stages.",
            )
        )

    if recent_errors:
        latest = recent_errors[0]
        focus_areas.append(
            MonitoringFocus(
                category="recent_errors",
                severity="medium",
                stage=latest.stage,
                stage_group=latest.stage_group,
                message=(
                    f"{len(recent_errors)} errors were recorded in the recent window. "
                    f"Latest: {latest.error_type} in {latest.stage}."
                ),
                recommendation="Start with the latest repeated error type and confirm whether it is transient or structural.",
            )
        )

    if not focus_areas:
        focus_areas.append(
            MonitoringFocus(
                category="steady_state",
                severity="low",
                stage=None,
                stage_group="monitoring",
                message=f"No major bottlenecks, regressions, or failure spikes were detected in the last {days} days.",
                recommendation="Keep collecting run history so the summary layer has enough baseline for stronger comparisons.",
            )
        )

    return MonitoringSummary(
        generated_at=generated_at,
        window_days=days,
        focus_areas=focus_areas[:5],
    )


def render_monitoring_summary(summary: MonitoringSummary) -> str:
    lines = [
        f"Monitoring Summary ({summary.window_days}d)",
        "-" * len(f"Monitoring Summary ({summary.window_days}d)"),
        f"generated_at={summary.generated_at.isoformat(timespec='seconds')}",
    ]
    for index, focus in enumerate(summary.focus_areas, start=1):
        lines.append(
            f"{index}. [{focus.severity}] {focus.category}: {focus.message}"
        )
        lines.append(f"   recommendation: {focus.recommendation}")
    return "\n".join(lines)


def _recommendation_for_stage(stage_group: str | None, symptom: str) -> str:
    if stage_group == "delivery":
        return "Batch delivery work, reduce duplicate rendering, and verify external send calls are not serialized unnecessarily."
    if stage_group == "enrichment":
        if symptom in {"bottleneck", "regression"}:
            return "Batch API work where possible, skip unchanged items, and measure seconds/item again after the change."
        return "Add retries/backoff and inspect whether external API latency or rate limits are driving the issue."
    if stage_group == "ranking":
        return "Check ranking window size, repeated item processing, and future score-history persistence before tuning prompts."
    if stage_group == "scrape":
        return "Reduce redundant network calls, cache stable lookups, and confirm skips happen before expensive fetches."
    return "Investigate the stage with normalized metrics first, then compare the next window against the previous one."
