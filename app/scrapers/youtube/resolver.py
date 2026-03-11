from __future__ import annotations

import re
import httpx


def get_channel_id(input: str) -> str | None:
    """Resolve a YouTube channel ID from a handle, name, or URL."""
    if m := re.search(r"youtube\.com/channel/(UC[\w-]+)", input):
        return m.group(1)

    if input.startswith("http"):
        url = input
    else:
        handle = input.lstrip("@")
        url = f"https://www.youtube.com/@{handle}"

    html = httpx.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        follow_redirects=True,
        timeout=10,
    ).text

    for pattern in [
        r'"channelId"\s*:\s*"(UC[\w-]+)"',
        r'"externalChannelId"\s*:\s*"(UC[\w-]+)"',
        r'"ucid"\s*:\s*"(UC[\w-]+)"',
        r'channel_id=\s*(UC[\w-]+)',
        r'"browseId"\s*:\s*"(UC[\w-]+)"',
    ]:
        if m := re.search(pattern, html):
            return m.group(1)
    return None
