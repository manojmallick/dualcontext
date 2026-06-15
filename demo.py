# © 2026 Manoj Mallick. DualContext — runnable end-to-end demo.
"""Run the full DualContext dual-MCP investigation with zero network access.

    python demo.py
    python demo.py --query "Payment service timing out. Why?"

It fans a developer question out to the (simulated) Splunk MCP Server and the
(simulated) SigMap MCP Server in parallel, fuses both with a Splunk hosted model
(gpt-oss-120b), and scores the answer's groundedness with that hosted model.
No Splunk instance, API key, or codebase required — DUALCONTEXT_DEMO=1 default.
"""

from __future__ import annotations

import sys

from dualcontext import Config, DualContextAgent


def banner(text: str) -> None:
    print(f"\n\033[1;36m{'─' * 64}\n{text}\n{'─' * 64}\033[0m")


def main() -> None:
    query = "Auth service throwing 47 errors per hour. What's causing it?"
    if "--query" in sys.argv:
        query = sys.argv[sys.argv.index("--query") + 1]

    config = Config(demo_mode=True)
    agent = DualContextAgent(config)

    banner("DualContext · one query → Splunk MCP + SigMap MCP (parallel)")
    print(f"  developer: \"{query}\"")
    print(f"  splunk MCP token: {config.mask_token(config.splunk_mcp_token)} | "
          f"hosted model: {config.hosted_model}")

    result = agent.investigate(query)

    banner("Dual-MCP query")
    for line in result.narrative:
        print(f"  {line}")

    banner(f"Investigation result · groundedness {result.groundedness} "
           f"{'✅ PASS' if result.passed else '❌ FAIL'}")
    print(result.answer)
    print()
    print(f"  splunk sources : {', '.join(result.splunk_sources)}")
    print(f"  code sources   : {', '.join(result.code_sources)}")
    print(f"  token reduction: {result.token_reduction_pct}% "
          f"(SigMap context vs full codebase)")
    print(f"  wall-clock     : {result.investigation_ms} ms (both MCP queries in parallel)")


if __name__ == "__main__":
    main()
