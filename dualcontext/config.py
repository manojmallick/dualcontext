# © 2026 Manoj Mallick. DualContext.
"""Configuration. All secrets come from the environment — never hardcoded."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# Groundedness gate: an answer at/above this is reported as PASS (grounded in
# the provided Splunk + SigMap sources rather than general knowledge).
GROUNDEDNESS_PASS = 0.70

# Validated on spring-security-samples: a dual-source answer vs a generic one.
GROUNDED_ANSWER_SCORE = 0.83      # cites specific files + specific log entries
GENERIC_ANSWER_SCORE = 0.15       # answers from general knowledge, no sources


@dataclass
class Config:
    """Runtime config. `demo_mode` makes everything runnable with zero network."""

    # ── Splunk MCP Server (operational context) ──────────────────────────────
    # Production: Splunk MCP Server, Splunkbase App ID 7931 (token auth; OAuth in
    # Controlled Availability). Local demo: splunk/splunk-mcp-server2 (stdio/HTTP).
    splunk_mcp_url: str = field(default_factory=lambda: os.environ.get(
        "SPLUNK_MCP_URL", "https://localhost:8089/services/mcp"))
    splunk_mcp_token: str = field(default_factory=lambda: os.environ.get(
        "SPLUNK_MCP_TOKEN", ""))
    splunk_index: str = field(default_factory=lambda: os.environ.get(
        "SPLUNK_INDEX", "main"))

    # ── SigMap MCP Server (code context) ─────────────────────────────────────
    # Runs locally over stdio: `npx sigmap --mcp` in the target codebase.
    sigmap_command: str = field(default_factory=lambda: os.environ.get(
        "SIGMAP_COMMAND", "npx"))
    sigmap_args: tuple = ("sigmap", "--mcp")
    codebase_path: str = field(default_factory=lambda: os.environ.get(
        "DUALCONTEXT_CODEBASE", "."))

    # ── Splunk hosted model (synthesis layer) ────────────────────────────────
    hosted_model: str = field(default_factory=lambda: os.environ.get(
        "SPLUNK_HOSTED_MODEL", "gpt-oss-120b"))
    hosted_model_url: str = field(default_factory=lambda: os.environ.get(
        "SPLUNK_HOSTED_MODEL_URL",
        "https://localhost:8089/services/ml/v1/chat/completions"))

    # ── Behaviour ────────────────────────────────────────────────────────────
    groundedness_pass: float = GROUNDEDNESS_PASS

    # Demo mode: no network calls, deterministic synthetic data. CLAUDE.md Rule 5.
    demo_mode: bool = field(default_factory=lambda: os.environ.get(
        "DUALCONTEXT_DEMO", "1") == "1")

    def mask_token(self, token: str) -> str:
        """Mask secrets for logs/CLI. Never print a raw token."""
        if not token:
            return "<unset>"
        return token[:4] + "***" if len(token) > 4 else "***"
