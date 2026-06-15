# © 2026 Manoj Mallick. DualContext.
"""Seed synthetic DualContext investigation events into Splunk via HEC, so the
`dashboards/dualcontext_analytics.json` dashboard has data to render.

Usage:
    export SPLUNK_HEC_URL=https://localhost:8088/services/collector/event   # default
    export SPLUNK_HEC_TOKEN=<your-hec-token>
    python scripts/seed_splunk.py [--count 40] [--hours 30]

Sends events to  index=main  sourcetype=dualcontext_investigation  with the
exact fields the dashboard queries: groundedness, investigation_ms,
token_reduction_pct, query. Events are spread over the last N hours so the
`timechart span=1h` panel has a trend. No secrets are hardcoded — token comes
from the environment only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

SERVICES = ["auth-service", "payment-service", "api-gateway", "database", "cache"]
QUERIES = [
    "Auth service throwing 47 errors per hour. What's causing it?",
    "Payment service timing out — which call?",
    "API gateway 502s spiking, why?",
    "Database connection pool exhausted?",
    "Cache miss rate jumped after deploy",
]


def make_event(i: int, now: float, span_hours: float) -> dict:
    # deterministic but varied — no Math.random needed
    g = round(0.62 + ((i * 7) % 31) / 100.0, 3)          # 0.62–0.92 groundedness
    ms = 850 + (i * 53) % 700                              # ~0.85–1.55 s
    reduction = round(98.5 + ((i * 3) % 15) / 10.0, 1)    # 98.5–99.9 %
    ts = now - (span_hours * 3600.0) * (i / max(1, SEED_COUNT))
    return {
        "time": round(ts, 3),
        "host": "dualcontext-demo",
        "source": "dualcontext",
        "sourcetype": "dualcontext_investigation",
        "index": "main",
        "event": {
            "query": QUERIES[i % len(QUERIES)],
            "service": SERVICES[i % len(SERVICES)],
            "groundedness": g,
            "passed": g >= 0.70,
            "investigation_ms": ms,
            "token_reduction_pct": reduction,
            "splunk_sources": 3,
            "code_sources": 3,
            "hosted_model": "gpt-oss-120b",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=40)
    ap.add_argument("--hours", type=float, default=30.0)
    args = ap.parse_args()

    global SEED_COUNT
    SEED_COUNT = args.count

    url = os.environ.get("SPLUNK_HEC_URL", "https://localhost:8088/services/collector/event")
    token = os.environ.get("SPLUNK_HEC_TOKEN", "")
    if not token:
        print("ERROR: set SPLUNK_HEC_TOKEN (and optionally SPLUNK_HEC_URL).", file=sys.stderr)
        return 2

    now = time.time()
    body = "\n".join(json.dumps(make_event(i, now, args.hours)) for i in range(args.count))
    req = urllib.request.Request(
        url, data=body.encode(),
        headers={"Authorization": f"Splunk {token}", "Content-Type": "application/json"},
        method="POST",
    )
    # local Splunk uses a self-signed cert; skip verification for localhost dev only.
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            print(f"HEC {resp.status}: {resp.read().decode()[:120]}")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR posting to HEC: {e}", file=sys.stderr)
        return 1
    print(f"Seeded {args.count} events → index=main sourcetype=dualcontext_investigation "
          f"over the last {args.hours}h. Open the DualContext dashboard to view.")
    return 0


SEED_COUNT = 40
if __name__ == "__main__":
    raise SystemExit(main())
