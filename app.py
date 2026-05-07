import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

from config import config
from models import db, User
from seed_data import register_seed_command


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialise extensions
    db.init_app(app)
    Migrate(app, db)

    # Login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.inventory import inventory_bp
    from routes.orders import orders_bp
    from routes.purchasing import purchasing_bp
    from routes.warehouse import warehouse_bp
    from routes.documents import documents_bp
    from routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(purchasing_bp)
    app.register_blueprint(warehouse_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(reports_bp)

    # Register CLI commands
    register_seed_command(app)

    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    return app


app = create_app()
