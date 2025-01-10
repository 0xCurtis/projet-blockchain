import pytest
from unittest.mock import patch, MagicMock
from services.xrpl_service import (
    verify_nft_ownership,
    submit_signed_transaction
)
from services.mongodb_service import (
    create_listing,
    get_active_listings,
    get_listing,
    get_account_nfts
)

def test_verify_nft_ownership():
    """Test NFT ownership verification."""
    test_address = "rTestAddress123"
    test_nft_id = "test-nft-id"
    
    with patch('xrpl.clients.JsonRpcClient.request') as mock_request:
        mock_request.return_value.is_successful.return_value = True
        mock_request.return_value.result = {
            "account_nfts": [{"NFTokenID": test_nft_id}]
        }
        
        result = verify_nft_ownership(test_address, test_nft_id)
        assert result is True

def test_submit_signed_transaction():
    """Test transaction submission."""
    test_tx = {
        "tx_blob": "test_blob",
        "hash": "test_hash"
    }
    
    with patch('xrpl.clients.JsonRpcClient.request') as mock_request:
        mock_request.return_value.status = "success"
        mock_request.return_value.result = {
            "engine_result": "tesSUCCESS",
            "tx_json": {"hash": "test_hash"}
        }
        
        result = submit_signed_transaction(test_tx, "rTestAddress123")
        assert result is not None
        assert result['status'] == "success"
        assert result['engine_result'] == "tesSUCCESS"

# MongoDB Service Tests
def test_create_listing():
    """Test marketplace listing creation."""
    test_data = {
        "nft_id": "test-nft-id",
        "seller_address": "rTestAddress123",
        "price_xrp": 100.0,
        "metadata_hash": "test-hash"
    }
    
    with patch('pymongo.collection.Collection.find_one') as mock_find_one, \
         patch('pymongo.collection.Collection.insert_one') as mock_insert:
        # Mock that NFT is not already listed
        mock_find_one.return_value = None
        mock_insert.return_value.inserted_id = "test-id"
        
        listing = create_listing(**test_data)
        assert listing is not None
        assert listing['nft_id'] == test_data['nft_id']
        assert listing['seller_address'] == test_data['seller_address']
        assert listing['price_drops'] == int(test_data['price_xrp'] * 1_000_000)
        assert listing['status'] == "active"

def test_get_active_listings():
    """Test retrieval of active listings."""
    mock_listings = [{
        "_id": "test-id",
        "listing_id": "test-listing-id",
        "nft_id": "test-nft-id",
        "seller_address": "rTestAddress123",
        "price_drops": 100_000_000,
        "metadata_hash": "test-hash",
        "status": "active"
    }]
    
    with patch('pymongo.collection.Collection.find') as mock_find, \
         patch('services.mongodb_service.get_metadata_by_hash') as mock_get_metadata:
        mock_find.return_value = mock_listings
        mock_get_metadata.return_value = {
            "metadata": {"title": "Test NFT"},
            "metadata_hash": "test-hash",
            "verified": True
        }
        
        listings = get_active_listings()
        assert listings is not None
        assert len(listings) == 1
        assert listings[0]['status'] == "active"
        assert listings[0]['metadata'] == {"title": "Test NFT"}

def test_get_listing():
    """Test retrieval of specific listing."""
    test_id = "test-listing-id"
    mock_listing = {
        "_id": "test-mongo-id",
        "listing_id": test_id,
        "nft_id": "test-nft-id",
        "status": "active",
        "metadata_hash": "test-hash"
    }
    
    with patch('pymongo.collection.Collection.find_one') as mock_find_one:
        mock_find_one.return_value = mock_listing
        
        listing = get_listing(test_id)
        assert listing is not None
        assert listing['listing_id'] == test_id

def test_get_nfts_by_address():
    """Test NFT retrieval by address."""
    test_address = "rTestAddress123"
    mock_nfts = [{
        "_id": "test-id",
        "nft_id": "test-nft-id",
        "account": test_address,
        "metadata": {
            "metadata_id": "test-metadata-id",
            "metadata_hash": "test-hash"
        }
    }]
    
    with patch('pymongo.collection.Collection.find') as mock_find, \
         patch('services.mongodb_service.get_metadata_by_id') as mock_get_metadata:
        mock_find.return_value = mock_nfts
        mock_get_metadata.return_value = {
            "metadata": {"title": "Test NFT"},
            "metadata_hash": "test-hash",
            "verified": True
        }
        
        nfts = get_account_nfts(test_address)
        assert nfts is not None
        assert len(nfts) == 1
        assert nfts[0]['account'] == test_address
        assert nfts[0]['full_metadata'] == {"title": "Test NFT"}
        assert nfts[0]['metadata_verified'] == True 