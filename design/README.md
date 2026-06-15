# DualContext — UI Design Prototype

High-fidelity, interactive HTML prototype of the DualContext product UI (Stitch
design system, Tailwind + Material Symbols). These three screens define the
target developer experience; the **functional** analytics equivalent runs live
on Splunk Dashboard Studio (see [`../dashboards/`](../dashboards/)).

| Screen | File | Notes |
|---|---|---|
| Investigation Interface | [investigation.html](investigation.html) | the dual-MCP query → grounded answer |
| Evidence Breakdown | [evidence.html](evidence.html) | what each MCP server contributed |
| Investigation History | [history.html](history.html) | analytics → live `dualcontext_analytics` dashboard |

The three screens are cross-linked via the left sidebar (Dashboard · Incidents ·
Analytics). Open [investigation.html](investigation.html) (or `index.html`) to start.

**Static captures** for the submission/deck: `investigation.png`, `evidence.png`,
`history.png`.

**Design system:** see [DESIGN.md](DESIGN.md) — Splunk green `#65E075` for the
operational half, SigMap teal for the code half, dual-source evidence panels,
groundedness badge. Inter for UI text + JetBrains Mono for code/log evidence.

> Prototype data is illustrative; the live Splunk analytics dashboard renders the
> Investigation History view from real `dualcontext_investigation` telemetry.
