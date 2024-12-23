from services.xrpl_service import issue_token

def create_token(wallet, token_name, total_supply, metadata):
    """Create a new token with the given parameters"""
    if not wallet.get('secret'):
        return {"success": False, "error": "'secret'"}
        
    return issue_token(wallet, token_name, total_supply, metadata)