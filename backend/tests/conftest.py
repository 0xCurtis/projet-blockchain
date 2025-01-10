import pytest
import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from app import create_app

@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def db(app):
    """Create a test database connection."""
    client = MongoClient(app.config['MONGODB_URI'])
    db = client[app.config['MONGODB_DB']]
    
    # Clear all collections before each test
    for collection in db.list_collection_names():
        db[collection].delete_many({})
    
    yield db
    
    # Clear all collections after each test
    for collection in db.list_collection_names():
        db[collection].delete_many({})
    
    client.close()

@pytest.fixture
def mock_xrpl_client():
    """Create a mock XRPL client."""
    class MockXRPLClient:
        def request(self, *args, **kwargs):
            class MockResponse:
                def is_successful(self):
                    return True
                
                @property
                def result(self):
                    return {"engine_result": "tesSUCCESS"}
            
            return MockResponse()
    
    return MockXRPLClient()

@pytest.fixture
def test_nft():
    """Create a test NFT object."""
    return {
        "nft_id": "test-nft-id",
        "account": "rTestAddress123",
        "uri": "ipfs://test",
        "metadata": {
            "title": "Test NFT",
            "asset_type": "Real Estate",
            "description": "Test description",
            "location": "Test location",
            "documentation_id": "TEST123"
        },
        "status": "minted",
        "transaction_hash": "test-hash",
        "created_at": "2025-01-10T00:00:00Z"
    }

@pytest.fixture
def test_listing():
    """Create a test marketplace listing."""
    return {
        "id": "test-listing-id",
        "nft_id": "test-nft-id",
        "seller_address": "rTestAddress123",
        "price_xrp": 100.0,
        "price_drops": "100000000",
        "metadata_hash": "test-hash",
        "status": "active",
        "created_at": "2025-01-10T00:00:00Z"
    }

@pytest.fixture
def test_transaction():
    """Create a test transaction object."""
    return {
        "hash": "test-hash",
        "type": "mint",
        "account": "rTestAddress123",
        "status": "success",
        "timestamp": "2025-01-10T00:00:00Z"
    } 