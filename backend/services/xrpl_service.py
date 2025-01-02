import os
import json
import xrpl
from xrpl.wallet import generate_faucet_wallet, Wallet
from xrpl.core.keypairs import derive_keypair
from xrpl.models.transactions import Payment, TrustSet, AccountSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.response import Response
from xrpl.models.requests import AccountInfo, AccountLines
from xrpl.transaction import submit_and_wait
from xrpl.constants import XRPLException
from typing import Dict, Union, Optional, Any, TypedDict, Literal

# Connect to XRP Ledger Testnet
CLIENT = xrpl.clients.JsonRpcClient("https://s.altnet.rippletest.net:51234")
TESTNET_EXPLORER = "https://testnet.xrpl.org"
MASTER_WALLET_FILE = "master_wallet.json"


def get_account_info(address: str) -> Dict[str, Any]:
    """Get account information from XRPL"""
    try:
        request = AccountInfo(account=address, ledger_index="validated", strict=True)
        response = CLIENT.request(request)
        return response.result
    except Exception as e:
        raise XRPLException(f"Failed to get account info: {str(e)}")


def get_account_lines(address: str) -> Dict[str, Any]:
    """Get account trust lines from XRPL"""
    try:
        request = AccountLines(account=address, ledger_index="validated")
        response = CLIENT.request(request)
        return response.result
    except Exception as e:
        raise XRPLException(f"Failed to get account lines: {str(e)}")


def load_or_create_master_wallet() -> Wallet:
    """Load the master wallet from a file or create one if it doesn't exist."""
    if os.path.exists(MASTER_WALLET_FILE):
        with open(MASTER_WALLET_FILE, "r") as file:
            wallet_data = json.load(file)
            # Derive keypair from seed
            public_key, private_key = derive_keypair(wallet_data["seed"])
            master_wallet = Wallet(
                seed=wallet_data["seed"], public_key=public_key, private_key=private_key
            )
            print("✅ Master wallet loaded successfully")
            print(f"📍 Address: {master_wallet.classic_address}")
            print(
                f"🔗 Explorer: {get_explorer_url('account', master_wallet.classic_address)}"
            )
            return master_wallet

    # Create a new master wallet
    print("⚠️ No existing master wallet found. Creating new one...")
    master_wallet = generate_faucet_wallet(CLIENT, debug=True)
    wallet_data = {"seed": master_wallet.seed, "address": master_wallet.classic_address}
    with open(MASTER_WALLET_FILE, "w") as file:
        json.dump(wallet_data, file, indent=4)
    print("✅ New master wallet created and saved")
    print(f"📍 Address: {master_wallet.classic_address}")
    print(f"🔗 Explorer: {get_explorer_url('account', master_wallet.classic_address)}")
    return master_wallet


def enable_rippling(wallet: Wallet) -> Response:
    """Enable rippling for the account to allow token issuance."""
    account_set = AccountSet(
        account=wallet.classic_address, set_flag=8  # Enable rippling
    )
    response = submit_and_wait(account_set, CLIENT, wallet)
    transaction_result = response.result.get("meta", {}).get("TransactionResult")
    if transaction_result != "tesSUCCESS":
        raise XRPLException(f"Failed to enable rippling: {transaction_result}")
    return response


def issue_token(
    wallet: Wallet, token_name: str, total_supply: int, metadata: RWAMetadata
) -> Union[TokenResponse, ErrorResponse]:
    """Issue a new token from the master wallet."""
    try:
        print_separator()
        print("🪙 TOKEN ISSUANCE PROCESS")
        print_separator()
        print(f"Token Name: {token_name}")
        print(f"Total Supply: {total_supply}")
        print(f"Asset Type: {metadata['asset_details']['type']}")
        print(f"Issuer Address: {wallet.classic_address}")
        print_separator()

        # Enable rippling on the master wallet
        enable_response = enable_rippling(wallet)

        currency_code = metadata["token_details"]["currency_code"]
        print(f"\n💱 Using currency code: {currency_code}")

        # Define the issued currency amount
        issue_amount = IssuedCurrencyAmount(
            currency=currency_code,
            issuer=wallet.classic_address,
            value=str(total_supply),
        )

        # Create a trustline to self
        print("\n🤝 Creating trustline...")
        trust_set = TrustSet(account=wallet.classic_address, limit_amount=issue_amount)
        trust_response = submit_and_wait(trust_set, CLIENT, wallet)
        transaction_result = trust_response.result.get("meta", {}).get(
            "TransactionResult"
        )
        if transaction_result != "tesSUCCESS":
            raise XRPLException(f"Failed to create trustline: {transaction_result}")

        print("✅ Trustline created successfully")
        print(f"📝 Transaction Hash: {trust_response.result.get('hash')}")
        print(
            f"🔗 Explorer: {get_explorer_url('transaction', trust_response.result.get('hash'))}"
        )

        # Issue the token by sending a payment to self
        print("\n💸 Issuing tokens through payment...")
        payment = Payment(
            account=wallet.classic_address,
            destination=wallet.classic_address,
            amount=issue_amount,
        )
        payment_response = submit_and_wait(payment, CLIENT, wallet)
        transaction_result = payment_response.result.get("meta", {}).get(
            "TransactionResult"
        )
        if transaction_result != "tesSUCCESS":
            raise XRPLException(f"Failed to issue token: {transaction_result}")

        print("✅ Token payment completed successfully")
        print(f"📝 Transaction Hash: {payment_response.result.get('hash')}")
        print(
            f"🔗 Explorer: {get_explorer_url('transaction', payment_response.result.get('hash'))}"
        )

        # Create success response
        response = TokenResponse(
            success=True,
            currency_code=currency_code,
            issuer=wallet.classic_address,
            total_supply=total_supply,
            metadata=metadata,
            enable_rippling_result=enable_response.result,
            trust_set_result=trust_response.result,
            payment_result=payment_response.result,
        )

        # Print summary
        print_separator()
        print("🎉 TOKEN CREATION SUMMARY")
        print_separator()
        print(f"Token Name: {token_name}")
        print(f"Currency Code: {currency_code}")
        print(f"Total Supply: {total_supply}")
        print(f"Asset Type: {metadata['asset_details']['type']}")
        print("\n📍 Address:")
        print(f"  Issuer: {wallet.classic_address}")
        print("\n🔍 Explorer Links:")
        print(
            f"  Issuer Account: {get_explorer_url('account', wallet.classic_address)}"
        )
        print("\n📝 Transactions:")
        print(
            f"  Enable Rippling: {get_explorer_url('transaction', enable_response.result.get('hash'))}"
        )
        print(
            f"  Create Trustline: {get_explorer_url('transaction', trust_response.result.get('hash'))}"
        )
        print(
            f"  Token Payment: {get_explorer_url('transaction', payment_response.result.get('hash'))}"
        )
        print("\n📋 Asset Details:")
        print(f"  Name: {metadata['asset_details']['name']}")
        print(f"  Type: {metadata['asset_details']['type']}")
        print(f"  Description: {metadata['asset_details']['description']}")
        if metadata["asset_details"].get("geolocation"):
            geo = metadata["asset_details"]["geolocation"]
            print("\n📍 Location:")
            for key, value in geo.items():
                print(f"  {key.title()}: {value}")
        print_separator()

        return response

    except Exception as e:
        print_separator()
        print("❌ ERROR DURING TOKEN ISSUANCE")
        print_separator()
        print(f"Error details: {str(e)}")
        print_separator()
        return ErrorResponse(success=False, error=str(e))


def get_explorer_url(type: str, identifier: str) -> str:
    """Get XRPL explorer URL"""
    if type == "transaction":
        return f"{TESTNET_EXPLORER}/transactions/{identifier}"
    elif type == "account":
        return f"{TESTNET_EXPLORER}/accounts/{identifier}"
    return f"{TESTNET_EXPLORER}/{type}/{identifier}"
