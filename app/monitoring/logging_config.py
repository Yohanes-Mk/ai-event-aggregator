from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(level: int = logging.INFO, log_path: str = "logs/pipeline.log") -> None:
    """Configure root logging once for console and file output."""
    root_logger = logging.getLogger()
    if getattr(configure_logging, "_configured", False):
        root_logger.setLevel(level)
        return

    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    configure_logging._configured = True  # type: ignore[attr-defined]
