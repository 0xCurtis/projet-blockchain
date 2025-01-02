from flask import Flask
from flask_cors import CORS
from backend.models import db
from backend.routes.token_routes import token_blueprint
from backend.routes.trade_routes import trade_blueprint


def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Configure CORS
    CORS(app)

    # Configure the app
    if test_config is None:
        # Default configuration
        app.config.update(
            {
                "SQLALCHEMY_DATABASE_URI": "sqlite:///rwa_tokens.db",
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
                "JSON_SORT_KEYS": False,
            }
        )
    else:
        # Test configuration
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    app.register_blueprint(token_blueprint, url_prefix="/api/tokens")
    app.register_blueprint(trade_blueprint, url_prefix="/api/trades")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
