# Project Status Log

Updates are appended at the bottom. Nothing is deleted — this is a running log.

> **Convention:** Update this file after every work session.
> Add what we built, what works, what doesn't, any errors hit, what's next.
> Keep the `Current Hierarchy` section below accurate for the current repo state.
> Keep the `Path Lifecycle Ledger` below accurate for major path creates, removes, moves, and renames.
> Never delete earlier session entries — append new sections at the bottom.
> If something is replaced, removed, or no longer relevant, update the lifecycle ledger and note it in the new session entry rather than erasing old session history.

---

## Current Hierarchy

Major paths only. This section is the current-state structure reference, not a full file inventory.

```
ai-event-agreegator/
├── agent/
│   ├── __init__.py
│   ├── curator_agent.py
│   ├── event_agent.py
│   ├── events_email_agent.py
│   ├── youtube_agent.py
│   └── youtube_email_agent.py
├── app/
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── session.py
│   ├── email/
│   │   ├── __init__.py
│   │   └── render.py
│   ├── models/
│   │   └── __init__.py
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── alerts.py
│   │   ├── logging_config.py
│   │   ├── models.py
│   │   ├── queries.py
│   │   ├── report.py
│   │   ├── stage.py
│   │   ├── summary.py
│   │   └── tracker.py
│   ├── scrapers/
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── feeds.py
│   │   │   └── scraper.py
│   │   └── youtube/
│   │       ├── __init__.py
│   │       ├── channels.py
│   │       ├── resolver.py
│   │       ├── scraper.py
│   │       └── selector.py
│   └── services/
│       ├── __init__.py
│       ├── process_curator.py
│       ├── process_digest.py
│       ├── process_events_email.py
│       ├── process_youtube_email.py
│       └── retry_utils.py
├── docs/
│   ├── FUTURE_FEATURES.md
│   ├── INTERACTIVE_WINDOW.md
│   ├── MONITORING_PHASES.md
│   ├── MONITORING_QUERIES.md
│   ├── PROJECT_STATUS.md
│   └── user_context.md
├── infra/
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/
│   ├── create_tables.py
│   ├── get_channel_id.py
│   └── monitoring_report.py
├── templates/
│   └── dashboard.html
├── tests/
│   ├── __init__.py
│   ├── test_event_scraper.py
│   └── test_youtube_scraper.py
├── .env.example
├── .gitignore
├── .python-version
├── AGENTS.md
├── Makefile
├── README.md
├── ai-event-agreegator.code-workspace
├── main.py
├── pyproject.toml
└── uv.lock
```

## Path Lifecycle Ledger

Major paths only. Use this ledger for creates, removes, moves, and renames that materially affect project structure.

| Path | Kind | Created | Removed | Notes |
|---|---|---|---|---|
| `agent/` | dir | 2026-03-10 |  | Initial project scaffold. |
| `app/` | dir | 2026-03-10 |  | Core application package. |
| `app/db/` | dir | 2026-03-10 |  | Scaffolded initially; DB models and repository added later the same day. |
| `app/models/` | dir | 2026-03-10 |  | Shared app-level models package; currently minimal. |
| `app/scrapers/events/` | dir | 2026-03-10 |  | Event scraping added in session 2. |
| `app/email/` | dir | 2026-03-11 |  | HTML email rendering package. |
| `app/monitoring/` | dir | 2026-03-12 |  | Pipeline monitoring foundation v1. |
| `app/monitoring/queries.py` | file | 2026-03-12 |  | Reusable monitoring analytics layer. |
| `app/monitoring/summary.py` | file | 2026-03-12 |  | Rule-based monitoring focus-area summary layer. |
| `app/services/retry_utils.py` | file | 2026-03-12 |  | Shared retry helper used by API-heavy stages for retry/backoff telemetry. |
| `docs/` | dir | 2026-03-10 |  | Introduced during project cleanup; houses project docs. |
| `docs/FUTURE_FEATURES.md` | file | 2026-03-12 |  | Append-only future feature tracker. |
| `docs/INTERACTIVE_WINDOW.md` | file | 2026-03-10 |  | Created at repo root, moved into `docs/` during cleanup. |
| `docs/MONITORING_PHASES.md` | file | 2026-03-12 |  | Monitoring roadmap and implementation checklist. |
| `docs/MONITORING_QUERIES.md` | file | 2026-03-12 |  | SQL reference and query-surface documentation for monitoring analytics. |
| `docs/PROJECT_STATUS.md` | file | 2026-03-10 |  | Created at repo root, moved into `docs/` during cleanup. |
| `docs/user_context.md` | file | 2026-03-11 |  | Curator personalization context. |
| `infra/` | dir | 2026-03-10 |  | Infrastructure files moved here during cleanup. |
| `scripts/` | dir | 2026-03-10 |  | Utility and DB bootstrap scripts. |
| `scripts/monitoring_report.py` | file | 2026-03-12 |  | CLI report for pipeline monitoring. |
| `templates/` | dir | 2026-03-11 |  | Dashboard HTML assets. |
| `tests/` | dir | 2026-03-10 |  | Integration tests. |
| `AGENTS.md` | file | 2026-03-12 |  | Repo-local agent workflow rules. |
| `Makefile` | file | 2026-03-10 |  | Added during project cleanup. |
| `main.py` | file | 2026-03-10 |  | Root pipeline entrypoint. |
| `docker-compose.yml` | file | 2026-03-10 | 2026-03-10 | Replaced by `infra/docker-compose.yml` during project cleanup. |
| `Dockerfile` | file | 2026-03-10 | 2026-03-10 | Replaced by `infra/Dockerfile` during project cleanup. |
| `INTERACTIVE_WINDOW.md` | file | 2026-03-10 | 2026-03-10 | Moved to `docs/INTERACTIVE_WINDOW.md` during project cleanup. |
| `PROJECT_STATUS.md` | file | 2026-03-10 | 2026-03-10 | Moved to `docs/PROJECT_STATUS.md` during project cleanup. |

## Session Log

---

## 2026-03-10 — Initial status snapshot

### Structure changes
- Baseline repo scaffold established with `agent/`, `app/`, `tests/`, root Docker files, and root project docs before later cleanup moved infrastructure/docs into dedicated directories.

### What's been built

**`app/scrapers/youtube/scraper.py`**
- `Channel(BaseModel)` — Pydantic model: `channel_id`, `name`
- `Video(BaseModel)` — Pydantic model: `video_id`, `title`, `url` (HttpUrl), `published_at`, `channel_name`, `channel_id`, `transcript | None`
- `YouTubeScraper` class — instantiated with `channel_id` + `channel_name`
  - `fetch_latest_videos(within_days=7)` — pulls from YouTube RSS feed, filters by age, returns `list[Video]`
  - `fetch_latest_video()` — returns the single most recent video regardless of age
  - `fetch_transcript(video)` — attaches transcript text via `youtube-transcript-api`, returns new `Video` via `model_copy`
  - `scrape(within_days=14, with_transcripts=True)` — full pipeline

**`app/scrapers/youtube/channels.py`**
- `CHANNELS` — list of 8 pre-configured channels (Fireship, Theo, Karpathy, AI Explained, Diary of a CEO, Lex Fridman, My First Million, How I Built This)

**`app/scrapers/youtube/__init__.py`**
- Exports: `YouTubeScraper`, `Video`, `Channel`, `CHANNELS`

**`tests/test_youtube_scraper.py`**
- `test_fetch_latest_video_returns_video` — hits real RSS feed for 2 channels, validates Video fields
- `test_fetch_transcript_attaches_text` — fetches transcript for Fireship's latest video

**Infrastructure**
- `docker-compose.yml` — Postgres 16 + app container
- `.env.example` — `DATABASE_URL`, `OPENAI_API_KEY`, Postgres credentials
- `pyproject.toml` — Python 3.14, deps: feedparser, youtube-transcript-api, pydantic, sqlalchemy, alembic, apscheduler, httpx, openai, beautifulsoup4, psycopg2-binary

### What works
- YouTube RSS scraping — confirmed working, returns valid `Video` Pydantic models
- `test_fetch_latest_video_returns_video` — PASSED
- `test_fetch_transcript_attaches_text` — SKIPPED (IP blocked by YouTube on this machine; expected in some environments, not a code bug)

### What doesn't work / not yet built
- `app/db/` — empty, no models, migrations, or connection setup
- `app/models/` — empty
- `app/services/` — empty, no LLM/summarisation logic
- `agent/` — empty
- `app/scrapers/events/` — empty, no event scraper yet
- No scheduler wired up (APScheduler installed but unused)
- No database writes — scraper returns data but nothing persists
- No OpenAI/LLM integration
- No API layer or entrypoint

### Errors hit
- `ModuleNotFoundError: No module named 'app'` when running tests from inside `tests/` dir — fixed by running pytest from project root
- `__init__.py` still exported old function names (`scrape_channel`, `fetch_latest_videos`, `fetch_transcript`) after refactor to class — fixed by updating exports
- `Video` was a `@dataclass` — replaced with Pydantic `BaseModel`; `fetch_transcript` updated to use `model_copy` instead of mutating in place

### What's next
1. Set up DB layer — SQLAlchemy models in `app/db/`, Alembic migrations
2. Persist scraped videos to Postgres
3. ~~Build event scraper in `app/scrapers/events/`~~ — done (see 2026-03-10 session 2)
4. Wire up APScheduler to run scrapers on a schedule
5. Add OpenAI summarisation in `app/services/`
6. Build agent logic in `agent/`

---

## 2026-03-10 — EventScraper built

### Structure changes
- Added `app/scrapers/events/` and `tests/test_event_scraper.py`.

### What was built

**`app/scrapers/events/feeds.py`**
- `FEEDS` — 2 iCal feeds initially: DC Tech Events, DC Startup Hub (expanded to 25 feeds in next session)

**`app/scrapers/events/scraper.py`**
- `Event(BaseModel)` — Pydantic model: `title`, `start_time`, `end_time | None`, `location | None`, `url | None`, `source`
- `_to_utc_datetime(dt)` — helper to normalise iCal `date` or naive `datetime` to UTC-aware `datetime`
- `EventScraper` class — instantiated with optional `feeds` list + `within_days=14`
  - `_fetch_feed(url)` — `httpx.get` with redirects + 10s timeout, raises on HTTP error
  - `_parse_feed(raw, source)` — parses iCal bytes, filters to upcoming window, handles `date` vs `datetime` DTSTART/DTEND
  - `scrape()` — fetches all feeds, combines, sorts by `start_time`; bad feeds log a warning and are skipped

**`app/scrapers/events/__init__.py`**
- Exports: `EventScraper`, `Event`, `FEEDS`

**`tests/test_event_scraper.py`**
- `test_scrape_returns_events` — hits both real feeds, validates Event fields and source names
- `test_events_are_upcoming` — asserts all events fall within [now, now+14d]
- `test_events_sorted_by_start_time` — asserts sort order

**`pyproject.toml`**
- Added `icalendar>=7.0.3`

### What works
- `test_scrape_returns_events` — PASSED
- `test_events_are_upcoming` — PASSED
- `test_events_sorted_by_start_time` — PASSED
- Both feeds (DC Tech Events + DC Startup Hub) return valid `Event` models

### What doesn't work / not yet built
- `app/db/` — still empty
- `app/models/` — still empty
- `app/services/` — still empty
- `agent/` — still empty
- No scheduler, no DB writes, no LLM integration, no API layer

### Errors hit
- None this session

### What's next
1. Set up DB layer — SQLAlchemy models in `app/db/`, Alembic migrations
2. Persist scraped `Video` and `Event` objects to Postgres
3. Wire up APScheduler to run both scrapers on a schedule
4. Add OpenAI summarisation in `app/services/`
5. Build agent logic in `agent/`
6. ~~Build main.py~~ — done (see 2026-03-10 session 3)
7. ~~Filter YouTube Shorts~~ — done (see 2026-03-10 session 3)
8. ~~Deduplicate events~~ — done (see 2026-03-10 session 3)

---

## 2026-03-10 — Feeds expanded to 25, INTERACTIVE_WINDOW.md created

### What was built / changed

**`app/scrapers/events/feeds.py`**
- Expanded from 2 feeds to 25 feeds across DC, DMV, and Baltimore
- Added categories: AI/ML (4 groups), Data & Analytics (3), Cloud (1), Web & Mobile (2), Diversity (1), Hardware (1), Blockchain (1), Gaming (1), Baltimore (3), Networking/General (6)
- All feeds use the Meetup iCal URL pattern: `https://www.meetup.com/[slug]/events/ical/`
- Luma feeds excluded — require authentication, no public `.ics`
- PyData DC excluded — returns 403
- Maryland non-Meetup sites (TEDCO, Maryland Tech Council, etc.) excluded — no `.ics` feeds

```python
FEEDS = [
    # --- Aggregators ---
    {"name": "DC Tech Events", "url": "https://dctech.events/events.ics"},
    {"name": "DC Startup Hub", "url": "https://tockify.com/api/feeds/ics/dcstartuphub"},

    # --- AI / ML ---
    {"name": "Generative AI DC", "url": "https://www.meetup.com/dataopsdc/events/ical/"},
    {"name": "DC AI & Deep Learning", "url": "https://www.meetup.com/washington-d-c-artificial-intelligence-deep-learning/events/ical/"},
    {"name": "AI Innovators Tysons", "url": "https://www.meetup.com/ai-innovators-network-tysons-meetup-dc-nova-md/events/ical/"},
    {"name": "DC AI Developers", "url": "https://www.meetup.com/dc-ai-llms/events/ical/"},

    # --- Data & Analytics ---
    {"name": "Data Science DC", "url": "https://www.meetup.com/data-science-dc/events/ical/"},
    {"name": "Data Engineers DC", "url": "https://www.meetup.com/data-engineers/events/ical/"},
    {"name": "Big Data & Analytics", "url": "https://www.meetup.com/big-data-and-analytics-world/events/ical/"},

    # --- Cloud & Infrastructure ---
    {"name": "AWS DMV", "url": "https://www.meetup.com/amazon-web-services-dmv/events/ical/"},

    # --- Web & Mobile ---
    {"name": "DC iOS", "url": "https://www.meetup.com/dc-ios/events/ical/"},
    {"name": "DC Android", "url": "https://www.meetup.com/dcandroid/events/ical/"},

    # --- Diversity & Inclusion ---
    {"name": "WGXC DC", "url": "https://www.meetup.com/women-and-gender-expansive-coders-dc-wgxc-dc/events/ical/"},

    # --- Hardware & Makers ---
    {"name": "HacDC", "url": "https://www.meetup.com/hac-dc/events/ical/"},

    # --- Blockchain & Crypto ---
    {"name": "Bitcoin District", "url": "https://www.meetup.com/bitcoin-district/events/ical/"},

    # --- Gaming & Creative ---
    {"name": "IGDA DC", "url": "https://www.meetup.com/igda-dc/events/ical/"},

    # --- Baltimore ---
    {"name": "Baltimore Tech Meetup", "url": "https://www.meetup.com/baltimore-tech/events/ical/"},
    {"name": "Baltimore Code and Coffee", "url": "https://www.meetup.com/baltimore-code-and-coffee/events/ical/"},
    {"name": "Baltimore Black Techies", "url": "https://www.meetup.com/baltimore-black-techies-meetup/events/ical/"},

    # --- Networking & General ---
    {"name": "DC Code & Coffee", "url": "https://www.meetup.com/dc-code-coffee/events/ical/"},
    {"name": "Nerd Dinner Tysons", "url": "https://www.meetup.com/nerd-dinner-tysons/events/ical/"},
    {"name": "Civic Tech DC", "url": "https://www.meetup.com/Code-for-DC/events/ical/"},
    {"name": "Geo DC", "url": "https://www.meetup.com/geo-dc/events/ical/"},
    {"name": "ProductTank DC", "url": "https://www.meetup.com/producttank-washington-dc/events/ical/"},
    {"name": "EdTech DMV", "url": "https://www.meetup.com/edtechdmv/events/ical/"},
]
```

**`app/scrapers/events/scraper.py`**
- Added `User-Agent: Mozilla/5.0 (compatible; event-aggregator/1.0)` header to `_fetch_feed` — required by Tockify (was returning 403 without it)
- Added regex fix for Tockify malformed iCal: `P15M` → `PT15M` in `X-PUBLISHED-TTL` / `REFRESH-INTERVAL` fields

**`INTERACTIVE_WINDOW.md`** (new file at project root)
- Cheatsheet for using VSCode Interactive Window
- Explains `sys.path.insert` fix needed once per session
- Ready-to-paste code cells for EventScraper, single-feed scraping, YouTubeScraper, transcripts
- Notes on `HttpUrl` vs `str`, where shell commands go, kernel restart behaviour

**`app/__init__.py`, `app/scrapers/__init__.py`, `app/db/__init__.py`, `app/models/__init__.py`, `app/services/__init__.py`, `tests/__init__.py`**
- All created (empty) — required for Python package imports to resolve correctly

### What works
- All 5 tests passing
- 25 feeds returning ~100+ events in the next 14 days
- EventScraper handles per-feed failures gracefully (one bad feed doesn't break others)

### Errors hit
- Tockify 403 — fixed with `User-Agent` header
- Tockify `InvalidCalendar: Invalid iCalendar duration: P15M` — fixed with raw bytes regex before parsing
- `ModuleNotFoundError: No module named 'app'` from missing `__init__.py` files — fixed by creating them
- Interactive window confusion: VSCode Interactive Window is Python-only; shell commands go in Terminal

### What's next
1. Set up DB layer — SQLAlchemy models in `app/db/`, Alembic migrations
2. Persist scraped `Video` and `Event` objects to Postgres
3. Wire up APScheduler to run both scrapers on a schedule
4. Add OpenAI summarisation in `app/services/`
5. Build agent logic in `agent/`

---

## 2026-03-10 — main.py + YouTube Shorts filter + Event deduplication

### Structure changes
- Added `main.py` at repo root.
- Added package `__init__.py` files under `app/` and `tests/`.

### What was built / changed

**`main.py`** (new file at project root)
- Runs both scrapers and prints a summary to the terminal
- `sys.path.insert(0, Path(__file__).parent)` ensures `app` resolves correctly from any working directory
- Run with: `.venv/bin/python main.py`

**`app/scrapers/youtube/scraper.py`**
- Added `_is_short(video_id)` — HEAD request to `https://www.youtube.com/shorts/{id}` with `follow_redirects=False`; returns `True` if status 200 (Short), `False` if redirect (regular video)
- `fetch_latest_videos()` now skips Shorts

**`app/scrapers/events/scraper.py`**
- `Event` model updated: `url: HttpUrl | None` → `urls: list[str] = []`, `source: str` → `sources: list[str] = []`
- Added `_deduplicate()` — groups by `(title.lower(), start_time.date())`, merges URLs + sources from duplicates
- `scrape()` calls `_deduplicate()` before sorting

**`tests/test_event_scraper.py`**
- Updated: `event.source` → `event.sources` (list)

### What works
- `main.py` runs end-to-end
- Shorts filtered from YouTube results
- Duplicate events merged into one entry with combined URLs and sources
- All tests passing

### Errors hit
- `AttributeError: 'dict' object has no attribute 'channel_id'` — `CHANNELS` is dicts not objects; fixed with `ch["channel_id"]`
- `AttributeError: 'Event' object has no attribute 'urls'` in Interactive Window — stale kernel; fixed by restarting kernel
- PDF `FPDFUnicodeEncodingException` on smart quotes — fixed with Arial TTF from `/System/Library/Fonts/Supplemental/`
- PDF date rendering off-screen — fixed by adding `new_x="LMARGIN", new_y="NEXT"` to `multi_cell`

### What's next
1. Set up DB layer — SQLAlchemy models in `app/db/`, Alembic migrations
2. Persist scraped `Video` and `Event` objects to Postgres
3. Wire up APScheduler to run both scrapers on a schedule
4. Add OpenAI summarisation in `app/services/`
5. Build agent logic in `agent/`

---

## 2026-03-10 — DB layer + project cleanup

### Structure changes
- Created `infra/`, `scripts/`, and `docs/`.
- Moved root `docker-compose.yml` and `Dockerfile` into `infra/`.
- Moved root `PROJECT_STATUS.md` and `INTERACTIVE_WINDOW.md` into `docs/`.

### What was built

**PostgreSQL DB layer (complete)**
- `app/db/session.py` — SQLAlchemy engine + `SessionLocal`; reads `DATABASE_URL` from env, defaults to `postgresql://postgres:postgres@localhost:5432/aggregator`
- `app/db/models.py` — `YouTubeVideo` (PK: `video_id`) and `Event` (composite PK: `title` + `start_time`) ORM models; uses `ARRAY(Text)` for `urls` and `sources` columns
- `app/db/repository.py` — `save_videos`, `save_events` (both use `db.merge()` for upsert safety), `get_videos`, `get_events`
- `scripts/create_tables.py` — runs `Base.metadata.create_all(engine)` to initialise tables

**`infra/docker-compose.yml`** — Postgres 16 container, credentials `postgres`/`postgres`, DB `aggregator`

**Project structure cleanup**
- Created `infra/` — moved `docker-compose.yml` and `Dockerfile` here
- Created `scripts/` — moved `create_tables.py` here
- Created `docs/` — moved `PROJECT_STATUS.md` and `INTERACTIVE_WINDOW.md` here
- Added `Makefile` at root with short aliases
- Added `.env` to `.gitignore`

**`Makefile` targets**
```
make up       → docker compose -f infra/docker-compose.yml up -d
make down     → docker compose -f infra/docker-compose.yml down
make db-init  → uv run scripts/create_tables.py
make run      → uv run main.py
make test     → uv run pytest
```

### What works
- `make up` starts Postgres
- `make db-init` creates `youtube_videos` and `events` tables
- Connection verified in Beekeeper Studio (localhost:5432, postgres/postgres, db: aggregator)

### What works
- `make up` starts Postgres
- `make db-init` creates `youtube_videos` and `events` tables
- Connection verified in Beekeeper Studio (localhost:5432, postgres/postgres, db: aggregator)

### What's next (superseded by next session)
1. Wire `repository.py` into `main.py` — persist scraped results to Postgres after each run
2. Wire up APScheduler to run both scrapers on a schedule
3. Add OpenAI summarisation in `app/services/`
4. Build agent logic in `agent/`

---

## 2026-03-10 — Transcripts + Webshare proxy + full pipeline wired up

### What was built

**`app/scrapers/youtube/scraper.py`**
- Fixed syntax bug: `except TranscriptsDisabled, NoTranscriptFound:` → `except (TranscriptsDisabled, NoTranscriptFound):`
- Added `_build_transcript_api()` — reads `WEBSHARE_PROXY_USERNAME` / `WEBSHARE_PROXY_PASSWORD` from env; if set, uses `WebshareProxyConfig`; otherwise direct requests
- `fetch_transcript()` now uses `_build_transcript_api()`

**`main.py`**
- Enabled `with_transcripts=True`
- Wired up `repository.save_videos()` and `repository.save_events()` — every run persists to Postgres

**`.env.example`** — added `WEBSHARE_PROXY_USERNAME` / `WEBSHARE_PROXY_PASSWORD` (blank by default)

### What works
- `make run` scrapes videos + events, fetches transcripts via Webshare proxy, saves everything to Postgres
- `youtube_videos.transcript` column populated in Beekeeper Studio
- Proxy is optional — leave blank in `.env` for direct requests (fine locally, may be blocked on cloud)

### What's next
1. Wire up APScheduler to run both scrapers on a schedule
2. Add OpenAI summarisation in `app/services/`
3. Build agent logic in `agent/`

---

## 2026-03-11 — Digest infrastructure + OpenAI integration

### What was built

**`app/db/models.py`** — added `Digest` table
- Composite PK: `(article_id, article_type)` — enables `db.merge()` upsert
- Fields: `url`, `title`, `summary`, `tools_concepts` (YouTube only), `relevance_score` (event only, 0–100), `source`, `created_at`
- `article_id` for events serialized as `"{title}||{start_time.isoformat()}"`

**`app/db/repository.py`** — added `digest_exists()` and `save_digest()`

**`agent/youtube_agent.py`** — YouTube digest agent
- Uses `gpt-4o-mini` with `client.beta.chat.completions.parse()` (structured output)
- Returns `YouTubeDigestResult(title, summary, tools_concepts)`

**`agent/event_agent.py`** — Event digest agent
- Uses `gpt-4o-mini` with `client.beta.chat.completions.parse()` (structured output)
- Returns `EventDigestResult(title, summary, relevance_score)`

**`app/services/process_digest.py`** — `process_digest(db)` orchestrator
- Reads all videos + events from DB, skips already-digested items
- Catches per-item errors without stopping the run

**`main.py`** — added `load_dotenv()` + wired `process_digest(db)` at end of pipeline

**`scripts/` and `Makefile`** — `make run` now runs the full pipeline end-to-end

### Current full pipeline (`make run`)
1. Scrape YouTube (last 2 days) → upsert to `youtube_videos`
2. Scrape Events (next 1 day) → upsert to `events`
3. Digest unprocessed videos via OpenAI → save to `digests`
4. Digest unprocessed events via OpenAI → save to `digests`

### What works
- All 3 tables (`youtube_videos`, `events`, `digests`) populated in Beekeeper Studio
- Digests contain AI-generated titles, summaries, tools/concepts, and relevance scores
- Re-runs are idempotent — already-digested items are skipped

### Errors hit
- `'GEMINI_API_KEY'` KeyError — `.env` not loaded at runtime; fixed with `load_dotenv()` in `main.py`
- Gemini free tier daily quota exhausted — switched to OpenAI `gpt-4o-mini`
- `IpBlocked` from YouTube transcript API — added to except clause, transcript stored as `null`

### What's next
1. Wire up APScheduler to run the full pipeline on a schedule
2. Build API layer to serve digest data
3. Build frontend or notification output (email / Slack digest)

---

## 2026-03-11 — Channel ID resolver + interactive selector (shelved)

### What was built

**`scripts/get_channel_id.py`**
- Standalone CLI to resolve a YouTube channel ID from a handle, name, or full URL
- Uses `httpx` + regex on the raw page HTML (no API key needed)
- Tries 5 regex patterns: `channelId`, `externalChannelId`, `ucid`, `channel_id=`, `browseId`
- Usage: `uv run scripts/get_channel_id.py fireship` → `UC2Xd-TjJByJyK2w1zNwY0zQ`
- Direct `/channel/UCxxx` URLs return the ID immediately (no HTTP request)

**`app/scrapers/youtube/resolver.py`** (new)
- Same `get_channel_id()` logic extracted as an importable module
- Exported from `app/scrapers/youtube/__init__.py`

**`app/scrapers/youtube/selector.py`** (new, shelved for later)
- `select_channels()` — interactive CLI prompt to pick channels from the library and optionally add new ones
- Supports session-only additions or permanent save to `channels.py`
- Not wired into `main.py` yet — will be added when interactive mode is needed

### What works
- `uv run scripts/get_channel_id.py fireship` → resolves correctly
- Direct channel URLs work immediately (no HTTP needed)
- Some channels (e.g. `@theo-t3gg`) return "Not found" — YouTube doesn't embed channel ID in all page types; workaround is to use the direct `/channel/UCxxx` URL

### What's next
1. Wire up APScheduler to run the full pipeline on a schedule
2. Build API layer to serve digest data
3. Build frontend or notification output (email / Slack digest)
4. Wire `select_channels()` from `selector.py` into `main.py` when interactive channel picking is needed

---

## 2026-03-11 — Curator agent + pipeline refactor

### What was built

**`agent/curator_agent.py`** (new)
- Reads `docs/user_context.md` at import time as system prompt context (Yohannes's profile)
- Sends all recent digests to `gpt-4o-mini`, asks for top 10 ranked by relevance 0–100
- Returns `CuratorResult(ranked_articles: list[RankedArticle])` via OpenAI structured output
- Each `RankedArticle`: `article_id`, `article_type`, `title`, `summary`, `score`, `ranking_reason`

**`docs/user_context.md`** (new)
- Yohannes's profile: CS+Economics student at SCSU, Applied AI Engineering focus
- Building AI Aggregator, CodePath AI110 (RAG+agentic), targeting AI/ML internship Summer 2026

**`app/services/process_curator.py`** (new)
- Fetches last 24h digests from DB, calls curator agent, prints top 10
- Deduplicates by `article_id` (LLM occasionally returns same item twice)
- Does **not** persist scores — ranking is display-only

**`app/services/process_digest.py`** refactored
- Event digesting removed — events are now summarized inline in `save_events()`
- `process_digest()` only processes YouTube videos now

**`app/db/repository.py`** additions
- `get_existing_video_ids(db) -> set[str]` — loads all known video IDs for skip optimization
- `get_recent_digests(db, hours=24) -> list[Digest]` — filtered by `uploaded_at`
- `save_events()` now calls `event_agent.run()` inline to generate `summary` + `relevance_score` for new events

**`app/db/models.py`** changes
- `Event` model: added `summary` (Text) and `relevance_score` (Integer) columns
- `Digest` model: renamed `created_at` → `uploaded_at`; removed `relevance_score`, `curator_score`, `curator_reason`

**`app/scrapers/youtube/scraper.py`** optimization
- Added `skip_ids: set[str] | None` to `fetch_latest_videos()` and `scrape()`
- Skip checked **before** `_is_short()` HEAD request — avoids all network calls for known videos

**`agent/event_agent.py`** simplified
- Now returns `EventSummaryResult(summary: str, relevance_score: int)` directly
- No longer writes full digest; just provides summary + score for the Event row

### Current full pipeline (`make run`)
1. Scrape events → upsert to `events` (summary + relevance_score generated inline for new events)
2. Load existing video IDs from DB
3. Scrape YouTube (last 5 days), skipping known IDs → upsert to `youtube_videos`
4. Digest unprocessed videos via OpenAI → save to `digests`
5. Run curator agent on last 24h digests → print top 10 ranked results

### What works
- Events get AI summary + relevance score directly on the `events` row (no separate digest)
- YouTube re-runs skip all already-scraped videos (no redundant Shorts checks or transcript fetches)
- Curator ranks and explains top 10 items personalized to Yohannes's profile
- Full pipeline is idempotent

### Errors hit
- `curator_score` NULL even after DB write: `db.merge()` on an already session-tracked object creates a detached copy — fix is to modify the object directly. Ultimately decided not to persist scores at all.
- `psycopg2.errors.UndefinedColumn` on `curator_score`: model updated before DB column added. Fixed with `ALTER TABLE digests ADD COLUMN IF NOT EXISTS`.

### What's next
1. Wire up APScheduler to run the full pipeline on a schedule
2. Build API layer to serve digest data
3. Build frontend or notification output (email / Slack digest)
---

## 2026-03-11 — Email agents + HTML dashboard

### What was built

**`agent/youtube_email_agent.py`** (new)
- Uses `gpt-4o-mini` structured output to generate a YouTube digest email
- Returns `YouTubeEmailResult(subject, greeting, introduction, articles: list[VideoSection], signature)`
- Each `VideoSection`: `title`, `channel_name`, `channel_url`, `summary`, `tools_concepts`, `score`, `ranking_reason`, `url`

**`agent/events_email_agent.py`** (new)
- Uses `gpt-4o-mini` structured output to generate an events digest email
- Returns `EventsEmailResult(subject, greeting, introduction, events: list[EventSection], signature)`
- Each `EventSection`: `title`, `date_time`, `location`, `summary`, `relevance_score`, `ranking_reason`, `url`

**`app/email/render.py`** (new)
- `render_youtube_email(result)` + `render_events_email(result)` — full HTML email builders
- Inline styles only (Gmail-compatible) — no CSS variables, no animations
- Matches dashboard palette: `#07070a` bg, amber `#e8a020` for videos, teal `#18c4a0` for events
- Score badge color-coded: gold (≥85), amber (≥70), orange (<70)
- Georgia serif fallback for headers

**`app/services/process_youtube_email.py`** (new)
- Fetches last 24h digests, builds `digest_map` with channel metadata joined from `youtube_videos`
- Calls curator agent → top 10 → `youtube_email_agent.run()` → renders HTML → sends via Gmail SMTP

**`app/services/process_events_email.py`** (new)
- Queries `events` table for next 14 days with `relevance_score >= 70`
- Calls `events_email_agent.run()` → renders HTML → sends via Gmail SMTP

**`templates/dashboard.html`** (new)
- Standalone HTML dashboard for "The Stack" — dark editorial aesthetic
- Bodoni Moda + Outfit fonts, amber/teal accents, rank number overlays, animated score bars
- "See More" toggle to expand lower-scored events
- Mock data — will connect to real API in next phase

**`main.py`** — added `process_youtube_email(db)` and `process_events_email(db)` calls

### Current full pipeline (`make run`)
1. Scrape events → upsert to `events` (summary + relevance_score inline)
2. Load existing video IDs from DB
3. Scrape YouTube (last 5 days), skipping known IDs → upsert to `youtube_videos`
4. Digest unprocessed videos → save to `digests`
5. Curator ranks last 24h digests → prints top 10
6. YouTube email: top 10 ranked → HTML email → Gmail
7. Events email: next 14 days, score ≥ 70 → HTML email → Gmail

### What works
- HTML emails send successfully via Gmail SMTP with app password
- Emails render correctly in Gmail (dark bg, amber/teal cards, score badges)
- Events email skips gracefully if no events qualify
- Dashboard HTML opens in browser with full mock data and "See More" toggle

### Errors hit
- `Send error: 'GMAIL_SENDER'` — env vars missing from `.env` (only in `.env.example`)
- Gmail app password with spaces must be quoted: `GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"`
- Channel name showing "Unknown" in emails — `d.source` empty for some digests; pending fix
- `ALTER TABLE digests DROP COLUMN curator_score/curator_reason` — ran manually to clean up DB

### What's next
1. Fix channel name/id in YouTube email — trace `source` field through digest pipeline
2. Wire up APScheduler for automated daily runs
3. Build FastAPI API layer to serve digest data
4. Wire dashboard to real API (replace mock data)

---

## 2026-03-12 — Project summary convention update + hierarchy refresh

### Structure changes
- None. This session only tightened the documentation convention around hierarchy maintenance.

### What was built / changed
- Updated the top `Convention` block: folder hierarchy/tree must be updated whenever session summaries are updated.
- Added this appended session entry with an up-to-date hierarchy snapshot of the current repo.

### What works
- Documentation now explicitly enforces keeping project summary and hierarchy snapshot in sync.

### Errors hit
- None.

### What's next
1. Keep appending new entries at the bottom only, including hierarchy updates in each future summary update.
2. Continue pending product work from the previous session backlog (scheduler, API layer, dashboard data wiring).

---

## 2026-03-12 — Pipeline monitoring foundation (v1) implemented

### Structure changes
- Added `app/monitoring/`.
- Added `scripts/monitoring_report.py`.

### What was built

**`app/monitoring/`** (new package)
- `logging_config.py` — `configure_logging()` sets console + `logs/pipeline.log` handlers via stdlib logging
- `models.py` — new SQLAlchemy tables: `pipeline_runs`, `pipeline_stage_metrics`, `pipeline_errors` using shared Postgres enum `pipeline_status` (`running/success/partial/failed`)
- `alerts.py` — `AlertHandler` protocol + `NoopAlertHandler`
- `tracker.py` — `PipelineTracker.start()`, `finish()`, `abort()`, `record_error()`, `record_stage_metric()`
- `stage.py` — `StageMonitor` context manager with `attempt()`, `succeed()`, `fail()` and no-op behavior when tracker is `None`
- `report.py` — terminal report generator for recent runs, stage metrics, and error counts
- `__init__.py` — exports public monitoring API

**Pipeline + service wiring**
- `main.py` now:
  - configures logging at startup
  - starts `PipelineTracker`
  - wraps scrape stages in `StageMonitor("youtube_scrape")` and `StageMonitor("events_scrape")`
  - passes `tracker` into service calls
  - uses `try/except/finally` with `tracker.finish()` / `tracker.abort(exc)` and guaranteed `db.close()`
- `app/services/process_digest.py` — added optional `tracker`; wraps digest loop in `StageMonitor("digest_videos")`; per-video failures call `stage.fail(..., item_id=video_id)`
- `app/services/process_curator.py` — added optional `tracker`; wrapped in `StageMonitor("curator")`
- `app/services/process_youtube_email.py` — added optional `tracker`; wrapped in `StageMonitor("youtube_email")`
- `app/services/process_events_email.py` — added optional `tracker`; wrapped in `StageMonitor("events_email")`
- `app/db/repository.py` — `save_events(..., tracker=None)` now includes `StageMonitor("events_enrichment")` for per-event summary generation failures

**DB + tooling updates**
- `app/db/models.py` now imports monitoring models at bottom:
  - `from app.monitoring import models as _monitoring_models  # noqa`
- `scripts/create_tables.py` now prints dynamic table names from `Base.metadata.tables`
- `scripts/monitoring_report.py` (new) — CLI for monitoring report (`--limit` supported)
- `Makefile` target added:
  - `make monitoring-report` → `uv run scripts/monitoring_report.py`

### What works
- New monitoring tables are created via `scripts/create_tables.py`:
  - `pipeline_runs`, `pipeline_stage_metrics`, `pipeline_errors`
- Monitoring report CLI runs successfully:
  - returns `No pipeline runs found.` on an empty monitoring dataset
- Python compile check passed for updated/new modules:
  - `.venv/bin/python -m compileall app scripts main.py`
- `StageMonitor` no-tracker compatibility works (no-op behavior confirmed in a direct smoke check)

### Errors hit
- Running `uv run ...` inside sandbox failed due UV cache permissions (`/Users/jon/.cache/uv`) — resolved by running the check with escalation
- Initial `scripts/monitoring_report.py` run failed with `UndefinedTable: pipeline_runs` because new tables were not created yet — resolved by running `scripts/create_tables.py` and re-running report

### What's next
1. Run `main.py` once end-to-end in your local environment to generate the first `pipeline_runs` row and stage/error metrics.
2. Validate `logs/pipeline.log` output and confirm expected run status transitions (`success`/`partial`/`failed`).
3. Add optional retention maintenance for `pipeline_errors` (manual SQL or scheduled cleanup later).
4. Add a real alert implementation (e.g., Slack) by implementing `AlertHandler`.

---

## 2026-03-12 — Future feature tracking + repo-local agent instructions

### Structure changes
- Added `AGENTS.md`.
- Added `docs/FUTURE_FEATURES.md`.

### What was built / changed
- Added `AGENTS.md` at repo root with repo-local instructions so any coding agent can consistently:
  - update `docs/PROJECT_STATUS.md` after work sessions
  - update `docs/FUTURE_FEATURES.md` whenever future work ideas come up
- Added `docs/FUTURE_FEATURES.md` as an append-only future feature tracker with:
  - a top `Current Backlog` section for quick agent handoff
  - dated log entries at the bottom
  - initial feature ideas seeded from project history and recent monitoring discussions
- Added `logs/` to `.gitignore` because `logs/pipeline.log` is runtime output, not source.

### What works
- There is now a repo-local mechanism for future agents to follow, instead of relying only on a convention buried inside `docs/PROJECT_STATUS.md`.
- Future feature ideas now have a dedicated place to live without mixing them into completed work history.

### Errors hit
- None this session.

### What's next
1. Keep `docs/FUTURE_FEATURES.md` current whenever new future work is mentioned in planning, implementation, review, or debugging.
2. Continue using `docs/PROJECT_STATUS.md` only for completed work/session history.
3. When a backlog item ships, mark it in `docs/FUTURE_FEATURES.md` and record the shipped work in `docs/PROJECT_STATUS.md`.

---

## 2026-03-12 — Project status hierarchy tracking refactored

### Structure changes
- None to repo paths. This session changed the documentation model only.

### What was built / changed
- Reworked `docs/PROJECT_STATUS.md` into:
  - one top-level `Current Hierarchy` section
  - one top-level `Path Lifecycle Ledger`
  - one append-only `Session Log`
- Removed repeated full-tree snapshots from historical session entries and replaced them with short `Structure changes` sections where needed.
- Updated `AGENTS.md` so future agents maintain the canonical hierarchy and lifecycle ledger instead of pasting full trees into every session entry.

### What works
- `docs/PROJECT_STATUS.md` now has exactly one canonical hierarchy section near the top.
- Major path create/remove/move history now has a dedicated ledger instead of being scattered across repeated snapshots.
- Historical session notes remain in place while structure tracking is less noisy and easier to maintain.

### Errors hit
- None.

### What's next
1. Keep the top hierarchy current when structure changes.
2. Update the lifecycle ledger whenever a major path is created, moved, renamed, or removed.
3. Keep future session entries append-only and use `Structure changes` only when structure actually changes.

---

## 2026-03-12 — Future features doc now includes shipped capabilities

### Structure changes
- None. This session changed documentation content only.

### What was built / changed
- Updated `docs/FUTURE_FEATURES.md` to include a top-level `Implemented Features` section in addition to the existing `Current Backlog`.
- Seeded the new implemented-features section with major capabilities already shipped, using this status log as the source of truth.
- Updated `AGENTS.md` so future agents maintain both:
  - shipped capabilities in `Implemented Features`
  - upcoming work in `Current Backlog`

### What works
- `docs/FUTURE_FEATURES.md` now answers both:
  - what the project already has
  - what is still planned

### Errors hit
- None.

### What's next
1. Move backlog items into `Implemented Features` when they ship.
2. Keep `docs/PROJECT_STATUS.md` as the detailed historical source and `docs/FUTURE_FEATURES.md` as the quick capability/backlog summary.

---

## 2026-03-12 — Monitoring query layer + analytics CLI

### Structure changes
- Added `app/monitoring/queries.py`.
- Added `docs/MONITORING_QUERIES.md`.

### What was built / changed
- Added `app/monitoring/queries.py` as the reusable monitoring analytics layer with parameterized helpers for:
  - recent runs
  - overall health
  - success and duration trends
  - slowest runs
  - stage performance and variance
  - failure analysis
  - throughput
  - before/after comparison
  - generic stage-grouped analytics such as AI workload and status distribution
- Reworked `app/monitoring/report.py` to format human-readable analytics reports using the new query layer instead of embedding query logic directly.
- Expanded `scripts/monitoring_report.py` into a multi-command CLI:
  - `recent-runs`
  - `health`
  - `stage-performance`
  - `failures`
  - `throughput`
  - `compare`
- Added `docs/MONITORING_QUERIES.md` with:
  - supported named queries
  - SQL reference examples
  - interpretation notes
  - known caveats
- Added `Monitoring Query Layer` to implemented capabilities and `Monitoring Telemetry Extension` to future backlog in `docs/FUTURE_FEATURES.md`.

### What works
- Query helpers compile and import successfully.
- `scripts/monitoring_report.py --help` now exposes the analytics command families.
- Stage grouping degrades safely to `unknown` for unseen future stage names.

### Errors hit
- None.

### What's next
1. Run the new monitoring commands against real monitoring data once pipeline runs exist.
2. Add telemetry fields later for truthful cost/model/provider analytics rather than inferring cost from duration.
3. Reuse this query layer in future API, dashboard, or MCP surfaces instead of duplicating SQL.

---

## 2026-03-12 — Makefile shortcuts for monitoring commands

### Structure changes
- None. This session changed developer workflow commands only.

### What was built / changed
- Expanded `Makefile` monitoring commands so common monitoring checks no longer require remembering the CLI subcommands.
- Kept `make monitoring-report` as the default recent-runs view.
- Added dedicated Make targets for:
  - `monitoring-runs`
  - `monitoring-health`
  - `monitoring-stage-performance`
  - `monitoring-failures`
  - `monitoring-throughput`
  - `monitoring-compare`
- `monitoring-compare` now accepts `BEFORE_START`, `BEFORE_END`, `AFTER_START`, and `AFTER_END` variables so period comparison can be run from `make` without editing commands manually.

### What works
- Common monitoring views now have direct `make` aliases.
- Period comparison can be launched through `make` with explicit date variables.

### Errors hit
- None.

### What's next
1. Use the new Make targets as the normal operator entrypoint for monitoring checks.
2. Add a `help` target later if the Makefile grows enough that command discovery becomes a friction point.

---

## 2026-03-12 — Monitoring phases checklist + summary layer kickoff

### Structure changes
- Added `docs/MONITORING_PHASES.md`.
- Added `app/monitoring/summary.py`.

### What was built / changed
- Added `docs/MONITORING_PHASES.md` as the monitoring roadmap checklist so future agents can continue phase work without reconstructing it from chat history.
- Updated `AGENTS.md` so monitoring work now also requires keeping `docs/MONITORING_PHASES.md` current.
- Started Phase 0 by adding `git_sha` and optional `config_version` attribution to `pipeline_runs`.
- Updated `PipelineTracker.start()` to auto-capture the current git SHA and optional `PIPELINE_CONFIG_VERSION` from env.
- Updated `scripts/create_tables.py` to add the new run-metadata columns to existing Postgres tables via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
- Added normalized stage-efficiency analytics to `app/monitoring/queries.py`:
  - `seconds_per_item`
  - `items_per_minute`
  - normalized before/after comparison
- Expanded monitoring reports so stage-performance and compare outputs include normalized efficiency, not just raw duration.
- Added `app/monitoring/summary.py` as the first deterministic monitoring summary layer:
  - bottleneck detection
  - regression detection
  - instability warnings
  - reliability warnings
  - incomplete-observability warnings
  - recent-error focus
- Expanded the monitoring CLI with `summary --days N`.
- Added `make monitoring-summary`.
- Updated `docs/MONITORING_QUERIES.md` and `docs/FUTURE_FEATURES.md` to reflect the new operator surface and the next monitoring backlog.

### What works
- Recent-run reports now surface run attribution metadata.
- Monitoring now supports normalized optimization analysis instead of raw duration only.
- A deterministic summary layer can now tell the operator where to focus next without using an LLM.
- The monitoring roadmap is now captured in a persistent checklist file rather than only in chat.

### Errors hit
- `.env.example` patch context mismatch due to file drift — resolved by reading the file and patching against the live contents.

### What's next
1. Implement ranking history persistence so score drift and ranking volatility become measurable.
2. Add digest freshness/version tracking so stale summaries are visible in ranking analysis.
3. Add batch/retry telemetry so batching and API optimizations can be measured honestly.

---

## 2026-03-12 — Ranking history persistence + digest freshness

### Structure changes
- None. This session changed schema, persistence, analytics, and docs, but did not add new major paths.

### What was built / changed
- Added `CuratorRun` and `CuratorRanking` ORM models so curator scoring history persists across runs.
- Added digest metadata fields on `Digest`:
  - `digest_version`
  - `digest_generated_at`
  - `source_updated_at`
  - `content_last_seen_at`
  - `model_name`
  - `prompt_version`
- Updated `scripts/create_tables.py` to backfill and alter existing `digests` rows for the new metadata fields.
- Updated `PipelineTracker`-adjacent digest flow so existing digests are now touched when the source item is seen again, instead of only recording the original generation timestamp forever.
- Updated `process_digest()` to stamp new digests with version/freshness/model metadata.
- Updated `process_curator()` to:
  - rank the last 7 days of digests instead of only same-day digests
  - persist each curator run and ranked item
- Updated `process_youtube_email()` to reuse the latest saved curator run for the current pipeline run when available, avoiding a redundant ranking API call.
- Added monitoring analytics for:
  - ranking drift
  - digest freshness
- Expanded monitoring CLI and Makefile with:
  - `ranking-drift`
  - `digest-freshness`
  - `make monitoring-ranking-drift`
  - `make monitoring-digest-freshness`
- Extended the rule-based monitoring summary so it can surface ranking drift and stale-ranked-digest warnings when enough data exists.
- Updated `docs/MONITORING_PHASES.md`, `docs/MONITORING_QUERIES.md`, and `docs/FUTURE_FEATURES.md` to reflect the shipped state.

### What works
- The database now contains `curator_runs` and `curator_rankings` tables.
- Digest freshness metadata is backfilled and queryable.
- `scripts/monitoring_report.py ranking-drift ...` works and handles the empty-history case cleanly.
- `scripts/monitoring_report.py digest-freshness ...` works against current DB data.
- `make monitoring-ranking-drift` and `make monitoring-digest-freshness` resolve to the expected commands.

### Errors hit
- Running schema creation and the new ranking/freshness reports in parallel caused a race where the reports executed before the new tables were created. The DB schema itself was correct; rerunning the reports after table creation resolved it.

### What's next
1. Add batch/retry telemetry so API-heavy stages can be optimized with evidence instead of inference.
2. Detect when stale digests dominate top-ranked results, not just when stale digests are present.
3. Add stronger ranking-stability summaries once enough persisted curator history exists.

---

## 2026-03-12 — Remaining monitoring phases completed

### Structure changes
- Added `app/services/retry_utils.py`.

### What was built / changed
- Added stage-level telemetry fields to `pipeline_stage_metrics` for:
  - `batch_size`
  - `total_batches`
  - `retry_count`
  - `backoff_count`
  - `concurrency_level`
  - `model_name`
  - `prompt_version`
- Extended `StageMonitor` and `PipelineTracker` so stages can record the new telemetry without changing the core monitoring lifecycle.
- Added `app/services/retry_utils.py` and wired retry/backoff handling into API-heavy stages:
  - `digest_videos`
  - `events_enrichment`
  - `curator`
  - `youtube_email`
  - `events_email`
- Added stage-performance analytics for:
  - p95 / p99 latency
  - batch telemetry
  - retry summary
  - focus-signal snapshot
  - stale top-rank dominance
- Expanded the CLI with `batch-telemetry`.
- Expanded `Makefile` with:
  - `monitoring-batch-telemetry`
  - `help`
- Strengthened the rule-based monitoring summary so it now:
  - ranks focus items by severity
  - scores regressions using both percentage and absolute increase
  - detects when stale digests dominate the latest top-ranked items
- Updated monitoring docs/checklists so nearly all monitoring phases are now marked complete.

### What works
- Monitoring can now report p95/p99 stage latency.
- Monitoring can now report batch/retry/concurrency/model/prompt telemetry for new runs.
- `make help` exposes the monitoring command surface directly.
- Summary output now includes ranking-drift signals and can detect stale-top-ranked dominance when the data supports it.

### Errors hit
- Running schema migration and telemetry-heavy reports in parallel caused a transient race where reports queried new columns before the `ALTER TABLE` finished. Rerunning after schema creation completed resolved it.
- Existing historical runs predate the new batch/retry telemetry columns, so telemetry sections show zero/default values until fresh runs are recorded with the new instrumentation.

### What's next
1. Reuse the monitoring query layer in future API, dashboard, or MCP surfaces instead of re-implementing reporting logic.
2. Add provider/token/cost telemetry later only if truthful cost analytics becomes a real requirement.

---

## 2026-03-12 — Run bootstrap and abort-path hardening

### Structure changes
- None. This session changed workflow and failure handling only.

### What was built / changed
- Updated `Makefile` so `make run` now depends on `db-init`, ensuring schema bootstrap runs before the pipeline starts.
- Hardened `PipelineTracker.abort()` to roll back the SQLAlchemy session before abort handling, which prevents a secondary `PendingRollbackError` after a flush failure.

### What works
- `make -n run` now expands to:
  - `uv run scripts/create_tables.py`
  - `uv run main.py`
- The abort path is now resilient to session rollback state after insert/flush failures.

### Errors hit
- The original `make run` failure happened because the pipeline started writing new `pipeline_stage_metrics` columns before the local DB schema had been updated with those columns.

### What's next
1. Re-run `make run` now that schema bootstrap is chained automatically.
2. Use the next fresh run to populate the new batch/retry telemetry columns.

---

## 2026-03-12 — YouTube Shorts cache + scrape telemetry

### Structure changes
- None. This session added a DB table and telemetry columns, but no new repo paths.

### What was built / changed
- Added `youtube_video_classifications` as a persisted cache for YouTube Shorts classification results.
- Updated `app/scrapers/youtube/scraper.py` so Shorts checks now:
  - reuse cached classifications across runs
  - reuse one `httpx.Client` per scrape pass instead of opening a fresh request client per check
  - avoid caching network failures as false negatives
- Added a dedicated `youtube_short_checks` monitoring stage in the main pipeline.
- Extended `pipeline_stage_metrics` with generic execution counters:
  - `items_skipped`
  - `cache_hit_count`
  - `network_call_count`
- Extended recent-runs and telemetry reports so scrape stages can now show cache hits, network calls, and skipped items instead of only duration.
- Extended the rule-based monitoring summary so it can flag an expensive Shorts-check path when network calls stay high and keep-rate stays low.
- Updated `scripts/create_tables.py` so existing Postgres tables gain the new monitoring columns and the new Shorts-classification table.
- Updated monitoring docs to record the new Shorts cache and scrape telemetry behavior.

### What works
- Schema bootstrap now creates `youtube_video_classifications`.
- Monitoring reports compile and run with the new stage-metric counters after schema bootstrap.
- The Shorts-classification path is now capable of recording:
  - total classification attempts
  - filtered Shorts
  - cache hits
  - fresh network calls
- Network classification failures no longer poison the cache.

### Errors hit
- Running `create_tables.py` and read-heavy monitoring reports in parallel caused a Postgres deadlock while altering `pipeline_stage_metrics`. Running schema bootstrap first and the reports second resolved it.
- The latest successful monitoring run still predates this Shorts-cache change, so `youtube_short_checks` will not appear in reports until the next fresh pipeline run is recorded.

### What's next
1. Run the pipeline again so `youtube_short_checks` telemetry is recorded on a fresh run.
2. Compare the next run against the current baseline to confirm Shorts cache hits replace repeated network calls.
3. If Shorts checks are still a major scrape bottleneck after the cache warms up, add bounded concurrency for uncached classifications.
