#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <nfd-name.algo>" 1>&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR%/scripts}"

if [[ -f "$ROOT_DIR/.env" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
fi

: "${NFD_API_URL:=https://api.nf.domains}"
NAME="$1"

curl -fsSL "$NFD_API_URL/nfd/$NAME?view=full" | jq . || curl -fsSL "$NFD_API_URL/nfd/$NAME?view=full"


