from typing import Dict, Any, Union, TypedDict, Optional
from xrpl.wallet import Wallet
from xrpl.core.keypairs import derive_keypair
from backend.services.xrpl_service import (
    issue_token,
    TokenResponse,
    ErrorResponse,
    RWAMetadata,
    AssetDetails,
    TokenizationDetails,
    AssetType,
    GeoLocation,
)


def create_token(
    wallet_data: Dict[str, str],
    asset_details: Dict[str, Any],
    token_details: Dict[str, Any],
    additional_details: Optional[Dict[str, Any]] = None,
) -> Union[TokenResponse, ErrorResponse]:
    """Create a new RWA token with the given parameters"""
    if not wallet_data.get("secret"):
        return {"success": False, "error": "Missing wallet secret"}

    try:
        # Create RWA metadata
        metadata: Dict[str, Any] = {
            "asset_details": asset_details,
            "token_details": token_details,
            "additional_details": additional_details,
        }

        # Create wallet from seed
        public_key, private_key = derive_keypair(wallet_data["secret"])
        wallet = Wallet(
            seed=wallet_data["secret"], public_key=public_key, private_key=private_key
        )

        # Issue the token
        return issue_token(
            wallet=wallet,
            token_name=token_details["token_name"],
            total_supply=int(token_details["total_supply"]),
            metadata=metadata,
        )
    except Exception as e:
        return {"success": False, "error": str(e)}
