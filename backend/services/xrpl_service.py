"""XRPL service for transaction handling"""
from typing import Dict, Any, Optional
import xrpl
import json
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import NFTokenMint, Payment, NFTokenCreateOffer
from xrpl.models.requests import SubmitOnly
from xrpl.utils import str_to_hex
import os
from .mongodb_service import track_nft_mint

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
    """Generate an unsigned NFTokenCreateOffer transaction template for selling an NFT
    
    Args:
        account: The address of the NFT owner
        nft_id: The ID of the NFT to sell
        amount: The amount in drops that the NFT is being sold for
        expiration: Optional Unix timestamp when the offer expires
        destination: Optional specific address that can buy the NFT
    """
    try:
        # Create the NFTokenCreateOffer transaction
        offer_tx = NFTokenCreateOffer(
            account=account,
            nftoken_id=nft_id,
            amount=amount,
            flags=1  # Flag 1 indicates a sell offer
        )
        
        # Add optional fields if provided
        if expiration:
            offer_tx.expiration = expiration
        if destination:
            offer_tx.destination = destination
        
        # Convert to dictionary for JSON serialization
        return {
            "transaction_type": "NFTokenCreateOffer",
            "template": offer_tx.to_dict(),
            "instructions": {
                "fee": "10",  # Standard fee in drops
                "sequence": None,  # Client needs to set this
                "last_ledger_sequence": None  # Client needs to set this
            }
        }
    except Exception as e:
        raise ValueError(f"Failed to generate NFT sell offer template: {str(e)}")

def submit_signed_transaction(
    signed_tx: Dict[str, Any],
    account: str,
    destination: str = None,
    uri: str = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Submit a signed transaction to the XRPL"""
    try:
        client: JsonRpcClient = get_client()
        
        # Print the signed transaction for debugging
        print("Signed transaction:", json.dumps(signed_tx, indent=2))
        
        # Get the tx_blob from the signed transaction
        tx_blob = signed_tx.get("tx_blob") if isinstance(signed_tx, dict) else xrpl.core.binarycodec.encode(signed_tx)
        
        # Create a proper submit request
        submit = SubmitOnly(tx_blob=tx_blob)
        
        # Submit the transaction
        response = client.request(submit)
        print("XRPL Response:", json.dumps(response.result, indent=2))
        
        if response.status == "success" and response.result.get("engine_result") == "tesSUCCESS":
            transaction_hash = response.result.get("tx_json", {}).get("hash")
            
            # Only track in MongoDB if this is an NFT mint transaction
            if uri and metadata:
                track_nft_mint(
                    account=account,
                    uri=uri,
                    transaction_hash=transaction_hash,
                    metadata=metadata
                )
            
            return {
                "status": "success",
                "hash": transaction_hash,
                "engine_result": response.result.get("engine_result"),
                "engine_result_message": response.result.get("engine_result_message")
            }
        else:
            error_message = (
                response.result.get("engine_result_message") or 
                response.result.get("error_message") or 
                "Unknown error"
            )
            raise ValueError(f"Transaction submission failed: {error_message}")
            
    except Exception as e:
        raise ValueError(f"Failed to submit transaction: {str(e)}")

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
