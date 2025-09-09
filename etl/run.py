#!/usr/bin/env python3
import json
import os
import time
from urllib.request import Request, urlopen

ALGOD_ADDR = os.environ.get("ALGOD_ADDR", "http://127.0.0.1:8080")
ALGOD_TOKEN_FILE = os.environ.get("ALGOD_TOKEN_FILE", "/var/lib/algorand/algod.token")
OUTPUT = os.environ.get("OUTPUT", os.path.expanduser("~/algorand-showcase/web/data/recent_blocks.json"))
NUM_BLOCKS = int(os.environ.get("NUM_BLOCKS", "50"))


def read_token(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def http_get(path: str, token: str):
    req = Request(ALGOD_ADDR + path)
    req.add_header("X-Algo-API-Token", token)
    with urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    token = read_token(ALGOD_TOKEN_FILE)
    status = http_get("/v2/status", token)
    last_round = int(status["last-round"])  # latest committed block

    start = max(0, last_round - NUM_BLOCKS + 1)
    blocks = []
    for rnd in range(start, last_round + 1):
        try:
            blk = http_get(f"/v2/blocks/{rnd}", token)
            tx_count = len(blk.get("block", {}).get("txns", []))
            blocks.append({
                "round": rnd,
                "tx_count": tx_count,
                "ts": blk.get("block", {}).get("ts", 0),
            })
        except Exception as e:
            blocks.append({"round": rnd, "error": str(e)})
        time.sleep(0.02)

    out_dir = os.path.dirname(OUTPUT)
    os.makedirs(out_dir, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": int(time.time()),
            "algod": ALGOD_ADDR,
            "last_round": last_round,
            "num_blocks": NUM_BLOCKS,
            "blocks": blocks,
        }, f)

    print(f"Wrote {len(blocks)} rounds to {OUTPUT}")


if __name__ == "__main__":
    main()


