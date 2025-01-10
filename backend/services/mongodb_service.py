"""MongoDB service for NFT tracking"""
from typing import Dict, Any, List, Tuple
from pymongo import MongoClient
import os
from datetime import datetime
import uuid
import json
import hashlib

def get_db():
    """Get MongoDB database connection"""
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    client = MongoClient(mongo_uri)
    db_name = os.getenv("MONGODB_DB", "xrpl_nft_platform")
    return client[db_name]

def compute_metadata_hash(metadata: Dict[str, Any]) -> str:
    """Compute a deterministic hash of metadata."""
    # Sort keys for consistent hashing
    metadata_str = json.dumps(metadata, sort_keys=True)
    return hashlib.sha256(metadata_str.encode()).hexdigest()[:16]

def verify_metadata(metadata_hash: str, metadata: Dict[str, Any]) -> bool:
    """Verify metadata integrity against its hash."""
    computed_hash = compute_metadata_hash(metadata)
    return computed_hash == metadata_hash

def store_metadata(metadata: Dict[str, Any]) -> Tuple[str, str]:
    """Store metadata and return its hash and ID.
    
    Returns:
        Tuple of (metadata_hash, metadata_id)
        - metadata_hash: SHA-256 hash of the metadata (stored on-chain)
        - metadata_id: Database ID for retrieval
    """
    try:
        db = get_db()
        metadata_collection = db.nft_metadata
        
        # Generate a deterministic hash of the metadata
        metadata_hash = compute_metadata_hash(metadata)
        
        # Generate unique ID for database storage
        metadata_id = str(uuid.uuid4())
        
        metadata_doc = {
            "metadata_id": metadata_id,
            "metadata_hash": metadata_hash,
            "metadata": metadata,
            "created_at": datetime.utcnow()
        }
        
        # Store with both hash and ID indexes
        metadata_collection.insert_one(metadata_doc)
        return metadata_hash, metadata_id
    except Exception as e:
        raise ValueError(f"Failed to store metadata: {str(e)}")

def get_metadata_by_hash(metadata_hash: str) -> Dict[str, Any]:
    """Retrieve and verify metadata by its hash."""
    try:
        db = get_db()
        metadata_collection = db.nft_metadata
        
        result = metadata_collection.find_one({"metadata_hash": metadata_hash})
        if not result:
            raise ValueError(f"Metadata not found for hash: {metadata_hash}")
        
        # Verify integrity
        if not verify_metadata(metadata_hash, result["metadata"]):
            raise ValueError("Metadata integrity check failed")
            
        return {
            "metadata": result["metadata"],
            "metadata_hash": metadata_hash,
            "verified": True
        }
    except Exception as e:
        raise ValueError(f"Failed to retrieve metadata: {str(e)}")

def get_metadata_by_id(metadata_id: str) -> Dict[str, Any]:
    """Retrieve metadata by its ID."""
    try:
        db = get_db()
        metadata_collection = db.nft_metadata
        
        result = metadata_collection.find_one({"metadata_id": metadata_id})
        if not result:
            raise ValueError(f"Metadata not found for ID: {metadata_id}")
            
        # Verify integrity
        metadata_hash = result["metadata_hash"]
        verified = verify_metadata(metadata_hash, result["metadata"])
            
        return {
            "metadata": result["metadata"],
            "metadata_hash": metadata_hash,
            "verified": verified
        }
    except Exception as e:
        raise ValueError(f"Failed to retrieve metadata: {str(e)}")

def track_nft_mint(
    account: str,
    uri: str,
    transaction_hash: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Track NFT minting in MongoDB"""
    try:
        db = get_db()
        nft_collection = db.nfts

        # Generate a unique NFT ID
        nft_id = str(uuid.uuid4())

        # Store the full metadata and get its hash and ID
        metadata_hash, metadata_id = store_metadata(metadata)

        # Create platform metadata with minimal info
        platform_metadata = {
            "platform_minted": True,
            "nft_id": nft_id,
            "metadata_id": metadata_id,
            "metadata_hash": metadata_hash
        }

        nft_data = {
            "nft_id": nft_id,
            "account": account,
            "uri": uri,
            "transaction_hash": transaction_hash,
            "metadata": platform_metadata,
            "created_at": datetime.utcnow(),
            "status": "minted"
        }

        result = nft_collection.insert_one(nft_data)
        nft_data["_id"] = str(result.inserted_id)
        return nft_data
    except Exception as e:
        raise ValueError(f"Failed to track NFT in database: {str(e)}")

def get_account_nfts(account: str) -> List[Dict[str, Any]]:
    """Get all NFTs minted by an account through our platform"""
    try:
        db = get_db()
        nft_collection = db.nfts
        
        nfts = list(nft_collection.find({"account": account}))
        # Convert ObjectId to string for JSON serialization
        for nft in nfts:
            nft["_id"] = str(nft["_id"])
            # Fetch full metadata for each NFT
            if "metadata" in nft and "metadata_id" in nft["metadata"]:
                try:
                    metadata_result = get_metadata_by_id(nft["metadata"]["metadata_id"])
                    nft["full_metadata"] = metadata_result["metadata"]
                    nft["metadata_verified"] = metadata_result["verified"]
                except ValueError:
                    nft["full_metadata"] = {"error": "Metadata not found"}
                    nft["metadata_verified"] = False
        
        return nfts
    except Exception as e:
        raise ValueError(f"Failed to retrieve NFTs from database: {str(e)}")

def update_nft_status(transaction_hash: str, status: str) -> Dict[str, Any]:
    """Update NFT status in database"""
    try:
        db = get_db()
        nft_collection = db.nfts
        
        result = nft_collection.update_one(
            {"transaction_hash": transaction_hash},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise ValueError(f"NFT with transaction hash {transaction_hash} not found")
            
        return {"status": "success", "message": f"NFT status updated to {status}"}
    except Exception as e:
        raise ValueError(f"Failed to update NFT status: {str(e)}")

def create_listing(
    nft_id: str,
    seller_address: str,
    price_xrp: float,
    metadata_hash: str
) -> Dict[str, Any]:
    """Create a new marketplace listing"""
    try:
        db = get_db()
        listing_collection = db.marketplace_listings
        
        # Check if NFT is already listed
        existing = listing_collection.find_one({
            "nft_id": nft_id,
            "status": "active"
        })
        if existing:
            raise ValueError(f"NFT {nft_id} is already listed for sale")
        
        listing = {
            "listing_id": str(uuid.uuid4()),
            "nft_id": nft_id,
            "seller_address": seller_address,
            "price_drops": int(price_xrp * 1_000_000),  # Convert XRP to drops
            "metadata_hash": metadata_hash,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = listing_collection.insert_one(listing)
        listing["_id"] = str(result.inserted_id)
        return listing
    except Exception as e:
        raise ValueError(f"Failed to create listing: {str(e)}")

def get_active_listings() -> List[Dict[str, Any]]:
    """Get all active marketplace listings"""
    try:
        db = get_db()
        listing_collection = db.marketplace_listings
        
        listings = list(listing_collection.find({"status": "active"}))
        for listing in listings:
            listing["_id"] = str(listing["_id"])
            # Get NFT metadata
            try:
                metadata_result = get_metadata_by_hash(listing["metadata_hash"])
                listing["metadata"] = metadata_result["metadata"]
            except ValueError:
                listing["metadata"] = {"error": "Metadata not found"}
        
        return listings
    except Exception as e:
        raise ValueError(f"Failed to get listings: {str(e)}")

def get_listing(listing_id: str) -> Dict[str, Any]:
    """Get a specific listing by ID"""
    try:
        db = get_db()
        listing_collection = db.marketplace_listings
        
        listing = listing_collection.find_one({"listing_id": listing_id})
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")
            
        listing["_id"] = str(listing["_id"])
        # Get NFT metadata
        try:
            metadata_result = get_metadata_by_hash(listing["metadata_hash"])
            listing["metadata"] = metadata_result["metadata"]
        except ValueError:
            listing["metadata"] = {"error": "Metadata not found"}
        
        return listing
    except Exception as e:
        raise ValueError(f"Failed to get listing: {str(e)}")

def update_listing_status(listing_id: str, status: str, additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Update the status of a marketplace listing and add additional data"""
    try:
        db = get_db()
        listing_collection = db.marketplace_listings
        
        # Verify listing exists
        existing = listing_collection.find_one({"listing_id": listing_id})
        if not existing:
            raise ValueError(f"Listing {listing_id} not found")
            
        # Prepare update data
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        # Add any additional data
        if additional_data:
            update_data.update(additional_data)
        
        # Update the listing
        result = listing_collection.update_one(
            {"listing_id": listing_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise ValueError(f"Failed to update listing {listing_id}")
            
        # Get and return the updated listing
        updated_listing = listing_collection.find_one({"listing_id": listing_id})
        updated_listing["_id"] = str(updated_listing["_id"])
        return updated_listing
        
    except Exception as e:
        raise ValueError(f"Failed to update listing status: {str(e)}")

def ensure_indexes():
    """Ensure required indexes exist in MongoDB"""
    try:
        db = get_db()
        nft_collection = db.nfts
        metadata_collection = db.nft_metadata
        listing_collection = db.marketplace_listings
        
        # Create unique index on nft_id
        nft_collection.create_index("nft_id", unique=True)
        
        # Create index on account for faster queries
        nft_collection.create_index("account")
        
        # Create unique index on transaction_hash
        nft_collection.create_index("transaction_hash", unique=True)
        
        # Create unique indexes for metadata collection
        metadata_collection.create_index("metadata_id", unique=True)
        metadata_collection.create_index("metadata_hash", unique=True)
        
        # Create indexes for marketplace listings
        listing_collection.create_index("listing_id", unique=True)
        listing_collection.create_index("nft_id")
        listing_collection.create_index("seller_address")
        listing_collection.create_index("status")
        
        return True
    except Exception as e:
        raise ValueError(f"Failed to create indexes: {str(e)}")

# Create indexes when module is imported
ensure_indexes() 