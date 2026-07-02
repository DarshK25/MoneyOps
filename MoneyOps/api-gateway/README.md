# MoneyOps API Gateway

**Spring Cloud Gateway 4.x / Java 21** — Reactive edge service for request routing, JWT authentication, rate limiting, tenant isolation, and observability.

## Responsibility

The API Gateway is the single entry point for all client traffic. It validates JWTs before requests reach the backend or AI Gateway, enforces rate limits per route type, logs every request with correlation IDs, and ensures tenant isolation. It replaces direct exposure of internal services.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Spring Cloud Gateway 4.x (WebFlux, reactive) |
| Auth | Spring Security + jjwt (HMAC-SHA256) |
| Rate Limiting | Redis (Lettuce reactive client) + custom token-bucket filter |
| Resilience | Circuit breaker pattern (via Spring Cloud Circuit Breaker) |
| Observability | Micrometer metrics, Actuator health probes, structured logging |
| Build | Maven + Spring Boot Maven plugin |

## Architecture

```
                         ┌─────────────────────────┐
Client ──► :8002 ──────►│     API Gateway         │
                         │  ┌───────────────────┐  │
                         │  │ RequestLogging    │  │  ← correlation ID, method, path
                         │  │ (Order: HIGHEST)  │  │
                         │  └────────┬──────────┘  │
                         │  ┌────────▼──────────┐  │
                         │  │ RequestDuration   │  │  ← X-Response-Time, Micrometer
                         │  │ (Order: HIGH+1)   │  │
                         │  └────────┬──────────┘  │
                         │  ┌────────▼──────────┐  │
                         │  │ Authentication    │  │  ← JWT validation, X-User-Id/X-Org-Id
                         │  │ (WebFilter)       │  │
                         │  └────────┬──────────┘  │
                         │  ┌────────▼──────────┐  │
                         │  │ TenantContext     │  │  ← enforces X-Org-Id for tenant paths
                         │  │ (Order: HIGH+2)   │  │
                         │  └────────┬──────────┘  │
                         │  ┌────────▼──────────┐  │
                         │  │ Route Matcher     │  │  ← routes to backend/AI/voice
                         │  │ + RateLimitFilter │  │  ← per-route token bucket
                         │  └───────────────────┘  │
                         └─────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
              Backend:8000         AI Gateway:8005      Voice:8003
```

## Routes

All routes are defined in `application.yml` with per-route rate limiting:

| Route ID | Path Pattern | Target | Rate Limit | Auth Required |
|----------|-------------|--------|------------|---------------|
| `auth-login` | `/api/auth/login`, `/api/auth/register` | Backend :8000 | 10/min per IP | No (public) |
| `ai-gateway` | `/api/v1/**` | AI Gateway :8005 | 20/min per user | Yes |
| `backend-api` | `/api/**` (catch-all) | Backend :8000 | 100/min per user | Yes |
| `voice-service` | `/voice/**` | Voice :8003 | 30/min per user | Yes |

Rate limits use Redis-backed token bucket with a sliding window. When Redis is unavailable, requests are allowed through (fail-open).

## Filters

| Filter | Type | Order | Purpose |
|--------|------|-------|---------|
| `RequestLoggingFilter` | WebFilter | HIGHEST_PRECEDENCE | Correlation ID, method/path/status/duration logging |
| `RequestDurationFilter` | WebFilter | HIGHEST_PRECEDENCE + 1 | X-Response-Time header, Micrometer metric recording |
| `AuthenticationFilter` | WebFilter | Via SecurityConfig | JWT validation, X-User-Id/X-Org-Id injection |
| `TenantContextFilter` | WebFilter | HIGHEST_PRECEDENCE + 2 | Multi-tenant isolation enforcement |
| `RateLimitFilter` | GatewayFilterFactory | Per-route | Redis token bucket (key, limit, window) |

## Security Model

1. **Public endpoints** (no JWT required): `/api/auth/login`, `/api/auth/register`, `/actuator/health`, `/actuator/ready`
2. **All other routes** require `Authorization: Bearer <token>` header
3. **JWT validation**: `AuthenticationFilter` extracts and validates the JWT, then injects `X-User-Id` and `X-Org-Id` headers from the token claims (NOT from client input — prevents spoofing)
4. **Tenant isolation**: `TenantContextFilter` checks that tenant-scoped paths (`/api/clients/**`, `/api/invoices/**`, etc.) have valid `X-Org-Id`
5. **CORS**: Configurable per-environment. Dev allows all origins (`*`), production should restrict to specific frontend URLs.
6. **CSRF**: Disabled (stateless JWT auth, no session cookies).

## Key Files

| File | Purpose |
|------|---------|
| `config/SecurityConfig.java` | Security rules, CORS, filter chain setup |
| `config/RedisConfig.java` | Reactive Redis connection (SSL configurable) |
| `config/RateLimitKeyResolverConfig.java` | IP, user, org, path, and composite key resolvers |
| `config/WebFluxConfig.java` | ObjectMapper with Java 8 time |
| `filter/AuthenticationFilter.java` | JWT validation WebFilter |
| `filter/RateLimitFilter.java` | Redis token-bucket GatewayFilter |
| `filter/RequestLoggingFilter.java` | Structured request/response logging |
| `filter/RequestDurationFilter.java` | Performance metrics + X-Response-Time |
| `filter/TenantContextFilter.java` | Multi-tenant isolation |
| `security/JwtTokenProvider.java` | JWT generation, validation, header matching |
| `resources/application.yml` | Main config (env-driven defaults) |
| `resources/application-dev.yml` | Dev overrides (local Redis, relaxed tenant) |
| `resources/application-prod.yml` | Production overrides (SSL Redis, strict) |

## Configuration

All properties have environment-variable defaults in `application.yml`, so the gateway starts without requiring a specific profile.

| Env Var | Property | Default | Description |
|---------|----------|---------|-------------|
| `PORT` | `server.port` | 8002 | HTTP port |
| `JWT_SECRET` | `jwt.secret` | (required) | HMAC-SHA256 key (must match backend) |
| `JWT_EXPIRATION` | `jwt.expiration` | 86400000 | Token TTL (ms) |
| `REDIS_HOST` | `spring.data.redis.host` | localhost | Redis for rate limiting |
| `REDIS_PORT` | `spring.data.redis.port` | 6379 | Redis port |
| `REDIS_PASSWORD` | `spring.data.redis.password` | — | Redis auth |
| `REDIS_TIMEOUT` | `spring.data.redis.timeout` | 2000 | Connection timeout (ms) |
| `BACKEND_CORE_URL` | `backend.core.url` | http://localhost:8000 | Backend HTTP URL |
| `AI_GATEWAY_URL` | `ai.gateway.url` | http://localhost:8005 | AI Gateway URL |
| `VOICE_SERVICE_URL` | `voice.service.url` | http://localhost:8003 | Voice service URL |
| `GATEWAY_PUBLIC_ENDPOINTS` | `gateway.public-endpoints` | /api/auth/login,/api/auth/register,/actuator/health | Public paths (comma-separated) |
| `GATEWAY_RATE_LIMIT_ENABLED` | `gateway.rate-limit.enabled` | true | Enable/disable rate limiting |
| `TENANT_ENFORCE_ISOLATION` | `gateway.tenant.enforce-isolation` | true | Enable tenant isolation |
| `GATEWAY_LOGGING_ENABLED` | `gateway.logging.enabled` | true | Enable request logging |

## Running

```bash
# Prerequisites: Java 21, running Redis on localhost:6379

# Development (with dev profile — localhost targets, relaxed tenant check)
cd api-gateway
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev

# Production (all config from env vars)
./mvnw spring-boot:run -Dspring-boot.run.profiles=prod

# Tests
./mvnw test

# Build + run
./mvnw package -DskipTests
java -jar target/api-gateway-*.jar --spring.profiles.active=prod
```

## Important Notes

- **JWT_SECRET must match the backend's JWT_SECRET** — tokens signed by the backend must be verifiable by the gateway. If they differ, all authenticated requests will fail with 401.
- **Rate limiting requires Redis** — without Redis, the gateway still works but rate limiting logs errors and allows all requests through (fail-open).
- **Default rate limits** are conservative. Adjust per route in `application.yml` based on load testing.
- **Tenant isolation** defaults to `true` in production. The `required-paths` property controls which routes require `X-Org-Id`.

## Dependencies

- **Redis** — required for rate limiting
- **Backend** — primary upstream service
- **AI Gateway** — upstream for `/api/v1/**`
- **Voice Service** — upstream for `/voice/**`
