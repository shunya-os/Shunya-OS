import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
db = SQLAlchemy()
load_dotenv()
def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'), static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY','dev-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://panchi:panchi_club_2024@localhost:5432/panchi_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    from app.routes import main, api
    app.register_blueprint(main)
    app.register_blueprint(api)
    @app.context_processor
    def inject_globals():
        return {'brand':'Panchi Club','assistant_identity':'AI@panchi.club'}
    with app.app_context():
        from sqlalchemy.exc import OperationalError
        try:
            db.create_all()
        except OperationalError:
            pass
    return app
