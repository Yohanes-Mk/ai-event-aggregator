from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.monitoring.queries import (
    compare_stage_efficiency_periods,
    get_digest_freshness,
    get_focus_signal_snapshot,
    get_incomplete_runs,
    get_recent_errors,
    get_recent_runs,
    get_ranking_drift,
    get_stage_efficiency,
    get_stage_failure_rates,
    get_stale_top_rank_dominance,
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
    focus_signals = get_focus_signal_snapshot(db, days=days)

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
    stale_top_rank = get_stale_top_rank_dominance(db, days=max(days, 30), stale_after_days=7, top_n=10)
    latest_run = next(iter(get_recent_runs(db, limit=1)), None)

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
        severity = _regression_severity(regression.change_percent, regression.before_seconds_per_item, regression.after_seconds_per_item)
        focus_areas.append(
            MonitoringFocus(
                category="regression",
                severity=severity,
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

    ranking_drift = get_ranking_drift(db, days=max(days, 30), min_score_delta=10, limit=5)
    if ranking_drift:
        item = ranking_drift[0]
        focus_areas.append(
            MonitoringFocus(
                category="ranking_drift",
                severity="medium",
                stage="curator",
                stage_group="ranking",
                message=(
                    f"{item.title} moved by {item.score_delta} points across {item.run_count} ranking runs."
                ),
                recommendation="Inspect whether ranking changes came from digest freshness, prompt changes, or a ranking-window change.",
            )
        )

    stale_ranked_digests = [
        row for row in get_digest_freshness(db, days=max(days, 30), stale_after_days=7, limit=20)
        if row.is_stale and row.ranking_count_recent > 0
    ]
    if stale_ranked_digests:
        item = stale_ranked_digests[0]
        focus_areas.append(
            MonitoringFocus(
                category="freshness",
                severity="medium",
                stage="digest_videos",
                stage_group="enrichment",
                message=(
                    f"{item.title} is being ranked with a stale digest (age {item.digest_age_days:.1f} days, "
                    f"{item.ranking_count_recent} recent ranking hits)."
                ),
                recommendation="Refresh digest versions when source content changes and audit how long ranked content should stay eligible.",
            )
        )

    if stale_top_rank.stale_share_percent >= 30.0 and stale_top_rank.ranked_items > 0:
        focus_areas.append(
            MonitoringFocus(
                category="stale_top_rank_dominance",
                severity="high" if stale_top_rank.stale_share_percent >= 50.0 else "medium",
                stage="curator",
                stage_group="ranking",
                message=(
                    f"{stale_top_rank.stale_share_percent:.1f}% of the latest top-ranked items are backed by stale digests "
                    f"({stale_top_rank.stale_ranked_items}/{stale_top_rank.ranked_items})."
                ),
                recommendation="Refresh digests before ranking or tighten the eligible ranking window so stale items do not dominate the top results.",
            )
        )

    if latest_run is not None:
        shorts_stage = next(
            (stage for stage in latest_run.stages if stage.stage == "youtube_short_checks"),
            None,
        )
        if (
            shorts_stage is not None
            and shorts_stage.duration_seconds >= 15.0
            and shorts_stage.network_call_count >= 10
            and shorts_stage.items_attempted > 0
        ):
            keep_rate = shorts_stage.items_succeeded / shorts_stage.items_attempted
            if keep_rate <= 0.15:
                focus_areas.append(
                    MonitoringFocus(
                        category="scrape_efficiency",
                        severity="high",
                        stage="youtube_short_checks",
                        stage_group="scrape",
                        message=(
                            f"youtube_short_checks spent {shorts_stage.duration_seconds:.1f}s on "
                            f"{shorts_stage.network_call_count} network calls, kept "
                            f"{shorts_stage.items_succeeded}/{shorts_stage.items_attempted} videos, "
                            f"and filtered {shorts_stage.items_skipped} shorts "
                            f"(cache_hits={shorts_stage.cache_hit_count})."
                        ),
                        recommendation=(
                            "Persist Shorts classifications, skip known IDs before network checks, "
                            "and verify cache hits climb on the next runs."
                        ),
                    )
                )

    if focus_signals.stale_top_rank_share_percent >= 30.0 and stale_top_rank.ranked_items == 0:
        focus_areas.append(
            MonitoringFocus(
                category="stale_top_rank_dominance",
                severity="medium",
                stage="curator",
                stage_group="ranking",
                message=f"Stale digests account for {focus_signals.stale_top_rank_share_percent:.1f}% of the latest ranked items.",
                recommendation="Refresh stale digests or reduce how long ranked content stays eligible.",
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

    focus_areas = sorted(
        focus_areas,
        key=lambda focus: (_severity_rank(focus.severity), focus.category),
        reverse=True,
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


def _severity_rank(severity: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(severity, 0)


def _regression_severity(
    change_percent: float | None,
    before_seconds_per_item: float | None,
    after_seconds_per_item: float | None,
) -> str:
    if change_percent is None:
        return "medium"
    absolute_increase = 0.0
    if before_seconds_per_item is not None and after_seconds_per_item is not None:
        absolute_increase = after_seconds_per_item - before_seconds_per_item
    if change_percent >= 50.0 or absolute_increase >= 5.0:
        return "high"
    if change_percent >= 25.0 or absolute_increase >= 2.0:
        return "medium"
    return "low"
