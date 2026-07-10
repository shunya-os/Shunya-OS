from datetime import datetime, date
from app import db
from sqlalchemy import Numeric, func

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    source = db.Column(db.String(50), default='telegram')  # telegram/manual
    customer_name = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    destination = db.Column(db.String(255))
    pax = db.Column(db.String(100))
    dates = db.Column(db.String(255))
    notes = db.Column(db.Text)
    status = db.Column(db.String(50), default='new')  # new/in_progress/converted/cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payments = db.relationship('Payment', backref='lead', cascade='all,delete')
    invoices = db.relationship('Invoice', backref='lead', cascade='all,delete')

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    type = db.Column(db.String(30), default='guest_payment')  # guest_payment/supplier_payment
    amount = db.Column(Numeric(12, 2), default=0)
    method = db.Column(db.String(80))
    ref_number = db.Column(db.String(120))
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    category = db.Column(db.String(120))  # hotel/flight/activity/transport
    contact = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    city = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    total_amount = db.Column(Numeric(12, 2), default=0)
    tax = db.Column(Numeric(12, 2), default=0)
    discount = db.Column(Numeric(12, 2), default=0)
    grand_total = db.Column(Numeric(12, 2), default=0)
    currency = db.Column(db.String(10), default='INR')
    pdf_path = db.Column(db.String(500))
    raised_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default='draft')  # draft/paid/void

class ItineraryRef(db.Model):
    __tablename__ = 'itinerary_refs'
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(255))
    destination = db.Column(db.String(255))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    pax = db.Column(db.String(100))
    highlights = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def next_inquiry_code(session) -> str:
    today = date.today()
    day_num = today.day
    month_num = today.month
    year_num = today.year % 100  # 2-digit year
    prefix = f"PC{day_num:02d}{month_num:02d}{year_num:02d}"
    # count today's leads
    start = datetime(today.year, today.month, today.day)
    end = datetime(today.year, today.month, today.day, 23, 59, 59)
    count = session.query(func.count(Lead.id)).filter(Lead.created_at.between(start, end)).scalar() or 0
    seq = count + 1
    return f"{prefix}{seq:02d}"
