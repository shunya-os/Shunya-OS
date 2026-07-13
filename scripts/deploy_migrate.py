"""Run DB migrations on deploy. Returns exit code 1 on failure."""
import sys
sys.path.insert(0, "/root/shunya_os")

try:
    from app import create_app, db
    from sqlalchemy import text
    
    app = create_app("production")
    with app.app_context():
        db.session.execute(text("SELECT 1"))
        db.session.commit()
        
        # Add any new columns/tables that might be missing
        tables_sql = [
            "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES team_members(id)",
            "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS brand_id INTEGER REFERENCES brands(id)",
            "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS business_id INTEGER REFERENCES businesses(id)",
            "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS vertical_config JSONB DEFAULT '{}'",
            "ALTER TABLE team_members ADD COLUMN IF NOT EXISTS secondary_phone VARCHAR(30)",
            "ALTER TABLE team_members ADD COLUMN IF NOT EXISTS whatsapp_phone VARCHAR(30)",
            "ALTER TABLE team_members ADD COLUMN IF NOT EXISTS whatsapp_verified BOOLEAN DEFAULT FALSE",
            "CREATE TABLE IF NOT EXISTS business_groups (id SERIAL PRIMARY KEY, name VARCHAR(255), owner_id INTEGER, description TEXT, industry VARCHAR(60), created_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS businesses (id SERIAL PRIMARY KEY, name VARCHAR(255), owner_id INTEGER, group_id INTEGER, business_type VARCHAR(60), description TEXT, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS brands (id SERIAL PRIMARY KEY, name VARCHAR(255), business_id INTEGER, is_default BOOLEAN DEFAULT FALSE, description TEXT, logo_url VARCHAR(500), brand_color VARCHAR(7), brand_tagline VARCHAR(500), created_at TIMESTAMP DEFAULT NOW())",
        ]
        for sql in tables_sql:
            try:
                db.session.execute(text(sql))
                db.session.commit()
            except Exception:
                db.session.rollback()
    
    print("Migration OK")
except Exception as e:
    print(f"Migration failed: {e}")
    sys.exit(1)