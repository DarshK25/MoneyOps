# Bug: "Dual persistence" was actually split-brain

**Severity:** SEV-1 (data integrity) · **Status:** root-caused, fix pending · **Found:** 2026-09-24

## Symptom
The compliance dashboard showed empty data even though invoices existed. Bulk-created invoices didn't appear in the normal invoice list.

## How I found it
Followed the write path vs the read path per module instead of trusting the "dual persistence" claim in the README.

## Root cause
The README claimed data was persisted to both Postgres and MongoDB for redundancy. In reality:
- **Postgres** takes core writes — invoices, clients, transactions (`InvoiceDocumentStore` is Postgres-only).
- **MongoDB** is still read/written by the **Compliance, Recurring, Payments, and Bulk** modules — an abandoned store.

There is **no sync** between them (no CDC, no outbox). So compliance queried an empty Mongo while the real data sat in Postgres, and bulk invoices written to Mongo were invisible to the Postgres-backed list.

## Blast radius
Whole modules silently operating on the wrong (empty/stale) datastore. No error thrown — just wrong answers, which is worse.

## Fix (planned)
Pick **one system of record (Postgres)**, migrate the straggler modules off Mongo, and delete the "dual persistence" claim. `scripts/migrate_to_pg.py` and `scripts/reconcile_stores.py` are the starting point.

## Tradeoff
Consolidating to one store removes the (imagined) redundancy. But "dual persistence" with no sync was never redundancy — it was two half-truths. Real redundancy would need CDC/outbox syncing the two, which is far more machinery than this app needs. A single well-backed-up Postgres is the honest, simpler choice.

## Interview lesson
A system of record must be **singular** unless you have real change-data-capture keeping copies in sync. "We write to two databases" is a red flag, not a feature, when nothing reconciles them. This is my go-to answer for "tell me about a data-consistency bug."
