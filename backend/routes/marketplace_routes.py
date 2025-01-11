"""Marketplace routes for NFT trading"""
from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from backend.services.mongodb_service import (
    create_listing,
    get_active_listings,
    get_listing,
    update_listing_status,
    get_metadata_by_hash,
    track_nft_offer
)
from backend.services.xrpl_service import (
    create_payment_template,
    create_nft_offer_template,
    verify_nft_ownership,
    create_nft_sell_offer_template,
    verify_xrpl_transaction
)
from datetime import datetime

bp = Blueprint('marketplace', __name__, url_prefix='/api/marketplace')

@bp.route('/list', methods=['POST'])
def list_nft() -> Tuple[Response, int]:
    """Create a new NFT listing"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('nft_id'):
            return jsonify({'error': 'nft_id is required'}), 400
        if not data.get('seller_address'):
            return jsonify({'error': 'seller_address is required'}), 400
        if not data.get('price_xrp'):
            return jsonify({'error': 'price_xrp is required'}), 400
        if not data.get('metadata_hash'):
            return jsonify({'error': 'metadata_hash is required'}), 400
            
        # Verify NFT ownership
        if not verify_nft_ownership(data['seller_address'], data['nft_id']):
            return jsonify({'error': 'Seller does not own this NFT'}), 403

        # Create the listing
        listing = create_listing(
            nft_id=data['nft_id'],
            seller_address=data['seller_address'],
            price_xrp=float(data['price_xrp']),
            metadata_hash=data['metadata_hash']
        )
        
        return jsonify({
            'listing': listing,
            'message': 'NFT listed successfully'
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/listings', methods=['GET'])
def get_listings() -> Tuple[Response, int]:
    """Get all active NFT listings"""
    try:
        listings = get_active_listings()
        return jsonify({
            'listings': listings,
            'count': len(listings)
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/listing/<listing_id>', methods=['GET'])
def get_listing_by_id(listing_id: str) -> Tuple[Response, int]:
    """Get a specific NFT listing"""
    try:
        listing = get_listing(listing_id)
        return jsonify(listing), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/buy/template/<listing_id>', methods=['POST'])
def get_buy_template(listing_id: str) -> Tuple[Response, int]:
    """Get transaction template for buying an NFT"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('buyer_address'):
            return jsonify({'error': 'buyer_address is required'}), 400
            
        # Get the listing
        listing = get_listing(listing_id)
        if listing['status'] != 'active':
            return jsonify({'error': 'Listing is not active'}), 400
            
        # Verify seller still owns the NFT
        if not verify_nft_ownership(listing['seller_address'], listing['nft_id']):
            # Update listing status to indicate NFT was transferred
            update_listing_status(listing_id, "invalid", reason="NFT no longer owned by seller")
            return jsonify({'error': 'NFT is no longer owned by the seller'}), 400
            
        # Create payment template
        payment_template = create_payment_template(
            account=data['buyer_address'],
            destination=listing['seller_address'],
            amount_drops=listing['price_drops']
        )
        
        # Create NFT offer template
        nft_offer_template = create_nft_offer_template(
            account=listing['seller_address'],
            destination=data['buyer_address'],
            nft_id=listing['nft_id']
        )
        
        return jsonify({
            'payment_template': payment_template,
            'nft_offer_template': nft_offer_template,
            'listing': listing,
            'message': 'Sign and submit both transactions to complete the purchase'
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/buy/submit/<listing_id>', methods=['POST'])
def submit_buy_transaction(listing_id: str) -> Tuple[Response, int]:
    """Submit signed transactions for buying an NFT"""
    pass

@bp.route('/listing/<listing_id>/prepare-buy', methods=['GET'])
def prepare_buy_info(listing_id: str) -> Tuple[Response, int]:
    """Get necessary information to create an NFT offer in the wallet"""
    try:
        listing = get_listing(listing_id)
        
        # Prepare the response with all necessary information for the wallet
        buy_info = {
            'nft_id': listing['nft_id'],
            'seller_address': listing['seller_address'],
            'price_drops': listing['price_drops'],  # Price in drops for exact amount
            'listing_id': listing_id,
            'metadata_hash': listing['metadata_hash']
        }
        
        return jsonify({
            'status': 'success',
            'buy_info': buy_info
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to prepare buy info: {str(e)}'}), 500

@bp.route('/listing/<listing_id>/validate-purchase', methods=['POST'])
def validate_purchase(listing_id: str) -> Tuple[Response, int]:
    """Validate a completed NFT purchase and update listing status"""
    try:
        data = request.get_json()
        required_fields = ['buyer_address', 'transaction_hash']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        listing = get_listing(listing_id)
        
        # Verify the new owner
        if not verify_nft_ownership(data['buyer_address'], listing['nft_id']):
            return jsonify({
                'status': 'pending',
                'message': 'Waiting for transaction confirmation'
            }), 202
            
        # Update listing status to sold
        update_listing_status(listing_id, 'sold', {
            'buyer_address': data['buyer_address'],
            'transaction_hash': data['transaction_hash'],
            'sold_at': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Purchase validated and listing updated'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to validate purchase: {str(e)}'}), 500

@bp.route('/listing/<listing_id>/cancel', methods=['POST'])
def cancel_listing(listing_id: str) -> Tuple[Response, int]:
    """Cancel an active listing"""
    try:
        data = request.get_json()
        if 'seller_address' not in data:
            return jsonify({'error': 'Seller address is required'}), 400
            
        listing = get_listing(listing_id)
        
        # Verify the seller owns the listing
        if listing['seller_address'] != data['seller_address']:
            return jsonify({'error': 'Unauthorized to cancel this listing'}), 403
            
        # Update listing status to cancelled
        update_listing_status(listing_id, 'cancelled', {
            'cancelled_at': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Listing cancelled successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to cancel listing: {str(e)}'}), 500 

@bp.route('/list/template', methods=['POST'])
def create_sell_offer_template() -> Tuple[Response, int]:
    """Create an NFTokenCreateOffer template for selling an NFT"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('nft_id'):
            return jsonify({'error': 'nft_id is required'}), 400
        if not data.get('price_xrp'):
            return jsonify({'error': 'price_xrp is required'}), 400
        if not data.get('seller_address'):
            return jsonify({'error': 'seller_address is required'}), 400
            
        # Verify NFT ownership
        if not verify_nft_ownership(data['seller_address'], data['nft_id']):
            return jsonify({'error': 'Seller does not own this NFT'}), 403

        # Create the NFTokenCreateOffer template
        amount_drops = int(float(data['price_xrp']) * 1_000_000)  # Convert XRP to drops
        offer_template = create_nft_sell_offer_template(
            account=data['seller_address'],
            nft_id=data['nft_id'],
            amount=str(amount_drops)  # Amount in drops as string
        )
        
        return jsonify({
            'offer_template': offer_template,
            'message': 'Offer template created successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/list/submit', methods=['POST'])
def submit_sell_offer() -> Tuple[Response, int]:
    """Submit a signed NFTokenCreateOffer transaction"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('response'):
            return jsonify({'error': 'XUMM response is required'}), 400
        if not data.get('nft_id'):
            return jsonify({'error': 'nft_id is required'}), 400
        if not data.get('amount'):
            return jsonify({'error': 'amount is required'}), 400
            
        xumm_response = data['response']
        if not xumm_response.get('txid'):
            return jsonify({'error': 'Transaction ID not found in XUMM response'}), 400
            
        # Verify the transaction on XRPL
        tx_result = verify_xrpl_transaction(
            transaction_hash=xumm_response['txid'],
            expected_type="NFTokenCreateOffer"
        )
        
        if not tx_result['success']:
            return jsonify({
                'status': 'error',
                'message': tx_result['message']
            }), 400
            
        # Track the offer in our database
        offer_data = {
            'transaction_hash': xumm_response['txid'],
            'nft_id': data['nft_id'],
            'seller_address': xumm_response['account'],
            'price_drops': data['amount'],
            'status': 'active',
            'offer_id': tx_result['transaction'].get('NFTokenOfferID', '')  # Store the offer ID from XRPL
        }
        
        tracked_offer = track_nft_offer(offer_data)
        
        return jsonify({
            'status': 'success',
            'transaction_hash': xumm_response['txid'],
            'offer_id': offer_data['offer_id'],
            'message': 'NFT offer created successfully'
        }), 200
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500 