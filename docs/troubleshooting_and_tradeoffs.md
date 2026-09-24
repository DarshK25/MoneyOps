# Troubleshooting, Tradeoffs, and Git Guide

## 🔧 AI Gateway Problems & Solutions Log

### 1. AI Gateway 500 Error on Client Creation
**Problem:** The seeding script was failing with a 500 Internal Server Error when creating a client.
**Diagnosis:** The Backend Core (Java) was returning a JSON response with a `message` field for errors, but the AI Gateway's `BackendHttpAdapter` was only looking for an `error` field.
**Solution:** Updated `BackendHttpAdapter._request`:
```python
error = response_data.get("error") or response_data.get("message")
```
**Lesson:** Always inspect the *exact* JSON wire format of the upstream service when building adapters.

### 2. Authentication Failure in Agents (BALANCE_CHECK)
**Problem:** The `BALANCE_CHECK` intent was failing because the `FinanceAgent` calls `backend_adapter.get_balance()`, but the backend requires an authenticated user context (JWT) which wasn't being passed.
**Diagnosis:** The `BackendHttpAdapter` method signatures accepted `context`, but `test_agents.py` and `FinanceAgent` weren't extracting/passing the `Authorization` header from the incoming request.
**Solution:**
1.  Updated `test_agents.py` to extract the Bearer token and put it in `context["auth_token"]`.
2.  Updated `BackendHttpAdapter._request` to look for `context["auth_token"]` and set the `Authorization` header.
**Lesson:** Context propagation is critical in microservices. The token must travel from User -> Gateway -> Agent -> Adapter -> Backend.

---

## ☕ Backend Core Development Issues Log
*This section summarizes the technical challenges, bugs, and code review feedback addressed during the development and stabilization of the `feature/backend-core` branch.*

### 1. Compilation & Build Issues

#### 1.1 `PageResponse` Builder Error
*   **Problem:** The `PageResponse` class was missing the `@Builder` annotation, but `AuditLogController` was attempting to use the builder pattern.
*   **Solution:** Added Lombok's `@Builder`, `@NoArgsConstructor`, and `@AllArgsConstructor` to `PageResponse.java`.

#### 1.2 Startup Failure (OAuth2)
*   **Problem:** Application failed to start with `NoSuchBeanDefinitionException` for `ClientRegistrationRepository`. Spring Security's `oauth2Login()` was enabled, but no OAuth2 clients were configured in `application.yml`.
*   **Solution:** Added placeholder Google OAuth2 configuration (`client-id` and `client-secret`) to `application.yml` to satisfy the bean requirement.

#### 1.3 Circular Dependency
*   **Problem:** Runtime startup error due to a circular dependency cycle: `SecurityConfig` -> `OAuth2SuccessHandler` -> `AuthService` -> `PasswordEncoder` -> `SecurityConfig`.
*   **Solution:** Extracted `PasswordEncoder` bean definition into a new, separate configuration class `PasswordEncoderConfig.java` to break the cycle.

### 2. Test Failures (`InvoiceControllerTest`)

#### 2.1 Missing Dependency Injection
*   **Problem:** `UnsatisfiedDependencyException` when loading the application context for `@WebMvcTest`. The test context lacked beans for `JwtFilter`, `JwtProvider`, `UserDetailsService`, `AuthEntryPoint`, and `OAuth2SuccessHandler`.
*   **Solution:** Added `@MockBean` for all missing security-related dependencies in `InvoiceControllerTest.java`.

#### 2.2 Security Configuration & 403 Errors
*   **Problem:** Tests failed with 403 Forbidden or 302 Found (redirect to login) because the mock MVC requests were not authenticated and lacked CSRF tokens.
*   **Solution:**
    1.  Added `spring-security-test` dependency.
    2.  Annotated test class with `@WithMockUser`.
    3.  Added `.with(csrf())` to request builders.
    4.  Correctly mocked `JwtFilter` behavior (eventually restored real filter with mocked dependencies) to ensure the filter chain proceeded correctly.

### 3. CodeRabbit Review Feedback (Security & Quality)

#### 3.1 Unsecured AI Gateway Module [CRITICAL]
*   **Problem:** CodeRabbit flagged an unsecured endpoint. Upon investigation, a rogue `ai-gateway` directory was found at the project root.
*   **Solution:** Deleted the entire `ai-gateway` directory as it was not part of the core backend requirements.

#### 3.2 Legacy Password Storage [RESOLVED]
*   **Problem:** Older invite and auth flows depended on persisted user passwords, which conflicts with the Clerk-based authentication model.
*   **Solution:** Removed `users.passwordHash` usage from active backend flows and kept hashing only for `business_organizations.teamActionCodeHash`.

#### 3.3 Broken Invite Status Check [BUG]
*   **Problem:** `UserService` compared an Enum (`invite.getStatus()`) with a String literal `"PENDING"`, which always evaluated to `false`.
*   **Solution:** Changed comparison to use the Enum constant: `Invite.InviteStatus.PENDING != invite.getStatus()`.

#### 3.4 Insecure Header Handling (Impersonation Risk) [CRITICAL]
*   **Problem:** `JwtFilter` trusted `X-User-Id` and `X-Org-Id` headers directly from the client without verification, allowing potential impersonation.
*   **Solution:** Added validation logic in `JwtFilter` to ensure the `X-User-Id` header matches the ID extracted from the validated JWT token. Wrapped the context setup in a `try-finally` block to ensure `OrgContext.clear()` is always called.

#### 3.5 Build Artifacts in Version Control
*   **Problem:** `target/` directory files were committed to the repository.
*   **Solution:** Removed `backend/target/` from git validation.

#### 3.6 Spring Boot Version
*   **Problem:** Version 3.2.1 is end-of-life/vulnerable.
*   **Attempt:** Tried upgrading to 3.2.14.
*   **Result:** Upgrade caused `UnresolvableModelException` build failures.

#### 3.7 Repository Enum Mismatch [BUG]
*   **Problem:** `UserService.getPendingInvites` and `createInvite` were passing a String `"PENDING"` to repository methods that query the status column, which is mapped to an Enum. This causes type mismatch errors or invalid queries.
*   **Solution:** Refactored `InviteRepository` methods (`findAllByOrgIdAndStatus`, `existsByEmailAndOrgIdAndStatus`) to accept `Invite.InviteStatus` instead of String. Updated `UserService` to pass `Invite.InviteStatus.PENDING`.

---

## ⚖️ Tradeoffs

### 1. Synchronous HTTP vs. gRPC
**Decision:** We are currently using **HTTP/REST** (httpx) for Gateway-to-Backend communication.
**Tradeoff:** 
*   *Pros:* Easier to debug (readable JSON), standard tooling, familiar to all devs.
*   *Cons:* Higher latency, larger payload size compared to gRPC.
**Future:** We plan to migrate to gRPC for performance in Phase 5/6, but REST allows faster iteration during MVP.

### 2. Lazy Singleton for Backend Adapter
**Decision:** `get_backend_adapter()` uses a global singleton.
**Tradeoff:** 
*   *Pros:* Simplicity, reuses the connection pool (critical for performance).
*   *Cons:* Makes unit testing slightly harder (need to mock the singleton or reset it).
**Mitigation:** Good testing patterns allow for dependency injection overrides if needed.

---

## 🐙 Git Branching & Synchronization Guide

**Current Situation:**
- `feature/backend-core`: Contains the Java Backend MVP.
- `ai-gateway`: Contains the Python AI Gateway MVP.
- `dev` (or `apigateway`): Integration branches.

### The "Missing Folder" Problem
**Symptom:** When switching from `ai-gateway` branch to `feature/backend-core`, the `ai-gateway` folder disappears.
**Cause:** The `ai-gateway` directory is not tracked in the `feature/backend-core` branch. Git cleans up "untracked" files that are tracked in the current branch when you switch.

### Solution: The "Grand Merge"

To synchronize everything so all branches have all folders:

1.  **Go to your integration branch (e.g., `dev` or `main`)**:
    ```bash
    git checkout dev
    ```

2.  **Merge Backend**:
    ```bash
    git merge feature/backend-core
    ```

3.  **Merge AI Gateway**:
    ```bash
    git merge ai-gateway
    ```

4.  **Resolve Conflicts**: If `README.md` or common files conflict, edit them to keep both sections.

5.  **Push Up**:
    ```bash
    git push origin dev
    ```

Now, anyone pulling `dev` will have both `MoneyOps/backend` and `MoneyOps/ai-gateway`.

## 🚨 Git Rescue Mission Log (Dev Restoration)

**Incident:**
A merge conflict resolution on `dev` accidentally reverted the project cleanup (folder structure reorganization) while introducing new Java files for `api-gateway`.

**The Problem:**
- `dev` branch had cluttered root (original state).
- `ai-gateway` branch had clean structure (`docs/`, `scripts/`, etc.).
- `api-gateway` folder (Teammate's work) was only present in the "bad" `dev` state.

**The Fix (The "Grand Combine"):**
We performed a surgical restoration to keep the best of both worlds:

1.  **Restored Clean Structure:** Checked out `docs/`, `scripts/`, `tests/` from `origin/ai-gateway`.
    ```bash
    git checkout origin/ai-gateway -- docs/ scripts/ tests/ README.md
    ```
2.  **Preserved New Code:** Kept the `MoneyOps/api-gateway` folder (Teammate's Java code) which was already on `dev`.
3.  **Cleaned Clutter:** Removed the redundant root files that were reintroduced by the bad merge.
    ```bash
    git rm TEST_ENDPOINTS.md TEST_RESULTS.md test_api.ps1 ...
    ```
4.  **Result:** A clean `dev` branch with:
    - Phase 4 AI Gateway (Python)
    - Original Backend Core (Java)
    - New API Gateway (Java)
    - Clean Docs/Scripts structure

**Recovery for Teammates:**
Teammates should force-align with the fixed `dev` branch:
```bash
git fetch origin
git checkout dev
git reset --hard origin/dev
```

## 🛡️ Phase 4 Finalization Issues

### 1. Security Incident: OAuth2 Secrets Exposure
**Problem:** GitGuardian flagged hardcoded Google OAuth2 client ID/secret in `application.yml`.
**Solution:**
1.  Replaced hardcoded values in `application.yml` with Spring placeholders: `${GOOGLE_CLIENT_ID:placeholder}`.
2.  Created a local `backend/.env` file to store the actual secrets.
3.  Ensured `.gitignore` includes `.env`.
4.  **Runtime:** We now inject these as environment variables when starting the process.

### 2. Backend Startup Failure (H2 Database Lock)
**Problem:** Application failed with `JDBCConnectionException: Database may be already in use` and `The file is locked: .../moneyops.mv.db`.
**Cause:** A previous Java process crashed or didn't shut down cleanly, holding a file system lock on the embedded H2 database.
**Solution:**
1.  **Kill Process:** Force-killed all Java processes to release the lock.
    ```powershell
    taskkill /F /IM java.exe
    ```
2.  **Clean Slate:** Deleted the corrupted/locked database files to ensure a fresh start.
    ```powershell
    rm MoneyOps/backend/data/*.db
    ```

---

## 🔍 September 2026 Revival — Deep Audit Bug Journal
*I reopened MoneyOps after ~4 months dormant. Before writing a single line of new code I did a read-the-real-code audit of every service (not the docs, not the docstrings — the actual code paths). These are the bugs that had genuinely killed the project. For each I record how I found it, what it actually was, the blast radius, the fix, and the tradeoff behind the fix — because the tradeoff is the interesting part.*

### R1. The entire AI Gateway couldn't import — a one-line `SyntaxError` [FATAL]
**How I found it:** Nothing in the Python service would boot. `python -c "import app.main"` failed immediately.
**What it was:** `ai-gateway/app/agents/base_executor.py:253` had two statements collapsed onto one physical line:
```python
state.delegation_message = message            logger.info(...)
```
A stray merge/edit had eaten the newline. Because `base_executor` is imported transitively by `app.main`, this single line took down the *whole* AI application — every agent, every route.
**Impact:** 100% of AI-gateway functionality dead. This is why "the agents are dumb" — they never ran at all.
**Fix:** Split the statements back onto two lines.
**Key lesson (interview):** A syntax error in a hot-path module is a *fail-closed* dependency — one bad line 250 levels deep blocks the import graph above it. Lint/CI (`python -m py_compile`, ruff) in the pipeline would have caught this before merge. This is my #1 argument for wiring a pre-commit compile step.

### R2. Redis reconnect storm filled 44 GB of disk [SEV-1]
**How I found it:** Two untracked log files were eating the disk — `backend_out_v5.log` at **34.8 GB** and a backend log at **9.68 GB**. I tailed and sampled them before deleting: thousands upon thousands of `io.lettuce.core.RedisConnectionException` / `java.net.ConnectException` stack traces.
**What it was:** The backend was configured to talk to Redis at `localhost:6379`, but no Redis was running locally (the `.env` even documents Redis as unavailable). Lettuce retried the connection **unboundedly, with no backoff and no circuit breaker**, and every single failed attempt logged a full multi-line stack trace. An Upstash serverless Redis was actually available in `.env` but nothing pointed at it.
**Impact:** 44 GB of pure noise logs; disk pressure; real signal buried; startup and steady-state both spammed.
**Fix (planned):** (a) point Redis at the Upstash serverless instance that already exists, and (b) make Redis a *graceful-degradation* dependency — capped exponential backoff, a circuit breaker, and log-once-then-suppress on repeated identical failures instead of a stack trace per attempt.
**Tradeoff:** Fail-open (in-memory fallback) keeps the app usable without Redis but silently loses the queue/cache/rate-limit guarantees; fail-closed is honest but blocks boot. I chose degrade-with-loud-single-warning over both extremes.
**Key lesson (interview):** Unbounded retry + per-attempt stack-trace logging + a hard dependency assumption = a disk-filling outage from a *missing* service. Retries need backoff, breakers, and log deduplication. This is one of my strongest "I debugged a production-shaped failure" stories.

### R3. Voice agent "always falls back" — a 10s-vs-30s timeout mismatch [SEV-1]
**How I found it:** Users reported the voice agent connecting after *minutes* and then always replying with a canned "this is taking too long" line. I traced the request path from the LiveKit worker → voice-service → AI gateway.
**What it was — three compounding bugs:**
1. **Timeout mismatch:** `voice-service/app/agent/config.py:53` sets the gateway timeout to **30s**, but `docker-compose.yml:143` overrode `AI_GATEWAY_TIMEOUT` to **10s**. The LLM + gRPC pipeline routinely takes >10s, so the client aborted and emitted the fallback line *while the gateway was still successfully producing the real answer*.
2. **Error laundering:** `guard.py:11` discarded the real gateway text on a `FAILED` stage and returned a canned "I hit a snag," and a broad regex sanitizer at `entrypoint.py:340` rewrote legitimate replies into fallbacks.
3. **Wrong prompt entirely:** the agent was constructed with `Agent(instructions="MoneyOps Voice Agent")` — a placeholder string. The real, carefully-written `instructions.py` prompt was never imported. So even when it *did* answer, it answered with no persona or tool guidance.
**Impact:** The single most-visible feature (voice-to-invoice) looked completely broken to every user.
**Fix (planned):** single source of truth for the timeout (env var, no docker override fighting config.py), raise it to a realistic budget, remove the sanitizer/guard laundering so real errors surface honestly, and import the real `instructions.py`.
**Key lesson (interview):** Config precedence bugs are brutal because *nothing errors* — the value is simply wrong, and a too-tight client timeout turns a slow-but-working backend into a "broken" one. And never launder a real error into a friendly fallback before you've logged the truth; you blind yourself.
**The minutes-to-connect** was separate: LiveKit worker control-socket drops (getaddrinfo/PONG failures) plus ~10–40s cold start per call (redundant health checks, STT/TTS built 3×, VAD cold-load, a broken prewarm using `asyncio.get_event_loop()` with no running loop). Prewarm and provider reuse are the fix.

### R4. "Dual persistence" was actually split-brain [SEV-1, data integrity]
**How I found it:** The compliance dashboard showed empty data even though invoices existed. I followed the write path vs the read path per module.
**What it was:** The README claimed "dual persistence" across Postgres + MongoDB. In reality, core writes (invoices/clients/transactions) go to **Postgres only**, while Compliance / Recurring / Payments / Bulk modules still read and write **MongoDB** — an abandoned store. So compliance queried an empty Mongo while the data sat in Postgres, and bulk-created invoices were invisible to the Postgres-backed list.
**Impact:** Whole modules silently operating on the wrong (empty/stale) datastore. No error — just wrong answers.
**Fix (planned):** pick one system of record (Postgres), migrate the stragglers off Mongo, and delete the "dual persistence" claim. `scripts/migrate_to_pg.py` and `scripts/reconcile_stores.py` are the start of this.
**Key lesson (interview):** "Dual persistence" with no sync is not redundancy, it's two half-truths. A system of record must be singular unless you have real CDC/outbox syncing them. This is my go-to answer for "tell me about a data-consistency bug."

### R5. Finance metrics gRPC always returned zeros — ThreadLocal lost across gRPC threads
**How I found it:** `getFinanceMetrics` returned an all-zeros object no matter the tenant. I compared the working HTTP path against the gRPC path.
**What it was:** Tenant scoping uses an `OrgContext` `ThreadLocal`. On the HTTP path a filter populates it per request; but gRPC calls are served on gRPC's own worker threads and **no server interceptor set the OrgContext there** (`FinanceGrpcService.java:28`). So every tenant-scoped query ran with a null org and matched nothing → zeros. There was also hardcoded "VoltNest" demo text at `FinanceIntelligenceService.java:360`.
**Impact:** Every metric surfaced over gRPC was silently zero — looked like "the numbers don't work" rather than "scoping is broken."
**Fix (planned):** a gRPC `ServerInterceptor` that extracts the org from call metadata and populates `OrgContext` (with a `finally` clear), mirroring the HTTP filter. Remove the demo text.
**Key lesson (interview):** `ThreadLocal` context does not cross execution boundaries for free — every entry point (HTTP filter, gRPC interceptor, async executor, Kafka consumer) must establish and tear down the context itself. This is a classic multi-transport tenancy bug.

### R6. The "AI agents" were keyword routing, not reasoning
**How I found it:** I read `_classify_action` expecting LLM tool-calling and found a regex/keyword `if/elif` ladder.
**What it was:** Routing was pattern-matching on keywords; the LLM was only used to extract entities and to write the fallback sentence — it never *decided* anything. Worse, a genuine second "brain" (`orchestration/intent_classifier.py`, `entity_extractor.py`, `agent_router.py`, `tools/*`, `agents/compliance_agent.py`) existed but was **dead code referenced only by tests**. Two agent systems, neither doing real reasoning in production.
**Impact:** The core product claim ("a team of AI agents") was theater. This is the single biggest gap between the pitch and the reality, and the heart of what this revival has to fix for real.
**Fix (direction):** real LLM tool-calling agents (the models decide which tool to call), with the executors demoted to *tools* the agent can invoke — then wire in memory, RAG, guardrails, and evals so the intelligence is measurable, not asserted.
**Key lesson (interview):** Be able to say clearly where the LLM actually makes a decision vs where it's decoration. "Keyword routing dressed as agents" is exactly the kind of honesty an interviewer respects, paired with the plan to make it real.

### Security findings (audit batch)
- **Committed JWT secret:** `start_services.ps1:2` hardcoded a real `JWT_SECRET` (tracked, and therefore in git history). I removed the file during cleanup, but the value **must be rotated** because deleting a file does not scrub history.
- **Tenant spoofing gap:** `api-gateway` `AuthenticationFilter.java:74` trusts an `X-Org-Id` header; the guard meant to validate it against the token (`validateHeadersAgainstToken`) is dead. Same class of impersonation bug I already fixed once in the backend `JwtFilter` (§3.4) — it reappeared at the gateway layer.
- **Wildcard CORS with credentials**, and a **fail-open rate limiter** (if the limiter backend is down, requests pass) — both need to fail-closed / be scoped.

*Cleanup done this pass: reclaimed ~44 GB by deleting the runaway logs and stray `nul`; removed leftover Copilot upgrade-tooling folders under `.github/`; pruned `__pycache__`/`.pytest_cache`; removed tracked scratch (`tests/test_*.{ps1,py}`) and consolidated five launch scripts down to one canonical `start.ps1` (also eliminating the hardcoded-secret script and one hardwired `C:\DARSH\...` absolute path).*
