# Frontend — Audit

**Stack:** React 18 / Vite 7 · **Port:** 3000 (Vite default 5173) · **~19,339 LOC** · **Last updated:** 2026-09-24

## Genuinely real & good 🟢
- **~22 real pages** — dashboard, invoices, clients, transactions, agent chat, voice, settings, etc. This is the most substantial and genuinely-built layer by LOC.
- `src/lib/api.js` now has **response cache + request dedup** and (after fixes) timeout handling.
- Real routing, auth token handling, and UI state.

## Fake / partial / broken 🟡
- **`getToken()` ReferenceError** in `src/pages/InvoicesPage.jsx:150` — the function was used but never imported, so **PDF download threw** at runtime.
- `src/lib/api.js` previously **lacked AbortController/timeout** despite a commit message claiming a "chat timeout" fix — the chat request could hang indefinitely.
- Pagination JSX structure in `InvoicesPage.jsx` had been reworked across a few commits (fragile area to regression-test).

## Security
- Frontend relies on the gateway for auth; the `X-Org-Id` trust gap upstream (see [`api-gateway.md`](api-gateway.md)) is the relevant risk, not the client itself.

## Top priorities
1. Confirm the `getToken` import fix holds and PDF download works end-to-end.
2. Ensure `api.js` timeout/AbortController is actually applied to the agent-chat call (this ties into the voice/gateway timeout story).
3. Keep the invoices pagination path under test — it's been churned.
