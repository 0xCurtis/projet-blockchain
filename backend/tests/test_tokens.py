import unittest
from unittest.mock import patch
from services.token_service import create_token


class TokenTest(unittest.TestCase):
    @patch("services.xrpl_service.submit_and_wait")
    def test_create_token(self, mock_submit):
        # Mock successful transaction responses
        mock_submit.return_value.is_successful.return_value = True
        mock_submit.return_value.result = {"hash": "test_hash", "status": "success"}

        wallet = {"classic_address": "demo_address", "secret": "demo_secret"}
        token_name = "TestToken"
        total_supply = 1000
        metadata = {"description": "Sample Metadata"}

        response = create_token(wallet, token_name, total_supply, metadata)
        self.assertTrue(response["success"])


if __name__ == "__main__":
    unittest.main()
