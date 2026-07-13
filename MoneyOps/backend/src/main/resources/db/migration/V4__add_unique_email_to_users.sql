-- V4__add_unique_email_to_users.sql
CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique_idx ON users (email) WHERE deleted_at IS NULL;
