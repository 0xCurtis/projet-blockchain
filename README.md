# XRPL NFT Platform

A platform for minting, trading, and managing NFTs on the XRP Ledger.

## Features

### NFT Management
- Mint NFTs with metadata
- Track NFT ownership
- View NFT details and history
- Transfer NFTs between accounts

### Marketplace
- List NFTs for sale
- Browse active listings
- Purchase NFTs using browser wallet
- Automatic listing status updates
- Metadata integrity verification

### Backend Services
- MongoDB integration for NFT and listing tracking
- XRPL integration for blockchain operations
- Metadata storage and verification
- Transaction validation

## Getting Started

### Prerequisites
- Python 3.8+
- MongoDB
- XRPL account
- Browser wallet (e.g., XUMM)

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-name]
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
MONGODB_URI=your_mongodb_uri
MONGODB_DB=your_database_name
XRPL_NODE_URL=your_xrpl_node_url
```

4. Run the application:
```bash
python run.py
```

## API Documentation

- [NFT API Documentation](backend/docs/nft_api.md)
- [Marketplace API Documentation](backend/docs/marketplace_api.md)

## Architecture

### Database Schema

#### NFT Collection
- NFT ID (unique)
- Account (owner)
- Transaction hash
- Metadata
- Status
- Creation timestamp

#### Marketplace Listings
- Listing ID (unique)
- NFT ID
- Seller address
- Price (in drops)
- Status (active/sold/cancelled/invalid)
- Metadata hash
- Timestamps

#### Metadata Collection
- Metadata ID (unique)
- Metadata hash
- Metadata content
- Creation timestamp

### Transaction Flow

1. **Listing NFT:**
   - Verify NFT ownership
   - Store listing in database
   - Return listing details

2. **Purchasing NFT:**
   - Frontend gets purchase info
   - Wallet creates and signs transaction
   - Backend validates transaction
   - Update listing status

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
