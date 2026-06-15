#!/usr/bin/env bash
# © 2026 Manoj Mallick. DualContext — one-command live setup against real Splunk.
#
#   SPLUNK_USER=admin SPLUNK_PASSWORD=*** ./run_live.sh
#
# Enables HEC + creates the token, seeds index=main with DualContext investigation
# telemetry, then prints how to open the analytics dashboard.
set -euo pipefail
cd "$(dirname "$0")"

: "${SPLUNK_USER:?set SPLUNK_USER}"
: "${SPLUNK_PASSWORD:?set SPLUNK_PASSWORD}"
export SPLUNK_REST_URL="${SPLUNK_REST_URL:-https://localhost:8089}"

echo "▶ 1/2  Splunk setup (HEC + token)"
TOKEN="$(python3 scripts/setup_splunk.py | sed -n 's/^HEC_TOKEN=//p')"
if [ -z "${TOKEN}" ]; then echo "setup failed — run scripts/setup_splunk.py directly to see why"; exit 1; fi
export SPLUNK_HEC_TOKEN="${TOKEN}"
export SPLUNK_HEC_URL="${SPLUNK_HEC_URL:-https://localhost:8088/services/collector/event}"
echo "  HEC token acquired: ${TOKEN:0:8}***"

echo "▶ 2/2  Seed index=main with investigation telemetry"
python3 scripts/seed_splunk.py

cat <<'EOF'
  • Open: http://localhost:8989/en-US/app/search/dualcontext_analytics
    (set time range to "Last 30 days")
  • Verify: index=main sourcetype=dualcontext_investigation | stats count
EOF
