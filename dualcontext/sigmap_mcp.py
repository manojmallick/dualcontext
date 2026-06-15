# © 2026 Manoj Mallick. DualContext.
"""SigMap MCP Server client — the CODE half of DualContext.

SigMap (https://github.com/manojmallick/sigmap) runs as an MCP server over
stdio (`npx sigmap --mcp`) inside the target codebase. It returns query-focused
code structure — ranked file/method signatures — at high token reduction vs
shipping the whole repo.

Tool used (verified against SigMap v7.0.0):
    query_context(query, topK)  -> ranked files + their signatures (Markdown)

SigMap also exposes read_context, search_signatures, explain_file, get_impact,
get_routing, list_modules, get_lines, get_map. DualContext uses query_context
for relevance ranking. SigMap has NO groundedness-judge tool — groundedness is
scored separately by the Splunk hosted model (see synthesizer.py).

In demo_mode the client returns deterministic synthetic context so the whole
loop runs offline (CLAUDE.md air-gapped rule).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field


@dataclass
class CodeContext:
    """What SigMap returned: ranked files/methods plus token accounting."""
    query: str
    files: list[dict] = field(default_factory=list)   # {name, score, signatures}
    context_text: str = ""
    tokens_used: int = 0
    tokens_raw: int = 0
    elapsed_ms: float = 0.0

    @property
    def reduction_pct(self) -> float:
        if not self.tokens_raw:
            return 0.0
        return round((1 - self.tokens_used / self.tokens_raw) * 100, 1)

    @property
    def file_names(self) -> list[str]:
        return [f["name"] for f in self.files]


class SigMapMCPClient:
    """Talks to the SigMap MCP Server over stdio (newline-delimited JSON-RPC)."""

    PROTOCOL_VERSION = "2025-06-18"

    def __init__(self, config):
        self.config = config

    # ── high-level operation the agent uses ──────────────────────────────────
    def code_context(self, query: str, top_k: int = 5) -> CodeContext:
        """Ask SigMap to rank the most relevant files for the query."""
        start = time.perf_counter()
        if self.config.demo_mode:
            time.sleep(0.8)  # simulate SigMap MCP round-trip so timing is realistic
            files, text, used, raw = self._demo_context()
        else:
            text = self._call_tool("query_context", {"query": query, "topK": top_k})
            files = self._parse_ranked_files(text)
            used = self._count_tokens(text)
            raw = 0  # full-repo token count is reported separately by `sigmap --report`
        return CodeContext(
            query=query, files=files, context_text=text,
            tokens_used=used, tokens_raw=raw,
            elapsed_ms=round((time.perf_counter() - start) * 1000, 1),
        )

    # Note: SigMap has no groundedness-judge tool, so there is deliberately no
    # judge() here. Groundedness is scored by the Splunk hosted model
    # (gpt-oss-120b) in synthesizer.groundedness() — one story across code + deck.

    # ── stdio MCP transport ──────────────────────────────────────────────────
    def _call_tool(self, tool: str, arguments: dict) -> str:
        """Spawn `npx sigmap --mcp`, handshake, call one tool, return its text.

        SigMap is a stdio MCP server: JSON-RPC messages are newline-delimited.
        We initialize, send `initialized`, then `tools/call`, then read the reply.
        """
        import subprocess

        proc = subprocess.Popen(
            [self.config.sigmap_command, *self.config.sigmap_args],
            cwd=self.config.codebase_path,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1,
        )
        try:
            self._send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                              "params": {"protocolVersion": self.PROTOCOL_VERSION,
                                         "capabilities": {},
                                         "clientInfo": {"name": "dualcontext",
                                                        "version": "1.0.0"}}})
            self._read(proc, want_id=1)
            self._send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
            self._send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                              "params": {"name": tool, "arguments": arguments}})
            reply = self._read(proc, want_id=2)
        finally:
            proc.terminate()

        result = (reply or {}).get("result", {})
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            return content[0]["text"]
        return ""

    @staticmethod
    def _send(proc, msg: dict) -> None:
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()

    @staticmethod
    def _read(proc, want_id: int | None = None, timeout_s: float = 25.0) -> dict | None:
        """Read newline-delimited JSON-RPC replies until the matching id arrives."""
        import threading

        box: dict = {}

        def pump():
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if want_id is None or msg.get("id") == want_id:
                    box["msg"] = msg
                    return

        t = threading.Thread(target=pump, daemon=True)
        t.start()
        t.join(timeout=timeout_s)
        return box.get("msg")

    # ── parsing the real query_context Markdown table ────────────────────────
    @staticmethod
    def _parse_ranked_files(text: str) -> list[dict]:
        """Parse SigMap's `query_context` output: a `| Rank | File | Score |` table."""
        files: list[dict] = []
        for line in text.splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3 or cells[1] in ("File", "") or set(cells[0]) <= {"-"}:
                continue
            try:
                score = float(cells[2])
            except ValueError:
                continue
            files.append({"name": cells[1], "score": score, "signatures": []})
        return files

    @staticmethod
    def _count_tokens(text: str) -> int:
        return max(1, len(text) // 4)  # ~4 chars/token heuristic

    # ── deterministic demo context (spring-security-samples) ─────────────────
    @staticmethod
    def _demo_context():
        files = [
            {"name": "JwtTokenProvider.java", "score": 0.91,
             "signatures": ["class JwtTokenProvider",
                            "  validateToken(String token): boolean",
                            "  getUsernameFromToken(String token): String  // may return null"]},
            {"name": "SecurityConfig.java", "score": 0.73,
             "signatures": ["class SecurityConfig",
                            "  configure(HttpSecurity http): void"]},
            {"name": "JwtAuthFilter.java", "score": 0.68,
             "signatures": ["class JwtAuthFilter",
                            "  doFilterInternal(...): void"]},
        ]
        text = "\n".join(
            f"{f['name']} (relevance {f['score']})\n  " + "\n  ".join(f["signatures"])
            for f in files
        )
        return files, text, 180, 45000
