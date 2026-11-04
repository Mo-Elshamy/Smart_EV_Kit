import socket
import subprocess
import threading
import time
import urllib.request
import json
from config import (
    JETSON_IP, JETSON_WEB_PORT, JETSON_SSH_PORT,
    JETSON_POLL_INTERVAL_SEC, JETSON_SSH_USER
)


class JetsonMonitor:
    """Non-blocking background monitor for Jetson (192.168.10.112) status and temperature."""

    def __init__(self):
        self._lock = threading.Lock()
        self._running = True
        self._status = {
            "host_online": False,
            "web_online": False,
            "temp_c": None,
            "latency_ms": None,
        }
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def get_status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def _check_tcp_port(self, port: int, timeout: float = 0.6):
        t0 = time.monotonic()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            ok = (s.connect_ex((JETSON_IP, port)) == 0)
            latency = (time.monotonic() - t0) * 1000.0 if ok else None
            return ok, latency
        except OSError:
            return False, None
        finally:
            s.close()

    def _fetch_temp_c(self, web_online: bool, ssh_online: bool):
        # 1. Try common HTTP status endpoints on port 3000 if web server is up
        if web_online:
            for path in ("/api/status", "/api/system", "/status", "/health"):
                try:
                    url = f"http://{JETSON_IP}:{JETSON_WEB_PORT}{path}"
                    req = urllib.request.Request(url, headers={"Accept": "application/json"})
                    with urllib.request.urlopen(req, timeout=0.6) as resp:
                        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                        if isinstance(data, dict):
                            for key in ("temp", "temperature", "cpu_temp", "gpu_temp", "soc_temp"):
                                if key in data and isinstance(data[key], (int, float)):
                                    return float(data[key])
                except Exception:
                    pass

        # 2. Try passwordless SSH thermal zone read if SSH is open
        if ssh_online:
            for user in (JETSON_SSH_USER, "nvidia", "ubuntu", "rqev"):
                try:
                    res = subprocess.run(
                        [
                            "ssh", "-o", "BatchMode=yes",
                            "-o", "ConnectTimeout=1",
                            "-o", "StrictHostKeyChecking=accept-new",
                            f"{user}@{JETSON_IP}",
                            "cat /sys/devices/virtual/thermal/thermal_zone0/temp"
                        ],
                        capture_output=True, text=True, timeout=1.5
                    )
                    if res.returncode == 0 and res.stdout.strip().isdigit():
                        val = float(res.stdout.strip())
                        return val / 1000.0 if val > 200 else val
                except Exception:
                    pass
        return None

    def _poll_loop(self):
        while self._running:
            web_ok, web_lat = self._check_tcp_port(JETSON_WEB_PORT, timeout=0.6)
            ssh_ok, ssh_lat = self._check_tcp_port(JETSON_SSH_PORT, timeout=0.6)
            host_ok = web_ok or ssh_ok
            latency = web_lat if web_lat is not None else ssh_lat
            temp_c = self._fetch_temp_c(web_ok, ssh_ok) if host_ok else None

            with self._lock:
                self._status = {
                    "host_online": host_ok,
                    "web_online": web_ok,
                    "temp_c": temp_c,
                    "latency_ms": round(latency, 1) if latency is not None else None,
                }

            time.sleep(JETSON_POLL_INTERVAL_SEC)

    def cleanup(self):
        self._running = False
