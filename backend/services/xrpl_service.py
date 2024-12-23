import xrpl
from xrpl.wallet import generate_faucet_wallet, Wallet
from xrpl.models.transactions import Payment, TrustSet, AccountSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountLines, AccountInfo
from xrpl.transaction import submit_and_wait
from xrpl.utils import str_to_hex
from xrpl.constants import XRPLException

# Connect to XRP Ledger Testnet
CLIENT = xrpl.clients.JsonRpcClient("https://s.altnet.rippletest.net:51234")
TESTNET_EXPLORER = "https://testnet.xrpl.org"

def get_explorer_url(type, identifier):
    """Get the explorer URL for a transaction or account"""
    if type == "transaction":
        return f"{TESTNET_EXPLORER}/transactions/{identifier}"
    elif type == "account":
        return f"{TESTNET_EXPLORER}/accounts/{identifier}"
    return None

def get_account_info(wallet_address):
    """Get account information including XRP balance"""
    try:
        acct_info = AccountInfo(
            account=wallet_address,
            ledger_index="validated"
        )
        response = CLIENT.request(acct_info)
        return response.result
    except Exception as e:
        return {"error": str(e)}

def get_account_lines(wallet_address):
    """Get all trust lines and token balances for an account"""
    try:
        acct_lines = AccountLines(
            account=wallet_address,
            ledger_index="validated"
        )
        response = CLIENT.request(acct_lines)
        return response.result
    except Exception as e:
        return {"error": str(e)}

def generate_wallet():
    """Generate a new testnet wallet with faucet funding"""
    wallet = generate_faucet_wallet(CLIENT)
    return wallet

def enable_rippling(wallet):
    """Enable rippling for the account to allow token issuance"""
    account_set = AccountSet(
        account=wallet.classic_address,
        set_flag=8  # Enable rippling
    )
    response = submit_and_wait(account_set, wallet, CLIENT)
    return response

def issue_token(wallet_data, token_name, total_supply, metadata):
    """Issue a new token on the XRPL testnet"""
    try:
        # Create XRPL wallet object from wallet data
        wallet = Wallet.from_seed(wallet_data['secret'])
        
        # First, enable rippling for the account
        enable_response = enable_rippling(wallet)
        if not enable_response.is_successful():
            raise XRPLException("Failed to enable rippling")

        # Create currency code (3 characters)
        currency_code = token_name[:3].upper()
        
        # Create the token issuance transaction
        issue_amount = IssuedCurrencyAmount(
            currency=currency_code,
            issuer=wallet.classic_address,
            value=str(total_supply)
        )

        # Create a trustline to self (required for issuance)
        trust_set = TrustSet(
            account=wallet.classic_address,
            limit_amount=issue_amount
        )
        
        trust_response = submit_and_wait(trust_set, wallet, CLIENT)
        
        if not trust_response.is_successful():
            raise XRPLException("Failed to create trustline")

        # Issue the token through a payment to self
        payment = Payment(
            account=wallet.classic_address,
            destination=wallet.classic_address,
            amount=issue_amount
        )
        
        payment_response = submit_and_wait(payment, wallet, CLIENT)

        if not payment_response.is_successful():
            raise XRPLException("Failed to issue token")

        return {
            "success": True,
            "currency_code": currency_code,
            "issuer": wallet.classic_address,
            "total_supply": total_supply,
            "metadata": metadata,
            "enable_rippling_result": enable_response.result,
            "trust_set_result": trust_response.result,
            "payment_result": payment_response.result,
            "explorer_urls": {
                "account": get_explorer_url("account", wallet.classic_address),
                "enable_tx": get_explorer_url("transaction", enable_response.result['hash']),
                "trust_tx": get_explorer_url("transaction", trust_response.result['hash']),
                "payment_tx": get_explorer_url("transaction", payment_response.result['hash'])
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }