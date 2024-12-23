import logging

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def log(message):
    logging.info(message)

def handle_error(message):
    return {"success": False, "error": message} 