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
    track_nft_mint
) 
import os
import json 

bp = Blueprint('transactions', __name__, url_prefix='/api/transaction')

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
        # check transfer fee
        transfer_fee = data.get('transfer_fee', 0)
        if transfer_fee > 0:
            # check if transfer fee is a percentage by multiplying by 1000 and be sure it's a int not a float if so round it to the nearest int
            transfer_fee = int(round(data.get('transfer_fee') * 1000))   
        # Generate the transaction template
        template = generate_nft_mint_template(
            account=data.get('account'),
            uri=uri,
            flags=data.get('flags', 8),
            transfer_fee=transfer_fee,
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
    """Submit a signed transaction from XUMM"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('response'):
            return jsonify({'error': 'XUMM response is required'}), 400
            
        xumm_response = data['response']
        if not xumm_response.get('txid'):
            return jsonify({'error': 'Transaction ID not found in XUMM response'}), 400
            
        # Verify the transaction on XRPL
        tx_result = verify_xrpl_transaction(
            transaction_hash=xumm_response['txid']
        )
        
        if not tx_result['success']:
            return jsonify({
                'status': 'error',
                'message': tx_result['message']
            }), 400
            
        # If this is an NFT mint, track it
        if (tx_result['transaction'].get('TransactionType') == 'NFTokenMint' 
            and data.get('uri') and data.get('metadata')):
            track_nft_mint(
                account=xumm_response['account'],
                uri=data['uri'],
                transaction_hash=xumm_response['txid'],
                metadata=data['metadata']
            )
            
        return jsonify({
            'status': 'success',
            'transaction_hash': xumm_response['txid'],
            'transaction_result': tx_result['transaction'],
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