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
