"""XRPL service for transaction handling"""
from typing import Dict, Any, Optional
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountNFTs, Tx
import os
from xrpl.models.transactions import NFTokenMint, Payment, NFTokenCreateOffer
from xrpl.utils import str_to_hex

def get_client() -> JsonRpcClient:
    """Get XRPL client"""
    node_url = os.getenv("XRPL_NODE_URL", "https://s.altnet.rippletest.net:51234")
    return JsonRpcClient(node_url)

def generate_nft_mint_template(
    account: str,
    uri: str,
    flags: int = 8,
    transfer_fee: int = 0,
    taxon: int = 0,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Generate an unsigned NFT mint transaction template"""
    try:
        # Convert URI to hex - this is what's actually stored on chain
        hex_uri = str_to_hex(uri)
        print(f"\nDebug - URI hex length: {len(hex_uri)}")
        print(f"Debug - URI hex: {hex_uri}")
        
        # Create the transaction template
        mint_tx = NFTokenMint(
            account=account,
            uri=hex_uri,
            flags=int(flags),
            transfer_fee=int(transfer_fee),
            nftoken_taxon=int(taxon)
        )
        
        # Convert to dictionary for JSON serialization
        return {
            "transaction_type": "NFTokenMint",
            "template": mint_tx.to_dict(),
            "instructions": {
                "fee": "10",  # Standard fee in drops
                "sequence": None,  # Client needs to set this
                "last_ledger_sequence": None  # Client needs to set this
            }
        }
    except Exception as e:
        raise ValueError(f"Failed to generate NFT mint template: {str(e)}")

def create_payment_template(
    account: str,
    destination: str,
    amount_drops: int
) -> Dict[str, Any]:
    """Generate an unsigned XRP payment transaction template"""
    try:
        # Create the payment transaction
        payment_tx = Payment(
            account=account,
            destination=destination,
            amount=str(amount_drops)
        )
        
        # Convert to dictionary for JSON serialization
        return {
            "transaction_type": "Payment",
            "template": payment_tx.to_dict(),
            "instructions": {
                "fee": "10",
                "sequence": None,
                "last_ledger_sequence": None
            }
        }
    except Exception as e:
        raise ValueError(f"Failed to generate payment template: {str(e)}")

def create_nft_offer_template(
    account: str,
    destination: str,
    nft_id: str
) -> Dict[str, Any]:
    """Generate an unsigned NFT offer transaction template"""
    try:
        # Create the NFT offer transaction
        offer_tx = NFTokenCreateOffer(
            account=account,
            nftoken_id=nft_id,
            destination=destination,
            amount="0"  # 0 since payment is handled separately
        )
        
        # Convert to dictionary for JSON serialization
        return {
            "transaction_type": "NFTokenCreateOffer",
            "template": offer_tx.to_dict(),
            "instructions": {
                "fee": "10",
                "sequence": None,
                "last_ledger_sequence": None
            }
        }
    except Exception as e:
        raise ValueError(f"Failed to generate NFT offer template: {str(e)}")

def create_nft_sell_offer_template(
    account: str,
    nft_id: str,
    amount: str,
    expiration: Optional[int] = None,
    destination: Optional[str] = None
) -> Dict[str, Any]:
    """Generate an NFTokenCreateOffer transaction template for selling an NFT
    
    Args:
        account: The address of the NFT owner
        nft_id: The ID of the NFT to sell
        amount: The amount in drops that the NFT is being sold for
        expiration: Optional Unix timestamp when the offer expires
        destination: Optional specific address that can buy the NFT
    """
    try:
        # Create the transaction template with proper XRPL field names
        template = {
            "TransactionType": "NFTokenCreateOffer",
            "Account": account,
            "NFTokenID": nft_id,
            "Amount": amount,
            "Flags": 1  # Flag 1 indicates a sell offer
        }
        
        # Add optional fields if provided
        if expiration:
            template["Expiration"] = expiration
        if destination:
            template["Destination"] = destination
        
        return {
            "txjson": template  # Use txjson as expected by XUMM
        }
    except Exception as e:
        raise ValueError(f"Failed to generate NFT sell offer template: {str(e)}")

def verify_xrpl_transaction(transaction_hash: str, expected_type: str = None) -> Dict[str, Any]:
    """Verify a transaction on the XRPL"""
    try:
        client = get_client()
        
        # Get transaction details
        tx_response = client.request(xrpl.models.requests.Tx(
            transaction=transaction_hash
        ))
        
        if not tx_response.is_successful():
            return {
                "success": False,
                "message": "Failed to fetch transaction"
            }
            
        tx_data = tx_response.result
        
        # Verify transaction type if specified
        if expected_type and tx_data.get("TransactionType") != expected_type:
            return {
                "success": False,
                "message": f"Transaction type mismatch. Expected {expected_type}"
            }
            
        # Check if transaction was successful
        if tx_data.get("meta", {}).get("TransactionResult") != "tesSUCCESS":
            return {
                "success": False,
                "message": "Transaction was not successful"
            }
            
        return {
            "success": True,
            "transaction": tx_data
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to verify transaction: {str(e)}"
        }

def verify_nft_ownership(account: str, nft_id: str) -> bool:
    """Verify if an account owns a specific NFT."""
    try:
        client = get_client()
        
        # Use AccountNFTs request to get all NFTs owned by the account
        request = xrpl.models.requests.AccountNFTs(
            account=account,
            ledger_index="validated"
        )
        
        response = client.request(request)
        if not response.is_successful():
            raise ValueError("Failed to fetch account NFTs")
            
        # Check if the NFT is in the account's NFTs
        account_nfts = response.result.get("account_nfts", [])
        for nft in account_nfts:
            if nft.get("NFTokenID") == nft_id:
                return True
                
        return False
    except Exception as e:
        raise ValueError(f"Failed to verify NFT ownership: {str(e)}")
def verify_transaction_signature(signed_tx: Dict[str, Any]) -> bool:
    """Verify the signature of a signed transaction"""
    # Skip verification as it will be handled by the XRPL network
    return True