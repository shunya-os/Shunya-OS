from app import db
from app.models import next_inquiry_code
import re, json, os
from datetime import datetime
from sqlalchemy import func

def save_telegram_token(token: str):
    token = token.strip()
    if not token:
        raise ValueError('Empty token')
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'telegram_bot_token.txt')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(token)

def get_telegram_token() -> str:
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'telegram_bot_token.txt')
    if not os.path.exists(path):
        return ''
    with open(path, 'r') as f:
        return f.read().strip()

def set_telegram_webhook(token: str, url: str):
    try:
        import requests
    except Exception as e:
        return False, f'requests unavailable: {e}'
    api = f"https://api.telegram.org/bot{token}/setWebhook"
    try:
        r = requests.post(api, json={'url': url}, timeout=15)
        data = r.json()
        if data.get('ok'):
            return True, url
        return False, data.get('description') or str(data)
    except Exception as e:
        return False, str(e)

def parse_inquiry_text(text: str):
    text = text.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    destination = None
    nights = None
    adults = None
    kids = None
    dates = None
    name = None
    m = re.search(r'(?i)(?:to|for|in)\s+([A-Z][a-zA-Z\s]{2,40})', text)
    if m:
        destination = m.group(1).strip()
    m = re.search(r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})', text)
    if m:
        dates = m.group(1)
    m = re.search(r'(\d+)\s*(?:night|nights)', text, flags=re.I)
    if m:
        nights = int(m.group(1))
    m = re.search(r'(\d+)\s*adults?', text, flags=re.I)
    if m:
        adults = int(m.group(1))
    m = re.search(r'(\d+)\s*(?:kids|children|child)', text, flags=re.I)
    if m:
        kids = int(m.group(1))
    return {
        'destination': destination,
        'nights': nights,
        'adults': adults,
        'kids': kids,
        'dates': dates,
        'name': name
    }

def _cached_or_new_code(session) -> str:
    cache_key = f'next_inquiry_code:{datetime.utcnow().date().isoformat()}'
    try:
        from app.cache import get as cache_get, set as cache_set
        cached = cache_get(cache_key)
        if cached:
            return str(cached)
    except Exception:
        pass
    code = next_inquiry_code(session)
    try:
        from app.cache import set as cache_set
        cache_set(cache_key, code, 3600)
    except Exception:
        pass
    return code

def get_summary(period='today'):
    cache_key = f'summary:{period}'
    try:
        from app.cache import get as cache_get, set as cache_set
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
    except Exception:
        pass
    from app.models import Lead, Payment
    today = datetime.utcnow().date()
    start = datetime(today.year, today.month, today.day)
    end = datetime(today.year, today.month, today.day, 23, 59, 59)
    q_leads = db.session.query(func.count(Lead.id))
    q_revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0))
    q_supplier = db.session.query(func.coalesce(func.sum(Payment.amount), 0))
    if period == 'today':
        q_leads = q_leads.filter(Lead.created_at.between(start, end))
        q_revenue = q_revenue.filter(Payment.type=='guest_payment', Payment.paid_at.between(start, end))
        q_supplier = q_supplier.filter(Payment.type=='supplier_payment', Payment.paid_at.between(start, end))
    elif period == 'month':
        month_start = datetime(today.year, today.month, 1)
        q_leads = q_leads.filter(Lead.created_at >= month_start)
        q_revenue = q_revenue.filter(Payment.type=='guest_payment', Payment.paid_at >= month_start)
        q_supplier = q_supplier.filter(Payment.type=='supplier_payment', Payment.paid_at >= month_start)
    data = {
        'leads': q_leads.scalar() or 0,
        'revenue': float(q_revenue.scalar() or 0),
        'supplier_out': float(q_supplier.scalar() or 0),
        'profit': float(q_revenue.scalar() or 0) - float(q_supplier.scalar() or 0),
    }
    try:
        from app.cache import set as cache_set
        cache_set(cache_key, data, 60)
    except Exception:
        pass
    return data
