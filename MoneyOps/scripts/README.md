# MoneyOps Scripts

Utility scripts for data backfill operations and async Redis queue workers.

## Responsibility

These scripts handle maintenance, data migration, and async processing outside the main service loop. Backfill scripts bring legacy data up to current schema standards. Workers consume from Redis queues to send emails and notifications without blocking API responses.

## Directory Structure

```
scripts/
├── backfill_compliance_fields.py          # GST/TDS compliance metadata backfill
├── backfill_voltnest_compliance_fields.py # VaultNest-specific compliance backfill
├── README.md
└── workers/
    ├── email_worker.py                    # Async transactional email dispatcher
    ├── notification_worker.py             # Async push notification dispatcher
    ├── redis_worker.py                    # Redis queue consumer base
    ├── requirements.txt                   # Python dependencies
    ├── Dockerfile.email                   # Docker build for email worker
    └── Dockerfile.notification            # Docker build for notification worker
```

## Workers

The workers are standalone Python processes that consume jobs from Redis queues. They are deployed as separate containers via `docker-compose.yml`.

### Email Worker (`workers/email_worker.py`)

Consumes from the Redis queue `email:jobs`. Each job contains:
- `to` — recipient email address
- `subject` — email subject
- `body` — email body (HTML)
- `type` — email type (invoice, invite, compliance, etc.)

Sends via Resend SMTP (configured through shared env vars).

Start:
```bash
cd scripts/workers
pip install -r requirements.txt
python email_worker.py
```

### Notification Worker (`workers/notification_worker.py`)

Consumes from the Redis queue `notification:jobs`. Each job contains:
- `userId` — target user
- `type` — notification type
- `title` — notification title
- `body` — notification body
- `data` — optional payload

Start:
```bash
cd scripts/workers
python notification_worker.py
```

## Backfill Scripts

### `backfill_compliance_fields.py`

Backfills compliance metadata (GST filing status, TDS deductions, audit readiness scores) for existing records that were created before the compliance module existed.

Run:
```bash
python backfill_compliance_fields.py
```

Dry-run mode:
```bash
python backfill_compliance_fields.py --dry-run
```

### `backfill_voltnest_compliance_fields.py`

Same as above but scoped to VaultNest (a specific tenant organization). Processes only records belonging to that org.

Run:
```bash
python backfill_voltnest_compliance_fields.py
```

## Configuration

Workers read from the same `.env` file as the rest of the stack:

| Env Var | Used By | Description |
|---------|---------|-------------|
| `REDIS_HOST` | All workers | Redis queue host |
| `REDIS_PORT` | All workers | Redis queue port |
| `REDIS_PASSWORD` | All workers | Redis auth |
| `RESEND_API_KEY` | email_worker | Resend SMTP API key |
| `MAIL_HOST` | email_worker | SMTP host |
| `MAIL_PORT` | email_worker | SMTP port |
| `EMAIL_FROM_ADDRESS` | email_worker | Sender email |
| `EMAIL_FROM_NAME` | email_worker | Sender name |

## Docker (via docker-compose)

Workers are defined in the root `docker-compose.yml` and start automatically when the full stack is deployed:

```bash
docker compose up -d email-worker notification-worker
```

Each worker has its own Dockerfile for minimal image size.
