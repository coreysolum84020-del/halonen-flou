from flask import Flask
from .config import config
from .extensions import db, csrf

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    csrf.init_app(app)

    from .blueprints.main import main_bp
    from .blueprints.services import services_bp
    from .blueprints.contact import contact_bp
    from .blueprints.subscriptions import subscriptions_bp
    from .blueprints.setup import setup_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(setup_bp)

    from datetime import datetime

    @app.context_processor
    def inject_globals():
        return {
            'current_year': datetime.now().year,
            'contact_email': 'bluealikeu@gmail.com',
            'contact_phone': '+19295039212',
        }

    with app.app_context():
        from . import models  # noqa: F401 — ensures tables are created
        db.create_all()

    return app
