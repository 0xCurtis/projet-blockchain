# RWA Token Platform Backend


<a href="https://github.com/psf/black/actions"><img alt="Actions Status" src="https://github.com/psf/black/workflows/Test/badge.svg"></a>
A Flask-based backend service for creating and managing Real World Asset (RWA) tokens on the XRP Ledger.

## Features

- 🪙 Create and manage RWA tokens for various asset types:
  - Real Estate
  - Fine Art
  - Vehicles
  - And more...
- 👛 Wallet management with XRPL integration
- 📊 Token and transaction tracking
- 🔍 Asset metadata storage and retrieval
- 🌐 XRPL Testnet support

## Prerequisites

- Python 3.8+
- SQLite3
- XRPL account (testnet for development)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
flask db upgrade
```

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the root directory:

```env
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=sqlite:///rwa_tokens.db
XRPL_NODE_URL=https://s.altnet.rippletest.net:51234
```

## Running the Application

1. Start the Flask server:
```bash
flask run
```

The server will start at `http://localhost:5000`

## API Endpoints

### Wallet Management

#### Create Wallet
- **POST** `/api/tokens/wallet/create`
- Creates a new XRPL wallet
- Response includes wallet address and seed

#### Get Wallet Info
- **GET** `/api/tokens/wallet/info/<address>`
- Returns wallet details and balances

### Token Management

#### Create Token
- **POST** `/api/tokens/create`
- Creates a new RWA token
- Request body:
```json
{
    "wallet": {
        "classic_address": "rXXX...",
        "secret": "sXXX..."
    },
    "asset_details": {
        "name": "Asset Name",
        "type": "real_estate",
        "description": "Asset Description",
        "geolocation": {
            "address": "123 Street",
            "city": "City",
            "country": "Country",
            "postal_code": "12345"
        }
    },
    "token_details": {
        "token_name": "Token Name",
        "currency_code": "TKN",
        "total_supply": "1"
    },
    "additional_details": {
        // Asset-specific details
    }
}
```

#### List Tokens
- **GET** `/api/tokens/list`
- Returns list of all created tokens

#### List Transactions
- **GET** `/api/tokens/transactions`
- Returns list of all token-related transactions

## Testing

Run the test suite:
```bash
pytest
```

For verbose output:
```bash
pytest -v
```

## Asset Types

### Real Estate
- Properties, buildings, land
- Includes location, square footage, amenities

### Fine Art
- Paintings, sculptures, collectibles
- Includes artist, provenance, authentication

### Vehicles
- Cars, boats, aircraft
- Includes VIN, specifications, features

## Development

### Project Structure
```
backend/
├── app.py              # Application entry point
├── models/             # Database models
├── routes/             # API routes
├── services/           # Business logic
├── tests/             # Test suite
└── migrations/        # Database migrations
```

### Adding New Features

1. Create new models in `models/`
2. Add routes in `routes/`
3. Implement business logic in `services/`
4. Add tests in `tests/`
5. Update documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)

## Support

For support, please open an issue in the GitHub repository. 