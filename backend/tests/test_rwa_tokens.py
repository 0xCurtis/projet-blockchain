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
def real_estate_asset():
    """Sample real estate asset details"""
    return {
        "name": "Luxury Apartment 1234",
        "type": "real_estate",
        "description": "Premium 3-bedroom apartment in downtown area with modern amenities",
        "geolocation": {
            "address": "123 Main Street",
            "city": "New York",
            "country": "USA",
            "postal_code": "10001",
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
    }


def test_create_real_estate_token(test_wallet, real_estate_asset):
    """Test creating a token for a real estate asset"""
    logger.info("Starting real estate token creation test")
    logger.debug(f"Using wallet: {test_wallet['classic_address']}")
    logger.debug(f"Asset details: {real_estate_asset}")

    token_details = {
        "token_name": "LuxApt1234",
        "currency_code": "LAP",
        "total_supply": "1",
    }
    logger.debug(f"Token details: {token_details}")

    additional_details = {
        "square_feet": 2000,
        "bedrooms": 3,
        "bathrooms": 2,
        "year_built": 2020,
        "amenities": ["pool", "gym", "parking"],
        "legal_details": {
            "deed_number": "NYC-2023-12345",
            "property_id": "MAN-1234-5678",
            "zoning": "residential",
        },
    }
    logger.debug(f"Additional details: {additional_details}")

    logger.info("Calling create_token...")
    response = create_token(
        wallet_data=test_wallet,
        asset_details=real_estate_asset,
        token_details=token_details,
        additional_details=additional_details,
    )
    logger.info("Token creation response received")
    logger.debug(f"Response: {response}")

    assert (
        response["success"] is True
    ), f"Token creation failed: {response.get('error', 'Unknown error')}"
    assert response["currency_code"] == "LAP"
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

    logger.info("Real estate token creation test completed successfully")


def test_create_fine_art_token(test_wallet):
    """Test creating a token for a fine art asset"""
    logger.info("Starting fine art token creation test")
    logger.debug(f"Using wallet: {test_wallet['classic_address']}")

    asset_details = {
        "name": "Mona Lisa Replica",
        "type": "fine_art",
        "description": "High-quality replica of the famous Mona Lisa painting",
        "geolocation": {
            "address": "Louvre Museum",
            "city": "Paris",
            "country": "France",
            "postal_code": "75001",
        },
    }
    logger.debug(f"Asset details: {asset_details}")

    token_details = {
        "token_name": "MonaLisa2023",
        "currency_code": "MLA",
        "total_supply": "1",
    }
    logger.debug(f"Token details: {token_details}")

    additional_details = {
        "artist": "Leonardo da Vinci (replica)",
        "year": 2023,
        "medium": "Oil on canvas",
        "dimensions": {"height": 77, "width": 53, "unit": "cm"},
        "provenance": ["Gallery XYZ", "Private Collection ABC"],
        "authentication": {
            "certificate_number": "ART-2023-789",
            "authenticator": "Fine Art Authentication Board",
        },
    }
    logger.debug(f"Additional details: {additional_details}")

    logger.info("Calling create_token...")
    response = create_token(
        wallet_data=test_wallet,
        asset_details=asset_details,
        token_details=token_details,
        additional_details=additional_details,
    )
    logger.info("Token creation response received")
    logger.debug(f"Response: {response}")

    assert (
        response["success"] is True
    ), f"Token creation failed: {response.get('error', 'Unknown error')}"
    assert response["currency_code"] == "MLA"
    assert response["total_supply"] == 1

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

    logger.info("Fine art token creation test completed successfully")


def test_create_vehicle_token(test_wallet):
    """Test creating a token for a vehicle asset"""
    logger.info("Starting vehicle token creation test")
    logger.debug(f"Using wallet: {test_wallet['classic_address']}")

    asset_details = {
        "name": "Tesla Model S 2023",
        "type": "vehicles",
        "description": "Electric luxury sedan with advanced autopilot features",
    }
    logger.debug(f"Asset details: {asset_details}")

    token_details = {
        "token_name": "TeslaS2023",
        "currency_code": "TSL",
        "total_supply": "1",
    }
    logger.debug(f"Token details: {token_details}")

    additional_details = {
        "vin": "5YJ3E1EA8PF123456",
        "color": "Midnight Silver",
        "mileage": 0,
        "features": ["Autopilot", "Full Self-Driving", "Premium Interior"],
        "specifications": {
            "range": "405 miles",
            "acceleration": "2.4 seconds 0-60 mph",
            "top_speed": "200 mph",
        },
    }
    logger.debug(f"Additional details: {additional_details}")

    logger.info("Calling create_token...")
    response = create_token(
        wallet_data=test_wallet,
        asset_details=asset_details,
        token_details=token_details,
        additional_details=additional_details,
    )
    logger.info("Token creation response received")
    logger.debug(f"Response: {response}")

    assert (
        response["success"] is True
    ), f"Token creation failed: {response.get('error', 'Unknown error')}"
    assert response["currency_code"] == "TSL"
    assert response["total_supply"] == 1

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

    logger.info("Vehicle token creation test completed successfully")


def test_missing_wallet_secret():
    """Test creating a token with missing wallet secret"""
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
    response = create_token(
        wallet_data={"classic_address": "test"},  # Missing secret
        asset_details=asset_details,
        token_details=token_details,
    )
    logger.info("Token creation response received")
    logger.debug(f"Response: {response}")

    assert response["success"] is False, "Token creation should have failed"
    assert "Missing wallet secret" in response["error"]
    logger.info("Missing wallet secret test completed successfully")
