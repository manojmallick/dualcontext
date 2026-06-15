# © 2026 Manoj Mallick. DualContext — Dual-Context Incident Investigation.
# Splunk Agentic Ops Hackathon — Platform & Developer Experience track.
"""DualContext: one developer query, two MCP servers, one grounded answer.

Pipeline:  developer query -> fan out to the Splunk MCP Server (operational
reality: errors, metrics, alerts) AND the SigMap MCP Server (code structure:
ranked files/methods) in parallel -> synthesize with a Splunk hosted model
(gpt-oss-120b) -> score groundedness with that hosted model -> return the answer.
"""

__version__ = "1.0.0"

from .config import Config
from .splunk_mcp import SplunkMCPClient, OperationalContext
from .sigmap_mcp import SigMapMCPClient, CodeContext
from .synthesizer import DualContextSynthesizer
from .agent import DualContextAgent, Investigation

__all__ = [
    "Config",
    "SplunkMCPClient",
    "OperationalContext",
    "SigMapMCPClient",
    "CodeContext",
    "DualContextSynthesizer",
    "DualContextAgent",
    "Investigation",
]
