#!/usr/bin/env bash
# © 2026 Manoj Mallick. DualContext — import the Studio dashboard via REST.
#
# Creates (or updates) the Dashboard Studio dashboard in Splunk directly through
# the management API — no UI clicking, no copy/paste. Idempotent.
#
# Usage (creds stay in YOUR shell only):
#   SPLUNK_USER=manoj SPLUNK_PASSWORD='***' bash scripts/import_dashboard.sh
set -euo pipefail

HOST=${SPLUNK_HOST:-localhost}
MGMT=${SPLUNK_MGMT:-https://$HOST:8089}
WEB_PORT=${SPLUNK_WEB_PORT:-8989}
APP=${SPLUNK_APP:-search}
NAME=${DASHBOARD_NAME:-dualcontext_analytics}
JSON=${1:-dashboards/dualcontext_analytics.json}
: "${SPLUNK_USER:?set SPLUNK_USER}"
: "${SPLUNK_PASSWORD:?set SPLUNK_PASSWORD}"
A=(-sk -u "$SPLUNK_USER:$SPLUNK_PASSWORD")

[ -f "$JSON" ] || { echo "ERROR: $JSON not found (run from the dualcontext/ repo root)"; exit 2; }

# Build the Dashboard Studio (version 2) view XML, embedding the JSON in CDATA.
WRAP=$(mktemp /tmp/dc_view.XXXXXX.xml)
trap 'rm -f "$WRAP"' EXIT
python3 - "$JSON" > "$WRAP" <<'PY'
import json, sys, html
d = json.load(open(sys.argv[1]))
label = d.get("title", "DualContext — Investigation Analytics")
defn = json.dumps(d)  # the Studio definition is the JSON itself
print(f'''<dashboard version="2" theme="dark">
  <label>{html.escape(label)}</label>
  <definition><![CDATA[
{defn}
  ]]></definition>
  <meta type="hiddenElements"><![CDATA[
{{"hideEdit": false, "hideOpenInSearch": false, "hideExport": false}}
  ]]></meta>
</dashboard>''')
PY

echo "▶ importing '$NAME' into app '$APP'…"
# Try create; if it already exists, update the existing view.
CREATE=$(curl "${A[@]}" -o /dev/null -w "%{http_code}" \
  "$MGMT/servicesNS/$SPLUNK_USER/$APP/data/ui/views" \
  -d name="$NAME" --data-urlencode "eai:data@$WRAP" || true)

if [ "$CREATE" = "201" ]; then
  echo "   created (HTTP 201)."
elif [ "$CREATE" = "409" ] || [ "$CREATE" = "400" ]; then
  echo "   exists — updating…"
  UP=$(curl "${A[@]}" -o /dev/null -w "%{http_code}" \
    "$MGMT/servicesNS/$SPLUNK_USER/$APP/data/ui/views/$NAME" \
    --data-urlencode "eai:data@$WRAP")
  echo "   update HTTP $UP"
else
  echo "   create HTTP $CREATE — full response:"
  curl "${A[@]}" "$MGMT/servicesNS/$SPLUNK_USER/$APP/data/ui/views" \
    -d name="$NAME" --data-urlencode "eai:data@$WRAP" | sed 's/<[^>]*>//g' | grep -i -A1 msg | head -4 || true
fi

echo ""
echo "✅ Open it:  http://$HOST:$WEB_PORT/en-US/app/$APP/$NAME"
echo "   (set the time picker to 'Last 24 hours' — seeded data spans ~30h)"
