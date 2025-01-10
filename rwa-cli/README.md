# RWA CLI Tool

A command-line interface tool for managing Real World Assets (RWA) tokens on the XRPL testnet.

## Features

- Create and manage XRPL testnet wallets
- Create RWA tokens for various asset types:
  - Real Estate
  - Fine Art
  - Commodities
  - Vehicles
  - Intellectual Property
- View wallet details and balances
- List created tokens and their details
- Track token transactions

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd rwa-cli
```

2. Install the package:
```bash
pip install -e .
```

## Usage

1. Start the CLI:
```bash
rwa-cli
```

2. Configure the backend endpoint (first time only):
```bash
rwa-cli config --api-url http://your-backend-url:5000
```

3. Follow the interactive prompts to:
- Create a new wallet
- Create RWA tokens
- View wallet details
- List tokens

## Asset Types

The CLI supports creating tokens for different types of real-world assets:

1. Real Estate
   - Property details
   - Location information
   - Legal documentation

2. Fine Art
   - Artist information
   - Authentication details
   - Provenance

3. Commodities
   - Specifications
   - Storage information
   - Quality metrics

4. Vehicles
   - Vehicle specifications
   - Documentation
   - History

5. Intellectual Property
   - Patent/Trademark details
   - Registration information
   - Licensing terms

## Configuration

The CLI stores its configuration in `~/.rwa-cli/config.json`. You can modify:
- Backend API endpoint
- Default values
- Display preferences

## Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## License

MIT License 