from __future__ import annotations

import json
from pathlib import Path


TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "dashboard.html"
DATA_MARKER = "<!-- __STACK_DATA__ -->"


def render_dashboard(payload: dict) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    data_script = "<script>\nwindow.__STACK_DATA__ = " + json.dumps(payload) + ";\n</script>"
    if DATA_MARKER not in template:
        raise ValueError("Dashboard template is missing the data marker.")
    return template.replace(DATA_MARKER, data_script, 1)
