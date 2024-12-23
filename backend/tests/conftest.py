import os
import sys
import pytest
import tempfile

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app import create_app
from models import db

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False
    })

    # Create the database and the database tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def _db(app):
    """Create and configure a new database for each test."""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()