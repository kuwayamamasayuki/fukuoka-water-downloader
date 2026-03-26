#!/usr/bin/env python3
"""環境変数名（WATER_EMAIL/PASSWORD）による認証情報取得を検証するテスト"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fukuoka_water_downloader import FukuokaWaterDownloader


class TestWaterEnvVars(unittest.TestCase):
    """WATER_EMAIL/WATER_PASSWORDによる認証情報取得のテスト"""

    def _get_credentials(self, env_vars, email=None, password=None):
        """環境変数を設定してget_credentialsを呼び出す"""
        downloader = FukuokaWaterDownloader()
        with patch.dict(os.environ, env_vars, clear=False), \
             patch('fukuoka_water_downloader.load_dotenv'):
            return downloader.get_credentials(email=email, password=password)

    def test_water_env_vars_used(self):
        """WATER_EMAIL/WATER_PASSWORDで認証情報が取得できること"""
        env = {'WATER_EMAIL': 'user@example.com', 'WATER_PASSWORD': 'pass123'}
        email, password = self._get_credentials(env)
        self.assertEqual(email, 'user@example.com')
        self.assertEqual(password, 'pass123')

    def test_cli_takes_priority_over_env(self):
        """CLI引数が環境変数より優先されること"""
        env = {'WATER_EMAIL': 'env@example.com', 'WATER_PASSWORD': 'envpass'}
        email, password = self._get_credentials(env, email='cli@example.com', password='clipass')
        self.assertEqual(email, 'cli@example.com')
        self.assertEqual(password, 'clipass')

    def test_water_email_only_prompts_password(self):
        """WATER_EMAILのみ設定時にパスワードは対話入力になること"""
        env = {'WATER_EMAIL': 'user@example.com'}
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('WATER_PASSWORD', None)
            downloader = FukuokaWaterDownloader()
            with patch.dict(os.environ, env, clear=False), \
                 patch('fukuoka_water_downloader.load_dotenv'), \
                 patch('getpass.getpass', return_value='inputpass'):
                email, password = downloader.get_credentials()
        self.assertEqual(email, 'user@example.com')
        self.assertEqual(password, 'inputpass')

    def test_no_env_prompts_both(self):
        """環境変数未設定時にメール・パスワード両方が対話入力になること"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('WATER_EMAIL', None)
            os.environ.pop('WATER_PASSWORD', None)
            downloader = FukuokaWaterDownloader()
            with patch('fukuoka_water_downloader.load_dotenv'), \
                 patch('builtins.input', return_value='input@example.com'), \
                 patch('getpass.getpass', return_value='inputpass'):
                email, password = downloader.get_credentials()
        self.assertEqual(email, 'input@example.com')
        self.assertEqual(password, 'inputpass')


class TestHelpTextMentionsWaterVars(unittest.TestCase):
    """ヘルプテキストにWATER_*環境変数名が記載されていることの検証"""

    def test_help_mentions_water_email(self):
        from io import StringIO
        from fukuoka_water_downloader import main
        help_output = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--help']), \
             patch('sys.stdout', help_output), \
             self.assertRaises(SystemExit):
            main()
        help_text = help_output.getvalue()
        self.assertIn('WATER_EMAIL', help_text)
        self.assertIn('WATER_PASSWORD', help_text)

    def test_help_does_not_mention_fukuoka_water(self):
        """ヘルプテキストにFUKUOKA_WATER_*が含まれないこと"""
        from io import StringIO
        from fukuoka_water_downloader import main
        help_output = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--help']), \
             patch('sys.stdout', help_output), \
             self.assertRaises(SystemExit):
            main()
        help_text = help_output.getvalue()
        self.assertNotIn('FUKUOKA_WATER_EMAIL', help_text)
        self.assertNotIn('FUKUOKA_WATER_PASSWORD', help_text)


if __name__ == '__main__':
    unittest.main()
