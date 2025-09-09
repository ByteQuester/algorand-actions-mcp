#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <address-or-nfd>" 1>&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR%/scripts}"

if [[ -f "$ROOT_DIR/.env" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
fi

ADDRESS_OR_NFD="$1"

# Resolve NFD to address if it ends with .algo
if [[ "$ADDRESS_OR_NFD" == *.algo ]]; then
  : "${NFD_API_URL:=https://api.nf.domains}"
  echo "Resolving NFD $ADDRESS_OR_NFD to address..." 1>&2
  ADDR=$(curl -fsSL "$NFD_API_URL/nfd/$ADDRESS_OR_NFD?view=basic" | jq -r '.owner' || true)
  if [[ -z "${ADDR:-}" || "$ADDR" == "null" ]]; then
    echo "Failed to resolve NFD to address" 1>&2
    exit 2
  fi
else
  ADDR="$ADDRESS_OR_NFD"
fi

if [[ -n "${INDEXER_URL:-}" ]]; then
  # Use public Indexer if provided
  echo "Fetching from Indexer: $INDEXER_URL" 1>&2
  curl -fsSL "$INDEXER_URL/v2/accounts/$ADDR" | jq . || curl -fsSL "$INDEXER_URL/v2/accounts/$ADDR"
else
  # Fallback to local algod
  : "${ALGOD_ADDR:=http://127.0.0.1:8080}"
  : "${ALGOD_TOKEN_FILE:=/var/lib/algorand/algod.token}"
  if [[ ! -f "$ALGOD_TOKEN_FILE" ]]; then
    echo "Algod token file not found: $ALGOD_TOKEN_FILE" 1>&2
    exit 3
  fi
  TOKEN=$(cat "$ALGOD_TOKEN_FILE")
  echo "Fetching from local algod: $ALGOD_ADDR" 1>&2
  curl -fsSL -H "X-Algo-API-Token: $TOKEN" "$ALGOD_ADDR/v2/accounts/$ADDR" | jq . || \
  curl -fsSL -H "X-Algo-API-Token: $TOKEN" "$ALGOD_ADDR/v2/accounts/$ADDR"
fi


