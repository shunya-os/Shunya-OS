"""Create the m6_media_assets table."""
import os
import sys
import psycopg2

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not set", file=sys.stderr)
    sys.exit(1)

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Check if table exists
cur.execute(
    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'm6_media_assets')"
)
exists = cur.fetchone()[0]
print(f"Table exists: {exists}")

if not exists:
    cur.execute("""
        CREATE TABLE m6_media_assets (
            id SERIAL PRIMARY KEY,
            identity_id VARCHAR(64) NOT NULL,
            runtime_state VARCHAR(30) NOT NULL DEFAULT 'idle',
            result_kind VARCHAR(30),
            raw_prompt TEXT NOT NULL,
            visual_brief TEXT,
            platform VARCHAR(40),
            aspect_ratio VARCHAR(10) DEFAULT '1:1',
            visual_style VARCHAR(30) DEFAULT 'realistic',
            business_context JSONB DEFAULT '{}'::jsonb,
            asset_url TEXT,
            description TEXT,
            provider VARCHAR(40),
            generation_job_id VARCHAR(80),
            failure_reason TEXT,
            campaign_id INTEGER REFERENCES m6_ad_campaigns(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX ix_m6_media_identity ON m6_media_assets(identity_id)")
    conn.commit()
    print("Created m6_media_assets table")
else:
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'm6_media_assets' ORDER BY ordinal_position"
    )
    cols = [r[0] for r in cur.fetchall()]
    print(f"Existing columns: {cols}")

cur.close()
conn.close()
print("Done")