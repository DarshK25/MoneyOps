-- V5: Add missing organization columns (JPA entity vs DB mismatch)
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS verification_tier VARCHAR(50) DEFAULT 'UNVERIFIED';
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS gst_registered BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN organizations.verification_tier IS 'Business verification level (UNVERIFIED, BASIC, VERIFIED, TRUSTED)';
COMMENT ON COLUMN organizations.gst_registered IS 'Whether the business is registered for GST';
