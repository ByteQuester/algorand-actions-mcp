#!/usr/bin/env python3
import os
import time
from collections import Counter
from typing import Any, Dict, Iterable, List, Tuple

from .common import (
    read_token,
    http_get_json,
    write_json_atomic,
    get_algod_addr,
    sleep_ms,
)


def iter_recent_rounds(last_round: int, num_blocks: int) -> Iterable[int]:
    start = max(0, last_round - max(0, int(num_blocks)) + 1)
    for rnd in range(start, last_round + 1):
        yield rnd


def extract_sender_receiver_addresses(block_json: Dict[str, Any]) -> Iterable[Tuple[str, str]]:
    """Yield (sender, receiver) for each transaction in a block.

    Inner transactions are ignored to keep it fast and simple.
    We handle common transaction types: pay, axfer (asset transfer), appl (app call) where receiver may be absent.
    """
    block = block_json.get("block", {})
    txns = block.get("txns", [])
    for tx in txns:
        txn = tx.get("txn", {})
        sender = txn.get("snd")
        if not sender:
            continue
        tx_type = txn.get("type")
        receiver = None
        if tx_type == "pay":
            receiver = txn.get("rcv")
        elif tx_type == "axfer":
            xfer = txn.get("xaid") is not None
            # For asset transfer, the receiver is in "arcv"
            receiver = txn.get("arcv")
        elif tx_type == "appl":
            # App call has no canonical receiver; skip receiver counting
            receiver = None
        # If we have both, yield pair; also count sender solo if no receiver
        if receiver:
            yield sender, receiver
        else:
            # Count at least the sender occurrence
            yield sender, ""


def main() -> None:
    token = read_token()
    num_blocks = int(os.environ.get("COUNTERPARTIES_NUM_BLOCKS", os.environ.get("NUM_BLOCKS", "50")))
    sleep_ms_between = int(float(os.environ.get("SLEEP_MS", "20")))
    output = os.environ.get(
        "TX_COUNTERPARTIES_OUTPUT",
        os.path.expanduser("~/algorand-showcase/web/data/tx_counterparties.json"),
    )

    status = http_get_json("/v2/status", token)
    last_round = int(status.get("last-round", 0))

    counter: Counter[str] = Counter()
    for rnd in iter_recent_rounds(last_round, num_blocks):
        try:
            blk = http_get_json(f"/v2/blocks/{rnd}", token)
        except Exception:
            sleep_ms(sleep_ms_between)
            continue
        for sender, receiver in extract_sender_receiver_addresses(blk):
            counter[sender] += 1
            if receiver:
                counter[receiver] += 1
        sleep_ms(sleep_ms_between)

    top_n = int(os.environ.get("TOP_N", "20"))
    top_list: List[Dict[str, Any]] = [
        {"address": addr, "tx_count": count} for addr, count in counter.most_common(top_n)
    ]

    snapshot: Dict[str, Any] = {
        "generated_at": int(time.time()),
        "algod": get_algod_addr(),
        "last_round": last_round,
        "num_blocks": num_blocks,
        "top": top_list,
    }
    write_json_atomic(snapshot, output)
    print(f"Wrote counterparties snapshot with {len(top_list)} addresses to {output}")


if __name__ == "__main__":
    main()


