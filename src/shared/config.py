"""Configuration uses real environment variables (systemd EnvironmentFile in production)."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data")).resolve()
LOG_DIR = Path(os.environ.get("LOG_DIR", ROOT / "logs")).resolve()


def required(name):
    value = os.environ.get(name, "").strip()
    if not value or value == "None":
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def proxy(name="TELEGRAM_PROXY"):
    value = os.environ.get(
        name, os.environ.get("PROXY", "") if name == "TELEGRAM_PROXY" else ""
    ).strip()
    if value in ("", "None"):
        return None
    if not value.startswith(("http://", "https://")):
        raise ValueError(f"{name} must be an HTTP(S) proxy URL")
    return value
