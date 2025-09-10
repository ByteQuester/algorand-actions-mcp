#!/usr/bin/env python3
import os
import time
from typing import Dict, Any

from .common import (
    get_algod_addr,
    read_token,
    http_get_json,
    write_json_atomic,
)


def map_status_to_snapshot(status: Dict[str, Any]) -> Dict[str, Any]:
    """Map algod /v2/status fields into a compact UI-friendly snapshot.

    Handles presence/absence of fast-catchup fields gracefully.
    """
    # Common fields
    last_committed_block = int(status.get("last-round", 0))
    time_since_last = status.get("time-since-last-round")
    sync_time_seconds = float(time_since_last) if isinstance(time_since_last, (int, float)) else None

    # Fast-catchup fields (may be absent)
    catchpoint = status.get("catchpoint")
    catchpoint_accounts_total = status.get("catchpoint-accounts-total")
    catchpoint_accounts_processed = status.get("catchpoint-accounts-processed")
    catchpoint_kv_total = status.get("catchpoint-kv-total")
    catchpoint_kv_processed = status.get("catchpoint-kv-processed")

    genesis_id = status.get("genesis-id")

    snapshot: Dict[str, Any] = {
        "generated_at": int(time.time()),
        "algod": get_algod_addr(),
        "last_committed_block": last_committed_block,
        "sync_time_seconds": sync_time_seconds,
        "catchpoint": catchpoint,
        "catchpoint_accounts_total": catchpoint_accounts_total,
        "catchpoint_accounts_processed": catchpoint_accounts_processed,
        "catchpoint_kv_total": catchpoint_kv_total,
        "catchpoint_kv_processed": catchpoint_kv_processed,
        "genesis_id": genesis_id,
    }
    # Remove keys with value None to keep output compact
    return {k: v for k, v in snapshot.items() if v is not None}


def main() -> None:
    token = read_token()
    status = http_get_json("/v2/status", token)

    output = os.environ.get(
        "NODE_STATUS_OUTPUT",
        os.path.expanduser("~/algorand-showcase/web/data/node_status.json"),
    )
    snapshot = map_status_to_snapshot(status)
    write_json_atomic(snapshot, output)
    print(f"Wrote node status snapshot to {output}")


if __name__ == "__main__":
    main()




