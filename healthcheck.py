from flask import Flask, jsonify
from sqlalchemy import text
from app import db
from app.models import Lead, Payment, Supplier, Invoice, ItineraryRef

def create_health_app():
    app = Flask(__name__)
    db.init_app(app)

    @app.route('/health')
    def health():
        try:
            with app.app_context():
                db.session.execute(text('SELECT 1'))
                counts = {
                    'Lead': db.session.query(Lead).count(),
                    'Payment': db.session.query(Payment).count(),
                    'Supplier': db.session.query(Supplier).count(),
                    'Invoice': db.session.query(Invoice).count(),
                    'ItineraryRef': db.session.query(ItineraryRef).count(),
                }
            return jsonify({'status': 'ok', 'checks': counts}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500

    return app

if __name__ == '__main__':
    create_health_app().run(host='0.0.0.0', port=8081)
