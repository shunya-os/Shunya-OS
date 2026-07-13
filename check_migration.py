"""Check if migration columns exist in the shunya_os database."""
from app import create_app, db
import sqlalchemy as sa

app = create_app("development")
with app.app_context():
    inspector = sa.inspect(db.engine)
    cols = [c["name"] for c in inspector.get_columns("team_members")]
    print("Has secondary_phone:", "secondary_phone" in cols)
    print("Has whatsapp_phone:", "whatsapp_phone" in cols)
    print("Has whatsapp_verified:", "whatsapp_verified" in cols)