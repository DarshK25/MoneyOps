# Architecture Decision Records

**Last updated:** 2026-09-24

This folder holds ADRs — short records of significant technical decisions and *why* I made them. The point is that future-me (and anyone reviewing the project) can see the reasoning, not just the result.

## Format

Each ADR follows:

- **Status** — Proposed / Accepted / Superseded.
- **Context** — the situation and forces at play (often a bug or constraint).
- **Decision** — what I chose to do.
- **Consequences** — what this makes better, and what it costs.

## Convention

- Files are named `ADR-NNN-short-slug.md`, numbered in the order decided.
- ADRs are append-only in spirit: I don't rewrite an old one, I supersede it with a new ADR and mark the old one `Superseded by ADR-NNN`.

## Index

| # | Title | Status |
|---|---|---|
| 001 | [Redis topology + graceful degradation](ADR-001-redis-and-degradation.md) | Accepted |
