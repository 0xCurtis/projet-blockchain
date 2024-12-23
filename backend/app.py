from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from routes.token_routes import token_blueprint
from routes.trade_routes import trade_blueprint
from models import db
import os

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(token_blueprint, url_prefix="/api/tokens")
    app.register_blueprint(trade_blueprint, url_prefix="/api/trades")

    # Create database tables
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True) 