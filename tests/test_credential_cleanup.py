#!/usr/bin/env python3
"""処理完了後にJWTトークンとユーザーIDがクリアされることを検証するテスト"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fukuoka_water_downloader import FukuokaWaterDownloader


class TestCredentialCleanup(unittest.TestCase):
    """run()メソッド完了後の認証情報クリアテスト"""

    def setUp(self):
        self.downloader = FukuokaWaterDownloader(debug=False, quiet=True)

    @patch.object(FukuokaWaterDownloader, 'get_credentials', return_value=('test@example.com', 'password'))
    @patch.object(FukuokaWaterDownloader, 'login', return_value=True)
    @patch.object(FukuokaWaterDownloader, 'download_billing_data', return_value=(b'data', 'test.csv'))
    @patch.object(FukuokaWaterDownloader, 'save_data')
    def test_tokens_cleared_after_success(self, mock_save, mock_download, mock_login, mock_creds):
        """正常終了後にjwt_tokenとuser_idがNoneになること"""
        self.downloader.jwt_token = "fake_token"
        self.downloader.user_id = "fake_user"

        self.downloader.run()

        self.assertIsNone(self.downloader.jwt_token)
        self.assertIsNone(self.downloader.user_id)

    @patch.object(FukuokaWaterDownloader, 'get_credentials', return_value=('test@example.com', 'password'))
    @patch.object(FukuokaWaterDownloader, 'login', return_value=False)
    def test_tokens_cleared_after_login_failure(self, mock_login, mock_creds):
        """ログイン失敗後にjwt_tokenとuser_idがNoneになること"""
        self.downloader.jwt_token = "fake_token"
        self.downloader.user_id = "fake_user"

        self.downloader.run()

        self.assertIsNone(self.downloader.jwt_token)
        self.assertIsNone(self.downloader.user_id)

    @patch.object(FukuokaWaterDownloader, 'get_credentials', return_value=('test@example.com', 'password'))
    @patch.object(FukuokaWaterDownloader, 'login', return_value=True)
    @patch.object(FukuokaWaterDownloader, 'download_billing_data', return_value=(None, None))
    def test_tokens_cleared_after_download_failure(self, mock_download, mock_login, mock_creds):
        """ダウンロード失敗後にjwt_tokenとuser_idがNoneになること"""
        self.downloader.jwt_token = "fake_token"
        self.downloader.user_id = "fake_user"

        self.downloader.run()

        self.assertIsNone(self.downloader.jwt_token)
        self.assertIsNone(self.downloader.user_id)

    @patch.object(FukuokaWaterDownloader, 'get_credentials', side_effect=Exception("unexpected error"))
    def test_tokens_cleared_after_exception(self, mock_creds):
        """例外発生後にjwt_tokenとuser_idがNoneになること"""
        self.downloader.jwt_token = "fake_token"
        self.downloader.user_id = "fake_user"

        self.downloader.run()

        self.assertIsNone(self.downloader.jwt_token)
        self.assertIsNone(self.downloader.user_id)

    def test_source_contains_finally_block(self):
        """runメソッドにfinallyブロックが含まれること"""
        import inspect
        source = inspect.getsource(FukuokaWaterDownloader.run)
        self.assertIn("finally:", source)
        self.assertIn("self.jwt_token = None", source)
        self.assertIn("self.user_id = None", source)


if __name__ == '__main__':
    unittest.main()
