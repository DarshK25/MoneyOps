# MoneyOps Backend

**Spring Boot 3.2.1 / Java 21** — Core business logic, REST API, gRPC server, dual persistence (MongoDB + PostgreSQL), async queue workers.

## Responsibility

The backend is the authoritative data layer and business logic engine. It handles all CRUD operations, financial calculations (GST/TDS), payment processing, PDF generation, user auth, and serves as the data source for the AI Gateway via gRPC.

## Tech Stack

| Component | Technology | Port |
|-----------|------------|------|
| Web Framework | Spring Boot 3.2.1 (Web, Security, Data, Mail, Validation) | 8000 |
| gRPC Server | net.devh:grpc-server-spring-boot-starter | 50051 |
| Primary DB | MongoDB Atlas (13 collections) | — |
| Relational DB | Neon PostgreSQL (Flyway migrations + JPA dual-write) | — |
| Auth | Spring Security + JWT (jjwt) + OAuth2 (Google) | — |
| Payments | Razorpay Java SDK | — |
| PDF | OpenPDF (iText fork) | — |
| Queue | Redis (Lettuce reactive client) | — |
| API Docs | springdoc-openapi → /swagger-ui.html | — |

## Architecture

```
HTTP :8000 ◄──── API Gateway / Frontend / External
   │
   ├── Controllers (REST endpoints under /api/)
   │
   ├── Services (business logic)
   │   ├── UserService          # Users + team invites + dual-write
   │   ├── ClientService        # Client CRUD + dual-write
   │   ├── OrganizationService  # Business orgs + verification + dual-write
   │   ├── InvoiceService       # Invoice CRUD + PDF + dual-write
   │   ├── TransactionService   # Income/expense + dual-write
   │   ├── AuthService          # Login/register/JWT/OAuth2
   │   ├── RazorpayService      # Payment orders, verification
   │   ├── ComplianceService    # GST/TDS calculation, deadlines
   │   ├── FinanceService       # Metrics, budget vs actual
   │   └── DocumentService      # File upload/retrieval
   │
   ├── Repositories
   │   ├── MongoRepository (primary)   # 13 MongoDB collections
   │   └── JpaRepository (dual-write)  # 5 PostgreSQL tables
   │
   └── gRPC :50051 ◄──── AI Gateway
        ├── OrganizationService   # GetOnboardingStatus, GetOrganization
        ├── ClientService         # GetClients, CreateClient
        ├── InvoiceService        # GetInvoices, GetInvoice, CreateInvoice, MarkPaid
        ├── FinanceService        # GetFinanceMetrics, GetFinancialSummary
        └── NotificationService   # SendCollectionEmail

Redis Queue ──► email_worker.py, notification_worker.py
```

## Data Model

### MongoDB Collections (Primary)

| Collection | Entity Class | Key Fields |
|-----------|-------------|------------|
| `users` | `User` | name, email, passwordHash, orgId, role, status |
| `clients` | `Client` | name, email, phone, gstNumber, orgId, address |
| `invoices` | `Invoice` | clientId, totalAmount, status, dueDate, orgId, items |
| `transactions` | `Transaction` | amount, type, category, clientId, invoiceId, orgId |
| `business_organizations` | `BusinessOrganization` | legalName, gstNumber, pan, status, businessType |
| `invites` | `Invite` | email, token, orgId, status, expiresAt |
| `team_invites` | `TeamInvite` | email, token, orgId, role |
| `recurring_invoices` | `RecurringInvoice` | template, interval, nextDate, clientId |
| `budgets` | `Budget` | category, year, month, amount, orgId |
| `documents` | `MoneyOpsDocument` | fileName, entityType, entityId, orgId |
| `audit_logs` | `AuditLog` | entityType, entityId, operation, userId, timestamp |
| `org_memory` | `OrgMemory` | key, value, orgId |
| `regulatory_profiles` | `RegulatoryProfile` | orgId, gstin, pan, complianceStatus |

### PostgreSQL Tables (Dual-Write)

| Table | JPA Entity | Status |
|-------|-----------|--------|
| `organizations` | `OrganizationEntity` | Dual-write active |
| `users` | `UserEntity` | Dual-write active |
| `clients` | `ClientEntity` | Dual-write active |
| `invoices` | `InvoiceEntity` | Dual-write active |
| `transactions` | `TransactionEntity` | Dual-write active |

The backend writes to **both** MongoDB (primary) and PostgreSQL on every create/update operation. Reads prefer PostgreSQL and fall back to MongoDB if not found. This is a live migration strategy — MongoDB remains the source of truth until PostgreSQL is fully validated in production.

## Packages

| Package | Purpose | Key Files |
|---------|---------|-----------|
| `auth/` | JWT provider, filters, OAuth2, login/register | `AuthController`, `JwtFilter`, `OAuth2Controller`, `UserDetailsServiceImpl` |
| `invoices/` | Invoice CRUD, PDF generation, recurring | `InvoiceController`, `InvoiceService`, `PdfGenerationService`, `RecurringInvoiceService` |
| `clients/` | Client CRUD, search, duplicate detection | `ClientController`, `ClientService`, `ClientValidator` |
| `transactions/` | Income/expense tracking, pagination, summaries | `TransactionController`, `TransactionService` |
| `organizations/` | Business orgs, verification, regulatory profiles | `OrganizationController`, `OrganizationService` |
| `users/` | User management, team invites (invite by email, role, accept) | `UserController`, `UserService`, `InviteService` |
| `payments/` | Razorpay order creation, payment verification | `RazorpayController`, `RazorpayService` |
| `compliance/` | GST/TDS calculation, deadlines, audit readiness | `ComplianceController`, `ComplianceService`, `TdsCalculator` |
| `intelligence/` | Finance metrics, budget vs actual, insights | `FinanceController`, `FinanceService` |
| `grpc/` | gRPC service implementations (5 services) | `*GrpcServiceImpl` |
| `jpa/` | JPA entities + repositories for PostgreSQL | `UserEntity`, `ClientEntity`, `OrganizationEntity`, `InvoiceEntity`, `TransactionEntity`, `*JpaRepository` |
| `queue/` | Redis-based async job queue | `JobProducer`, `JobConsumer`, `WorkerConfig` |
| `documents/` | File upload/retrieval, entity-linked docs | `DocumentController`, `DocumentService` |
| `audit/` | Immutable audit trail for all entity changes | `AuditLogService` |
| `onboarding/` | Org setup wizard, business details | `OnboardingController`, `OnboardingService` |
| `bulk/` | CSV/Excel bulk upload for clients, invoices | `BulkUploadController`, `BulkUploadService` |
| `budget/` | Budget CRUD, category management | `BudgetService` |
| `email/` | Email dispatch via Resend SMTP | `EmailService` |
| `memory/` | Org-level key/value memory store | `OrgMemoryService` |
| `security/` | Team action authorization, security codes | `TeamActionAuthorizationService`, `TeamSecurityCodeService` |
| `shared/` | `OrgContext`, `ApiResponse`, custom exceptions | — |

## API Endpoints

All under `/api/`. Full docs at `/swagger-ui.html` when running.

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Email/password login → JWT |
| POST | `/api/auth/register` | Create account → JWT |
| POST | `/api/auth/google` | Google OAuth2 → JWT |

### Invoices
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/invoices` | List invoices (paginated, filterable) |
| POST | `/api/invoices` | Create invoice |
| GET | `/api/invoices/{id}` | Get invoice details |
| PUT | `/api/invoices/{id}` | Update invoice |
| DELETE | `/api/invoices/{id}` | Delete invoice |
| POST | `/api/invoices/{id}/mark-paid` | Mark invoice as paid |
| POST | `/api/invoices/{id}/send` | Send invoice email |
| POST | `/api/invoices/{id}/pdf` | Generate PDF |
| GET | `/api/invoices/{id}/pdf` | Download PDF |

### Clients
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/clients` | List clients (paginated, searchable) |
| POST | `/api/clients` | Create client |
| GET | `/api/clients/{id}` | Get client details |
| PUT | `/api/clients/{id}` | Update client |
| DELETE | `/api/clients/{id}` | Delete client |

### Transactions
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/transactions` | List transactions (paginated, filterable) |
| POST | `/api/transactions` | Create transaction |
| GET | `/api/transactions/summary` | Financial summary (income, expenses, net) |

### Payments
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/payments/create-order` | Create Razorpay order |
| POST | `/api/payments/verify` | Verify payment signature |
| GET | `/api/payments/{invoiceId}/status` | Check payment status |

### Compliance
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/compliance/status` | Overall compliance health |
| GET | `/api/compliance/gst` | GST details |
| GET | `/api/compliance/gst/deadlines` | Upcoming GST deadlines |
| GET | `/api/compliance/tds` | TDS details |
| GET | `/api/compliance/audit-readiness` | Audit-ready score |

### Intelligence
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/finance-intelligence/metrics` | Dashboard metrics |
| GET | `/api/finance-intelligence/budget-vs-actual` | Budget comparison |
| GET | `/api/finance-intelligence/cash-flow` | Cash flow projection |
| GET | `/api/finance-intelligence/collection-insights` | Collection efficiency |

### Organizations
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/org/create` | Create organization |
| GET | `/api/org/my` | Get current org |
| PUT | `/api/org/my` | Update org details |
| POST | `/api/org/verify` | Verify GST/PAN |

### Users / Teams
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/users` | List team members |
| POST | `/api/users/invite` | Send team invite |
| GET | `/api/users/invite/{token}` | Get invite by token |
| POST | `/api/users/invite/accept` | Accept invite |
| GET | `/api/users/me` | Current user profile |
| PUT | `/api/users/me` | Update profile |

### Other
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/budgets` | List budgets |
| POST | `/api/budgets` | Create budget |
| GET | `/api/documents` | List documents |
| POST | `/api/documents/upload` | Upload document |
| POST | `/api/bulk/upload` | Bulk CSV upload |
| GET | `/api/onboarding/status` | Onboarding progress |
| POST | `/api/onboarding/complete` | Complete onboarding |

## gRPC Services (port 50051)

Defined in `moneyops.proto`, consumed by AI Gateway:

| Service | RPC | Request | Response |
|---------|-----|---------|----------|
| `OrganizationService` | `GetOnboardingStatus` | `OrganizationRequest` | `OnboardingStatus` |
| `OrganizationService` | `GetOrganization` | `OrganizationRequest` | `BusinessOrganizationDto` |
| `ClientService` | `GetClients` | `ClientListRequest` | stream `ClientDto` |
| `ClientService` | `CreateClient` | `CreateClientRequest` | `ClientDto` |
| `InvoiceService` | `GetInvoices` | `InvoiceListRequest` | stream `InvoiceDto` |
| `InvoiceService` | `GetInvoice` | `InvoiceRequest` | `InvoiceDto` |
| `InvoiceService` | `CreateInvoice` | `CreateInvoiceRequest` | `InvoiceDto` |
| `InvoiceService` | `MarkPaid` | `MarkPaidRequest` | `InvoiceDto` |
| `FinanceService` | `GetFinanceMetrics` | `FinanceMetricsRequest` | `FinanceMetricsResponse` |
| `FinanceService` | `GetFinancialSummary` | `FinancialSummaryRequest` | `FinancialSummaryResponse` |
| `NotificationService` | `SendCollectionEmail` | `CollectionEmailRequest` | `CollectionEmailResponse` |

## Auth Flow

```
Frontend                    Backend                         API Gateway
   │                          │                                │
   │──── POST /api/auth/login ──►                              │
   │◄─── { token, userId } ────                              │
   │                          │                                │
   │──── GET /api/invoices ──────────────────► (via Gateway)   │
   │     Authorization: Bearer <token>        │                │
   │                                          │ JwtFilter     │
   │                                          │ validates JWT │
   │                                          │ sets OrgContext│
   │◄─── { invoices[] } ◄────────────────────                │
```

## Event Publishing

An interface-based event system (`IEventPublisher`) with two implementations:

- **KafkaEventPublisher**: Active when `app.events.enabled=true` (uses Kafka topic `moneyops-events`).
- **NoOpEventPublisher**: Default (no-op, events are ignored).

`KafkaEventProducer` is the convenience facade that creates and publishes typed domain events.

## Configuration

Key `application.yml` properties (all overridable via env vars):

| Property | Env Var | Default | Description |
|----------|---------|---------|-------------|
| `server.port` | `BACKEND_PORT` | 8000 | HTTP port |
| `grpc.server.port` | `GRPC_PORT` | 50051 | gRPC port |
| `spring.data.mongodb.uri` | `MONGODB_URI` | — | MongoDB Atlas connection |
| `spring.datasource.url` | `DATABASE_URL` | — | PostgreSQL JDBC URL |
| `jwt.secret` | `JWT_SECRET` | — | HS256 key (min 32 chars) |
| `jwt.expiration` | `JWT_EXPIRATION` | 86400000 | Token TTL in ms |
| `app.events.enabled` | `EVENTS_ENABLED` | false | Enable Kafka events |
| `spring.jpa.hibernate.ddl-auto` | `DDL_AUTO` | validate | Schema management |

## Running

```bash
# Prerequisites: Java 21, running Redis on localhost:6379

# Build
./mvnw clean compile

# Run (dev profile)
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev

# Run (production)
./mvnw spring-boot:run -Dspring-boot.run.profiles=prod

# Tests
./mvnw test

# Package
./mvnw package -DskipTests
java -jar target/moneyops-backend-*.jar --spring.profiles.active=dev
```

## Dependencies

- **MongoDB Atlas** — primary operational database
- **Neon PostgreSQL** — relational data (dual-write target)
- **Redis** — async job queue (`email_worker`, `notification_worker`)
- **Kafka** (optional) — event publishing when `EVENTS_ENABLED=true`
- **Razorpay** — payment gateway (external API)
- **Resend** — transactional email SMTP
- **Google OAuth2** — social login
- **AI Gateway** — consumes gRPC services
