"""Inspect PostgreSQL schema."""
import psycopg2

conn = psycopg2.connect(
    host="ep-plain-haze-anq6dxcn-pooler.c-6.us-east-1.aws.neon.tech",
    dbname="neondb",
    user="neondb_owner",
    password="npg_6qJ2TvBGMwca",
    sslmode="require",
    connect_timeout=10,
)
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = cur.fetchall()
print("Tables:", [t[0] for t in tables])
for t in tables:
    cur.execute(
        f"SELECT column_name, data_type FROM information_schema.columns "
        f"WHERE table_schema='public' AND table_name='{t[0]}' ORDER BY ordinal_position"
    )
    cols = cur.fetchall()
    print(f"  {t[0]}:", [(c[0], c[1]) for c in cols])
conn.close()
