"""
MoneyOps — MongoDB ↔ PostgreSQL Reconciliation Script

Compares all records across 5 dual-written entities and reports mismatches.
"""
import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv

import pymongo
import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Entity mapping: Mongo collection → Postgres table, plus how to match records
# ---------------------------------------------------------------------------
ENTITIES = [
    {
        "name": "users",
        "mongo_collection": "users",
        "pg_table": "users",
        "match_key": "email",               # match by email since IDs differ in format
        "mongo_fields": ["_id", "email", "name", "orgId", "role", "status", "createdAt", "updatedAt"],
        "pg_fields": ["id", "email", "name", "org_id", "role", "created_at", "updated_at"],
    },
    {
        "name": "organizations",
        "mongo_collection": "business_organizations",
        "pg_table": "organizations",
        "match_key": "legalName",            # match by legal name
        "mongo_fields": ["_id", "legalName", "tradingName", "primaryEmail", "createdBy", "createdAt", "updatedAt"],
        "pg_fields": ["id", "legal_name", "trading_name", "primary_email", "created_by", "created_at", "updated_at"],
    },
    {
        "name": "clients",
        "mongo_collection": "clients",
        "pg_table": "clients",
        "match_key": "email",               # match by email
        "mongo_fields": ["_id", "email", "name", "company", "orgId", "status", "createdAt"],
        "pg_fields": ["id", "email", "name", "company", "org_id", "status", "created_at"],
    },
    {
        "name": "invoices",
        "mongo_collection": "invoices",
        "pg_table": "invoices",
        "match_key": "invoiceNumber",       # match by invoice number
        "mongo_fields": ["_id", "invoiceNumber", "clientId", "orgId", "status", "totalAmount", "issueDate", "dueDate", "createdAt"],
        "pg_fields": ["id", "invoice_number", "client_id", "org_id", "status", "total_amount", "issue_date", "due_date", "created_at"],
    },
    {
        "name": "transactions",
        "mongo_collection": "transactions",
        "pg_table": "transactions",
        "match_key": "description",         # weak match — fallback to id
        "mongo_fields": ["_id", "description", "amount", "type", "orgId", "invoiceId", "date", "createdAt"],
        "pg_fields": ["id", "description", "amount", "type", "org_id", "invoice_id", "date", "created_at"],
    },
]

FIELD_MAP_CACHE = {}

def build_field_map(mongo_fields, pg_fields):
    """Build a map from Mongo field name -> Postgres field name for the same logical field."""
    # Manual mapping based on known field correspondences
    manual = {
        "_id": "id",
        "orgId": "org_id",
        "clientId": "client_id",
        "invoiceId": "invoice_id",
        "totalAmount": "total_amount",
        "issueDate": "issue_date",
        "dueDate": "due_date",
        "createdAt": "created_at",
        "updatedAt": "updated_at",
        "legalName": "legal_name",
        "tradingName": "trading_name",
        "primaryEmail": "primary_email",
        "createdBy": "created_by",
        "registrationDate": "registration_date",
        "employeeCount": "employee_count",
        "numberOfEmployees": "number_of_employees",
        "primaryPhone": "primary_phone",
        "registeredAddress": "registered_address",
        "gstRegistered": "gst_registered",
        "gstFilingFrequency": "gst_filing_frequency",
        "panNumber": "pan_number",
        "tanNumber": "tan_number",
        "msmeNumber": "msme_number",
        "iecCode": "iec_code",
        "llpin": "llpin",
        "professionalTaxReg": "professional_tax_reg",
        "stateOfRegistration": "state_of_registration",
        "cin": "cin",
        "businessType": "business_type",
        "annualTurnover": "annual_turnover",
        "primaryActivity": "primary_activity",
        "targetMarket": "target_market",
        "keyProducts": "key_products",
        "currentChallenges": "current_challenges",
        "accountingMethod": "accounting_method",
        "fyStartMonth": "fy_start_month",
        "preferredLanguage": "preferred_language",
        "teamActionCodeHash": "team_action_code_hash",
        "invoiceNumber": "invoice_number",
        "paymentTerms": "payment_terms",
        "recurringInvoiceId": "recurring_invoice_id",
    }
    return manual


def normalize(val):
    """Normalize a value for comparison."""
    from bson import Binary, ObjectId
    if isinstance(val, Binary):
        return str(val)
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, ObjectId):
        return str(val)
    if val is None:
        return None
    return val


def fetch_mongo_all(mongo_db, collection_name, fields):
    """Fetch all documents from a Mongo collection, returning only requested fields."""
    from bson import ObjectId
    projection = {f: 1 for f in fields if f != "_id"}
    projection["_id"] = 1
    docs = []
    for doc in mongo_db[collection_name].find({}, projection):
        row = {}
        for f in fields:
            if f == "_id":
                val = doc.get("_id")
                row["_id"] = str(val) if isinstance(val, ObjectId) else str(val) if val else ""
            else:
                row[f] = normalize(doc.get(f))
        docs.append(row)
    return docs


def fetch_pg_all(pg_conn, table_name, fields):
    """Fetch all records from a Postgres table."""
    cols = ", ".join(fields)
    sql = f"SELECT {cols} FROM {table_name}"
    with pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        rows = []
        for row in cur.fetchall():
            r = {}
            for f in fields:
                val = row[f]
                if isinstance(val, datetime):
                    val = val.isoformat()
                if val is None:
                    val = None
                r[f] = val
            rows.append(r)
        return rows


def reconcile_entity(name, mongo_collection, pg_table, match_key, mongo_fields, pg_fields, mongo_db, pg_conn):
    """Compare a single entity across Mongo and Postgres."""
    print("")
    print("="*60)
    print(f"RECONCILING: {name}")
    print(f"  Mongo: {mongo_collection}  |  Postgres: {pg_table}")
    print(f"  Match key: {match_key}")
    print("="*60)

    mongo_docs = fetch_mongo_all(mongo_db, mongo_collection, mongo_fields)
    pg_rows = fetch_pg_all(pg_conn, pg_table, pg_fields)

    print(f"  Mongo count: {len(mongo_docs)}")
    print(f"  Postgres count: {len(pg_rows)}")

    # Index by match key
    mongo_by_key = {}
    for doc in mongo_docs:
        key = normalize(doc.get(match_key, ""))
        if key:
            mongo_by_key[key] = doc

    pg_by_key = {}
    for row in pg_rows:
        key = normalize(row.get(match_key, ""))
        if key:
            pg_by_key[key] = row

    mongo_keys = set(mongo_by_key.keys())
    pg_keys = set(pg_by_key.keys())

    in_both = mongo_keys & pg_keys
    only_mongo = mongo_keys - pg_keys
    only_pg = pg_keys - mongo_keys

    print(f"  In both stores: {len(in_both)}")
    print(f"  Only in Mongo: {len(only_mongo)}")
    print(f"  Only in Postgres: {len(only_pg)}")

    field_map = build_field_map(mongo_fields, pg_fields)
    conflicts = []
    matches = 0

    for key in sorted(in_both):
        mdoc = mongo_by_key[key]
        prow = pg_by_key[key]
        diffs = []

        for mf in mongo_fields:
            if mf == "_id":
                continue
            pf = field_map.get(mf)
            if not pf or pf not in prow:
                continue

            mv = normalize(mdoc.get(mf))
            pv = normalize(prow.get(pf))
            if str(mv) != str(pv):
                diffs.append((mf, pf, mv, pv))

        if diffs:
            conflicts.append({"key": key, "mongo_id": mdoc.get("_id"), "pg_id": prow.get("id"), "diffs": diffs})
        else:
            matches += 1

    print(f"  Exact matches: {matches}")
    print(f"  With differences: {len(conflicts)}")

    if only_mongo:
        print(f"\n  [!] Records MISSING from Postgres (only in Mongo):")
        for key in sorted(only_mongo)[:10]:
            doc = mongo_by_key[key]
            print(f"      {key}  (Mongo _id: {doc.get('_id')})")

    if only_pg:
        print(f"\n  [!] Records MISSING from Mongo (only in Postgres):")
        for key in sorted(only_pg)[:10]:
            row = pg_by_key[key]
            print(f"      {key}  (PG id: {row.get('id')})")

    if conflicts:
        print(f"\n  [!] Records with FIELD DIFFERENCES:")
        for c in conflicts[:10]:
            print(f"      Key: {c['key']}  (Mongo: {c['mongo_id']} | PG: {c['pg_id']})")
            for mf, pf, mv, pv in c["diffs"][:5]:
                print(f"        {mf} -> Mongo: {mv}  |  Postgres: {pv}")

    summary = {
        "name": name,
        "mongo_count": len(mongo_docs),
        "pg_count": len(pg_rows),
        "in_both": len(in_both),
        "only_mongo": len(only_mongo),
        "only_pg": len(only_pg),
        "matches": matches,
        "conflicts": len(conflicts),
    }
    return summary


def main():
    parser = argparse.ArgumentParser(description="Reconcile data between MongoDB and PostgreSQL")
    parser.add_argument("--env-file", default="../MoneyOps/.env", help="Path to .env file")
    parser.add_argument("--entity", choices=[e["name"] for e in ENTITIES] + ["all"], default="all")
    args = parser.parse_args()

    # Load environment
    env_path = os.path.join(os.path.dirname(__file__), args.env_file)
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        print(f"Warning: .env not found at {env_path}, using OS environment")

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/moneyops")
    pg_url = os.getenv("DATABASE_URL", "")
    pg_user = os.getenv("DB_USERNAME", "neondb_owner")
    pg_pass = os.getenv("DB_PASSWORD", "")

    # Parse Neon connection
    # DATABASE_URL=jdbc:postgresql://host/db?params
    pg_host = "ep-plain-haze-anq6dxcn-pooler.c-6.us-east-1.aws.neon.tech"
    pg_dbname = "neondb"
    if pg_url:
        pg_url = pg_url.replace("jdbc:", "")
        parts = pg_url.replace("postgresql://", "").split("/")
        if len(parts) >= 2:
            pg_host = parts[0].split("?")[0]
            pg_dbname = parts[1].split("?")[0]

    print(f"MongoDB URI: {mongo_uri[:50]}...")
    print(f"PostgreSQL: {pg_host}/{pg_dbname}")

    # Connect
    mongo_client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    mongo_db = mongo_client.get_database()

    pg_conn = psycopg2.connect(
        host=pg_host,
        dbname=pg_dbname,
        user=pg_user,
        password=pg_pass,
        sslmode="require",
        connect_timeout=10,
    )

    summaries = []
    entities = [e for e in ENTITIES if args.entity == "all" or e["name"] == args.entity]
    for ent in entities:
        summary = reconcile_entity(
            ent["name"],
            ent["mongo_collection"],
            ent["pg_table"],
            ent["match_key"],
            ent["mongo_fields"],
            ent["pg_fields"],
            mongo_db,
            pg_conn,
        )
        summaries.append(summary)

    # Overall report
    print("")
    print("="*60)
    print("RECONCILIATION SUMMARY")
    print("="*60)
    print(f"{'Entity':<20} {'Mongo':>7} {'PG':>7} {'Both':>7} {'Match':>7} {'Conflict':>9} {'OnlyM':>7} {'OnlyP':>7}")
    print("-"*20 + " " + "-"*7 + " " + "-"*7 + " " + "-"*7 + " " + "-"*7 + " " + "-"*9 + " " + "-"*7 + " " + "-"*7)
    total_m = total_p = total_both = total_match = total_conflict = total_om = total_op = 0
    for s in summaries:
        print(f"{s['name']:<20} {s['mongo_count']:>7} {s['pg_count']:>7} {s['in_both']:>7} {s['matches']:>7} {s['conflicts']:>9} {s['only_mongo']:>7} {s['only_pg']:>7}")
        total_m += s["mongo_count"]
        total_p += s["pg_count"]
        total_both += s["in_both"]
        total_match += s["matches"]
        total_conflict += s["conflicts"]
        total_om += s["only_mongo"]
        total_op += s["only_pg"]
    print(f"{'-'*20} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*9} {'-'*7} {'-'*7}")
    print(f"{'TOTAL':<20} {total_m:>7} {total_p:>7} {total_both:>7} {total_match:>7} {total_conflict:>9} {total_om:>7} {total_op:>7}")

    mongo_client.close()
    pg_conn.close()

    if total_conflict > 0 or total_om > 0 or total_op > 0:
        print(f"\n[!] DISCREPANCIES FOUND! Reconciliation needed before migration.")
        return 1
    else:
        print(f"\n[OK] All records consistent. Ready for migration.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
