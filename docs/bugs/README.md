# Bugs Index

**Last updated:** 2026-09-24

One file per significant bug I found and fixed (or scoped a fix for) during the revival. Each follows the same shape: **symptom → how I found it → root cause → blast radius → fix → tradeoff → interview lesson**.

The full running narrative also lives in [`../troubleshooting_and_tradeoffs.md`](../troubleshooting_and_tradeoffs.md) (including older backend/OAuth2/H2/invite-enum bugs from the original build). This folder breaks out the biggest revival-era bugs into standalone, linkable write-ups.

## Index

| Bug | Severity | Status | File |
|---|---|---|---|
| Redis reconnect storm (44 GB logs) | SEV-1 | Fix decided (ADR-001) | [redis-reconnect-storm.md](redis-reconnect-storm.md) |
| AI gateway won't import — SyntaxError | Fatal | **Fixed 2026-09-24** | [ai-gateway-boot-syntaxerror.md](ai-gateway-boot-syntaxerror.md) |
| Voice agent "always falls back" | SEV-1 | Root-caused, fix pending | [voice-fallback-timeout.md](voice-fallback-timeout.md) |
| Split-brain persistence (PG vs Mongo) | SEV-1 | Root-caused, fix pending | [split-brain-persistence.md](split-brain-persistence.md) |
| Finance metrics gRPC returns zeros | SEV-2 | Root-caused, fix pending | [finance-metrics-zero-grpc.md](finance-metrics-zero-grpc.md) |
