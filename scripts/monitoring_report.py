import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.monitoring.report import (
    generate_compare_report,
    generate_failures_report,
    generate_health_report,
    generate_recent_runs_report,
    generate_stage_performance_report,
    generate_summary_report,
    generate_throughput_report,
)


def _parse_datetime(value: str, *, end_of_day: bool = False) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        if len(value) == 10:
            if end_of_day:
                parsed = parsed + timedelta(days=1) - timedelta(microseconds=1)
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pipeline monitoring analytics.")
    subparsers = parser.add_subparsers(dest="command")

    recent_runs = subparsers.add_parser("recent-runs", help="Print recent pipeline runs.")
    recent_runs.add_argument("--limit", type=int, default=10, help="Number of recent runs to print.")

    health = subparsers.add_parser("health", help="Print overall pipeline health.")
    health.add_argument("--days", type=int, default=30, help="Window size in days.")
    health.add_argument("--limit", type=int, default=10, help="Number of slow runs to include.")

    stage_performance = subparsers.add_parser("stage-performance", help="Print stage performance analytics.")
    stage_performance.add_argument("--days", type=int, default=30, help="Window size in days.")

    failures = subparsers.add_parser("failures", help="Print failure-oriented analytics.")
    failures.add_argument("--days", type=int, default=30, help="Window size in days.")
    failures.add_argument("--limit", type=int, default=20, help="Row limit for detailed sections.")

    throughput = subparsers.add_parser("throughput", help="Print throughput analytics.")
    throughput.add_argument("--days", type=int, default=30, help="Window size in days.")

    summary = subparsers.add_parser("summary", help="Print rule-based monitoring focus areas.")
    summary.add_argument("--days", type=int, default=7, help="Window size in days.")

    compare = subparsers.add_parser("compare", help="Compare stage performance across two periods.")
    compare.add_argument("--before-start", required=True, help="Inclusive before-window start (ISO date or datetime).")
    compare.add_argument("--before-end", required=True, help="Inclusive before-window end (ISO date or datetime).")
    compare.add_argument("--after-start", required=True, help="Inclusive after-window start (ISO date or datetime).")
    compare.add_argument("--after-end", required=True, help="Inclusive after-window end (ISO date or datetime).")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.command in (None, "recent-runs"):
            limit = getattr(args, "limit", 10)
            report = generate_recent_runs_report(db, limit=limit)
        elif args.command == "health":
            report = generate_health_report(db, days=args.days, slowest_limit=args.limit)
        elif args.command == "stage-performance":
            report = generate_stage_performance_report(db, days=args.days)
        elif args.command == "failures":
            report = generate_failures_report(db, days=args.days, limit=args.limit)
        elif args.command == "throughput":
            report = generate_throughput_report(db, days=args.days)
        elif args.command == "summary":
            report = generate_summary_report(db, days=args.days)
        elif args.command == "compare":
            report = generate_compare_report(
                db,
                before_start=_parse_datetime(args.before_start),
                before_end=_parse_datetime(args.before_end, end_of_day=True),
                after_start=_parse_datetime(args.after_start),
                after_end=_parse_datetime(args.after_end, end_of_day=True),
            )
        else:
            parser.error(f"Unsupported command: {args.command}")
        print(report)
    finally:
        db.close()


if __name__ == "__main__":
    main()
