# Feature Landscape

**Domain:** AI-powered Financial Operations Platform for Indian SMEs  
**Researched:** 2026-07-14

---

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Invoice CRUD + PDF** | Core invoice product | Medium | Already implemented (dual-write Mongo + PG) |
| **Client Management** | Invoices need counterparties | Low | Already implemented |
| **Payment Recording** | Track received/pending | Medium | Razorpay integration exists; manual recording needed |
| **GST/TDS Compliance** | Mandatory in India | High | ComplianceService exists; needs filing automation |
| **Multi-tenant Organizations** | B2B SaaS requirement | Medium | Org isolation via JWT + TenantContextFilter done |
| **Team Invitations + RBAC** | Collaboration | Medium | Invite flow exists; roles: ADMIN/MEMBER/VIEWER |
| **Dashboard / Analytics** | Financial visibility | High | FinanceIntelligenceService + 25+ frontend pages |
| **Recurring Invoices** | Subscription billing | Medium | RecurringInvoicesService exists |
| **Document Storage** | Attachments, contracts | Low | DocumentService + MongoDB GridFS |
| **Audit Trail** | Compliance requirement | Medium | AuditLog entity + service exists; needs immutability |
| **Email Notifications** | Transactional comms | Low | Resend/Brevo workers exist |
| **OAuth2 (Google) + JWT** | Standard auth | Low | Implemented in backend + gateway |

---

## Differentiators

Features that set product apart. Not expected, but high value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Voice-to-Action (LiveKit + AI Gateway)** | "Create invoice for Acme ₹50k" via voice | Very High | Voice pipeline: WebRTC → STT → Orchestrator → gRPC → Backend. Unique for Indian SME market |
| **Multi-Agent Orchestration (AgentOS)** | CEO agent delegates to Finance/Compliance/Collections/Growth/TReDS | Very High | 5 specialized executors + message bus + governance + memory |
| **Semantic Cache (Pinecone + Redis)** | Sub-100ms repeated LLM queries; cost reduction | High | Embedding-based deduplication; 40% threshold |
| **Multi-Provider LLM Fallback** | Groq → Cerebras → Gemini → Anthropic | Medium | Resilience + cost optimization; already in multi_provider.py |
| **TReDS Integration (Invoice Discounting)** | Working capital access for SMEs | High | RXIL/M1xchange/InvoiceMart adapters scaffolded |
| **Morning Briefing / Evening Summary** | Proactive financial insights | Medium | CEO agent generates daily digests |
| **Compliance Agent (GST/TDS auto-calc)** | Reduces CA dependency | High | Rule engine + govt API integration needed |
| **Collections Agent (Automated Reminders)** | Improves cash flow | Medium | Escalation workflows + WhatsApp/Email |
| **Growth Agent (Revenue Forecast, Churn)** | Strategic value beyond bookkeeping | High | ML-based; needs historical data pipeline |

---

## Anti-Features

Explicitly NOT building. Avoids scope creep and strategic drift.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **General Accounting (GL, Chart of Accounts)** | Tally/Zoho Books own this; too broad | Integrate via API; focus on invoicing/collections |
| **Payroll / HR** | Different domain, high compliance | Partner with Keka/RazorpayX Payroll |
| **Inventory Management** | Different user persona | Integrate with Unicommerce/Zoho Inventory |
| **Banking Core (Ledger, Reconciliation)** | Requires banking license/partnership | RazorpayX / Open banking APIs for statements |
| **Tax Filing (GSTR-1/3B direct submission)** | Govt portal changes break integrations | Generate JSON/Excel for CA upload; keep filing manual |
| **Custom Report Builder** | Low usage, high maintenance | Curated dashboards + CSV export for power users |
| **White-label / Multi-brand** | Enterprise feature; dilutes focus | Single strong brand; API for partners later |
| **Mobile App (Native)** | Web PWA covers 90% use cases | PWA + responsive; React Native only when ARR > $5M |
| **AI Chat as Primary UI** | Voice + guided forms better for structured data | Keep chat for queries; forms for creation |

---

## Feature Dependencies

```
Voice Service (LiveKit)
    → AI Gateway /voice/process
        → Master Orchestrator
            → Intent Classifier
            → Domain Executor (Finance/Compliance/Collections/TReDS/Growth)
                → Backend Adapter (gRPC preferred)
                    → Backend gRPC Services
                        → MongoDB (primary) + PostgreSQL (dual-write)
                            → Event → Redis Queue → Email/Notification Workers

Frontend (React)
    → API Gateway (Spring Cloud Gateway)
        ├── /api/auth/** → Backend Auth
        ├── /api/v1/** → AI Gateway
        └── /api/** → Backend REST

AgentOS Memory (Pinecone)
    ← Semantic Cache (Redis + Pinecone)
    ← Conversation History (Redis)
    ← Agent State (Redis)

Compliance Filing
    → Government GST Portal API (sandbox → prod)
    → TDS Return Generation (FVU)
```

**Critical Path:** Voice → AI Gateway → Orchestrator → Finance Executor → Backend gRPC → DB  
**Blocking:** AI Gateway must be healthy for voice; Backend must be healthy for everything

---

## MVP Recommendation

### Prioritize (Ship First)

| Priority | Feature | Rationale |
|----------|---------|-----------|
| 1 | **Invoice CRUD + PDF + Payments** | Revenue core; already 90% done |
| 2 | **Client + Org + Team Management** | Multi-tenant foundation; done |
| 3 | **GST Invoice Compliance (HSN/SAC, GSTIN validation)** | Legal requirement; differentiates from generic invoicing |
| 4 | **Dashboard: Receivables, Cash Flow, Tax Liability** | Daily value; retains users |
| 5 | **Email Notifications (Invoice sent, Payment received, Overdue)** | Automates follow-up; low effort |
| 6 | **AI Chat (Text) for Invoice Creation** | Lower barrier than voice; validates orchestrator |
| 7 | **Recurring Invoices** | Retention driver for subscription businesses |

### Defer (Post-MVP)

| Feature | Reason |
|---------|--------|
| **Voice Pipeline** | High complexity; requires LiveKit infra, STT/TTS tuning, VAD calibration; ship text-first |
| **Collections Agent (Automated Escalation)** | Needs volume to tune; start with manual reminders + templates |
| **TReDS Integration** | Requires partnership + sandbox access; niche (only ~50k SMEs on TReDS) |
| **Growth Agent (Forecasting)** | Needs 6+ months historical data; build data pipeline first |
| **Compliance Auto-filing** | Govt API instability; generate returns for CA review first |
| **Advanced RBAC (Field-level, Custom Roles)** | Over-engineering for <50 orgs; ADMIN/MEMBER/VIEWER sufficient |

---

## Sources

- **Codebase**: `MoneyOps/backend/src/main/java/com/moneyops/**`, `MoneyOps/ai-gateway/app/agents/**`, `MoneyOps/voice-service/`, `MoneyOps/Frontend/src/pages/**`
- **Architecture**: `docs/architecture.md` (Mermaid diagrams, service matrix)
- **Domain Knowledge**: Indian SME finance workflows (GST, TDS, TReDS), competitive landscape (Zoho, Tally, RazorpayX, ClearTax)