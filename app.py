from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate, upgrade
from config import config
import os
import logging

from models import db, User
from cli import register_cli_commands

logger = logging.getLogger(__name__)

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        register_cli_commands(app)

        # Run migrations on startup in production
        if os.environ.get('FLASK_ENV') == 'production':
            try:
                logger.info("Running database migrations...")
                upgrade()
                logger.info("Migrations completed successfully")
            except Exception as e:
                logger.error(f"Migration failed: {e}")
                logger.warning("App starting anyway - check database manually")

        from routes.auth import auth_bp
        from routes.main import main_bp
        from routes.documents import documents_bp
        from routes.admin import admin_bp
        from routes.transmittal import transmittal_bp
        from routes.source_of_truth import sot_bp
        from routes.invoices import invoices_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(documents_bp)
        app.register_blueprint(admin_bp)
        app.register_blueprint(transmittal_bp)
        app.register_blueprint(sot_bp)
        app.register_blueprint(invoices_bp)

        @app.context_processor
        def inject_user():
            return {'current_user': current_user}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
