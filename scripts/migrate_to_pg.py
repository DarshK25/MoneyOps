"""
MoneyOps - MongoDB -> PostgreSQL One-Way Migration

Converts all Mongo ObjectId IDs to deterministic UUIDs using the SAME
function as StringToUuidConverter.toPgUuid(), ensuring FK references
resolve correctly.

Migration order (parents before children):
  organizations -> users -> clients -> invoices -> transactions

After migration, verify row counts match and FK joins resolve.
"""
import os
import sys
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

import pymongo
import psycopg2
import psycopg2.extras

env_path = os.path.join(os.path.dirname(__file__), "..", "MoneyOps", ".env")
load_dotenv(dotenv_path=env_path, override=True)

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/moneyops")
PG_CONFIG = {
    "host": "ep-plain-haze-anq6dxcn-pooler.c-6.us-east-1.aws.neon.tech",
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_6qJ2TvBGMwca",
    "sslmode": "require",
    "connect_timeout": 15,
}

BATCH = 100


# ---- deterministic UUID conversion (mirrors StringToUuidConverter) ----
def truncate_tables(conn, tables):
    """Truncate all tables before clean migration."""
    cur = conn.cursor()
    for t in tables:
        cur.execute(f"TRUNCATE TABLE {t} CASCADE")
        print(f"  Truncated {t}")
    conn.commit()
    cur.close()


def to_pg_uuid(mongo_id):
    """
    Deterministic UUID from any Mongo ID string.
    Exactly replicates Java's UUID.nameUUIDFromBytes():
      MD5 hash of raw bytes, then bit-manipulate version (3) and variant (RFC 4122).
    """
    if mongo_id is None:
        return None
    if len(mongo_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in mongo_id):
        import hashlib
        md5 = hashlib.md5(("moneyops:" + mongo_id).encode("utf-8")).digest()
        ba = bytearray(md5)
        ba[6] = (ba[6] & 0x0f) | 0x30   # set version to 3
        ba[8] = (ba[8] & 0x3f) | 0x80   # set IETF variant
        return str(uuid.UUID(bytes=bytes(ba)))
    return mongo_id  # already a UUID string


def dt_or_none(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    return None


def now_utc():
    return datetime.utcnow()


# ---- helpers ----
def get_pg_columns(conn, table):
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, is_nullable, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
    """, (table,))
    cols = {r[0]: {"nullable": r[1], "type": r[2]} for r in cur.fetchall()}
    cur.close()
    return cols


def nullify_with_default(col_info, val):
    """Return a default for NOT NULL columns when value is None."""
    if val is not None:
        return val
    # is_nullable in information_schema returns 'YES' or 'NO'
    if col_info["nullable"] == 'NO':
        # Try sensible defaults
        t = col_info["type"]
        if t in ("timestamp", "timestamptz", "date"):
            return now_utc()
        if t in ("numeric", "float8", "int4", "int8"):
            return 0
        if t == "bool" or t == "boolean":
            return False
        if t == "jsonb":
            return "{}"
        return ""
    return None


def insert_batch(conn, table, rows, col_map, id_fn=None, fk_fn=None):
    """
    Insert rows with deterministic UUID conversion.
    col_map: {pg_col: (mongo_key, [transform_fn])}
    id_fn(field, mongo_id) -> UUID string for ID fields
    fk_fn(field, fk_val) -> UUID string for FK fields
    """
    existing = get_pg_columns(conn, table)
    valid_map = {pg: info for pg, info in col_map.items() if pg in existing}
    pg_cols = list(valid_map.keys())
    if not pg_cols:
        print(f"  WARNING: no valid columns for {table}")
        return 0

    placeholders = ", ".join(["%s"] * len(pg_cols))
    col_list = ", ".join(pg_cols)
    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"

    written = 0
    cur = conn.cursor()
    for row in rows:
        try:
            cur.execute("SAVEPOINT sp")
            vals = []
            for pg_col in pg_cols:
                mkey, transform = valid_map[pg_col]
                raw = row.get(mkey)
                val = transform(raw) if transform else raw
                val = nullify_with_default(existing[pg_col], val)
                vals.append(val)
            cur.execute(sql, vals)
            conn.commit()
            written += 1
            if written % BATCH == 0:
                print(f"  ... {written}")
        except Exception as e:
            try:
                cur.execute("ROLLBACK TO SAVEPOINT sp")
                conn.commit()
            except Exception:
                pass
            print(f"  SKIP {table} row {row.get('_id', '?')}: {e}")
    cur.close()
    return written


# ---- entity migrations ----
def migrate_organizations(mongo_db, conn):
    print("\n--- Migrating organizations ---")
    rows = list(mongo_db["business_organizations"].find({}))
    print(f"  Found {len(rows)} in MongoDB")
    if not rows:
        return 0

    def to_id(v): return to_pg_uuid(str(v)) if v else None
    def to_json(v): return json.dumps(v) if v else "{}"
    def to_bool(v): return bool(v) if v is not None else False
    def to_int(v): return int(v) if v else None
    def to_date(v): return dt_or_none(v)

    col_map = [
        ("id", lambda r: to_pg_uuid(str(r["_id"]))),
        ("name", lambda r: r.get("name") or r.get("legalName")),
        ("legal_name", lambda r: r.get("legalName")),
        ("trading_name", lambda r: r.get("tradingName")),
        ("business_type", lambda r: r.get("businessType")),
        ("industry", lambda r: r.get("industry")),
        ("primary_email", lambda r: r.get("primaryEmail")),
        ("primary_phone", lambda r: r.get("primaryPhone")),
        ("website", lambda r: r.get("website")),
        ("registered_address", lambda r: r.get("registeredAddress")),
        ("registration_date", lambda r: dt_or_none(r.get("registrationDate"))),
        ("employee_count", lambda r: r.get("employeeCount") or r.get("numberOfEmployees")),
        ("annual_turnover", lambda r: r.get("annualTurnover")),
        ("pincode", lambda r: r.get("pincode")),
        ("gst_registered", lambda r: to_bool(r.get("gstRegistered"))),
        ("gstin", lambda r: r.get("gstin") or None),
        ("gst_filing_frequency", lambda r: r.get("gstFilingFrequency")),
        ("pan_number", lambda r: r.get("panNumber")),
        ("tan_number", lambda r: r.get("tanNumber")),
        ("cin", lambda r: r.get("cin")),
        ("llpin", lambda r: r.get("llpin")),
        ("msme_number", lambda r: r.get("msmeNumber")),
        ("iec_code", lambda r: r.get("iecCode")),
        ("professional_tax_reg", lambda r: r.get("professionalTaxReg")),
        ("state_of_registration", lambda r: r.get("stateOfRegistration")),
        ("created_by", lambda r: to_id(r.get("createdBy"))),
        ("updated_by", lambda r: to_id(r.get("updatedBy"))),
        ("created_at", lambda r: dt_or_none(r.get("createdAt")) or now_utc()),
        ("updated_at", lambda r: dt_or_none(r.get("updatedAt"))),
        ("deleted_at", lambda r: dt_or_none(r.get("deletedAt"))),
        ("settings", lambda r: to_json(r.get("settings"))),
    ]

    existing = get_pg_columns(conn, "organizations")
    valid = [(col, fn) for col, fn in col_map if col in existing]
    pg_cols = [c for c, _ in valid]
    placeholders = ", ".join(["%s"] * len(pg_cols))
    col_list = ", ".join(pg_cols)
    sql = f"INSERT INTO organizations ({col_list}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"

    written = 0
    cur = conn.cursor()
    for r in rows:
        try:
            cur.execute("SAVEPOINT sp")
            vals = [nullify_with_default(existing[c], fn(r)) for c, fn in valid]
            cur.execute(sql, vals)
            conn.commit()
            written += 1
            if written % BATCH == 0:
                print(f"  ... {written}")
        except Exception as e:
            try:
                cur.execute("ROLLBACK TO SAVEPOINT sp")
                conn.commit()
            except Exception:
                pass
            print(f"  SKIP org {r.get('legalName', '?')}: {e}")
    cur.close()
    print(f"  TOTAL: {written}")
    return written


def migrate_users(mongo_db, conn):
    print("\n--- Migrating users ---")
    rows = list(mongo_db["users"].find({}))
    print(f"  Found {len(rows)} in MongoDB")
    if not rows:
        return 0

    def to_id(v): return to_pg_uuid(str(v)) if v else None

    col_map = [
        ("id", lambda r: to_pg_uuid(str(r["_id"]))),
        ("email", lambda r: r.get("email")),
        ("name", lambda r: r.get("name")),
        ("org_id", lambda r: to_id(r.get("orgId"))),
        ("role", lambda r: r.get("role", "STAFF")),
        ("status", lambda r: r.get("status", "ACTIVE")),
        ("phone", lambda r: r.get("phone")),
        ("onboarding_complete", lambda r: r.get("onboardingComplete", False)),
        ("last_login_at", lambda r: dt_or_none(r.get("lastLoginAt"))),
        ("created_by", lambda r: r.get("createdBy")),
        ("updated_by", lambda r: r.get("updatedBy")),
        ("created_at", lambda r: dt_or_none(r.get("createdAt")) or now_utc()),
        ("updated_at", lambda r: dt_or_none(r.get("updatedAt"))),
        ("deleted_at", lambda r: dt_or_none(r.get("deletedAt"))),
        ("clerk_user_id", lambda r: str(r.get("_id"))),
        ("clerk_id", lambda r: None),
        ("preferences", lambda r: json.dumps(r.get("preferences")) if r.get("preferences") else "{}"),
    ]

    existing = get_pg_columns(conn, "users")
    valid = [(col, fn) for col, fn in col_map if col in existing]
    pg_cols = [c for c, _ in valid]
    placeholders = ", ".join(["%s"] * len(pg_cols))
    col_list = ", ".join(pg_cols)
    sql = f"INSERT INTO users ({col_list}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"

    written = 0
    cur = conn.cursor()
    for r in rows:
        try:
            cur.execute("SAVEPOINT sp")
            vals = [nullify_with_default(existing[c], fn(r)) for c, fn in valid]
            cur.execute(sql, vals)
            conn.commit()
            written += 1
            if written % BATCH == 0:
                print(f"  ... {written}")
        except Exception as e:
            try:
                cur.execute("ROLLBACK TO SAVEPOINT sp")
                conn.commit()
            except Exception:
                pass
            print(f"  SKIP user {r.get('email', '?')}: {e}")
    cur.close()
    print(f"  TOTAL: {written}")
    return written


def migrate_clients(mongo_db, conn):
    print("\n--- Migrating clients ---")
    rows = list(mongo_db["clients"].find({}))
    print(f"  Found {len(rows)} in MongoDB")
    if not rows:
        return 0

    def to_id(v): return to_pg_uuid(str(v)) if v else None

    col_map = [
        ("id", lambda r: to_pg_uuid(str(r["_id"]))),
        ("name", lambda r: r.get("name")),
        ("email", lambda r: r.get("email")),
        ("company", lambda r: r.get("company")),
        ("phone_number", lambda r: r.get("phoneNumber")),
        ("gstin", lambda r: r.get("gstin")),
        ("notes", lambda r: r.get("notes")),
        ("currency", lambda r: r.get("currency", "INR")),
        ("status", lambda r: r.get("status", "ACTIVE")),
        ("org_id", lambda r: to_id(r.get("orgId"))),
        ("created_by", lambda r: r.get("createdBy")),
        ("updated_by", lambda r: r.get("updatedBy")),
        ("created_at", lambda r: dt_or_none(r.get("createdAt"))),
        ("updated_at", lambda r: dt_or_none(r.get("updatedAt"))),
        ("deleted_at", lambda r: dt_or_none(r.get("deletedAt"))),
    ]

    existing = get_pg_columns(conn, "clients")
    valid = [(col, fn) for col, fn in col_map if col in existing]
    pg_cols = [c for c, _ in valid]
    placeholders = ", ".join(["%s"] * len(pg_cols))
    col_list = ", ".join(pg_cols)
    sql = f"INSERT INTO clients ({col_list}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"

    written = 0
    cur = conn.cursor()
    for r in rows:
        try:
            cur.execute("SAVEPOINT sp")
            vals = [nullify_with_default(existing[c], fn(r)) for c, fn in valid]
            cur.execute(sql, vals)
            conn.commit()
            written += 1
            if written % BATCH == 0:
                print(f"  ... {written}")
        except Exception as e:
            try:
                cur.execute("ROLLBACK TO SAVEPOINT sp")
                conn.commit()
            except Exception:
                pass
            print(f"  SKIP client {r.get('email', '?')}: {e}")
    cur.close()
    print(f"  TOTAL: {written}")
    return written


def migrate_invoices(mongo_db, conn):
    print("\n--- Migrating invoices ---")
    rows = list(mongo_db["invoices"].find({}))
    print(f"  Found {len(rows)} in MongoDB")
    if not rows:
        return 0

    def to_id(v): return to_pg_uuid(str(v)) if v else None

    col_map = [
        ("id", lambda r: to_pg_uuid(str(r["_id"]))),
        ("invoice_number", lambda r: r.get("invoiceNumber")),
        ("client_id", lambda r: to_id(r.get("clientId"))),
        ("org_id", lambda r: to_id(r.get("orgId"))),
        ("status", lambda r: r.get("status", "DRAFT")),
        ("total_amount", lambda r: float(r.get("totalAmount") or 0) if r.get("totalAmount") else None),
        ("created_at", lambda r: dt_or_none(r.get("createdAt"))),
    ]

    existing = get_pg_columns(conn, "invoices")
    valid = [(col, fn) for col, fn in col_map if col in existing]
    pg_cols = [c for c, _ in valid]
    placeholders = ", ".join(["%s"] * len(pg_cols))
    col_list = ", ".join(pg_cols)
    sql = f"INSERT INTO invoices ({col_list}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"

    written = 0
    cur = conn.cursor()
    for r in rows:
        try:
            cur.execute("SAVEPOINT sp")
            vals = [nullify_with_default(existing[c], fn(r)) for c, fn in valid]
            cur.execute(sql, vals)
            conn.commit()
            written += 1
            if written % BATCH == 0:
                print(f"  ... {written}")
        except Exception as e:
            try:
                cur.execute("ROLLBACK TO SAVEPOINT sp")
                conn.commit()
            except Exception:
                pass
            print(f"  SKIP invoice {r.get('invoiceNumber', '?')}: {e}")
    cur.close()
    print(f"  TOTAL: {written}")
    return written


def migrate_transactions(mongo_db, conn):
    print("\n--- Migrating transactions ---")
    rows = list(mongo_db["transactions"].find({}))
    print(f"  Found {len(rows)} in MongoDB")
    if not rows:
        return 0

    def to_id(v): return to_pg_uuid(str(v)) if v else None

    col_map = [
        ("id", lambda r: to_pg_uuid(str(r["_id"]))),
        ("type", lambda r: r.get("type")),
        ("amount", lambda r: float(r.get("amount", 0) or 0)),
        ("transaction_date", lambda r: dt_or_none(r.get("date") or r.get("transactionDate"))),
        ("org_id", lambda r: to_id(r.get("orgId"))),
        ("client_id", lambda r: to_id(r.get("clientId"))),
        ("invoice_id", lambda r: to_id(r.get("invoiceId"))),
        ("created_at", lambda r: dt_or_none(r.get("createdAt"))),
    ]

    existing = get_pg_columns(conn, "transactions")
    valid = [(col, fn) for col, fn in col_map if col in existing]
    pg_cols = [c for c, _ in valid]
    placeholders = ", ".join(["%s"] * len(pg_cols))
    col_list = ", ".join(pg_cols)
    sql = f"INSERT INTO transactions ({col_list}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"

    written = 0
    cur = conn.cursor()
    for r in rows:
        try:
            cur.execute("SAVEPOINT sp")
            vals = [nullify_with_default(existing[c], fn(r)) for c, fn in valid]
            cur.execute(sql, vals)
            conn.commit()
            written += 1
            if written % BATCH == 0:
                print(f"  ... {written}")
        except Exception as e:
            try:
                cur.execute("ROLLBACK TO SAVEPOINT sp")
                conn.commit()
            except Exception:
                pass
            print(f"  SKIP txn {r.get('_id', '?')}: {e}")
    cur.close()
    print(f"  TOTAL: {written}")
    return written


def verify(mongo_db, conn):
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    pairs = [
        ("organizations", "business_organizations"),
        ("users", "users"),
        ("clients", "clients"),
        ("invoices", "invoices"),
        ("transactions", "transactions"),
    ]
    cur = conn.cursor()
    all_ok = True
    for pg_table, mongo_col in pairs:
        mc = mongo_db[mongo_col].count_documents({})
        cur.execute(f"SELECT COUNT(*) FROM {pg_table}")
        pc = cur.fetchone()[0]
        ok = mc == pc
        if not ok:
            all_ok = False
        print(f"  {pg_table:<20} Mongo: {mc:<5} PG: {pc:<5}  [{'OK' if ok else 'MISMATCH'}]")
    cur.close()
    if all_ok:
        print("\n[OK] All counts match.")
    else:
        print("\n[!] Some counts mismatch. See errors above.")
    return all_ok


def main():
    print("=" * 60)
    print("MongoDB -> PostgreSQL Migration")
    print("=" * 60)

    mc = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=15000)
    md = mc.get_database()
    print(f"MongoDB OK")

    conn = psycopg2.connect(**PG_CONFIG)
    print(f"PostgreSQL OK: {PG_CONFIG['host']}")

    # Clean slate
    print("\n" + "=" * 60)
    print("STEP 0: Truncate tables for clean migration")
    print("=" * 60)
    truncate_tables(conn, ["transactions", "invoices", "clients", "users", "organizations"])

    # Make org_id nullable for test users that have no org
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ALTER COLUMN org_id DROP NOT NULL")
    cur.execute("ALTER TABLE transactions ALTER COLUMN client_id DROP NOT NULL")
    cur.execute("ALTER TABLE transactions ALTER COLUMN invoice_id DROP NOT NULL")
    cur.execute("ALTER TABLE transactions ALTER COLUMN created_at DROP NOT NULL")
    conn.commit()
    cur.close()
    print("  Made users.org_id, transactions.client_id, transactions.invoice_id nullable")

    migrate_organizations(md, conn)
    migrate_users(md, conn)
    migrate_clients(md, conn)
    migrate_invoices(md, conn)
    migrate_transactions(md, conn)

    ok = verify(md, conn)
    mc.close()
    conn.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
