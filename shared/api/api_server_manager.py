import subprocess
import sys
import time
import urllib.request
from pathlib import Path

API_SERVER_DIR = Path(__file__).resolve().parents[2] / "api" / "server"


class ApiServerManager:
    def __init__(self, server_dir: Path = API_SERVER_DIR, port: int = 8080):
        self._server_dir = server_dir
        self._port = port
        self._proc: subprocess.Popen | None = None

    def start(self) -> None:
        # Kill any process already on the port
        subprocess.run(
            f"kill $(lsof -ti :{self._port}) 2>/dev/null || true",
            shell=True, check=False
        )
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "openapi_server"],
            cwd=self._server_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Wait until the server is ready
        for _ in range(30):
            try:
                urllib.request.urlopen(
                    f"http://localhost:{self._port}/health", timeout=1)
                print("API server ready.")
                return
            except Exception:
                time.sleep(1)
        raise RuntimeError("API server did not start in time.")

    def stop(self) -> None:
        if self._proc:
            self._proc.terminate()
            self._proc.wait()
            self._proc = None

    def __enter__(self) -> "ApiServerManager":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.stop()
