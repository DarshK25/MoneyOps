# MoneyOps — Engineering Documentation

This is my living record of MoneyOps: what it is, how it's built, what's genuinely working, what was broken, and how I fixed it. I update it every work session so the picture stays honest and current — no stale claims, no theater.

**Last updated:** 2026-09-24

## Why this exists

I built MoneyOps, let it rot under a pile of bugs, and then came back to revive it properly. Rather than trust the old README or the docstrings (which lied in several places), I re-audited every service against the actual code. These docs capture that ground truth and every decision I make from here on.

## How the docs are organized

| Folder | What's in it |
|---|---|
| `architecture/` | The system as a whole: services, ports, how they talk, data flows, external dependencies. |
| `audits/` | Per-service honest audit — what's real, what's fake/partial, top bugs, security gaps, with file:line references. |
| `decisions/` | Architecture Decision Records (ADRs) — the choices I made and *why*, with consequences. |
| `bugs/` | One file per significant bug: symptom → root cause → fix → tradeoff → the lesson. |
| `interview/` | The same material distilled into talking points I can defend out loud. |

The detailed running bug journal also lives in [`../troubleshooting_and_tradeoffs.md`](../troubleshooting_and_tradeoffs.md); `bugs/` links into it.

## Ground rules I hold myself to here

- **Honest over impressive.** If a layer is fake or half-built, it says so, labelled `(not yet verified in code)` where I haven't confirmed against source.
- **Depth over breadth.** Every claim should be one I can explain and defend.
- **Progressive.** These files grow session by session; each update carries a date.
