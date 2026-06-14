# © 2026 LearnHubPlay BV. DualContext.
"""The DualContext Agent — the dual-MCP core.

One developer query fans out to TWO MCP servers in parallel:

    Splunk MCP Server  -> operational reality (errors, metrics, alerts)
    SigMap MCP Server  -> code structure (ranked files/methods)

A Splunk hosted model (gpt-oss-120b) then synthesizes both into one grounded
answer, and SigMap's judge scores how grounded that answer is. Neither source
alone is sufficient: Splunk knows *which line* but not *which file/method*;
SigMap knows *which file/method* but not *which error*. Together they pinpoint
both — that is the whole thesis.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict

from .config import Config
from .splunk_mcp import SplunkMCPClient, OperationalContext
from .sigmap_mcp import SigMapMCPClient, CodeContext
from .synthesizer import DualContextSynthesizer


@dataclass
class Investigation:
    query: str
    answer: str
    groundedness: float
    passed: bool
    splunk_sources: list[str] = field(default_factory=list)
    code_sources: list[str] = field(default_factory=list)
    investigation_ms: float = 0.0
    token_reduction_pct: float = 0.0
    narrative: list[str] = field(default_factory=list)

    def as_event(self) -> dict:
        d = asdict(self)
        d["component"] = "dualcontext_agent"
        return d


class DualContextAgent:
    def __init__(self, config: Config,
                 splunk: SplunkMCPClient | None = None,
                 sigmap: SigMapMCPClient | None = None,
                 synthesizer: DualContextSynthesizer | None = None):
        self.config = config
        self.splunk = splunk or SplunkMCPClient(config)
        self.sigmap = sigmap or SigMapMCPClient(config)
        self.synthesizer = synthesizer or DualContextSynthesizer(config)

    def investigate(self, query: str) -> Investigation:
        log: list[str] = []
        service = self._extract_service(query)

        # 1. DUAL QUERY — fire both MCP servers in parallel (real wall-clock win).
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_splunk = pool.submit(self.splunk.operational_context, service)
            f_sigmap = pool.submit(self.sigmap.code_context, query)
            operational: OperationalContext = f_splunk.result()
            code: CodeContext = f_sigmap.result()
        parallel_ms = max(operational.elapsed_ms, code.elapsed_ms)
        log.append(f"SPLUNK MCP · ran {len(operational.queries_run)} SPL searches, "
                   f"{operational.events_analyzed} events ({operational.elapsed_ms} ms)")
        log.append(f"SIGMAP MCP · ranked {len(code.files)} files, "
                   f"{code.tokens_used} tokens vs {code.tokens_raw} raw "
                   f"({code.reduction_pct}% reduction, {code.elapsed_ms} ms)")
        log.append(f"PARALLEL   · both contexts ready in {parallel_ms} ms "
                   f"(not {round(operational.elapsed_ms + code.elapsed_ms, 1)} ms serial)")

        # 2. SYNTHESIS — fuse both contexts with a Splunk hosted model.
        answer = self.synthesizer.synthesize(query, operational, code)
        log.append(f"SYNTHESIS  · {self.config.hosted_model} fused both sources")

        # 3. GROUNDEDNESS — the Splunk hosted model scores how grounded the
        #    answer is in the two sources (SigMap has no judge tool).
        groundedness = self.synthesizer.groundedness(answer, code.context_text)
        passed = groundedness >= self.config.groundedness_pass
        log.append(f"JUDGE      · {self.config.hosted_model} groundedness {groundedness} "
                   f"{'PASS' if passed else 'FAIL'} "
                   f"(threshold {self.config.groundedness_pass})")

        return Investigation(
            query=query, answer=answer, groundedness=groundedness, passed=passed,
            splunk_sources=operational.sources, code_sources=code.file_names,
            investigation_ms=round(parallel_ms, 1),
            token_reduction_pct=code.reduction_pct, narrative=log,
        )

    @staticmethod
    def _extract_service(query: str) -> str:
        """Pull a service name from the query; default to auth-service for the demo."""
        m = re.search(r"([a-z][a-z0-9-]*-service)", query.lower())
        if m:
            return m.group(1)
        m = re.search(r"\b(auth|payment|api-gateway|database|cache)\b", query.lower())
        return f"{m.group(1)}-service" if m else "auth-service"
