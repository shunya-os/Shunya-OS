"""Add secondary_phone, whatsapp_phone, whatsapp_verified columns to team_members."""
import sqlalchemy as sa
from app import create_app, db

app = create_app()
with app.app_context():
    inspector = sa.inspect(db.engine)
    cols = [c["name"] for c in inspector.get_columns("team_members")]

    to_add = []
    if "secondary_phone" not in cols:
        to_add.append("secondary_phone VARCHAR(30)")
    if "whatsapp_phone" not in cols:
        to_add.append("whatsapp_phone VARCHAR(30)")
    if "whatsapp_verified" not in cols:
        to_add.append("whatsapp_verified BOOLEAN DEFAULT FALSE")

    if to_add:
        stmt = f"ALTER TABLE team_members ADD COLUMN {', ADD COLUMN '.join(to_add)}"
        db.session.execute(sa.text(stmt))
        db.session.commit()
        print(f"Added columns: {', '.join(c.split()[0] for c in to_add)}")
    else:
        print("All columns already exist")