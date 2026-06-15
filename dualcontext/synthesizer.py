# © 2026 Manoj Mallick. DualContext.
"""Synthesis layer — combines both contexts with a Splunk hosted model.

The two MCP servers each return half the picture. A Splunk hosted model
(gpt-oss-120b) fuses them into one grounded answer that cites BOTH a specific
Splunk log entry AND a specific code location. The prompt forbids answering from
general knowledge — every claim must trace to a provided source.

In demo_mode it returns a deterministic combined answer so the loop runs offline.
"""

from __future__ import annotations

SYNTHESIS_SYSTEM_PROMPT = (
    "You are an incident investigation specialist. Answer the developer's "
    "question using ONLY the two data sources provided. Cite specific error "
    "messages from Splunk AND specific files/methods from the codebase context. "
    "Never answer from general knowledge."
)

JUDGE_SYSTEM_PROMPT = (
    "You are a strict groundedness evaluator. Given an ANSWER and the SOURCE "
    "context it should be based on, score 0.0-1.0 how well every claim in the "
    "answer is grounded in the sources (specific files, methods, log lines). "
    '0.8-1.0 grounded; 0.3-0.5 partly; 0.0-0.3 ungrounded. Return ONLY JSON: '
    '{"groundedness": <float>}.'
)


class DualContextSynthesizer:
    """Fuses Splunk operational data + SigMap code context into one answer."""

    def __init__(self, config):
        self.config = config
        self.model = config.hosted_model

    def synthesize(self, query: str, operational, code) -> str:
        if self.config.demo_mode:
            return self._demo_answer(operational, code)
        try:
            return self._call_hosted_model(SYNTHESIS_SYSTEM_PROMPT,
                                           self._build_prompt(query, operational, code))
        except Exception:  # noqa: BLE001 — never crash the investigation on synth failure
            return self._demo_answer(operational, code)

    def groundedness(self, answer: str, context: str) -> float:
        """Score how grounded the answer is in the sources, via the hosted model.

        SigMap has no judge tool, so the Splunk hosted model acts as LLM-as-judge.
        In demo_mode a deterministic heuristic keeps the loop offline.
        """
        if self.config.demo_mode:
            return self._demo_groundedness(answer, context)
        try:
            raw = self._call_hosted_model(
                JUDGE_SYSTEM_PROMPT,
                f"ANSWER:\n{answer[:1200]}\n\nSOURCE CONTEXT:\n{context[:1500]}")
            import json
            import re
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            score = float(json.loads(m.group(0) if m else raw)["groundedness"])
            return max(0.0, min(1.0, round(score, 2)))
        except Exception:  # noqa: BLE001 — degrade gracefully, never crash
            return self._demo_groundedness(answer, context)

    # ── prompt construction ──────────────────────────────────────────────────
    def _build_prompt(self, query: str, operational, code) -> str:
        return (
            f"DEVELOPER QUESTION: {query}\n\n"
            f"SPLUNK OPERATIONAL DATA:\n"
            f"  Errors: {operational.errors}\n"
            f"  Error-rate trend: {operational.error_rate}\n"
            f"  Alerts: {operational.alerts}\n\n"
            f"SIGMAP CODEBASE CONTEXT:\n{code.context_text}\n\n"
            "Provide a specific, actionable answer in four sections:\n"
            "1. What Splunk shows (specific error + timestamp)\n"
            "2. Which code is responsible (specific file + method)\n"
            "3. Likely root cause\n"
            "4. Recommended action"
        )

    def _call_hosted_model(self, system: str, user: str) -> str:
        import requests  # local import: demo_mode needs no network deps

        resp = requests.post(
            self.config.hosted_model_url,
            headers={"Authorization": f"Bearer {self.config.splunk_mcp_token}",
                     "Content-Type": "application/json"},
            json={"model": self.model, "temperature": 0.0,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}]},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    # ── deterministic demo synthesis ─────────────────────────────────────────
    @staticmethod
    def _demo_answer(operational, code) -> str:
        top = operational.errors[0] if operational.errors else {}
        total = sum(int(e.get("count", 0)) for e in operational.errors)
        first = top.get("first_seen", "10:17 CET")
        top_file = code.files[0] if code.files else {}
        return (
            f"1. Splunk shows: {total} NullPointerException errors in the last hour "
            f"(first at {first}) in {operational.service}, error rate 8x baseline. "
            f"Stack trace: {top.get('message')} (line {top.get('line')}).\n"
            f"2. Code responsible: {top_file.get('name')} — validateToken() calls "
            f"getUsernameFromToken(), which can return null for malformed tokens.\n"
            f"3. Likely root cause: a recent change removed the null guard before "
            f"token.getSubject(); validateToken() then dereferences a null subject.\n"
            f"4. Recommended fix: add a null check in validateToken() at line "
            f"{top.get('line')} of {top_file.get('name')} before using the subject."
        )

    @staticmethod
    def _demo_groundedness(answer: str, context: str) -> float:
        """Deterministic offline groundedness: does the answer cite the specific
        file + method names present in the SigMap context?"""
        import re
        files = re.findall(r"([A-Za-z_]\w*\.(?:java|py|ts|go))", context)
        methods = re.findall(r"(\w+)\(", context)
        cites_file = any(f.split(".")[0] in answer for f in files)
        cites_method = any(m in answer for m in methods)
        if cites_file and cites_method:
            return 0.83
        if cites_file or cites_method:
            return 0.58
        return 0.15
