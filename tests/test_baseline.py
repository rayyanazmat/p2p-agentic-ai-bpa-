"""End-to-end baseline workflow test using a local Uvicorn process."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from src.agents.heuristic_agent import HeuristicAgent
from src.agents.react_agent import OfflineBackend, ReActAgent, ToolClient
from src.pipeline.loader import make_case

PROJECT_DIR = Path(__file__).resolve().parents[1]


def free_port() -> int:
    """Reserve an ephemeral local TCP port number."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start_server() -> tuple[subprocess.Popen[str], str]:
    """Start Uvicorn and wait for its health endpoint."""
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_DIR)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.simulator.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "error",
        ],
        cwd=PROJECT_DIR,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(base_url + "/health", timeout=0.3):
                return process, base_url
        except (urllib.error.URLError, TimeoutError):
            if process.poll() is not None:
                raise RuntimeError("Uvicorn exited before health check passed")
            time.sleep(0.1)
    process.terminate()
    raise RuntimeError("Timed out waiting for Uvicorn")


def test_baselines_complete_end_to_end() -> None:
    """Both baselines reach the expected states on clear and exception cases."""
    process, base_url = start_server()
    client = ToolClient(base_url)
    cases = [
        make_case(1, "two_way"),
        make_case(2, "three_way_complete"),
        make_case(3, "three_way_missing_gr"),
        make_case(4, "fault_injected", "amount_mismatch"),
    ]
    try:
        for agent_type, kwargs in (
            (ReActAgent, {"backend": OfflineBackend()}),
            (HeuristicAgent, {}),
        ):
            client.reset(cases)
            for case in cases:
                agent = agent_type(client, **kwargs)
                result = agent.run(case)
                invoice = client.get_invoice(case["invoice_id"])
                assert invoice["status"] == case["expected_state"]["invoice_status"]
                assert result["outcome"] in {"cleared", "held"}
                assert client.audit(case["case_id"])["tool_calls"]
    finally:
        process.terminate()
        process.wait(timeout=5)

