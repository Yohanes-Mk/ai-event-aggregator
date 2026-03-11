"""Interactive channel selection for CLI use. Wire into main.py when ready."""
from __future__ import annotations

from pathlib import Path

from .channels import CHANNELS
from .resolver import get_channel_id


_CHANNELS_FILE = Path(__file__).parent / "channels.py"


def _append_to_channels_file(name: str, channel_id: str) -> None:
    content = _CHANNELS_FILE.read_text()
    last_bracket = content.rfind("]")
    updated = content[:last_bracket] + f'    {{"name": "{name}", "channel_id": "{channel_id}"}},\n]'
    _CHANNELS_FILE.write_text(updated)


def select_channels() -> list[dict]:
    """Prompt user to pick channels from the library and optionally add new ones."""
    print("\n=== YouTube Channel Library ===")
    for i, ch in enumerate(CHANNELS, 1):
        print(f"  {i:2}. {ch['name']:<25} ({ch['channel_id']})")

    raw = input("\nChannels to scrape (e.g. 1,3,5) or ENTER for all: ").strip()
    if raw:
        indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip().isdigit()]
        selected = [CHANNELS[i] for i in indices if 0 <= i < len(CHANNELS)]
    else:
        selected = list(CHANNELS)

    while True:
        handle = input("Add a channel? Enter handle/URL (or ENTER to skip): ").strip()
        if not handle:
            break
        print(f"  Resolving '{handle}'...")
        channel_id = get_channel_id(handle)
        if not channel_id:
            print("  Could not resolve channel ID. Check the handle/URL and try again.")
            continue
        name = input(f"  Display name for {channel_id}: ").strip() or handle
        selected.append({"name": name, "channel_id": channel_id})
        save = input(f"  Save '{name}' to channel library permanently? [y/N]: ").strip().lower()
        if save == "y":
            _append_to_channels_file(name, channel_id)
            print("  Saved to channels.py")

    print(f"\n  Scraping {len(selected)} channel(s): {', '.join(ch['name'] for ch in selected)}\n")
    return selected
