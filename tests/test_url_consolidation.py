#!/usr/bin/env python3
"""Origin/Refererヘッダーがハードコードではなくself.base_urlから生成されることを検証するテスト"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fukuoka_water_downloader import FukuokaWaterDownloader


class TestOriginRefererFromBaseUrl(unittest.TestCase):
    """Origin/Refererヘッダーがself.base_urlから動的に生成されることの検証"""

    def _create_downloader(self):
        downloader = FukuokaWaterDownloader()
        downloader.jwt_token = "test_token"
        downloader.user_id = "test_user"
        return downloader

    def test_cors_preflight_uses_base_url_origin(self):
        """send_cors_preflightのOriginがself.base_urlであること"""
        downloader = self._create_downloader()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': '*'
        }

        with patch.object(downloader.session, 'options', return_value=mock_response) as mock_options:
            downloader.send_cors_preflight("https://api.example.com/test", "POST", ["authorization"])

        call_kwargs = mock_options.call_args
        headers = call_kwargs[1]['headers'] if 'headers' in call_kwargs[1] else call_kwargs[0][1] if len(call_kwargs[0]) > 1 else call_kwargs[1].get('headers', {})
        self.assertEqual(headers['Origin'], downloader.base_url)
        self.assertEqual(headers['Referer'], f'{downloader.base_url}/')

    def test_get_user_data_uses_base_url_origin(self):
        """get_user_dataのOrigin/Refererがself.base_urlであること"""
        downloader = self._create_downloader()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'token': 'new_token',
            'data': {'dwKey': '12345'}
        }
        mock_response.headers = {'content-type': 'application/json'}

        # CORSプリフライトをスキップ
        with patch.object(downloader, 'send_cors_preflight', return_value=True), \
             patch.object(downloader.session, 'get', return_value=mock_response) as mock_get:
            downloader.get_user_data()

        call_kwargs = mock_get.call_args
        headers = call_kwargs[1].get('headers', {})
        self.assertEqual(headers['Origin'], downloader.base_url)
        self.assertEqual(headers['Referer'], f'{downloader.base_url}/')

    def test_no_hardcoded_fukuoka_in_headers(self):
        """ヘッダー生成時にハードコードされた福岡ドメインが使われないこと"""
        downloader = self._create_downloader()
        # base_urlを別のドメインに変更してテスト
        downloader.base_url = "https://www.suido-madoguchi-tokyo.jp"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': '*'
        }

        with patch.object(downloader.session, 'options', return_value=mock_response) as mock_options:
            downloader.send_cors_preflight("https://api.example.com/test", "POST", ["authorization"])

        headers = mock_options.call_args[1]['headers']
        self.assertEqual(headers['Origin'], "https://www.suido-madoguchi-tokyo.jp")
        self.assertEqual(headers['Referer'], "https://www.suido-madoguchi-tokyo.jp/")
        self.assertNotIn("fukuoka", headers['Origin'])


class TestDownloadUrlFallback(unittest.TestCase):
    """ダウンロードURLフォールバックがbase_urlから導出されることの検証"""

    def test_fallback_url_derived_from_base_url(self):
        """downloadUrl未提供時のフォールバックURLがbase_urlから生成されること"""
        downloader = FukuokaWaterDownloader()
        downloader.jwt_token = "test_token"
        downloader.user_id = "test_user"

        # ファイル作成成功、downloadUrlなしのレスポンスを模擬
        create_response = MagicMock()
        create_response.status_code = 200
        create_response.json.return_value = {
            'result': '00000',
            'data': {'fileName': 'test.csv'},
            'token': 'new_token'
        }
        create_response.headers = {'content-type': 'application/json'}

        # downloadUrlなしのレスポンス
        download_info_response = MagicMock()
        download_info_response.status_code = 200
        download_info_response.json.return_value = {
            'result': '00000',
            'token': 'new_token2'
            # downloadUrl フィールドなし
        }
        download_info_response.headers = {'content-type': 'application/json'}

        # 実際のダウンロードレスポンス
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.content = b'test data'
        file_response.headers = {'content-type': 'text/csv'}

        with patch.object(downloader, 'send_cors_preflight', return_value=True), \
             patch.object(downloader.session, 'post', return_value=create_response), \
             patch.object(downloader.session, 'get', side_effect=[download_info_response, file_response]) as mock_get:
            downloader.download_billing_data("2024-01", "2024-01", "csv")

        # 2回目のGET呼び出し（実ファイルダウンロード）のURLを確認
        second_get_url = mock_get.call_args_list[1][0][0]
        self.assertIn("download.suido-madoguchi-fukuoka.jp", second_get_url)
        self.assertNotIn("www.", second_get_url)

    def test_fallback_url_changes_with_base_url(self):
        """base_urlを変更するとフォールバックURLも変わること"""
        downloader = FukuokaWaterDownloader()
        downloader.base_url = "https://www.suido-madoguchi-tokyo.jp"
        downloader.jwt_token = "test_token"
        downloader.user_id = "test_user"

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.json.return_value = {
            'result': '00000',
            'data': {'fileName': 'test.csv'},
            'token': 'new_token'
        }
        create_response.headers = {'content-type': 'application/json'}

        download_info_response = MagicMock()
        download_info_response.status_code = 200
        download_info_response.json.return_value = {
            'result': '00000',
            'token': 'new_token2'
        }
        download_info_response.headers = {'content-type': 'application/json'}

        file_response = MagicMock()
        file_response.status_code = 200
        file_response.content = b'test data'
        file_response.headers = {'content-type': 'text/csv'}

        with patch.object(downloader, 'send_cors_preflight', return_value=True), \
             patch.object(downloader.session, 'post', return_value=create_response), \
             patch.object(downloader.session, 'get', side_effect=[download_info_response, file_response]) as mock_get:
            downloader.download_billing_data("2024-01", "2024-01", "csv")

        second_get_url = mock_get.call_args_list[1][0][0]
        self.assertIn("download.suido-madoguchi-tokyo.jp", second_get_url)
        self.assertNotIn("fukuoka", second_get_url)


class TestDefaultBaseUrls(unittest.TestCase):
    """デフォルトのURLが福岡のままであることの検証（後方互換）"""

    def test_default_base_url(self):
        downloader = FukuokaWaterDownloader()
        self.assertEqual(downloader.base_url, "https://www.suido-madoguchi-fukuoka.jp")

    def test_default_api_base_url(self):
        downloader = FukuokaWaterDownloader()
        self.assertEqual(downloader.api_base_url, "https://api.suido-madoguchi-fukuoka.jp")


if __name__ == '__main__':
    unittest.main()
