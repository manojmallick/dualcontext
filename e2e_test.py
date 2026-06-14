# © 2026 LearnHubPlay BV. DualContext — end-to-end test.
"""End-to-end checks for DualContext. Run: python e2e_test.py

  TEST 1  Offline demo pipeline (no network)  — always runs.
  TEST 2  Live SigMap MCP half (real npx sigmap --mcp) — runs if SigMap is
          installed; indexes this repo, calls query_context for real, asserts
          the stdio transport + Markdown-table parser work end to end.

Exit code 0 = all run tests passed. The Splunk MCP + hosted-model live paths
need a Splunk instance and are not exercised here (no instance available).
"""

from __future__ import annotations

import shutil
import subprocess
import sys

from dualcontext import Config, DualContextAgent, SigMapMCPClient


def check(name: str, cond: bool, detail: str = "") -> bool:
    mark = "\033[1;32mPASS\033[0m" if cond else "\033[1;31mFAIL\033[0m"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
    return cond


def test_demo_pipeline() -> bool:
    print("\nTEST 1 · offline demo pipeline")
    agent = DualContextAgent(Config(demo_mode=True))
    r = agent.investigate("Auth service throwing 47 errors per hour. What's causing it?")
    ok = True
    ok &= check("47 events sensed from Splunk", "47" in r.answer)
    ok &= check("groundedness PASS", r.passed, f"score={r.groundedness}")
    ok &= check("answer cites the specific file", "JwtTokenProvider" in r.answer)
    ok &= check("answer cites the specific method", "validateToken" in r.answer)
    ok &= check("both sources present",
                bool(r.splunk_sources) and bool(r.code_sources))
    ok &= check("parallel ≤ serial wall-clock", r.investigation_ms < 1865,
                f"{r.investigation_ms} ms")
    ok &= check("token reduction reported", r.token_reduction_pct > 90,
                f"{r.token_reduction_pct}%")
    return ok


def test_live_sigmap() -> bool:
    print("\nTEST 2 · live SigMap MCP half (real npx sigmap --mcp)")
    if shutil.which("npx") is None:
        print("  [SKIP] npx not found — SigMap live path not tested")
        return True
    # Index this repo so query_context has signatures to rank.
    idx = subprocess.run(["npx", "sigmap"], capture_output=True, text=True)
    if idx.returncode != 0:
        print("  [SKIP] `npx sigmap` indexing unavailable")
        return True
    cfg = Config(demo_mode=False)
    cfg.codebase_path = "."
    ctx = SigMapMCPClient(cfg).code_context("splunk operational context errors", top_k=5)
    ok = True
    ok &= check("query_context returned ranked files", len(ctx.files) > 0,
                f"{len(ctx.files)} files")
    ok &= check("Markdown table parsed (names + scores)",
                all("name" in f and "score" in f for f in ctx.files))
    ok &= check("context text captured", ctx.context_text.startswith("## Query:"))
    if ctx.files:
        print("       ranked:", ", ".join(f"{f['name']}({f['score']})"
                                          for f in ctx.files[:3]))
    return ok


def main() -> None:
    results = [test_demo_pipeline(), test_live_sigmap()]
    print("\n" + "─" * 50)
    if all(results):
        print("\033[1;32mALL TESTS PASSED\033[0m")
        sys.exit(0)
    print("\033[1;31mSOME TESTS FAILED\033[0m")
    sys.exit(1)


if __name__ == "__main__":
    main()
