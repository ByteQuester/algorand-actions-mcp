#!/usr/bin/env python3
"""
Common stdlib helpers for interacting with a local algod node and writing JSON outputs.

Constraints:
- Only Python standard library
- Functional style with small, focused functions
- Bounded retries with short sleeps
"""

import json
import os
import time
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_algod_addr() -> str:
    """Return algod base URL from env or default to local node."""
    return os.environ.get("ALGOD_ADDR", "http://127.0.0.1:8080")


def get_algod_token_file() -> str:
    """Return algod token file path from env or default."""
    return os.environ.get("ALGOD_TOKEN_FILE", "/var/lib/algorand/algod.token")


def read_token(path: Optional[str] = None) -> str:
    """Read the algod API token from filesystem."""
    token_path = path or get_algod_token_file()
    with open(token_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def http_get_json(path: str, token: str, *, timeout: float = 30.0, retries: int = 2, sleep_between_retries_sec: float = 0.2, base_url: Optional[str] = None) -> Dict[str, Any]:
    """GET JSON from algod with bounded retries.

    Args:
        path: The request path beginning with '/v2/...'
        token: Algod API token
        timeout: Per-request timeout in seconds
        retries: Number of retry attempts after the first try
        sleep_between_retries_sec: Sleep between attempts
        base_url: Override algod base URL

    Returns:
        Parsed JSON object (dict)
    """
    url = (base_url or get_algod_addr()) + path
    attempt = 0
    last_exc: Optional[Exception] = None
    while attempt <= max(0, int(retries)):
        attempt += 1
        try:
            req = Request(url)
            req.add_header("X-Algo-API-Token", token)
            with urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:  # ValueError for JSON parse
            last_exc = exc
            if attempt > retries:
                break
            time.sleep(max(0.0, float(sleep_between_retries_sec)))
    raise RuntimeError(f"GET {url} failed after {attempt} attempts: {last_exc}")


def ensure_parent_dir(path: str) -> None:
    """Ensure parent directory exists for a file path."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_json_atomic(obj: Dict[str, Any], path: str) -> None:
    """Write JSON atomically to avoid partial files."""
    ensure_parent_dir(path)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp_path, path)


def sleep_ms(milliseconds: int) -> None:
    """Sleep for N milliseconds."""
    time.sleep(max(0, int(milliseconds)) / 1000.0)


