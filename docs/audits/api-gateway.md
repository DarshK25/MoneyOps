# API Gateway — Audit

**Stack:** Spring Cloud Gateway (WebFlux) · **Port:** 8002 · **~1,947 LOC** · **Last updated:** 2026-09-24

> Note: historically this service was substantially a teammate's work. I own the revival of it but not the original authorship.

## Genuinely real & good 🟢
- **Single front door:** all browser traffic routes through here.
- **Routing + auth filtering** (`filter/AuthenticationFilter.java`) — validates JWT, forwards identity/tenant headers.
- **Public-endpoint allowlist** (login/register/health/oauth2) works.

## Fake / partial / broken 🟡🔴
- **X-Org-Id tenant spoofing gap** — `AuthenticationFilter.java:74` trusts the `X-Org-Id` header from the client. The guard that should cross-check it against the validated JWT (`JwtTokenProvider.validateHeadersAgainstToken`) is **dead code**. A caller could assert another org's id.
- This is the *same class* of impersonation bug I already fixed once in the backend `JwtFilter` (`X-User-Id`, documented in `../troubleshooting_and_tradeoffs.md` §3.4) — it reappeared here at the gateway layer.

## Security
- **X-Org-Id spoofing** (above) — highest priority.
- **Wildcard CORS with credentials.**
- **Rate limiter fail-open** — if the limiter backend is unavailable, requests pass unthrottled.

## Top priorities
1. Wire up `validateHeadersAgainstToken` (or equivalent): the org/user in headers must be derived from, or validated against, the token — never trusted raw.
2. Scope CORS to known origins.
3. Make rate limiting fail-closed (or degrade with a loud warning).
