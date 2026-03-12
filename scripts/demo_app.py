from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()

from app.db import repository
from app.db.models import CuratorRun, Digest, Event, YouTubeVideo
from app.db.session import SessionLocal
from app.monitoring import configure_logging
from app.scrapers.youtube.channels import CHANNELS
from app.services.process_curator import process_curator
from app.services.process_dashboard import ARTIFACT_PATH, process_dashboard
from app.services.process_events_email import process_events_email
from app.services.process_youtube_email import process_youtube_email
from agent.curator_agent import load_user_context, save_user_context, snapshot_user_context

configure_logging()

st.set_page_config(
    page_title="AI Aggregator Demo",
    page_icon=":material/auto_awesome:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Manrope:wght@400;500;600;700;800&display=swap');

        .stApp {
          background:
            radial-gradient(circle at top right, rgba(184, 92, 56, 0.08), transparent 28%),
            radial-gradient(circle at top left, rgba(24, 97, 86, 0.07), transparent 22%),
            linear-gradient(180deg, #f7f2ea 0%, #efe8de 100%);
        }

        .block-container {
          max-width: 1360px;
          padding-top: 1.4rem;
          padding-bottom: 4rem;
        }

        section[data-testid="stSidebar"] {
          border-right: 1px solid rgba(32, 24, 21, 0.08);
        }

        h1, h2, h3 {
          font-family: "Instrument Serif", serif !important;
          letter-spacing: -0.02em;
        }

        .hero-wrap {
          padding: 0.4rem 0 1.1rem 0;
        }

        .hero-kicker {
          font-size: 0.82rem;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: #9b5538;
          font-weight: 700;
          margin-bottom: 0.65rem;
        }

        .hero-title {
          font-family: "Instrument Serif", serif;
          font-size: 4.2rem;
          line-height: 0.9;
          color: #201815;
          margin: 0;
        }

        .hero-copy {
          color: #5d534b;
          font-size: 1.05rem;
          max-width: 58rem;
          margin-top: 0.8rem;
        }

        .section-label {
          color: #7b6f66;
          text-transform: uppercase;
          letter-spacing: 0.14em;
          font-size: 0.73rem;
          font-weight: 700;
          margin-bottom: 0.35rem;
        }

        .subtle-card {
          background: rgba(255, 252, 247, 0.9);
          border: 1px solid rgba(32, 24, 21, 0.08);
          border-radius: 22px;
          padding: 1rem 1.05rem;
        }

        div[data-testid="stMetric"] {
          background: rgba(255, 252, 247, 0.88);
          border: 1px solid rgba(32, 24, 21, 0.08);
          border-radius: 20px;
          padding: 0.9rem 1rem;
        }

        div[data-testid="stMetricLabel"] p {
          font-size: 0.8rem;
          letter-spacing: 0.05em;
          text-transform: uppercase;
          color: #736860;
        }

        div[data-testid="stMetricValue"] {
          font-family: "Instrument Serif", serif;
          color: #201815;
        }

        .env-chip {
          display: inline-block;
          margin: 0 0.5rem 0.55rem 0;
          padding: 0.35rem 0.75rem;
          border-radius: 999px;
          font-size: 0.82rem;
          font-weight: 600;
          border: 1px solid rgba(32, 24, 21, 0.08);
          background: rgba(255,255,255,0.78);
          color: #2b231f;
        }

        .env-chip.ready {
          background: rgba(24, 97, 86, 0.12);
          color: #14594d;
        }

        .env-chip.missing {
          background: rgba(184, 92, 56, 0.12);
          color: #9b5538;
        }

        .rank-title {
          font-weight: 700;
          color: #201815;
          margin-bottom: 0.2rem;
        }

        .rank-meta,
        .small-muted {
          color: #6e6259;
          font-size: 0.93rem;
        }

        .rank-reason {
          color: #544b44;
          margin-top: 0.45rem;
          line-height: 1.55;
        }

        .artifact-note code {
          background: rgba(0,0,0,0.06);
          padding: 0.18rem 0.35rem;
          border-radius: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@contextmanager
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "n/a"
    return value.astimezone().strftime("%b %d, %Y %I:%M %p")


def _env_ready() -> dict[str, bool]:
    return {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "GMAIL_SENDER": bool(os.getenv("GMAIL_SENDER")),
        "GMAIL_APP_PASSWORD": bool(os.getenv("GMAIL_APP_PASSWORD")),
        "GMAIL_RECIPIENT": bool(os.getenv("GMAIL_RECIPIENT")),
    }


def _load_snapshot() -> dict:
    with get_db() as db:
        latest_curator_run = db.query(CuratorRun).order_by(CuratorRun.started_at.desc()).first()
        recent_videos = db.query(YouTubeVideo).order_by(YouTubeVideo.published_at.desc()).limit(6).all()
        upcoming_events = db.query(Event).order_by(Event.start_time.asc()).limit(8).all()
        recent_digests = db.query(Digest).order_by(Digest.uploaded_at.desc()).limit(6).all()
        top_rankings = (
            repository.get_curator_rankings(db, latest_curator_run.id, limit=10)
            if latest_curator_run is not None
            else []
        )
        metrics = {
            "videos": db.query(YouTubeVideo).count(),
            "events": db.query(Event).count(),
            "digests": db.query(Digest).count(),
            "curator_runs": db.query(CuratorRun).count(),
        }

    return {
        "metrics": metrics,
        "latest_curator_run": latest_curator_run,
        "top_rankings": top_rankings,
        "recent_videos": recent_videos,
        "upcoming_events": upcoming_events,
        "recent_digests": recent_digests,
    }


def _section_intro(label: str, title: str, copy: str) -> None:
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
    st.subheader(title)
    st.caption(copy)


def _render_sidebar(snapshot: dict) -> None:
    with st.sidebar:
        st.markdown("### :material/space_dashboard: Demo Console")
        st.caption(
            "Operator-facing shell over the real pipeline. Use this sidebar for context, not as the main presentation surface."
        )

        with st.container(border=True):
            st.markdown("#### :material/check_circle: Demo Flow")
            st.markdown(
                "1. Show the dashboard preview\n"
                "2. Trigger a real action\n"
                "3. Show the ranked items and events\n"
                "4. Open the inbox or the generated artifact"
            )

        with st.container(border=True):
            st.markdown("#### :material/hub: Tracked Channels")
            st.pills(
                "Configured channels",
                [channel["name"] for channel in CHANNELS],
                selection_mode="multi",
                key="channel_pills",
                help="This is a visual list of the current configured YouTube sources. Changes are still code-driven, not edited here.",
            )

        with st.container(border=True):
            st.markdown("#### :material/settings: Environment")
            for key, ready in _env_ready().items():
                icon = ":material/check_circle:" if ready else ":material/error:"
                st.write(f"{icon} `{key}`")

        with st.container(border=True):
            st.markdown("#### :material/query_stats: Current Snapshot")
            st.write(f"Videos: **{snapshot['metrics']['videos']}**")
            st.write(f"Events: **{snapshot['metrics']['events']}**")
            st.write(f"Digests: **{snapshot['metrics']['digests']}**")
            st.write(f"Curator runs: **{snapshot['metrics']['curator_runs']}**")


def _render_hero(snapshot: dict) -> None:
    latest_run = snapshot["latest_curator_run"]
    col1, col2 = st.columns([3.2, 1.25], gap="large")
    with col1:
        st.markdown(
            """
            <div class="hero-wrap">
              <div class="hero-kicker">NSBE demo shell · real pipeline data</div>
              <div class="hero-title">AI Aggregator</div>
              <div class="hero-copy">
                Start with the polished dashboard artifact, trigger the live actions second, and only then drill down into the ranked items, upcoming events, and raw supporting records.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        with st.container(border=True):
            st.markdown("#### :material/verified: Demo Status")
            st.write(f"Latest curator run: **#{latest_run.id if latest_run else '-'}**")
            st.write(f"Last ranked at: **{_fmt_dt(latest_run.started_at) if latest_run else 'n/a'}**")
            st.write(f"Artifact ready: **{'yes' if ARTIFACT_PATH.exists() else 'no'}**")


def _preview_dashboard() -> None:
    with st.container(border=True):
        _section_intro(
            "Dashboard",
            "Preview",
            "This is the real generated artifact from the pipeline. It stays at the top because it is the strongest demo proof point.",
        )

        meta1, meta2 = st.columns([3, 1])
        with meta1:
            modified_at = None
            if ARTIFACT_PATH.exists():
                modified_at = datetime.fromtimestamp(ARTIFACT_PATH.stat().st_mtime, tz=timezone.utc)
            st.markdown(
                f'<div class="artifact-note">Artifact: <code>{ARTIFACT_PATH}</code> • last updated {_fmt_dt(modified_at)}</div>',
                unsafe_allow_html=True,
            )
        with meta2:
            st.caption("Generated by `process_dashboard()`")

        if not ARTIFACT_PATH.exists():
            st.info("No generated dashboard yet. Use `Render Dashboard` below or run `make run`.")
            return

        html = ARTIFACT_PATH.read_text(encoding="utf-8")
        components.html(html, height=920, scrolling=True)


def _render_actions(default_recipient: str | None) -> None:
    with st.container(border=True):
        _section_intro(
            "Actions",
            "Live Demo Controls",
            "These buttons call the real service layer from this repo. The tooltips explain exactly what each action does.",
        )

        readiness_markup = []
        for key, ready in _env_ready().items():
            state = "ready" if ready else "missing"
            readiness_markup.append(
                f'<span class="env-chip {state}">{key}: {state}</span>'
            )
        st.markdown("".join(readiness_markup), unsafe_allow_html=True)

        recipient_col, note_col = st.columns([2.3, 1], gap="large")
        with recipient_col:
            recipient = st.text_input(
                "Recipient email",
                value=default_recipient or "",
                placeholder="you@example.com",
                key="recipient_email",
                help="Overrides `GMAIL_RECIPIENT` for this demo action only.",
            )
        with note_col:
            st.caption("If a send fails here, check the terminal logs. The UI intentionally stays thin and surfaces the real service outcome.")

        btn1, btn2, btn3 = st.columns(3, gap="medium")
        with btn1:
            render_clicked = st.button(
                ":material/preview: Render Dashboard",
                key="render_dashboard_btn",
                use_container_width=True,
                type="primary",
                help="Rebuilds `artifacts/dashboard.html` from the current database state.",
            )
        with btn2:
            youtube_clicked = st.button(
                ":material/mail: Send YouTube Digest",
                key="send_youtube_btn",
                use_container_width=True,
                help="Runs the persisted ranking + YouTube email generation path and sends the result to the recipient above.",
            )
        with btn3:
            events_clicked = st.button(
                ":material/event: Send Events Digest",
                key="send_events_btn",
                use_container_width=True,
                help="Builds the events digest from the DB and sends it to the recipient above.",
            )

        if render_clicked:
            with st.spinner("Rendering dashboard from live DB data..."):
                with get_db() as db:
                    artifact = process_dashboard(db)
            if artifact is None:
                st.error("Dashboard render failed. Check the terminal logs.")
            else:
                st.success(f"Dashboard rendered: {artifact}")
                st.rerun()

        missing_core_env = not (
            _env_ready()["OPENAI_API_KEY"]
            and _env_ready()["GMAIL_SENDER"]
            and _env_ready()["GMAIL_APP_PASSWORD"]
        )

        if youtube_clicked:
            if not recipient:
                st.error("Recipient email is required for YouTube send.")
            elif missing_core_env:
                st.error("Email/OpenAI env vars are incomplete. Fix the missing settings shown above.")
            else:
                with st.spinner("Generating and sending YouTube digest..."):
                    with get_db() as db:
                        ok = process_youtube_email(db, recipient=recipient)
                if ok:
                    st.success(f"YouTube digest sent to {recipient}.")
                else:
                    st.error("YouTube digest failed. Check the terminal logs for the exact exception.")

        if events_clicked:
            if not recipient:
                st.error("Recipient email is required for events send.")
            elif missing_core_env:
                st.error("Email/OpenAI env vars are incomplete. Fix the missing settings shown above.")
            else:
                with st.spinner("Generating and sending events digest..."):
                    with get_db() as db:
                        ok = process_events_email(db, recipient=recipient)
                if ok:
                    st.success(f"Events digest sent to {recipient}.")
                else:
                    st.error("Events digest failed. Check the terminal logs for the exact exception.")


def _render_context_editor() -> None:
    with st.container(border=True):
        _section_intro(
            "Context",
            "Ranking Context Editor",
            "Edit the plain-text curator context directly. Save it here, then rerank so the dashboard and future YouTube digest actions use the updated profile.",
        )

        current_context = load_user_context()
        context_value = st.text_area(
            "User context markdown",
            value=current_context,
            height=320,
            key="user_context_editor",
            help="This is the live contents of `docs/user_context.md`. The curator reads this file at runtime.",
        )

        btn1, btn2, btn3 = st.columns([1, 1.3, 1], gap="medium")
        with btn1:
            save_clicked = st.button(
                ":material/save: Save Context",
                key="save_context_btn",
                use_container_width=True,
                help="Writes the text area contents back to `docs/user_context.md`.",
            )
        with btn2:
            rerank_clicked = st.button(
                ":material/refresh: Save, Re-rank, Refresh Dashboard",
                key="save_rerank_context_btn",
                use_container_width=True,
                help="Saves the context, runs the curator against recent digests, and rebuilds the dashboard so the change is visible immediately.",
            )
        with btn3:
            snapshot_clicked = st.button(
                ":material/archive: Archive Context Snapshot",
                key="archive_context_btn",
                use_container_width=True,
                help="Saves a timestamped markdown snapshot under `docs/context_snapshots/` without changing the active context file.",
            )

        st.caption(
            "Events email does not depend on this context. The YouTube digest and dashboard do, but only after a fresh curator run."
        )

        if save_clicked:
            save_user_context(context_value)
            st.success("Context saved to docs/user_context.md.")

        if snapshot_clicked:
            snapshot_path = snapshot_user_context(context_value, label="streamlit-context")
            st.success(f"Context snapshot saved: {snapshot_path}")

        if rerank_clicked:
            save_user_context(context_value)
            with st.spinner("Saving context, running curator, and refreshing the dashboard..."):
                with get_db() as db:
                    curator_run = process_curator(db)
                    artifact = process_dashboard(db)
            if curator_run is None:
                st.error("Context was saved, but no curator run was produced. Check whether recent digests exist and inspect the terminal logs.")
            elif artifact is None:
                st.warning(f"Context saved and curator run #{curator_run.id} completed, but dashboard refresh failed. Check the terminal logs.")
            else:
                st.success(
                    f"Context saved, curator run #{curator_run.id} completed, and dashboard refreshed."
                )
                st.rerun()


def _render_metrics(snapshot: dict) -> None:
    _section_intro(
        "Metrics",
        "System Snapshot",
        "These counts come directly from Postgres. They anchor the demo in stored system state, not a one-off UI rendering.",
    )
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    col1.metric("Videos", snapshot["metrics"]["videos"], help="Stored rows in `youtube_videos`.")
    col2.metric("Events", snapshot["metrics"]["events"], help="Stored rows in `events`.")
    col3.metric("Digests", snapshot["metrics"]["digests"], help="Stored rows in `digests`.")
    col4.metric("Curator Runs", snapshot["metrics"]["curator_runs"], help="Persisted ranking runs in `curator_runs`.")


def _render_rankings(snapshot: dict) -> None:
    with st.container(border=True):
        _section_intro(
            "Rankings",
            "Latest Ranked Videos",
            "These are pulled from the latest persisted curator run, not re-ranked ad hoc in the UI.",
        )

        latest_run = snapshot["latest_curator_run"]
        if latest_run is None or not snapshot["top_rankings"]:
            st.info("No curator run found yet. Run `make run` first.")
            return

        meta_left, meta_right = st.columns([3, 1])
        with meta_left:
            st.caption(
                f"Curator run #{latest_run.id} • model `{latest_run.model_name or '-'}` • prompt `{latest_run.prompt_version or '-'}` • {_fmt_dt(latest_run.started_at)}"
            )
        with meta_right:
            st.caption(f"{len(snapshot['top_rankings'])} items loaded")

        for ranking in snapshot["top_rankings"]:
            item_col, score_col = st.columns([6, 1], gap="medium")
            with item_col:
                with st.container(border=True):
                    st.markdown(f"**#{ranking.rank_position} · {ranking.title}**")
                    st.markdown(
                        f'<div class="rank-meta">{ranking.article_type} item</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="rank-reason">{ranking.ranking_reason}</div>',
                        unsafe_allow_html=True,
                    )
            with score_col:
                with st.container(border=True):
                    st.metric("Score", ranking.score)


def _render_content(snapshot: dict) -> None:
    _section_intro(
        "Data",
        "Supporting Records",
        "These sections show the source rows feeding the dashboard and email layers.",
    )
    tab1, tab2, tab3 = st.tabs(
        [":material/event: Upcoming Events", ":material/play_circle: Recent Videos", ":material/description: Recent Digests"]
    )

    with tab1:
        if not snapshot["upcoming_events"]:
            st.info("No upcoming events found.")
        for event in snapshot["upcoming_events"]:
            score = event.relevance_score if event.relevance_score is not None else "n/a"
            with st.container(border=True):
                st.markdown(f"**{event.title}**")
                st.caption(f"{_fmt_dt(event.start_time)} • {event.location or 'Location TBD'} • score {score}")
                if event.summary:
                    st.write(event.summary)

    with tab2:
        if not snapshot["recent_videos"]:
            st.info("No videos found.")
        for video in snapshot["recent_videos"]:
            with st.container(border=True):
                st.markdown(f"**{video.title}**")
                st.caption(f"{video.channel_name} • {_fmt_dt(video.published_at)}")
                st.link_button("Open video", video.url, use_container_width=False)

    with tab3:
        if not snapshot["recent_digests"]:
            st.info("No digests found.")
        for digest in snapshot["recent_digests"]:
            with st.container(border=True):
                st.markdown(f"**{digest.title}**")
                st.caption(f"{digest.article_type} • {digest.source} • version {digest.digest_version}")
                st.write(digest.summary)
                tags = []
                if digest.tools_concepts:
                    tags = [part.strip() for part in digest.tools_concepts.split(",") if part.strip()][:6]
                if tags:
                    st.pills(
                        "Top tags",
                        tags,
                        selection_mode="multi",
                        key=f"digest_tags_{digest.article_id}_{digest.article_type}",
                        help="Display-only tag extraction from the current `tools_concepts` text field.",
                    )


def main() -> None:
    _apply_styles()
    snapshot = _load_snapshot()
    _render_sidebar(snapshot)
    _render_hero(snapshot)
    _preview_dashboard()
    st.divider()
    _render_actions(default_recipient=os.getenv("GMAIL_RECIPIENT"))
    st.divider()
    _render_context_editor()
    st.divider()
    _render_metrics(snapshot)
    st.divider()
    _render_rankings(snapshot)
    st.divider()
    _render_content(snapshot)


if __name__ == "__main__":
    main()
