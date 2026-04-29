"""
Session-scoped fixture that starts the openapi_server in a subprocess and
waits until it is accepting connections before any test runs.
"""
import subprocess
import sys
import time
from pathlib import Path

import pytest
import urllib.request
import urllib.error

SERVER_DIR = Path(__file__).resolve().parents[3] / "api" / "server"
BASE_URL = "http://localhost:8080/v2"


def _wait_for_server(timeout: int = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BASE_URL}/pet/1", timeout=1)
            return
        except urllib.error.HTTPError:
            # Any HTTP response (even 4xx) means the server is up
            return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError("API server did not start within timeout")


@pytest.fixture(scope="session", autouse=True)
def api_server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "openapi_server"],
        cwd=SERVER_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server()
        yield
    finally:
        proc.terminate()
        proc.wait()
