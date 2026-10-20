"""Project configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MANIFEST_PATH = DATA_DIR / "test_manifest_100.json"

API_BASE_URL = os.getenv("P2P_API_BASE_URL", "http://127.0.0.1:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AGENT_MAX_TURNS = int(os.getenv("AGENT_MAX_TURNS", "8"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("P2P_REQUEST_TIMEOUT", "5"))
RUN_CASE_LIMIT = int(os.getenv("P2P_RUN_CASES", "5"))

