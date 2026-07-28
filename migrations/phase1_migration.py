"""Phase 1 migration — additive, nullable, compatibility-preserving."""
import psycopg2

conn = psycopg2.connect("host=localhost dbname=shunya_db user=shunya password=shunya_os_2026")
cur = conn.cursor()

# New tables
tables = [
    """
    CREATE TABLE IF NOT EXISTS persons (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER REFERENCES tenants(id),
        canonical_name VARCHAR(255) NOT NULL,
        preferred_name VARCHAR(255) DEFAULT '',
        status VARCHAR(30) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS person_identities (
        id SERIAL PRIMARY KEY,
        person_id INTEGER NOT NULL REFERENCES persons(id),
        identity_type VARCHAR(60) NOT NULL,
        identity_value VARCHAR(255) NOT NULL,
        normalized_value VARCHAR(255) NOT NULL,
        verification_state VARCHAR(30) DEFAULT 'unverified'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS employee_profiles (
        id SERIAL PRIMARY KEY,
        person_id INTEGER NOT NULL UNIQUE REFERENCES persons(id),
        tenant_id INTEGER REFERENCES tenants(id),
        employee_code VARCHAR(60) UNIQUE,
        department VARCHAR(120) DEFAULT '',
        manager_person_id INTEGER,
        role VARCHAR(60) DEFAULT '',
        status VARCHAR(30) DEFAULT 'active',
        joined_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS customer_profiles (
        id SERIAL PRIMARY KEY,
        person_id INTEGER NOT NULL UNIQUE REFERENCES persons(id),
        tenant_id INTEGER REFERENCES tenants(id),
        lifetime_value NUMERIC(14,2) DEFAULT 0,
        segment VARCHAR(60) DEFAULT '',
        preferred_channel VARCHAR(30) DEFAULT '',
        preferred_channel_provenance TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS supplier_contact_profiles (
        id SERIAL PRIMARY KEY,
        person_id INTEGER NOT NULL UNIQUE REFERENCES persons(id),
        tenant_id INTEGER REFERENCES tenants(id),
        supplier_id INTEGER,
        role_in_organization VARCHAR(120) DEFAULT '',
        is_primary BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS client_user_profiles (
        id SERIAL PRIMARY KEY,
        person_id INTEGER NOT NULL UNIQUE REFERENCES persons(id),
        tenant_id INTEGER REFERENCES tenants(id),
        portal_access_granted BOOLEAN DEFAULT FALSE,
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
]

for sql in tables:
    cur.execute(sql)
print("Tables created")

# Add person_id columns to existing tables
alterations = [
    ("team_members", "person_id"),
    ("leads", "person_id"),
]
for table, col in alterations:
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'")
    if not cur.fetchone():
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} INTEGER REFERENCES persons(id)")
        print(f"Added {col} to {table}")

# Indexes
cur.execute("CREATE INDEX IF NOT EXISTS ix_person_tenant ON persons(tenant_id, status)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_pi_type_value ON person_identities(identity_type, normalized_value)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_pi_person ON person_identities(person_id)")

conn.commit()
print("Migration complete")

# Backfill
from app.auth import TeamMember, UserRole
from app.models import Person, PersonIdentity, EmployeeProfile
from app.shunya.identity import normalize_email, normalize_phone

members = TeamMember.query.all()
count = 0
for tm in members:
    if tm.person_id:
        continue
    p = Person(canonical_name=tm.name, preferred_name=tm.name.split()[0] if tm.name else tm.name)
    from app import db
    db.session.add(p)
    db.session.flush()
    tm.person_id = p.id
    ep = EmployeeProfile(person_id=p.id, role=tm.role, department="General")
    db.session.add(ep)
    if tm.email:
        pi = PersonIdentity(person_id=p.id, identity_type="email",
                            identity_value=tm.email, normalized_value=normalize_email(tm.email),
                            verification_state="verified")
        db.session.add(pi)
    if tm.phone:
        pi = PersonIdentity(person_id=p.id, identity_type="phone",
                            identity_value=tm.phone, normalized_value=normalize_phone(tm.phone),
                            verification_state="verified")
        db.session.add(pi)
    count += 1
db.session.commit()
print(f"Backfilled {count} TeamMembers")
print(f"Total Persons: {Person.query.count()}")

cur.close()
conn.close()