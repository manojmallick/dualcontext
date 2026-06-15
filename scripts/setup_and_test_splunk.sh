#!/usr/bin/env bash
# © 2026 Manoj Mallick. DualContext — one-command Splunk setup + test.
#
# Creates an HEC token, seeds demo investigation events, and verifies every
# panel query in dashboards/dualcontext_analytics.json against the live data.
#
# Usage (run from the dualcontext/ repo root; creds stay in YOUR shell only):
#   SPLUNK_USER=admin SPLUNK_PASSWORD='yourpass' bash scripts/setup_and_test_splunk.sh
#
# Tip: avoid shell history leaking the password ->  read -rs SPLUNK_PASSWORD
set -euo pipefail

HOST=${SPLUNK_HOST:-localhost}
MGMT=${SPLUNK_MGMT:-https://$HOST:8089}
HEC=${SPLUNK_HEC_URL:-https://$HOST:8088/services/collector/event}
: "${SPLUNK_USER:?set SPLUNK_USER}"
: "${SPLUNK_PASSWORD:?set SPLUNK_PASSWORD}"
A=(-sk -u "$SPLUNK_USER:$SPLUNK_PASSWORD")

echo "▶ 1/5 enabling HEC globally…"
curl "${A[@]}" "$MGMT/servicesNS/nobody/splunk_httpinput/data/inputs/http/http" \
  -d disabled=0 >/dev/null 2>&1 || true

echo "▶ 2/5 ensuring HEC token 'dualcontext' (index=main, sourcetype=dualcontext_investigation)…"
curl "${A[@]}" "$MGMT/servicesNS/nobody/splunk_httpinput/data/inputs/http" \
  -d name=dualcontext -d index=main -d indexes=main \
  -d sourcetype=dualcontext_investigation -d disabled=0 >/dev/null 2>&1 || true

TOKEN=$(curl "${A[@]}" \
  "$MGMT/servicesNS/nobody/splunk_httpinput/data/inputs/http/dualcontext?output_mode=json" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["entry"][0]["content"]["token"])')
echo "   token: ${TOKEN:0:8}… (created/loaded)"

echo "▶ 3/5 seeding 40 investigation events over the last 30h…"
SPLUNK_HEC_TOKEN="$TOKEN" SPLUNK_HEC_URL="$HEC" python3 scripts/seed_splunk.py --count 40 --hours 30

echo "▶ 4/5 waiting for indexing…"; sleep 4

echo "▶ 5/5 verifying each dashboard panel query against live data:"
run() { curl "${A[@]}" -d "output_mode=csv" -d "exec_mode=oneshot" \
  --data-urlencode "search=$1" "$MGMT/services/search/jobs/export" | tail -n +2; }

printf "   • Total Investigations          : "; run 'search index=main sourcetype=dualcontext_investigation | stats count as n | fields n'
printf "   • Groundedness Pass Rate (%%)     : "; run 'search index=main sourcetype=dualcontext_investigation | stats count as t, count(eval(groundedness>=0.7)) as p | eval rate=round(p/t*100,0) | fields rate'
printf "   • Avg Groundedness              : "; run 'search index=main sourcetype=dualcontext_investigation | stats avg(groundedness) as g | eval g=round(g,2) | fields g'
printf "   • Avg Investigation Time (s)    : "; run 'search index=main sourcetype=dualcontext_investigation | stats avg(investigation_ms) as ms | eval s=round(ms/1000,1) | fields s'
printf "   • Avg Token Reduction (%%)        : "; run 'search index=main sourcetype=dualcontext_investigation | stats avg(token_reduction_pct) as r | eval r=round(r,1) | fields r'
printf "   • Timechart rows (groundedness) : "; run 'search index=main sourcetype=dualcontext_investigation | timechart span=1h avg(groundedness) as g | stats count as rows | fields rows'

echo ""
echo "✅ If the numbers above are non-empty, the dashboard will render."
echo "   Next: open Splunk Web → Dashboards → Create New → Dashboard Studio →"
echo "   (blank) → Edit → Source → paste dashboards/dualcontext_analytics.json → Save."
