-- MoneyOps Initial Schema Migration
-- Creates tables for PostgreSQL migration from MongoDB

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    business_type VARCHAR(100),
    gstin VARCHAR(50) UNIQUE,
    pan VARCHAR(50) UNIQUE,
    settings JSONB,
    created_by VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for organizations
CREATE INDEX IF NOT EXISTS idx_organizations_gstin ON organizations(gstin) WHERE gstin IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_organizations_pan ON organizations(pan) WHERE pan IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations(name);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clerk_user_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    org_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL,
    preferences JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_org_id FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE
);

-- Create indexes for users
CREATE INDEX IF NOT EXISTS idx_users_clerk_user_id ON users(clerk_user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_org_role ON users(org_id, role);

-- Create invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL,
    client_id UUID NOT NULL,
    invoice_number VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(19, 4) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_invoices_org_id FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT uk_invoices_org_invoice_number UNIQUE (org_id, invoice_number)
);

-- Create indexes for invoices
CREATE INDEX IF NOT EXISTS idx_invoices_org_id ON invoices(org_id);
CREATE INDEX IF NOT EXISTS idx_invoices_client_id ON invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_org_status ON invoices(org_id, status);
CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON invoices(created_at);
CREATE INDEX IF NOT EXISTS idx_invoices_org_created ON invoices(org_id, created_at DESC);

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL,
    invoice_id UUID,
    client_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    amount DECIMAL(19, 4) NOT NULL DEFAULT 0,
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transactions_org_id FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_transactions_invoice_id FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE SET NULL,
    CONSTRAINT fk_transactions_client_id FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for transactions
CREATE INDEX IF NOT EXISTS idx_transactions_org_id ON transactions(org_id);
CREATE INDEX IF NOT EXISTS idx_transactions_invoice_id ON transactions(invoice_id) WHERE invoice_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_client_id ON transactions(client_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_org_type ON transactions(org_id, type);
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_org_date ON transactions(org_id, transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_org_type_date ON transactions(org_id, type, transaction_date DESC);

-- Create clients table
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    gstin VARCHAR(50),
    email VARCHAR(255),
    phone_number VARCHAR(50),
    company VARCHAR(255),
    currency VARCHAR(10) DEFAULT 'INR',
    notes TEXT,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    CONSTRAINT fk_clients_org_id FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_clients_org_id ON clients(org_id);
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
CREATE INDEX IF NOT EXISTS idx_clients_gstin ON clients(gstin) WHERE gstin IS NOT NULL;

-- Create audit_logs table for tracking migration operations
CREATE TABLE IF NOT EXISTS migration_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    mongo_id VARCHAR(255),
    postgres_id UUID,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit logs
CREATE INDEX IF NOT EXISTS idx_migration_audit_operation ON migration_audit_logs(operation);
CREATE INDEX IF NOT EXISTS idx_migration_audit_entity_type ON migration_audit_logs(entity_type);
CREATE INDEX IF NOT EXISTS idx_migration_audit_status ON migration_audit_logs(status);
CREATE INDEX IF NOT EXISTS idx_migration_audit_created_at ON migration_audit_logs(created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE organizations IS 'Stores organization/business entity data migrated from MongoDB business_organizations collection';
COMMENT ON TABLE users IS 'Stores user data migrated from MongoDB users collection';
COMMENT ON TABLE invoices IS 'Stores invoice data migrated from MongoDB invoices collection';
COMMENT ON TABLE transactions IS 'Stores transaction data migrated from MongoDB transactions collection';
COMMENT ON TABLE migration_audit_logs IS 'Tracks all migration operations for audit and resumability';

COMMENT ON COLUMN users.clerk_user_id IS 'Clerk authentication user ID';
COMMENT ON COLUMN users.preferences IS 'JSONB column storing user preferences and metadata';
COMMENT ON COLUMN organizations.settings IS 'JSONB column storing organization settings and metadata';
COMMENT ON COLUMN invoices.total_amount IS 'Total invoice amount including taxes';
COMMENT ON COLUMN transactions.transaction_date IS 'Date when the transaction occurred';

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
