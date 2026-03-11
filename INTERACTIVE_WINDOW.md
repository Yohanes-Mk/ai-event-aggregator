# Interactive Window Cheatsheet

The VSCode Interactive Window runs **Python only** — no shell commands.
Use the Terminal (`Ctrl+`` `) for shell commands like `cd`, `pytest`, `python`.

---

## Step 1 — Fix the path (run once per session)

```python
import sys
sys.path.insert(0, "/Users/jon/Projects/Building/ai-event-agreegator")
```

> Without this, Python doesn't know where the `app` package lives.
> The interactive window doesn't inherit the project root like `pytest` does,
> so you have to tell it manually. Only needed once — stays active for the session.

---

## Step 2 — Scrape upcoming events (both feeds)

```python
from app.scrapers.events import EventScraper

events = EventScraper().scrape()
for e in events:
    # print number of events 
    print(f"{len(events)}events found in the next 14 days")
    print(e.start_time.date(), "-", e.title, f"({e.source})", "-", e.url)
```

> `EventScraper()` uses the default `FEEDS` list (DC Tech Events + DC Startup Hub)
> and filters to the next 14 days. Results come back sorted by start time.

---

## Step 3 - turn PDF

```python
from app.scrapers.events import EventScraper
from fpdf import FPDF

events = EventScraper().scrape()

pdf = FPDF()
pdf.add_font("Arial", "", "/System/Library/Fonts/Supplemental/Arial.ttf")
pdf.add_font("Arial", "B", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")
pdf.add_page()

pdf.set_font("Arial", "B", 16)
pdf.cell(0, 10, "DC/DMV Tech Events", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Arial", "", 8)
pdf.cell(0, 6, f"{len(events)} events in the next 14 days", new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)

for e in events:
    pdf.set_font("Arial", "B", 10)
    pdf.multi_cell(0, 6, e.title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "", 9)
    if e.location:
        pdf.cell(0, 5, f"📍 {e.location}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, e.start_time.strftime("%a %b %d, %Y  %I:%M %p"), new_x="LMARGIN", new_y="NEXT")
    if e.url:
        url_str = str(e.url)
        pdf.set_text_color(0, 0, 200)
        pdf.cell(0, 5, url_str, new_x="LMARGIN", new_y="NEXT", link=url_str)
        pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, e.source, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

output_path = "/Users/jon/Desktop/dc_events.pdf"
pdf.output(output_path)
print(f"Saved {len(events)} events to {output_path}")

```
------------
## Step 4 — Scrape a single feed

```python
from app.scrapers.events import EventScraper

scraper = EventScraper(
    feeds=[{"name": "DC Tech Events", "url": "https://dctech.events/events.ics"}],
    within_days=7,  # narrow the window if you want
)
events = scraper.scrape()
for e in events:
    print(e.start_time.date(), "-", e.title, "-", e.url)
```

> Pass a custom `feeds` list to test one feed at a time.
> Useful for debugging when one feed is broken.

---

## Step 5 — YouTube: latest video from a channel

```python
from app.scrapers.youtube import YouTubeScraper

scraper = YouTubeScraper(channel_id="UCsBjURrPoezykLs9EqgamOA", channel_name="Fireship")
video = scraper.fetch_latest_video()
print(video.title, "-", video.url)
```

> `fetch_latest_video()` returns the single most recent video regardless of age.
> `channel_id` is the YouTube channel ID (not the handle).

---

## Step 6 — YouTube: recent videos with transcript

```python
from app.scrapers.youtube import YouTubeScraper

scraper = YouTubeScraper(channel_id="UCsBjURrPoezykLs9EqgamOA", channel_name="Fireship")
videos = scraper.scrape(within_days=7, with_transcripts=True)
for v in videos:
    preview = v.transcript[:200] if v.transcript else "no transcript"
    print(v.title, "\n", preview, "\n")
```

> `scrape()` fetches all videos within the window and optionally attaches transcripts.
> Transcripts can be blocked by YouTube depending on IP — if so, `transcript` will be `None`.

---

## Notes

- `video.url` and `event.url` are Pydantic `HttpUrl` objects, not plain strings.
  Wrap with `str()` if you need to do string operations like `startswith`:
  ```python
  str(video.url).startswith("https://")
  ```

- Shell commands (`cd`, `pytest`, `.venv/bin/python`) go in the **Terminal**, not here.

- If you restart the kernel, re-run Step 1 before anything else.
