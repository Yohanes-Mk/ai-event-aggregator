# Project Status Log

Updates are appended at the bottom. Nothing is deleted — this is a running log.

> **Convention:** Update this file after every work session.
> Add what we built, what works, what doesn't, any errors hit, what's next.
> Never delete earlier entries — append new sections at the bottom.
> If something is replaced, removed, or no longer relevant, note that in the new entry (e.g. "replaced X with Y", "X removed — no longer needed") rather than erasing the old entry.

---

## 2026-03-10 — Initial status snapshot

### Folder Hierarchy

```
ai-event-agreegator/
├── agent/                          # (empty) future agent logic
├── app/
│   ├── db/                         # (empty) database setup, connection
│   ├── models/                     # (empty) shared app-level models
│   ├── scrapers/
│   │   ├── events/                 # (empty) future event scraper
│   │   └── youtube/
│   │       ├── __init__.py         # exports: YouTubeScraper, Video, Channel, CHANNELS
│   │       ├── channels.py         # CHANNELS list (8 pre-configured channels)
│   │       └── scraper.py          # Channel, Video (Pydantic), YouTubeScraper class
│   └── services/                   # (empty) future summarisation / LLM services
├── tests/
│   └── test_youtube_scraper.py     # integration tests (hits real YouTube RSS)
├── .env.example                    # DATABASE_URL, OPENAI_API_KEY, Postgres creds
├── docker-compose.yml              # Postgres 16 + app container
├── Dockerfile
├── pyproject.toml                  # Python 3.14, all deps declared
└── uv.lock
```

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

### Folder Hierarchy changes
`app/scrapers/events/` was empty — now populated:

```
ai-event-agreegator/
├── agent/                          # (empty) future agent logic
├── app/
│   ├── db/                         # (empty) database setup, connection
│   ├── models/                     # (empty) shared app-level models
│   ├── scrapers/
│   │   ├── events/
│   │   │   ├── __init__.py         # exports: EventScraper, Event, FEEDS
│   │   │   ├── feeds.py            # FEEDS list (2 iCal feed URLs)
│   │   │   └── scraper.py          # Event (Pydantic), EventScraper class
│   │   └── youtube/
│   │       ├── __init__.py         # exports: YouTubeScraper, Video, Channel, CHANNELS
│   │       ├── channels.py         # CHANNELS list (8 pre-configured channels)
│   │       └── scraper.py          # Channel, Video (Pydantic), YouTubeScraper class
│   └── services/                   # (empty) future summarisation / LLM services
├── tests/
│   ├── test_event_scraper.py       # integration tests (hits real iCal feeds)
│   └── test_youtube_scraper.py     # integration tests (hits real YouTube RSS)
├── .env.example                    # DATABASE_URL, OPENAI_API_KEY, Postgres creds
├── docker-compose.yml              # Postgres 16 + app container
├── Dockerfile
├── pyproject.toml                  # added: icalendar>=7.0.3
└── uv.lock
```

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

### Folder hierarchy (current, complete)

```
ai-event-agreegator/
├── agent/                          # (empty) future agent logic
├── app/
│   ├── __init__.py                 # (empty) package resolution
│   ├── db/
│   │   └── __init__.py             # (empty) package resolution
│   ├── models/
│   │   └── __init__.py             # (empty) package resolution
│   ├── scrapers/
│   │   ├── __init__.py             # (empty) package resolution
│   │   ├── events/
│   │   │   ├── __init__.py         # exports: EventScraper, Event, FEEDS
│   │   │   ├── feeds.py            # FEEDS list — 25 iCal feeds
│   │   │   └── scraper.py          # Event (Pydantic), EventScraper class
│   │   └── youtube/
│   │       ├── __init__.py         # exports: YouTubeScraper, Video, Channel, CHANNELS
│   │       ├── channels.py         # CHANNELS list (8 pre-configured channels)
│   │       └── scraper.py          # Channel, Video (Pydantic), YouTubeScraper class
│   └── services/
│       └── __init__.py             # (empty) package resolution
├── tests/
│   ├── __init__.py                 # (empty) package resolution
│   ├── test_event_scraper.py       # integration tests (hits real iCal feeds)
│   └── test_youtube_scraper.py     # integration tests (hits real YouTube RSS)
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── INTERACTIVE_WINDOW.md           # cheatsheet for VSCode Interactive Window
├── main.py                         # NEW — runs both scrapers, prints summary
├── PROJECT_STATUS.md
├── pyproject.toml
└── uv.lock
```

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

### Current folder structure
```
ai-event-agreegator/
├── infra/
│   ├── docker-compose.yml
│   └── Dockerfile
├── scripts/
│   └── create_tables.py
├── docs/
│   ├── PROJECT_STATUS.md
│   └── INTERACTIVE_WINDOW.md
├── app/
│   ├── db/
│   │   ├── models.py
│   │   ├── session.py
│   │   └── repository.py
│   ├── scrapers/
│   │   ├── events/
│   │   └── youtube/
│   └── services/
├── tests/
├── main.py
├── Makefile
├── .env.example
└── pyproject.toml
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
