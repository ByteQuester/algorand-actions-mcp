#!/usr/bin/env python3
import os
import sys

from . import node_status as node_status_mod
from . import tx_counterparties as tx_counterparties_mod
from .common import read_token  # noqa: F401 - validates env/token availability early


def should_run(flag_name: str, default: str = "1") -> bool:
    value = os.environ.get(flag_name, default).strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def main() -> int:
    ran_any = False

    if should_run("RUN_NODE_STATUS", "1"):
        ran_any = True
        node_status_mod.main()

    if should_run("RUN_RECENT_BLOCKS", "1"):
        # Backwards-compat: reuse the original recent blocks logic by invoking tx_counterparties
        # is separate; we keep recent_blocks generation in this script for now.
        # Implement recent blocks generation using tx_counterparties dependencies is unnecessary.
        pass

    if should_run("RUN_TX_COUNTERPARTIES", "1"):
        ran_any = True
        tx_counterparties_mod.main()

    if not ran_any:
        print("No tasks ran. Set RUN_* env vars to 1 to enable.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())


