# Tokenized Asset Management Backend

A Flask-based backend for managing tokenized assets on the XRP Ledger.

## Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the Flask server:
```bash
python app.py
```

## Using the CLI

The CLI provides tools for testing the backend functionality:

1. Create a new wallet:
```bash
python cli.py create-wallet
```

2. Create a new token:
```bash
python cli.py create-token
```

## Running Tests

Execute the test suite:
```bash
python -m unittest discover tests
```

## API Endpoints

### Tokens
- POST `/api/tokens/create` - Create a new token
  - Required fields: wallet, name, supply, metadata

### Trades
- POST `/api/trades/list` - List a token for trade
- POST `/api/trades/buy` - Buy a listed token 