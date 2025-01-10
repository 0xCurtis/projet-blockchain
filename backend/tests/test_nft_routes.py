import pytest
from flask import json
from app import create_app
from unittest.mock import patch, MagicMock

@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client() 