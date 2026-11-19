#!/usr/bin/env bash
# Ejecuta el plan AAA del día y lo publica en la web.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="${AAA_PYTHON:-/tmp/opencode/trading-venv/bin/python}"
CAPITAL="${AAA_CAPITAL:-10000}"
TIMEZONE="${AAA_TIMEZONE:-America/New_York}"

cd "$REPO_ROOT"

TRADING_DATE="$(TZ="$TIMEZONE" date +%F)"

"$PYTHON" strategies/aaa/main.py plan --capital "$CAPITAL"
"$PYTHON" scripts/aaa_web_sync/sync.py \
  --file "reports/${TRADING_DATE}/candidates.json"
