"""Project configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MANIFEST_PATH = DATA_DIR / "test_manifest_100.json"
BPI_LOG_PATH = RAW_DIR / "BPI_Challenge_2019.xes"
BPI_MANIFEST_PATH = PROCESSED_DIR / "bpi_test_manifest_100.json"

API_BASE_URL = os.getenv("P2P_API_BASE_URL", "http://127.0.0.1:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MODEL_PROVIDER = os.getenv("P2P_MODEL_PROVIDER", "offline").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:0.8b")
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "2048"))
OLLAMA_NUM_THREADS = int(os.getenv("OLLAMA_NUM_THREADS", "2"))
MODEL_CALL_BUDGET = int(os.getenv("P2P_MODEL_CALL_BUDGET", "600"))
AGENT_MAX_TURNS = int(os.getenv("AGENT_MAX_TURNS", "8"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("P2P_REQUEST_TIMEOUT", "5"))
RUN_CASE_LIMIT = int(os.getenv("P2P_RUN_CASES", "5"))

