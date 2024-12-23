from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Wallet(db.Model):
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(256), unique=True, nullable=False)
    seed = db.Column(db.String(256), nullable=False)  # In production, this should be encrypted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_synced = db.Column(db.DateTime)
    tokens = db.relationship('Token', backref='issuer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'address': self.address,
            'created_at': self.created_at.isoformat(),
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
            'tokens_count': len(self.tokens)
        }

class Token(db.Model):
    __tablename__ = 'tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    currency_code = db.Column(db.String(40), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    total_supply = db.Column(db.BigInteger, nullable=False)
    token_metadata = db.Column(db.JSON)
    issuer_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Transaction hashes for token creation steps
    enable_rippling_tx = db.Column(db.String(256))
    trust_set_tx = db.Column(db.String(256))
    payment_tx = db.Column(db.String(256))

    def to_dict(self):
        return {
            'id': self.id,
            'currency_code': self.currency_code,
            'name': self.name,
            'total_supply': self.total_supply,
            'token_metadata': self.token_metadata,
            'issuer_address': self.issuer.address,
            'created_at': self.created_at.isoformat(),
            'transactions': {
                'enable_rippling_tx': self.enable_rippling_tx,
                'trust_set_tx': self.trust_set_tx,
                'payment_tx': self.payment_tx
            }
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    tx_hash = db.Column(db.String(256), unique=True, nullable=False)
    tx_type = db.Column(db.String(50), nullable=False)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    token_id = db.Column(db.Integer, db.ForeignKey('tokens.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_data = db.Column(db.JSON)

    wallet = db.relationship('Wallet', backref='transactions')
    token = db.relationship('Token', backref='transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'tx_hash': self.tx_hash,
            'tx_type': self.tx_type,
            'wallet_address': self.wallet.address,
            'token_name': self.token.name if self.token else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'raw_data': self.raw_data
        } 