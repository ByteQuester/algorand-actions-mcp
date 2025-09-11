#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR%/scripts}"

if [[ -f "$ROOT_DIR/.env" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
fi

GOAL="/var/lib/algorand/goal"
DATA_DIR="/var/lib/algorand"

if [[ ! -x "$GOAL" ]]; then
  echo "goal not found at $GOAL" 1>&2
  exit 1
fi

"$GOAL" node status -d "$DATA_DIR"





