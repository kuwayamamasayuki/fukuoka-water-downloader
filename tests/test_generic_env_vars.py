#!/usr/bin/env python3
"""汎用環境変数名（WATER_EMAIL/PASSWORD）のサポートを検証するテスト"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fukuoka_water_downloader import FukuokaWaterDownloader


class TestGenericEnvVars(unittest.TestCase):
    """WATER_EMAIL/WATER_PASSWORDによる認証情報取得のテスト"""

    def _get_credentials(self, env_vars, email=None, password=None):
        """環境変数を設定してget_credentialsを呼び出す"""
        downloader = FukuokaWaterDownloader()
        with patch.dict(os.environ, env_vars, clear=False), \
             patch('fukuoka_water_downloader.load_dotenv'):
            return downloader.get_credentials(email=email, password=password)

    def test_water_email_used_when_fukuoka_not_set(self):
        """FUKUOKA_WATER_EMAIL未設定時にWATER_EMAILが使われること"""
        env = {'WATER_EMAIL': 'generic@example.com', 'WATER_PASSWORD': 'genpass'}
        # FUKUOKA_WATER_* が設定されていないことを保証
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('FUKUOKA_WATER_EMAIL', None)
            os.environ.pop('FUKUOKA_WATER_PASSWORD', None)
            email, password = self._get_credentials(env)
        self.assertEqual(email, 'generic@example.com')
        self.assertEqual(password, 'genpass')

    def test_fukuoka_takes_priority_over_water(self):
        """FUKUOKA_WATER_*がWATER_*より優先されること"""
        env = {
            'FUKUOKA_WATER_EMAIL': 'fukuoka@example.com',
            'FUKUOKA_WATER_PASSWORD': 'fukupass',
            'WATER_EMAIL': 'generic@example.com',
            'WATER_PASSWORD': 'genpass'
        }
        email, password = self._get_credentials(env)
        self.assertEqual(email, 'fukuoka@example.com')
        self.assertEqual(password, 'fukupass')

    def test_cli_takes_priority_over_all_env(self):
        """CLI引数がすべての環境変数より優先されること"""
        env = {
            'FUKUOKA_WATER_EMAIL': 'fukuoka@example.com',
            'FUKUOKA_WATER_PASSWORD': 'fukupass',
            'WATER_EMAIL': 'generic@example.com',
            'WATER_PASSWORD': 'genpass'
        }
        email, password = self._get_credentials(env, email='cli@example.com', password='clipass')
        self.assertEqual(email, 'cli@example.com')
        self.assertEqual(password, 'clipass')

    def test_mixed_fukuoka_email_water_password(self):
        """FUKUOKA_WATER_EMAILとWATER_PASSWORDの混在が動作すること"""
        env = {
            'FUKUOKA_WATER_EMAIL': 'fukuoka@example.com',
            'WATER_PASSWORD': 'genpass'
        }
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('FUKUOKA_WATER_PASSWORD', None)
            email, password = self._get_credentials(env)
        self.assertEqual(email, 'fukuoka@example.com')
        self.assertEqual(password, 'genpass')

    def test_water_email_only(self):
        """WATER_EMAILのみ設定時にemailが取得できること"""
        env = {'WATER_EMAIL': 'generic@example.com'}
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('FUKUOKA_WATER_EMAIL', None)
            os.environ.pop('FUKUOKA_WATER_PASSWORD', None)
            os.environ.pop('WATER_PASSWORD', None)
            downloader = FukuokaWaterDownloader()
            with patch.dict(os.environ, env, clear=False), \
                 patch('fukuoka_water_downloader.load_dotenv'), \
                 patch('builtins.input', return_value=''), \
                 patch('getpass.getpass', return_value='inputpass'):
                email, password = downloader.get_credentials()
        self.assertEqual(email, 'generic@example.com')


class TestHelpTextMentionsGenericVars(unittest.TestCase):
    """ヘルプテキストに汎用環境変数名が記載されていることの検証"""

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


if __name__ == '__main__':
    unittest.main()
