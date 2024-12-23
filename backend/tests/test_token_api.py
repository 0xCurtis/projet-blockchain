import os
import sys
import pytest
import json
from unittest.mock import patch
from flask import current_app

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from models import Wallet, Token, Transaction, db

@pytest.fixture
def app_context(app):
    with app.app_context():
        yield

def test_create_wallet(client, app_context):
    """Test creating a new wallet"""
    response = client.post('/api/tokens/wallet/create')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'address' in data['response']
    assert 'seed' in data['response']
    assert 'explorer_url' in data['response']
    
    # Verify wallet was saved in database
    wallet = Wallet.query.filter_by(address=data['response']['address']).first()
    assert wallet is not None
    assert wallet.address == data['response']['address']

def test_get_wallet_info(client, app_context):
    """Test getting wallet information"""
    # First create a wallet
    response = client.post('/api/tokens/wallet/create')
    wallet_data = json.loads(response.data)['response']
    
    # Get wallet info
    response = client.get(f'/api/tokens/wallet/info/{wallet_data["address"]}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'wallet' in data['response']
    assert 'account_info' in data['response']
    assert 'account_lines' in data['response']
    assert 'explorer_url' in data['response']

@patch('services.xrpl_service.submit_and_wait')
def test_create_token(mock_submit, client, app_context):
    """Test creating a new token"""
    # Mock successful transaction responses
    mock_submit.return_value.is_successful.return_value = True
    mock_submit.return_value.result = {
        'hash': 'test_hash',
        'status': 'success'
    }
    
    # First create a wallet
    response = client.post('/api/tokens/wallet/create')
    wallet_data = json.loads(response.data)['response']
    
    # Create token data
    token_data = {
        "wallet": {
            "classic_address": wallet_data['address'],
            "secret": wallet_data['seed']
        },
        "name": "TestToken",
        "supply": 1000000,
        "metadata": {
            "description": "Test token for unit testing",
            "website": "https://test.com"
        }
    }
    
    # Create token
    response = client.post('/api/tokens/create', 
                          json=token_data,
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'currency_code' in data['response']
    assert data['response']['currency_code'] == "TES"  # First 3 letters of TestToken
    
    # Verify token was saved in database
    token = Token.query.filter_by(name="TestToken").first()
    assert token is not None
    assert token.total_supply == 1000000
    assert token.token_metadata['description'] == "Test token for unit testing"
    
    # Verify transactions were saved
    transactions = Transaction.query.filter_by(token_id=token.id).all()
    assert len(transactions) == 3  # enable_rippling, trust_set, and payment transactions

@patch('services.xrpl_service.submit_and_wait')
def test_list_tokens(mock_submit, client, app_context):
    """Test listing all tokens"""
    # Mock successful transaction responses
    mock_submit.return_value.is_successful.return_value = True
    mock_submit.return_value.result = {
        'hash': 'test_hash',
        'status': 'success'
    }
    
    # First create a wallet and token
    response = client.post('/api/tokens/wallet/create')
    wallet_data = json.loads(response.data)['response']
    
    # Create two tokens
    for i in range(2):
        token_data = {
            "wallet": {
                "classic_address": wallet_data['address'],
                "secret": wallet_data['seed']
            },
            "name": f"TestToken{i}",
            "supply": 1000000 * (i + 1),
            "metadata": {
                "description": f"Test token {i} for unit testing"
            }
        }
        response = client.post('/api/tokens/create', 
                             json=token_data,
                             content_type='application/json')
        assert response.status_code == 200
    
    # List tokens
    response = client.get('/api/tokens/list')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'tokens' in data['response']
    assert len(data['response']['tokens']) == 2
    
    # Verify token details
    tokens = data['response']['tokens']
    assert tokens[0]['name'] == "TestToken0"
    assert tokens[1]['name'] == "TestToken1"
    assert tokens[0]['total_supply'] == 1000000
    assert tokens[1]['total_supply'] == 2000000

@patch('services.xrpl_service.submit_and_wait')
def test_list_transactions(mock_submit, client, app_context):
    """Test listing all transactions"""
    # Mock successful transaction responses
    mock_submit.return_value.is_successful.return_value = True
    mock_submit.return_value.result = {
        'hash': 'test_hash',
        'status': 'success'
    }
    
    # First create a wallet and token
    response = client.post('/api/tokens/wallet/create')
    wallet_data = json.loads(response.data)['response']
    
    token_data = {
        "wallet": {
            "classic_address": wallet_data['address'],
            "secret": wallet_data['seed']
        },
        "name": "TestToken",
        "supply": 1000000,
        "metadata": {
            "description": "Test token for unit testing"
        }
    }
    response = client.post('/api/tokens/create', 
                          json=token_data,
                          content_type='application/json')
    assert response.status_code == 200
    
    # List transactions
    response = client.get('/api/tokens/transactions')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'transactions' in data['response']
    
    # Should have 3 transactions for token creation
    transactions = data['response']['transactions']
    assert len(transactions) == 3
    
    # Verify transaction types
    tx_types = [tx['tx_type'] for tx in transactions]
    assert 'enable_rippling' in tx_types
    assert 'trust_set' in tx_types
    assert 'payment' in tx_types

def test_wallet_not_found(client, app_context):
    """Test error handling when wallet is not found"""
    response = client.get('/api/tokens/wallet/info/nonexistentaddress')
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert data['success'] is False
    assert "Wallet not found" in data['error']

def test_create_token_invalid_wallet(client, app_context):
    """Test error handling when creating token with invalid wallet"""
    token_data = {
        "wallet": {
            "classic_address": "invalid_address",
            "secret": "invalid_seed"
        },
        "name": "TestToken",
        "supply": 1000000,
        "metadata": {}
    }
    
    response = client.post('/api/tokens/create', 
                          json=token_data,
                          content_type='application/json')
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert data['success'] is False
    assert "Wallet not found" in data['error']