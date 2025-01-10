"""Flask application entry point"""
from flask import Flask
from flask_cors import CORS
from routes import transaction_routes, marketplace_routes
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)

    # Get MongoDB URI and database name
    mongodb_uri = os.getenv('MONGODB_URI')
    
    # Configuration based on environment
    if config_name == 'testing':
        app.config.update({
            'TESTING': True,
            'MONGODB_URI': mongodb_uri,
            'MONGODB_DB': os.getenv('MONGODB_TEST_DB', 'rwa_test'),
            'XRPL_NODE_URL': os.getenv('XRPL_NODE_URL')
        })
    else:
        app.config.update({
            'MONGODB_URI': mongodb_uri,
            'MONGODB_DB': os.getenv('MONGODB_DB', 'rwa'),
            'XRPL_NODE_URL': os.getenv('XRPL_NODE_URL')
        })

    # Register blueprints
    app.register_blueprint(transaction_routes.bp)
    app.register_blueprint(marketplace_routes.bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=True
    ) 