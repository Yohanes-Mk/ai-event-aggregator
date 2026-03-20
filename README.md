# AI Event Agreegator

Local pipeline that:

- scrapes recent YouTube videos
- scrapes upcoming events
- stores everything in Postgres
- generates AI digests and rankings
- sends Gmail digests
- renders a static dashboard artifact
- exposes a Streamlit demo shell over the stored data

## Prerequisites

- `uv`
- Docker Desktop or another local Docker runtime
- OpenAI API key
- Gmail app password if you want the email steps to send successfully

This project expects Python `>=3.14`, but the normal workflow is to let `uv` manage that for you.

## First-Time Setup

1. Install dependencies:

```bash
uv sync
```

2. Create a local env file:

```bash
cp .env.example .env
```

3. Fill in the variables you need in `.env`.

4. Start Postgres:

```bash
make up
```

5. Run the full pipeline:

```bash
make run
```

`make run` already runs `make db-init` first, so you do not need to initialize tables separately for the normal path.

## Normal Run Paths

### Full pipeline

```bash
make run
```

What it does:

- creates/updates tables
- scrapes YouTube
- scrapes events
- generates digests
- runs the curator ranking
- tries to send YouTube and events emails
- rebuilds `artifacts/dashboard.html`

### Initialize the database only

```bash
make db-init
```

### Rebuild the dashboard from current DB data

```bash
make dashboard
```

Output:

- `artifacts/dashboard.html`

### Launch the Streamlit demo app

```bash
make demo
```

This also runs `db-init` first.

### Run tests

```bash
make test
```

## Monitoring Commands

These all read from the current database:

```bash
make monitoring-report
make monitoring-runs
make monitoring-health
make monitoring-stage-performance
make monitoring-failures
make monitoring-throughput
make monitoring-batch-telemetry
make monitoring-summary
make monitoring-ranking-drift
make monitoring-digest-freshness
```

Comparison mode uses Make variables:

```bash
make monitoring-compare \
  BEFORE_START=2026-03-01 \
  BEFORE_END=2026-03-07 \
  AFTER_START=2026-03-08 \
  AFTER_END=2026-03-14
```

Accepted values are ISO dates or datetimes.

## Environment Variables

### App runtime variables

| Variable | Required | Used by | What happens if missing |
|---|---|---|---|
| `DATABASE_URL` | Usually yes | App runtime, scripts, monitoring | Falls back to `postgresql://postgres:postgres@localhost:5432/aggregator` if unset. |
| `OPENAI_API_KEY` | Yes for AI stages | Digest generation, curator ranking, email copy generation, demo actions | Scraping and DB writes can still happen, but AI-backed stages will fail or return no output. |
| `GMAIL_SENDER` | Only for sending email | YouTube/events email stages, demo email actions | Email send fails. Other stages can still complete. |
| `GMAIL_RECIPIENT` | Only for sending email | YouTube/events email stages, demo defaults | Email send fails unless a recipient is provided another way inside the demo UI. |
| `GMAIL_APP_PASSWORD` | Only for sending email | Gmail SMTP login | Email send fails. Use a Gmail app password, not your normal account password. |
| `WEBSHARE_PROXY_USERNAME` | Optional | YouTube transcript fetches | If blank, transcript requests go direct. This may be fine locally, but some IPs get blocked. |
| `WEBSHARE_PROXY_PASSWORD` | Optional | YouTube transcript fetches | Same as above; only used when username and password are both set. |
| `PIPELINE_CONFIG_VERSION` | Optional | Monitoring metadata on pipeline runs | No behavior change; only affects stored monitoring metadata. |
| `DASHBOARD_RECIPIENT_NAME` | Optional | Static dashboard render | Defaults to `Yohannes`. |

### Docker Compose variables

These are only used by `infra/docker-compose.yml` when you run `make up`:

| Variable | Required | Default |
|---|---|---|
| `POSTGRES_USER` | No | `postgres` |
| `POSTGRES_PASSWORD` | No | `postgres` |
| `POSTGRES_DB` | No | `aggregator` |

If you change these, make sure `DATABASE_URL` matches them.

## Common Setups

### Minimum local setup for scraping + DB + dashboard

Set:

- `DATABASE_URL`

Run:

```bash
make up
make run
```

This works best if your DB already has prior digests, otherwise the AI stages will not produce new digest/ranking content.

### Full local setup

Set:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `GMAIL_SENDER`
- `GMAIL_RECIPIENT`
- `GMAIL_APP_PASSWORD`

Optional:

- `WEBSHARE_PROXY_USERNAME`
- `WEBSHARE_PROXY_PASSWORD`
- `PIPELINE_CONFIG_VERSION`
- `DASHBOARD_RECIPIENT_NAME`

Run:

```bash
make up
make run
```

### Using your own Postgres instead of Docker

Skip `make up`, point `DATABASE_URL` at your existing database, then run:

```bash
make db-init
make run
```

## Helpful Notes

- `main.py` and `scripts/demo_app.py` both call `load_dotenv()`, so local `.env` values are picked up automatically.
- `make dashboard` and `make demo` both depend on the database being reachable.
- The pipeline is resilient in a few places: missing Gmail settings do not stop scraping, and digest failures are handled per item.
- The dashboard artifact is static HTML, so it will not auto-refresh unless you rerun the dashboard build or the full pipeline.
