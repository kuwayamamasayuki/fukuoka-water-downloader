#!/usr/bin/env python3
"""デバッグ出力にJWTトークンが含まれないことを検証するテスト"""

import json
import sys
import os
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fukuoka_water_downloader import FukuokaWaterDownloader


class TestDebugTokenMasking(unittest.TestCase):
    """デバッグ出力でJWTトークンがマスクされることを検証"""

    def setUp(self):
        self.downloader = FukuokaWaterDownloader(debug=True, quiet=False)
        self.fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"

    def test_log_request_masks_authorization_header(self):
        """log_requestでAuthorizationヘッダーが[MASKED]になること"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': self.fake_token,
        }
        output = StringIO()
        with patch('sys.stdout', output):
            self.downloader.log_request("GET", "https://example.com/api", headers)

        result = output.getvalue()
        self.assertNotIn(self.fake_token, result)
        self.assertIn("Authorization: [MASKED]", result)
        self.assertIn("Content-Type: application/json", result)

    def test_log_request_masks_authorization_case_insensitive(self):
        """Authorizationヘッダーの大文字小文字を問わずマスクされること"""
        headers = {
            'authorization': self.fake_token,
        }
        output = StringIO()
        with patch('sys.stdout', output):
            self.downloader.log_request("GET", "https://example.com/api", headers)

        result = output.getvalue()
        self.assertNotIn(self.fake_token, result)
        self.assertIn("[MASKED]", result)

    def test_log_response_masks_token_in_json_body(self):
        """log_responseでレスポンスボディ内のtokenフィールドがマスクされること"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/api"
        mock_response.headers = {
            'content-type': 'application/json',
        }
        mock_response.json.return_value = {
            'result': '00000',
            'token': self.fake_token,
            'data': {'someField': 'value'}
        }

        output = StringIO()
        with patch('sys.stdout', output):
            self.downloader.log_response(mock_response)

        result = output.getvalue()
        self.assertNotIn(self.fake_token, result)
        self.assertIn('"token": "[MASKED]"', result)
        self.assertIn('"result": "00000"', result)

    def test_log_response_masks_email_in_data(self):
        """log_responseで既存のメールマスクも引き続き動作すること"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/api"
        mock_response.headers = {
            'content-type': 'application/json',
        }
        mock_response.json.return_value = {
            'token': self.fake_token,
            'data': {'mailAddress': 'user@example.com'}
        }

        output = StringIO()
        with patch('sys.stdout', output):
            self.downloader.log_response(mock_response)

        result = output.getvalue()
        self.assertNotIn(self.fake_token, result)
        self.assertNotIn('user@example.com', result)
        self.assertIn('[MASKED_EMAIL]', result)

    def test_authentication_debug_info_no_token(self):
        """AUTHENTICATION DEBUG INFOにJWTトークンが含まれないこと"""
        self.downloader.jwt_token = self.fake_token
        self.downloader.user_id = "test_user_123"

        output = StringIO()
        with patch('sys.stdout', output):
            self.downloader.print_output("=== AUTHENTICATION DEBUG INFO ===")
            self.downloader.print_output(f"User ID (dwKey): {self.downloader.user_id}")
            self.downloader.print_output("=" * 40)

        result = output.getvalue()
        self.assertNotIn(self.fake_token, result)
        self.assertIn("test_user_123", result)

    def test_no_jwt_payload_output(self):
        """JWTペイロードの出力コードが削除されていること（ソースコード検証）"""
        import inspect
        source = inspect.getsource(FukuokaWaterDownloader.login)
        self.assertNotIn("JWT Payload:", source)
        self.assertNotIn("base64.b64decode", source)
        self.assertNotIn("jwt_data", source)

    def test_no_jwt_token_first_100_chars(self):
        """'JWT Token (first 100 chars)'の出力が削除されていること"""
        import inspect
        source = inspect.getsource(FukuokaWaterDownloader.download_billing_data)
        self.assertNotIn("JWT Token (first 100 chars)", source)
        self.assertNotIn("Authorization header:", source)

    def test_log_request_without_headers(self):
        """ヘッダーなしのlog_requestが正常に動作すること"""
        output = StringIO()
        with patch('sys.stdout', output):
            self.downloader.log_request("GET", "https://example.com/api")

        result = output.getvalue()
        self.assertIn("GET", result)
        self.assertIn("https://example.com/api", result)

    def test_log_request_masks_password_in_body(self):
        """リクエストボディ内のパスワードが引き続きマスクされること"""
        data = {"loginId": "user@example.com", "password": "secret123"}
        output = StringIO()
        with patch('sys.stdout', output):
            self.downloader.log_request("POST", "https://example.com/login", data=data)

        result = output.getvalue()
        self.assertNotIn("secret123", result)
        self.assertNotIn("user@example.com", result)
        self.assertIn("[MASKED_PASSWORD]", result)
        self.assertIn("[MASKED_EMAIL]", result)


if __name__ == '__main__':
    unittest.main()
