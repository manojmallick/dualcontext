# © 2026 LearnHubPlay BV. DualContext.
"""Splunk MCP Server client — the OPERATIONAL half of DualContext.

The agent reads operational reality from Splunk through the Splunk MCP Server
(Model Context Protocol over streamable HTTP, JSON-RPC). Errors, error-rate
metrics, and alert history are all expressed as SPL and run through the real
`run_splunk_query` tool exposed by the Splunk MCP Server (Splunkbase App 7931).

In demo_mode the client returns a deterministic synthetic incident so the whole
loop runs offline (CLAUDE.md air-gapped rule).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field


@dataclass
class OperationalContext:
    """What Splunk saw: errors, the error-rate trend, and recent alerts."""
    service: str
    errors: list[dict] = field(default_factory=list)
    error_rate: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    queries_run: list[str] = field(default_factory=list)
    events_analyzed: int = 0
    elapsed_ms: float = 0.0

    @property
    def sources(self) -> list[str]:
        return [f"Splunk:{self.service}:errors", f"Splunk:{self.service}:metrics",
                f"Splunk:{self.service}:alerts"]

    def summary(self) -> str:
        top = self.errors[0] if self.errors else {}
        return (f"{self.events_analyzed} events; top error "
                f"{top.get('message', 'n/a')} (×{top.get('count', 0)})")


class SplunkMCPClient:
    """Talks to the Splunk MCP Server. Token-based auth, with the MCP handshake."""

    PROTOCOL_VERSION = "2025-06-18"

    def __init__(self, config):
        self.config = config
        self._rpc_id = 0
        self._session_id: str | None = None
        self._session_ready = False

    # ── high-level operation the agent uses ──────────────────────────────────
    def operational_context(self, service: str) -> OperationalContext:
        """Sense errors, error-rate, and alerts for a service — three SPL searches.

        Every operational signal is SPL through `run_splunk_query`; there is no
        separate metrics/alerts tool in the Splunk MCP Server, so metrics and
        alert history are expressed as SPL (| timechart, index=_audit).
        """
        start = time.perf_counter()
        idx = self.config.splunk_index

        error_spl = (
            f"search index={idx} service={service} level=ERROR earliest=-1h latest=now "
            "| head 20 | stats count by message, source, line | sort -count"
        )
        rate_spl = (
            f"search index={idx} service={service} level=ERROR earliest=-1h latest=now "
            "| timechart span=5m count as error_rate"
        )
        alert_spl = (
            f"search index=_audit action=alert_fired service={service} earliest=-24h "
            "| table _time, severity, message"
        )

        errors = self._run_splunk_query(error_spl)
        error_rate = self._run_splunk_query(rate_spl)
        alerts = self._run_splunk_query(alert_spl)

        events = sum(int(r.get("count", 0)) for r in errors) or len(errors)
        return OperationalContext(
            service=service, errors=errors, error_rate=error_rate, alerts=alerts,
            queries_run=[error_spl, rate_spl, alert_spl],
            events_analyzed=events,
            elapsed_ms=round((time.perf_counter() - start) * 1000, 1),
        )

    # ── MCP / JSON-RPC transport (handshake-aware) ───────────────────────────
    def _run_splunk_query(self, spl: str) -> list[dict]:
        if self.config.demo_mode:
            time.sleep(0.35)  # simulate one MCP round-trip so timing is realistic
            return self._demo_rows(spl)
        return self._call_tool("run_splunk_query", {"query": spl, "earliest": "-24h"})

    def _ensure_session(self) -> None:
        """MCP `initialize` handshake once: streamable-HTTP servers require it
        (server returns Mcp-Session-Id) before any tools/call."""
        if self._session_ready:
            return
        init = self._post({
            "jsonrpc": "2.0", "id": self._next_id(), "method": "initialize",
            "params": {"protocolVersion": self.PROTOCOL_VERSION, "capabilities": {},
                       "clientInfo": {"name": "dualcontext-agent", "version": "1.0.0"}},
        })
        self._session_id = init.headers.get("Mcp-Session-Id") or self._session_id
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"},
                   expect_response=False)
        self._session_ready = True

    def _call_tool(self, tool: str, arguments: dict) -> list[dict]:
        self._ensure_session()
        resp = self._post({
            "jsonrpc": "2.0", "id": self._next_id(), "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        })
        result = self._decode(resp).get("result", {})
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            return json.loads(content[0]["text"])
        return result.get("rows", [])

    def _post(self, body: dict, expect_response: bool = True):
        import requests  # local import: demo_mode needs no network deps

        headers = {
            "Authorization": f"Bearer {self.config.splunk_mcp_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": self.PROTOCOL_VERSION,
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        resp = requests.post(self.config.splunk_mcp_url, headers=headers,
                             json=body, timeout=15)
        resp.raise_for_status()
        return resp

    @staticmethod
    def _decode(resp) -> dict:
        if "text/event-stream" in resp.headers.get("Content-Type", ""):
            for line in reversed(resp.text.splitlines()):
                if line.startswith("data:"):
                    return json.loads(line[5:].strip())
            return {}
        return resp.json() if resp.content else {}

    def _next_id(self) -> int:
        self._rpc_id += 1
        return self._rpc_id

    # ── deterministic demo data (a real auth NullPointerException spike) ──────
    @staticmethod
    def _demo_rows(spl: str) -> list[dict]:
        if "| timechart" in spl:
            # error-rate spike starting 10:17
            return [
                {"_time": "10:00", "error_rate": 6}, {"_time": "10:05", "error_rate": 5},
                {"_time": "10:15", "error_rate": 7}, {"_time": "10:20", "error_rate": 41},
                {"_time": "10:25", "error_rate": 38}, {"_time": "10:45", "error_rate": 34},
            ]
        if "index=_audit" in spl:
            return [
                {"_time": "10:18 CET", "severity": "high",
                 "message": "auth-service error rate 8x baseline"},
            ]
        # error search: 47 NullPointerException at JwtTokenProvider:47
        return [
            {"message": "NullPointerException at JwtTokenProvider.validateToken",
             "source": "auth-service", "line": 47, "count": 23,
             "first_seen": "10:17:33 CET"},
            {"message": "NullPointerException at JwtTokenProvider.validateToken",
             "source": "auth-service", "line": 47, "count": 14,
             "first_seen": "10:23:15 CET"},
            {"message": "NullPointerException at JwtTokenProvider.validateToken",
             "source": "auth-service", "line": 47, "count": 10,
             "first_seen": "10:41:02 CET"},
        ]
