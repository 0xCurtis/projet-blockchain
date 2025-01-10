# Documentation Backend RWA-CLI

## Table des matières
1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Routes API](#routes-api)
5. [Services](#services)
6. [Base de données](#base-de-données)
7. [Sécurité](#sécurité)
8. [Déploiement](#déploiement)

## Introduction
Le backend RWA-CLI est un serveur Flask qui gère les interactions entre l'interface utilisateur et la blockchain XRPL (XRP Ledger). Il permet la gestion des NFTs représentant des actifs réels (Real World Assets - RWA) sur la blockchain XRPL.

### Fonctionnalités principales
- Création et gestion des NFTs
- Transfert de NFTs entre utilisateurs
- Stockage des métadonnées des NFTs
- Interaction avec la blockchain XRPL
- Gestion des portefeuilles

## Architecture

### Structure du projet
```
backend/
├── app.py              # Point d'entrée de l'application
├── routes/            # Définitions des routes API
│   ├── transaction_routes.py
│   └── marketplace_routes.py
├── services/         # Services métier
│   ├── mongodb_service.py
│   └── xrpl_service.py
└── config/          # Configuration
    └── config.py
```

## Configuration

### Variables d'environnement requises
```env
MONGODB_URI=mongodb://localhost:27017/rwa_cli
XRPL_NODE_URL=https://s.altnet.rippletest.net:51234
```

### Configuration de la base de données
Le système utilise MongoDB pour stocker :
- Métadonnées des NFTs
- Historique des transactions
- État des NFTs

## Routes API

### Gestion des NFTs
```
POST /api/transaction/nft/mint/template
- Crée un template pour le minting d'un NFT
- Paramètres requis: account, uri, metadata

POST /api/transaction/submit
- Soumet une transaction signée à la blockchain
- Paramètres requis: signed_transaction

GET /api/transaction/nfts/{address}
- Récupère tous les NFTs d'une adresse
- Paramètre: address (adresse du portefeuille)
```

### Place de marché
```
POST /api/marketplace/list
- Crée une nouvelle annonce de vente NFT
- Paramètres requis: nft_id, seller_address, price_xrp

GET /api/marketplace/listings
- Récupère toutes les annonces actives

GET /api/marketplace/listing/{listing_id}
- Récupère les détails d'une annonce spécifique
```

## Services

### Service XRPL
Le service XRPL (`xrpl_service.py`) gère toutes les interactions avec la blockchain :
- Création de transactions NFT
- Vérification de propriété
- Soumission de transactions
- Surveillance des événements blockchain

### Service MongoDB
Le service MongoDB (`mongodb_service.py`) gère :
- Stockage des métadonnées NFT
- Suivi des transactions
- État des annonces de vente

## Base de données

### Collections MongoDB
1. **nfts**
```json
{
    "nft_id": "string",
    "account": "string",
    "uri": "string",
    "metadata": {
        "title": "string",
        "asset_type": "string",
        "description": "string",
        "location": "string",
        "documentation_id": "string"
    },
    "status": "string",
    "transaction_hash": "string",
    "created_at": "datetime"
}
```

2. **transactions**
```json
{
    "hash": "string",
    "type": "string",
    "account": "string",
    "status": "string",
    "timestamp": "datetime"
}
```

## Sécurité

### Bonnes pratiques
- Validation des entrées utilisateur
- Vérification de propriété des NFTs
- Protection contre les attaques CSRF
- Rate limiting sur les routes API
- Validation des signatures de transactions

### Authentification
- Vérification des signatures de transactions XRPL
- Validation des adresses XRPL

## Déploiement

### Prérequis
- Python 3.8+
- MongoDB 4.4+
- Connexion Internet stable (pour XRPL)

### Installation
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