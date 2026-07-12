"""Payment gateway service — Razorpay integration."""
import os, razorpay, logging
from flask import current_app

logger = logging.getLogger('shunya.payments')

def get_razorpay_client():
    try:
        key_id = os.environ.get('RAZORPAY_KEY_ID', current_app.config.get('RAZORPAY_KEY_ID', ''))
        key_secret = os.environ.get('RAZORPAY_KEY_SECRET', current_app.config.get('RAZORPAY_KEY_SECRET', ''))
    except RuntimeError:
        key_id = os.environ.get('RAZORPAY_KEY_ID', '')
        key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
    if not key_id or not key_secret:
        logger.warning('Razorpay not configured - returning mock client')
        return None
    return razorpay.Client(auth=(key_id, key_secret))

def create_order(amount_paise, currency='INR', receipt=None, notes=None):
    """Create a Razorpay order. amount_paise is in paise (1/100th of rupee)."""
    client = get_razorpay_client()
    if not client:
        # Return mock order when not configured
        import uuid
        return {
            'id': f'mock_order_{uuid.uuid4().hex[:8]}',
            'amount': amount_paise,
            'currency': currency,
            'status': 'created',
            'receipt': receipt or '',
            'notes': notes or {},
            'mock': True
        }
    order_data = {
        'amount': amount_paise,
        'currency': currency,
        'receipt': receipt or '',
        'notes': notes or {},
    }
    return client.order.create(order_data)

def verify_payment(order_id, payment_id, signature):
    """Verify Razorpay payment signature."""
    client = get_razorpay_client()
    if not client:
        return True  # mock: always verify
    try:
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        client.utility.verify_payment_signature(params_dict)
        return True
    except Exception as e:
        logger.error(f'Payment verification failed: {e}')
        return False