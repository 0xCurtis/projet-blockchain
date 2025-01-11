# Marketplace API Documentation

## Overview
The Marketplace API provides endpoints for listing, buying, and managing NFTs on the XRPL. The API is designed to work with browser wallets (like XUMM) for transaction signing.

## Base URL
```
/api/marketplace
```

## Endpoints

### List an NFT for Sale
Create a new listing for an NFT in the marketplace.

```http
POST /list
```

**Request Body:**
```json
{
    "nft_id": "string",
    "seller_address": "string",
    "price_xrp": "number",
    "metadata_hash": "string"
}
```

**Response (200):**
```json
{
    "listing": {
        "listing_id": "string",
        "nft_id": "string",
        "seller_address": "string",
        "price_drops": "number",
        "metadata_hash": "string",
        "status": "active",
        "created_at": "string",
        "updated_at": "string"
    },
    "message": "NFT listed successfully"
}
```

### Get All Active Listings
Retrieve all active NFT listings from the marketplace.

```http
GET /listings
```

**Response (200):**
```json
{
    "listings": [
        {
            "listing_id": "string",
            "nft_id": "string",
            "seller_address": "string",
            "price_drops": "number",
            "metadata_hash": "string",
            "metadata": {
                // NFT metadata object
            },
            "status": "active"
        }
    ],
    "count": "number"
}
```

### Get Specific Listing
Get details of a specific listing by its ID.

```http
GET /listing/{listing_id}
```

**Response (200):**
```json
{
    "listing_id": "string",
    "nft_id": "string",
    "seller_address": "string",
    "price_drops": "number",
    "metadata_hash": "string",
    "metadata": {
        // NFT metadata object
    },
    "status": "string"
}
```

### Prepare Buy Information
Get necessary information to create an NFT purchase offer in the wallet.

```http
GET /listing/{listing_id}/prepare-buy
```

**Response (200):**
```json
{
    "status": "success",
    "buy_info": {
        "nft_id": "string",
        "seller_address": "string",
        "price_drops": "number",
        "listing_id": "string",
        "metadata_hash": "string"
    }
}
```

### Validate Purchase
Validate a completed NFT purchase and update the listing status.

```http
POST /listing/{listing_id}/validate-purchase
```

**Request Body:**
```json
{
    "buyer_address": "string",
    "transaction_hash": "string"
}
```

**Response (200):**
```json
{
    "status": "success",
    "message": "Purchase validated and listing updated"
}
```

**Response (202):** - When waiting for transaction confirmation
```json
{
    "status": "pending",
    "message": "Waiting for transaction confirmation"
}
```

### Cancel Listing
Cancel an active NFT listing.

```http
POST /listing/{listing_id}/cancel
```

**Request Body:**
```json
{
    "seller_address": "string"
}
```

**Response (200):**
```json
{
    "status": "success",
    "message": "Listing cancelled successfully"
}
```

## Error Responses

All endpoints may return the following error responses:

**400 Bad Request:**
```json
{
    "error": "Description of what went wrong"
}
```

**403 Forbidden:**
```json
{
    "error": "Unauthorized action message"
}
```

**404 Not Found:**
```json
{
    "error": "Resource not found message"
}
```

**500 Internal Server Error:**
```json
{
    "error": "Internal server Error message"
}
```

## Listing Status Values
- `active`: Listing is active and NFT can be purchased
- `sold`: NFT has been sold
- `cancelled`: Listing was cancelled by the seller
- `invalid`: NFT is no longer owned by the seller

## Notes
1. All prices are stored internally in drops (1 XRP = 1,000,000 drops)
2. NFT ownership is verified before listing and purchase
3. Metadata integrity is verified using the metadata_hash
4. Browser wallet should be used for signing and submitting transactions
5. The API supports asynchronous purchase validation 