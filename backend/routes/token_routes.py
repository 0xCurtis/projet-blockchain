from flask import Blueprint, request, jsonify
from services.token_service import create_token
from services.xrpl_service import (
    generate_wallet, get_account_info,
    get_account_lines, get_explorer_url
)
from models import db, Wallet, Token, Transaction
from datetime import datetime

token_blueprint = Blueprint("tokens", __name__)

@token_blueprint.route("/wallet/create", methods=["POST"])
def create_wallet_route():
    try:
        # Create wallet on XRPL
        xrpl_wallet = generate_wallet()
        
        # Save to database
        wallet = Wallet(
            address=xrpl_wallet.classic_address,
            seed=xrpl_wallet.seed,
            last_synced=datetime.utcnow()
        )
        db.session.add(wallet)
        db.session.commit()
        
        response = {
            'address': wallet.address,
            'seed': wallet.seed,
            'explorer_url': get_explorer_url('account', wallet.address)
        }
        return jsonify({"success": True, "response": response}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

@token_blueprint.route("/wallet/info/<address>", methods=["GET"])
def get_wallet_info_route(address):
    try:
        # Get wallet from database
        wallet = Wallet.query.filter_by(address=address).first()
        if not wallet:
            return jsonify({"success": False, "error": "Wallet not found"}), 404
        
        # Get XRPL data
        account_info = get_account_info(address)
        account_lines = get_account_lines(address)
        explorer_url = get_explorer_url('account', address)
        
        # Update last synced time
        wallet.last_synced = datetime.utcnow()
        db.session.commit()
        
        response = {
            'wallet': wallet.to_dict(),
            'account_info': account_info,
            'account_lines': account_lines,
            'explorer_url': explorer_url
        }
        return jsonify({"success": True, "response": response}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

@token_blueprint.route("/create", methods=["POST"])
def create_token_route():
    try:
        data = request.json
        wallet_data = data["wallet"]
        token_name = data["name"]
        total_supply = data["supply"]
        token_metadata = data.get("metadata", {})  # Optional metadata
        
        # Get wallet from database
        wallet = Wallet.query.filter_by(address=wallet_data["classic_address"]).first()
        if not wallet:
            return jsonify({"success": False, "error": "Wallet not found"}), 404
        
        # Create token on XRPL
        response = create_token(wallet_data, token_name, total_supply, token_metadata)
        
        if response["success"]:
            # Save token to database
            token = Token(
                currency_code=response["currency_code"],
                name=token_name,
                total_supply=total_supply,
                token_metadata=token_metadata,
                issuer_id=wallet.id,
                enable_rippling_tx=response["enable_rippling_result"]["hash"],
                trust_set_tx=response["trust_set_result"]["hash"],
                payment_tx=response["payment_result"]["hash"]
            )
            db.session.add(token)
            
            # Save transactions
            transactions = [
                Transaction(
                    tx_hash=response["enable_rippling_result"]["hash"],
                    tx_type="enable_rippling",
                    wallet_id=wallet.id,
                    token_id=token.id,
                    status="success",
                    raw_data=response["enable_rippling_result"]
                ),
                Transaction(
                    tx_hash=response["trust_set_result"]["hash"],
                    tx_type="trust_set",
                    wallet_id=wallet.id,
                    token_id=token.id,
                    status="success",
                    raw_data=response["trust_set_result"]
                ),
                Transaction(
                    tx_hash=response["payment_result"]["hash"],
                    tx_type="payment",
                    wallet_id=wallet.id,
                    token_id=token.id,
                    status="success",
                    raw_data=response["payment_result"]
                )
            ]
            db.session.add_all(transactions)
            db.session.commit()
            
            return jsonify({"success": True, "response": response}), 200
        else:
            return jsonify({"success": False, "error": response["error"]}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

@token_blueprint.route("/list", methods=["GET"])
def list_tokens_route():
    try:
        tokens = Token.query.all()
        return jsonify({
            "success": True,
            "response": {
                "tokens": [token.to_dict() for token in tokens]
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@token_blueprint.route("/transactions", methods=["GET"])
def list_transactions_route():
    try:
        transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
        return jsonify({
            "success": True,
            "response": {
                "transactions": [tx.to_dict() for tx in transactions]
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400 