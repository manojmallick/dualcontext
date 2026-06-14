# © 2026 LearnHubPlay BV. DualContext.
"""Investigation telemetry → Splunk HEC (optional, env-only).

DualContext *reads* operational reality from Splunk via the MCP Server. This
module adds the write-back: it ships each Investigation (the `as_event()`
payload) to Splunk via HEC as `sourcetype=dualcontext_investigation`, which
powers the analytics dashboard (`dashboards/dualcontext_analytics.json`).

It is deliberately decoupled — secrets come only from the environment, and in
demo mode (or with no HEC configured) it is a no-op so the core loop still runs
with zero network access (CLAUDE.md air-gapped rule).

    from dualcontext.telemetry import InvestigationTelemetry
    InvestigationTelemetry(config).log(investigation.as_event())
"""

from __future__ import annotations

import os
import time


class InvestigationTelemetry:
    """Writes investigation events to Splunk HEC. No-op when unconfigured."""

    def __init__(self, config):
        self.config = config
        self.hec_url = os.environ.get("SPLUNK_HEC_URL", "")
        self.hec_token = os.environ.get("SPLUNK_HEC_TOKEN", "")
        self.index = getattr(config, "splunk_index", "main")
        self.events: list[dict] = []

    @property
    def enabled(self) -> bool:
        return bool(self.hec_url and self.hec_token and not self.config.demo_mode)

    def log(self, event: dict) -> None:
        """Buffer the event; ship to HEC when configured (else stay offline)."""
        payload = {
            "time": time.time(),
            "source": "dualcontext",
            "sourcetype": "dualcontext_investigation",
            "index": self.index,
            "event": event,
        }
        self.events.append(payload)
        if not self.enabled:
            return
        import requests  # local import: demo/offline needs no network deps

        requests.post(
            self.hec_url,
            headers={"Authorization": f"Splunk {self.hec_token}"},
            json=payload,
            timeout=5,
        )
