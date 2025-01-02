import pytest
from unittest.mock import patch
from backend.models import db, Wallet, Token, Transaction


@pytest.fixture
def sample_token_request():
    """Sample token creation request data"""
    return {
        "wallet": {"classic_address": "rTest123", "secret": "sTest123"},
        "asset_details": {
            "name": "Test Asset",
            "type": "real_estate",
            "description": "Test description",
        },
        "token_details": {
            "token_name": "Test Token",
            "currency_code": "TST",
            "total_supply": "1000",
        },
        "additional_details": {
            "square_feet": 1000,
            "bedrooms": 2,
            "bathrooms": 2,
            "year_built": 2020,
        },
    }


@pytest.fixture
def sample_wallet(session):
    """Create a sample wallet in the database"""
    wallet = Wallet(address="rTest123", seed="sTest123")
    session.add(wallet)
    session.commit()
    return wallet


def test_create_wallet_success(client, session):
    """Test successful wallet creation route"""
    with patch(
        "backend.services.xrpl_service.load_or_create_master_wallet"
    ) as mock_create:
        # Mock successful wallet creation
        class MockWallet:
            def __init__(self):
                self.classic_address = "rTest123"
                self.seed = "sTest123"

        mock_create.return_value = MockWallet()

        response = client.post("/api/tokens/wallet/create")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "response" in data
        assert data["response"]["address"] == "rTest123"


def test_create_token_success(client, session, sample_wallet, sample_token_request):
    """Test successful token creation route"""
    with patch("backend.services.token_service.create_token") as mock_create:
        # Mock successful token creation
        mock_create.return_value = {
            "success": True,
            "currency_code": "TST",
            "issuer": "rTest123",
            "total_supply": 1000,
            "metadata": sample_token_request,
            "enable_rippling_result": {"hash": "hash1"},
            "trust_set_result": {"hash": "hash2"},
            "payment_result": {"hash": "hash3"},
        }

        response = client.post("/api/tokens/create", json=sample_token_request)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "response" in data

        # Verify token was saved in database
        token = (
            session.query(Token)
            .filter_by(currency_code="TST", issuer_id=sample_wallet.id)
            .first()
        )
        assert token is not None
        assert token.name == sample_token_request["token_details"]["token_name"]
        assert (
            token.total_supply == sample_token_request["token_details"]["total_supply"]
        )

        # Verify transactions were saved
        transactions = session.query(Transaction).filter_by(token_id=token.id).all()
        assert len(transactions) == 3  # enable_rippling, trust_set, and payment


def test_create_token_wallet_not_found(client, sample_token_request):
    """Test token creation with non-existent wallet"""
    response = client.post("/api/tokens/create", json=sample_token_request)

    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False
    assert "Wallet not found" in data["error"]


def test_create_token_missing_fields(client, sample_wallet):
    """Test token creation with missing required fields"""
    # Test with missing wallet data
    response = client.post("/api/tokens/create", json={})

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "Missing required field" in data["error"]


def test_create_token_xrpl_error(client, session, sample_wallet, sample_token_request):
    """Test token creation with XRPL error"""
    with patch("backend.services.token_service.create_token") as mock_create:
        # Mock XRPL error
        mock_create.return_value = {"success": False, "error": "XRPL Error"}

        response = client.post("/api/tokens/create", json=sample_token_request)

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert data["error"] == "XRPL Error"


def test_list_tokens(client, session, sample_wallet):
    """Test token listing route"""
    # Create a test token
    token = Token(
        currency_code="TST",
        name="Test Token",
        total_supply="1000",
        token_metadata={},
        issuer_id=sample_wallet.id,
        enable_rippling_tx="hash1",
        trust_set_tx="hash2",
        payment_tx="hash3",
    )
    session.add(token)
    session.commit()

    response = client.get("/api/tokens/list")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["response"]["tokens"]) == 1
    assert data["response"]["tokens"][0]["currency_code"] == "TST"


def test_list_transactions(client, session, sample_wallet):
    """Test transaction listing route"""
    # Create a test token and transaction
    token = Token(
        currency_code="TST",
        name="Test Token",
        total_supply="1000",
        token_metadata={},
        issuer_id=sample_wallet.id,
        enable_rippling_tx="hash1",
        trust_set_tx="hash2",
        payment_tx="hash3",
    )
    session.add(token)
    session.commit()

    transaction = Transaction(
        tx_hash="hash1",
        tx_type="enable_rippling",
        wallet_id=sample_wallet.id,
        token_id=token.id,
        status="success",
        raw_data={"test": "data"},
    )
    session.add(transaction)
    session.commit()

    response = client.get("/api/tokens/transactions")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["response"]["transactions"]) == 1
    assert data["response"]["transactions"][0]["tx_hash"] == "hash1"
