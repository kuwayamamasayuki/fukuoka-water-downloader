#!/usr/bin/env python3
"""CORSプリフライト失敗時のエラーメッセージがユーザーフレンドリーであることを検証するテスト"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fukuoka_water_downloader import FukuokaWaterDownloader


class TestCorsErrorMessageNormalMode(unittest.TestCase):
    """通常モードでCORSの技術用語がエラーメッセージに含まれないことの検証"""

    def _create_downloader(self, verbose=False):
        downloader = FukuokaWaterDownloader(verbose=verbose)
        downloader.jwt_token = "test_token"
        downloader.user_id = "test_user"
        return downloader

    def test_status_error_no_cors_term(self):
        """ステータスコードエラー時にCORS用語が表示されないこと"""
        downloader = self._create_downloader()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {}

        stderr = StringIO()
        with patch.object(downloader.session, 'options', return_value=mock_response), \
             patch('sys.stderr', stderr):
            result = downloader.send_cors_preflight("https://example.com", "POST", ["authorization"])

        self.assertFalse(result)
        self.assertIn("サーバーとの通信に失敗しました", stderr.getvalue())
        self.assertNotIn("CORS", stderr.getvalue())

    def test_method_not_allowed_no_cors_term(self):
        """メソッド不許可時にCORS用語が表示されないこと"""
        downloader = self._create_downloader()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': '*'
        }

        stderr = StringIO()
        with patch.object(downloader.session, 'options', return_value=mock_response), \
             patch('sys.stderr', stderr):
            result = downloader.send_cors_preflight("https://example.com", "POST", ["authorization"])

        self.assertFalse(result)
        self.assertIn("サーバーとの通信に失敗しました", stderr.getvalue())
        self.assertNotIn("CORS", stderr.getvalue())

    def test_header_not_allowed_no_cors_term(self):
        """ヘッダー不許可時にCORS用語が表示されないこと"""
        downloader = self._create_downloader()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'content-type'
        }

        stderr = StringIO()
        with patch.object(downloader.session, 'options', return_value=mock_response), \
             patch('sys.stderr', stderr):
            result = downloader.send_cors_preflight("https://example.com", "POST", ["authorization"])

        self.assertFalse(result)
        self.assertNotIn("CORS", stderr.getvalue())

    def test_exception_no_cors_term(self):
        """例外発生時にCORS用語が表示されないこと"""
        downloader = self._create_downloader()

        stderr = StringIO()
        with patch.object(downloader.session, 'options', side_effect=Exception("connection refused")), \
             patch('sys.stderr', stderr):
            result = downloader.send_cors_preflight("https://example.com", "POST", ["authorization"])

        self.assertFalse(result)
        self.assertIn("ネットワーク接続を確認", stderr.getvalue())
        self.assertNotIn("CORS", stderr.getvalue())


class TestCorsErrorMessageVerboseMode(unittest.TestCase):
    """verboseモードで技術詳細が表示されることの検証"""

    def test_status_error_shows_details_in_verbose(self):
        """verboseモードでステータスコードの技術詳細が表示されること"""
        downloader = FukuokaWaterDownloader(verbose=True)
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {}

        stderr = StringIO()
        stdout = StringIO()
        with patch.object(downloader.session, 'options', return_value=mock_response), \
             patch('sys.stderr', stderr), \
             patch('sys.stdout', stdout):
            downloader.send_cors_preflight("https://example.com", "POST", ["authorization"])

        self.assertIn("403", stdout.getvalue())

    def test_exception_shows_details_in_verbose(self):
        """verboseモードで例外の技術詳細が表示されること"""
        downloader = FukuokaWaterDownloader(verbose=True)

        stderr = StringIO()
        stdout = StringIO()
        with patch.object(downloader.session, 'options', side_effect=Exception("timeout")), \
             patch('sys.stderr', stderr), \
             patch('sys.stdout', stdout):
            downloader.send_cors_preflight("https://example.com", "POST", ["authorization"])

        self.assertIn("timeout", stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
