"""Transaction routes for handling XRPL transactions"""
from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from backend.services.xrpl_service import (
    generate_nft_mint_template,
    verify_xrpl_transaction,
)
from backend.services.mongodb_service import (
    get_account_nfts,
    get_metadata_by_hash,
    get_metadata_by_id,
    compute_metadata_hash,
    track_nft_mint,
    get_metadata_with_image,
    store_metadata
) 
import os
import json 

bp = Blueprint('transactions', __name__, url_prefix='/api/transaction')

# Get the API endpoint from environment or use default
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://localhost:5000/api/transaction")

@bp.route('/nft/mint/template', methods=['POST'])
def get_nft_mint_template() -> Tuple[Response, int]:
    """Generate an NFT mint transaction template.
    
    Expected request body:
    {
        "account": str,          # XRPL account address
        "metadata": dict,        # NFT metadata
        "image": str,           # Optional base64 encoded image
        "transfer_fee": float,   # Optional transfer fee percentage
        "flags": int,           # Optional flags
        "taxon": int            # Optional taxon
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('account'):
            return jsonify({'error': 'account is required'}), 400
        if not data.get('metadata'):
            return jsonify({'error': 'metadata is required'}), 400
            
        # Extract image if present
        image_data = data.get('image')
        metadata = data.get('metadata', {})
        
        # Store metadata and get hash
        metadata_hash, _ = store_metadata(metadata, image_data)
        
        # Create URI with metadata hash
        uri = f"RWA-XRPL_REAL_WORLD-{metadata.get('asset_type', 'UNKNOWN')}-{metadata_hash}"
        
        # Handle transfer fee
        transfer_fee = data.get('transfer_fee', 0)
        if transfer_fee > 0:
            transfer_fee = int(round(transfer_fee * 1000))
            
        # Generate template
        template = generate_nft_mint_template(
            account=data.get('account'),
            uri=uri,
            flags=data.get('flags', 8),
            transfer_fee=transfer_fee,
            taxon=data.get('taxon', 0),
            metadata=metadata
        )
        
        return jsonify({
            'template': template,
            'metadata_hash': metadata_hash,
            'uri': uri,
            'message': 'Sign this transaction template with your private key'
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/metadata/hash/<metadata_hash>', methods=['GET'])
def get_metadata_by_hash_route(metadata_hash: str) -> Tuple[Response, int]:
    """Get NFT metadata by hash"""
    try:
        metadata_result = get_metadata_by_hash(metadata_hash)
        return jsonify(metadata_result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/metadata/id/<metadata_id>', methods=['GET'])
def get_metadata_by_id_route(metadata_id: str) -> Tuple[Response, int]:
    """Get NFT metadata by ID"""
    try:
        metadata_result = get_metadata_by_id(metadata_id)
        return jsonify(metadata_result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/submit', methods=['POST'])
def submit_transaction() -> Tuple[Response, int]:
    """Submit a signed transaction from XUMM"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('response'):
            return jsonify({'error': 'XUMM response is required'}), 400
        if not data.get('uri'):
            return jsonify({'error': 'URI is required'}), 400
        if not data.get('metadata'):
            return jsonify({'error': 'Metadata is required'}), 400
            
        xumm_response = data['response']
        if not xumm_response.get('txid'):
            return jsonify({'error': 'Transaction ID not found in XUMM response'}), 400
            
        # Add transaction hash to metadata
        metadata = data['metadata']
        metadata['minting_transaction'] = xumm_response['txid']
        
        track_nft_mint(
            account=xumm_response['account'],
            uri=data['uri'],
            transaction_hash=xumm_response['txid'],
            metadata=metadata
        )
            
        return jsonify({
            'status': 'success',
            'message': 'Transaction submitted successfully'
        }), 200
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/nfts/<address>', methods=['GET'])
def get_address_nfts(address: str) -> Tuple[Response, int]:
    """Get all NFTs for an address with their full metadata"""
    try:
        # Get NFTs with metadata already included from MongoDB
        nfts = get_account_nfts(address)
        
        # Format the response
        formatted_nfts = []
        for nft in nfts:
            # Get metadata with image if available
            metadata = get_metadata_with_image(nft["metadata_hash"]) if "metadata_hash" in nft else {}
            
            formatted_nft = {
                "nft_id": nft["nft_id"],
                "account": nft["account"],
                "transaction_hash": nft["transaction_hash"],
                "created_at": nft["created_at"],
                "status": nft["status"],
                "uri": nft["uri"],
                "metadata": metadata,
                "metadata_verified": nft.get("metadata_verified", False)
            }
            formatted_nfts.append(formatted_nft)
        
        return jsonify({
            'nfts': formatted_nfts,
            'count': len(formatted_nfts),
            'address': address
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500 