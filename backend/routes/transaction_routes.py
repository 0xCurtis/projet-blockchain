"""Transaction routes for NFT operations"""
from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from backend.services.xrpl_service import (
    generate_nft_mint_template,
    submit_signed_transaction,
    verify_transaction_signature
)
from backend.services.mongodb_service import (
    get_account_nfts,
    get_metadata_by_hash,
    get_metadata_by_id,
    compute_metadata_hash
)
import os
import json

bp = Blueprint('transaction', __name__, url_prefix='/api/transaction')

# Get the API endpoint from environment or use default
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://localhost:5000/api/transaction")

@bp.route('/nft/mint/template', methods=['POST'])
def get_nft_mint_template() -> Tuple[Response, int]:
    """Generate an NFT mint transaction template"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('account'):
            return jsonify({'error': 'account is required'}), 400
        if not data.get('metadata'):
            return jsonify({'error': 'metadata is required'}), 400
            
        # Generate a URI that references the metadata
        metadata = data.get('metadata', {})
        
        # Compute metadata hash for the URI
        metadata_hash = compute_metadata_hash(metadata)
        
        # Simple identifier format: RWA-XRPL_REAL_WORLD-{asset_type}-{metadata_hash}
        uri = f"RWA-XRPL_REAL_WORLD-{metadata.get('asset_type', 'UNKNOWN')}-{metadata_hash}"
        
        print("\n=== Debug Info ===")
        print(f"URI length: {len(uri)}")
        print(f"URI: {uri}")
        print(f"Metadata: {json.dumps(metadata, indent=2)}")
            
        # Generate the transaction template
        template = generate_nft_mint_template(
            account=data.get('account'),
            uri=uri,
            flags=data.get('flags', 8),
            transfer_fee=data.get('transfer_fee', 0),
            taxon=data.get('taxon', 0),
            metadata=metadata
        )
        
        print("\nTemplate to be sent:")
        print(json.dumps(template, indent=2))
        print("=== End Debug Info ===\n")
        
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
    """Submit a signed transaction"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('signed_transaction'):
            return jsonify({'error': 'signed_transaction is required'}), 400
        if not data.get('account'):
            return jsonify({'error': 'account is required'}), 400
        if not data.get('uri'):
            return jsonify({'error': 'uri is required'}), 400
            
        # Verify the transaction signature if provided in the correct format
        if isinstance(data.get('signed_transaction'), dict):
            if not verify_transaction_signature(data['signed_transaction']):
                return jsonify({'error': 'Invalid transaction signature'}), 400
            
        # Submit the transaction
        result = submit_signed_transaction(
            data['signed_transaction'],
            account=data['account'],
            uri=data['uri'],
            metadata=data.get('metadata', {})
        )
        
        return jsonify({
            'result': result,
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
            formatted_nft = {
                "nft_id": nft["nft_id"],
                "account": nft["account"],
                "transaction_hash": nft["transaction_hash"],
                "created_at": nft["created_at"],
                "status": nft["status"],
                "uri": nft["uri"],
                "metadata": nft.get("full_metadata", {}),
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