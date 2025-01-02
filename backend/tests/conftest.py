import pytest
from flask import Flask
from backend.models import db
from backend.routes.token_routes import token_blueprint
from backend.routes.trade_routes import trade_blueprint


@pytest.fixture(scope="session")
def app():
    """Create and configure a test Flask application"""
    app = Flask(__name__)
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
        }
    )

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(token_blueprint, url_prefix="/api/tokens")
    app.register_blueprint(trade_blueprint, url_prefix="/api/trades")

    return app


@pytest.fixture(scope="function")
def _db(app):
    """Create database tables for testing"""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def session(_db):
    """Create a new database session for testing"""
    connection = _db.engine.connect()
    transaction = connection.begin()

    session = _db._make_scoped_session(options={"bind": connection, "binds": {}})

    _db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture
def client(app, _db):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()
