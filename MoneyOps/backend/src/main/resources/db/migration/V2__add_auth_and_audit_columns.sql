-- V2: Add auth and audit columns to support PostgreSQL as primary store
-- Added after migrating data from MongoDB (V1 data not deleted, kept as backup)

-- Add password_hash for local auth (previously only in Mongo)
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_complete BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_by VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS clerk_id VARCHAR(255);

-- Relax constraints for users table (some test users have no org)
ALTER TABLE users ALTER COLUMN org_id DROP NOT NULL;
ALTER TABLE users ALTER COLUMN email DROP NOT NULL;
ALTER TABLE users ALTER COLUMN name DROP NOT NULL;

-- Relax constraints for transactions (some have null client_id)
ALTER TABLE transactions ALTER COLUMN client_id DROP NOT NULL;
ALTER TABLE transactions ALTER COLUMN invoice_id DROP NOT NULL;
ALTER TABLE transactions ALTER COLUMN created_at DROP NOT NULL;

-- Widen ID columns from UUID to VARCHAR(64) for compatibility with Mongo ObjectIds
ALTER TABLE users ALTER COLUMN id TYPE VARCHAR(64);
ALTER TABLE users ALTER COLUMN org_id TYPE VARCHAR(64);
ALTER TABLE organizations ALTER COLUMN id TYPE VARCHAR(64);
ALTER TABLE organizations ALTER COLUMN created_by TYPE VARCHAR(64);
ALTER TABLE organizations ALTER COLUMN updated_by TYPE VARCHAR(64);
ALTER TABLE clients ALTER COLUMN id TYPE VARCHAR(64);
ALTER TABLE clients ALTER COLUMN org_id TYPE VARCHAR(64);
ALTER TABLE clients ALTER COLUMN created_by TYPE VARCHAR(64);
ALTER TABLE clients ALTER COLUMN updated_by TYPE VARCHAR(64);
ALTER TABLE invoices ALTER COLUMN id TYPE VARCHAR(64);
ALTER TABLE invoices ALTER COLUMN org_id TYPE VARCHAR(64);
ALTER TABLE invoices ALTER COLUMN client_id TYPE VARCHAR(64);
ALTER TABLE transactions ALTER COLUMN id TYPE VARCHAR(64);
ALTER TABLE transactions ALTER COLUMN org_id TYPE VARCHAR(64);
ALTER TABLE transactions ALTER COLUMN client_id TYPE VARCHAR(64);
ALTER TABLE transactions ALTER COLUMN invoice_id TYPE VARCHAR(64);

-- Drop foreign key constraints that break with VARCHAR IDs (re-add if needed)
ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_org_id;
ALTER TABLE invoices DROP CONSTRAINT IF EXISTS fk_invoices_org_id;
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS fk_transactions_org_id;
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS fk_transactions_invoice_id;
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS fk_transactions_client_id;
ALTER TABLE clients DROP CONSTRAINT IF EXISTS fk_clients_org_id;

-- Add organizations columns for onboarding fields
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS legal_name VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS trading_name VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS industry VARCHAR(100);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS primary_email VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS primary_phone VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS website VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS registered_address TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS registration_date DATE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS employee_count INTEGER;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS annual_turnover VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS pincode VARCHAR(20);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS gst_filing_frequency VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS pan_number VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS tan_number VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS cin VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS llpin VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS msme_number VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS iec_code VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS professional_tax_reg VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS state_of_registration VARCHAR(100);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);

-- Clients audit columns
ALTER TABLE clients ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

COMMENT ON COLUMN users.password_hash IS 'BCrypt hash for local auth users';
COMMENT ON COLUMN users.onboarding_complete IS 'Whether user completed onboarding flow';
COMMENT ON COLUMN organizations.legal_name IS 'Legal business name from onboarding';
