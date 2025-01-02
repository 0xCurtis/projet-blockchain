import pytest
import time
import logging
from xrpl.wallet import generate_faucet_wallet
from xrpl.clients import JsonRpcClient
from xrpl.models import AccountInfo
from backend.services.token_service import create_token

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# XRPL testnet client
JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)


@pytest.fixture(scope="module")
def test_wallet():
    """Create and fund a real wallet on XRPL testnet"""
    logger.info("Generating new testnet wallet...")
    # Generate a funded testnet wallet
    wallet = generate_faucet_wallet(client, debug=True)
    logger.info(f"Generated wallet with address: {wallet.classic_address}")

    # Wait for funding to complete
    logger.info("Waiting for wallet funding...")
    time.sleep(5)  # Give some time for funding transaction to complete

    # Verify wallet is funded
    logger.info("Verifying wallet funding...")
    account_info = AccountInfo(
        account=wallet.classic_address,
        strict=True,
    )
    response = client.request(account_info)
    balance = float(response.result["account_data"]["Balance"])
    logger.info(f"Wallet balance: {balance} drops")
    assert balance > 0, "Wallet not funded"

    wallet_data = {"classic_address": wallet.classic_address, "secret": wallet.seed}
    logger.info("Wallet setup complete")
    return wallet_data


@pytest.fixture
def sample_asset_details():
    """Sample asset details"""
    details = {
        "name": "Test Asset",
        "type": "real_estate",
        "description": "Test description",
        "geolocation": {
            "address": "123 Test St",
            "city": "Test City",
            "country": "Test Country",
            "postal_code": "12345",
        },
    }
    logger.debug(f"Created sample asset details: {details}")
    return details


@pytest.fixture
def sample_token_details():
    """Sample token details"""
    details = {"token_name": "Test Token", "currency_code": "TST", "total_supply": "1"}
    logger.debug(f"Created sample token details: {details}")
    return details


@pytest.fixture
def sample_additional_details():
    """Sample additional details"""
    details = {
        "square_feet": 1000,
        "bedrooms": 2,
        "bathrooms": 2,
        "year_built": 2020,
        "legal_details": {
            "deed_number": "123",
            "property_id": "456",
            "zoning": "residential",
        },
    }
    logger.debug(f"Created sample additional details: {details}")
    return details


def test_create_token_success(
    test_wallet, sample_asset_details, sample_token_details, sample_additional_details
):
    """Test successful token creation"""
    logger.info("Starting successful token creation test")
    logger.debug(f"Using wallet: {test_wallet['classic_address']}")
    logger.debug(f"Asset details: {sample_asset_details}")
    logger.debug(f"Token details: {sample_token_details}")
    logger.debug(f"Additional details: {sample_additional_details}")

    logger.info("Calling create_token...")
    response = create_token(
        wallet_data=test_wallet,
        asset_details=sample_asset_details,
        token_details=sample_token_details,
        additional_details=sample_additional_details,
    )
    logger.info("Token creation response received")
    logger.debug(f"Response: {response}")

    assert (
        response["success"] is True
    ), f"Token creation failed: {response.get('error', 'Unknown error')}"
    assert response["currency_code"] == sample_token_details["currency_code"]
    assert response["total_supply"] == 1
    assert "metadata" in response
    assert "enable_rippling_result" in response
    assert "trust_set_result" in response
    assert "payment_result" in response

    # Verify the transactions on XRPL
    logger.info("Verifying transactions on XRPL...")
    for tx_type in ["enable_rippling_result", "trust_set_result", "payment_result"]:
        tx_hash = response[tx_type]["hash"]
        logger.info(f"Verifying {tx_type} transaction: {tx_hash}")

        # Wait for transaction to be validated
        logger.debug(f"Waiting for {tx_type} validation...")
        time.sleep(5)

        # Verify transaction exists and was successful
        logger.debug(f"Checking {tx_type} status...")
        tx_response = client.request({"command": "tx", "transaction": tx_hash})
        logger.debug(f"Transaction response: {tx_response.result}")

        assert (
            tx_response.is_successful()
        ), f"Transaction verification failed for {tx_type}"
        assert tx_response.result.get(
            "validated", False
        ), f"Transaction not validated for {tx_type}"
        logger.info(f"{tx_type} verified successfully")

    logger.info("Successful token creation test completed")


def test_create_token_missing_secret():
    """Test token creation with missing wallet secret"""
    logger.info("Starting missing wallet secret test")

    asset_details = {
        "name": "Test Asset",
        "type": "real_estate",
        "description": "Test description",
    }
    logger.debug(f"Asset details: {asset_details}")

    token_details = {
        "token_name": "Test Token",
        "currency_code": "TST",
        "total_supply": "1",
    }
    logger.debug(f"Token details: {token_details}")

    logger.info("Attempting token creation with missing secret...")
    result = create_token(
        wallet_data={"classic_address": "rTest123"},  # Missing secret
        asset_details=asset_details,
        token_details=token_details,
    )
    logger.info("Token creation response received")
    logger.debug(f"Response: {result}")

    assert result["success"] is False, "Token creation should have failed"
    assert "Missing wallet secret" in result["error"]
    logger.info("Missing wallet secret test completed successfully")


def test_create_token_invalid_supply(test_wallet, sample_asset_details):
    """Test token creation with invalid supply value"""
    logger.info("Starting invalid supply test")
    logger.debug(f"Using wallet: {test_wallet['classic_address']}")
    logger.debug(f"Asset details: {sample_asset_details}")

    token_details = {
        "token_name": "Test Token",
        "currency_code": "TST",
        "total_supply": "invalid",  # Invalid supply
    }
    logger.debug(f"Token details with invalid supply: {token_details}")

    logger.info("Attempting token creation with invalid supply...")
    result = create_token(
        wallet_data=test_wallet,
        asset_details=sample_asset_details,
        token_details=token_details,
    )
    logger.info("Token creation response received")
    logger.debug(f"Response: {result}")

    assert result["success"] is False, "Token creation should have failed"
    assert "invalid literal for int()" in result["error"]
    logger.info("Invalid supply test completed successfully")
