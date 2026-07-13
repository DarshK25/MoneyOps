-- V3: Finalize PostgreSQL as sole store for relational entities

-- Rename migration bridge column
ALTER TABLE users RENAME COLUMN clerk_user_id TO legacy_mongo_id;

-- Unique email for active users (prevents duplicate OAuth accounts)
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_active
    ON users (LOWER(email)) WHERE deleted_at IS NULL AND email IS NOT NULL;

-- JSONB document store for rich fields (single write path, no Mongo mirror)
ALTER TABLE clients ADD COLUMN IF NOT EXISTS document_data JSONB DEFAULT '{}';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS document_data JSONB DEFAULT '{}';
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS document_data JSONB DEFAULT '{}';

-- Queryable invoice columns (synced from document on write)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS due_date DATE;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS issue_date DATE;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- Transaction query columns
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'INR';

-- Organization team security (also stored in settings JSONB from onboarding)
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS team_action_code_hash VARCHAR(255);

COMMENT ON COLUMN clients.document_data IS 'Full client document JSON — sole source for extended fields';
COMMENT ON COLUMN invoices.document_data IS 'Full invoice document JSON — sole source for line items etc';
COMMENT ON COLUMN transactions.document_data IS 'Full transaction document JSON — sole source for compliance fields';
COMMENT ON COLUMN users.legacy_mongo_id IS 'Original Mongo ObjectId for audit traceability only';
