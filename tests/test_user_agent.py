#!/usr/bin/env python3
"""User-Agentが定数として一元管理されていることを検証するテスト"""

import inspect
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fukuoka_water_downloader import FukuokaWaterDownloader


class TestUserAgent(unittest.TestCase):
    """User-Agent定数管理のテスト"""

    def test_default_user_agent_defined(self):
        """DEFAULT_USER_AGENTクラス定数が定義されていること"""
        self.assertTrue(hasattr(FukuokaWaterDownloader, 'DEFAULT_USER_AGENT'))
        self.assertIsInstance(FukuokaWaterDownloader.DEFAULT_USER_AGENT, str)
        self.assertIn('Mozilla', FukuokaWaterDownloader.DEFAULT_USER_AGENT)

    def test_session_uses_default_user_agent(self):
        """セッションのUser-AgentがDEFAULT_USER_AGENTと一致すること"""
        downloader = FukuokaWaterDownloader(debug=False, quiet=True)
        self.assertEqual(
            downloader.session.headers.get('User-Agent'),
            FukuokaWaterDownloader.DEFAULT_USER_AGENT
        )

    def test_no_hardcoded_user_agent_in_methods(self):
        """メソッド内にUser-Agent文字列がハードコードされていないこと"""
        hardcoded_pattern = re.compile(r"Mozilla/5\.0.*Firefox")
        methods = [
            FukuokaWaterDownloader.setup_session,
            FukuokaWaterDownloader.send_cors_preflight,
            FukuokaWaterDownloader.get_user_data,
            FukuokaWaterDownloader.login,
            FukuokaWaterDownloader.download_billing_data,
        ]
        for method in methods:
            source = inspect.getsource(method)
            matches = hardcoded_pattern.findall(source)
            self.assertEqual(
                len(matches), 0,
                f"{method.__name__}にUser-Agentがハードコードされています: {matches}"
            )

    def test_all_methods_reference_constant(self):
        """User-Agentを使用するメソッドがDEFAULT_USER_AGENTを参照していること"""
        methods_with_ua = [
            FukuokaWaterDownloader.setup_session,
            FukuokaWaterDownloader.send_cors_preflight,
            FukuokaWaterDownloader.get_user_data,
            FukuokaWaterDownloader.download_billing_data,
        ]
        for method in methods_with_ua:
            source = inspect.getsource(method)
            self.assertIn(
                'DEFAULT_USER_AGENT', source,
                f"{method.__name__}がDEFAULT_USER_AGENTを参照していません"
            )


if __name__ == '__main__':
    unittest.main()
