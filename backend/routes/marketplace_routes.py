"""Marketplace routes for NFT trading"""
from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from backend.services.mongodb_service import (
    get_listing,
    update_listing_status,
    get_metadata_by_hash,
    track_nft_offer,
    update_listing_by_offer,
    record_purchase_transaction,
    update_nft_ownership,
    get_active_offers_for_nft,
    get_all_active_offers
)
from backend.services.xrpl_service import (
    create_nft_sell_offer_template,
    verify_xrpl_transaction,
    verify_nft_ownership
)
from datetime import datetime

bp = Blueprint('marketplace', __name__, url_prefix='/api/marketplace')

@bp.route('/offers', methods=['GET'])
def get_active_offers() -> Tuple[Response, int]:
    """Get all active NFT offers with their metadata
    
    Returns:
        List of active offers with NFT metadata and offer details
    """
    try:
        # Get all active offers
        offers = get_all_active_offers()
        
        # Enrich each offer with metadata
        for offer in offers:
            if 'metadata_hash' in offer:
                metadata = get_metadata_by_hash(offer['metadata_hash'])
                if metadata:
                    offer['metadata'] = metadata
        
        return jsonify({
            'offers': offers,
            'count': len(offers)
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            
        # Convert XRP to drops
        amount_drops = int(float(data['price_xrp']) * 1_000_000)
        
        # Create the NFTokenCreateOffer template
        offer_template = create_nft_sell_offer_template(
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
        if not data.get('transaction_hash'):
            return jsonify({'error': 'transaction_hash is required'}), 400
        if not data.get('nft_id'):
            return jsonify({'error': 'nft_id is required'}), 400
        if not data.get('seller_address'):
            return jsonify({'error': 'seller_address is required'}), 400
        if not data.get('amount'):
            return jsonify({'error': 'amount is required'}), 400
            
        # Verify the transaction on XRPL
        tx_result = verify_xrpl_transaction(
            transaction_hash=data['transaction_hash'],
            expected_type="NFTokenCreateOffer"
        )
        
        if not tx_result['success']:
            return jsonify({
                'status': 'error',
                'message': tx_result['message']
            }), 400
            
        # Track the offer in our database
        offer_data = {
            'transaction_hash': data['transaction_hash'],
            'nft_id': data['nft_id'],
            'seller_address': data['seller_address'],
            'price_drops': data['amount'],
            'status': 'active',
            'offer_id': tx_result['transaction'].get('NFTokenOfferID')
        }
        
        tracked_offer = track_nft_offer(offer_data)
        
        return jsonify({
            'status': 'success',
            'transaction_hash': data['transaction_hash'],
            'offer_id': offer_data['offer_id'],
            'message': 'NFT offer created successfully'
        }), 200
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/buy/template/<offer_id>', methods=['GET'])
def create_buy_template(offer_id: str) -> Tuple[Response, int]:
    """Create an NFTokenAcceptOffer template for buying an NFT"""
    try:
        # Get the offer details from our database
        offer = get_listing(offer_id)
        if not offer:
            return jsonify({'error': 'Offer not found'}), 404
            
        if offer['status'] != 'active':
            return jsonify({'error': 'Offer is no longer active'}), 400
            
        # Create template for NFTokenAcceptOffer
        template = {
            'TransactionType': 'NFTokenAcceptOffer',
            'NFTokenSellOffer': offer_id
        }
        
        return jsonify({
            'template': template,
            'offer_details': {
                'nft_id': offer['nft_id'],
                'price_drops': offer['price_drops'],
                'seller_address': offer['seller_address']
            }
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/buy/submit', methods=['POST'])
def submit_buy_transaction() -> Tuple[Response, int]:
    """Submit a signed NFTokenAcceptOffer transaction"""
    try:
        data = request.get_json()
        required_fields = [
            'transaction_hash', 
            'nft_id', 
            'buyer_address', 
            'sell_offer_id',
            'price_drops'
        ]
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Verify the transaction on XRPL
        tx_result = verify_xrpl_transaction(
            data['transaction_hash'],
            expected_type="NFTokenAcceptOffer"
        )
        if not tx_result['success']:
            return jsonify({
                'status': 'pending',
                'message': 'Waiting for transaction confirmation'
            }), 202

        # Update NFT ownership in database
        update_nft_ownership(
            nft_id=data['nft_id'],
            new_owner=data['buyer_address'],
            transaction_hash=data['transaction_hash']
        )

        # Update marketplace listing status
        update_listing_by_offer(
            sell_offer_id=data['sell_offer_id'],
            status='completed',
            buyer_address=data['buyer_address'],
            transaction_hash=data['transaction_hash'],
            final_price_drops=data['price_drops']
        )

        # Record the purchase transaction
        record_purchase_transaction(
            nft_id=data['nft_id'],
            buyer=data['buyer_address'],
            price_drops=data['price_drops'],
            transaction_hash=data['transaction_hash']
        )

        return jsonify({
            'status': 'success',
            'message': 'Purchase tracked successfully',
            'transaction_hash': data['transaction_hash']
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to track purchase: {str(e)}'}), 500 