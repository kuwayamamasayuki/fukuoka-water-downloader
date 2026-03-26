#!/usr/bin/env python3
"""終了コードのドキュメント化を検証するテスト"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fukuoka_water_downloader import main


class TestExitCodeHelpText(unittest.TestCase):
    """ヘルプテキストに終了コードが記載されていることの検証"""

    def _get_help_text(self):
        help_output = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--help']), \
             patch('sys.stdout', help_output), \
             self.assertRaises(SystemExit):
            main()
        return help_output.getvalue()

    def test_help_mentions_exit_codes(self):
        """ヘルプに終了コードセクションがあること"""
        help_text = self._get_help_text()
        self.assertIn("終了コード", help_text)

    def test_help_mentions_exit_code_0(self):
        """ヘルプに終了コード0の説明があること"""
        help_text = self._get_help_text()
        self.assertIn("0", help_text)
        self.assertIn("正常終了", help_text)

    def test_help_mentions_exit_code_1(self):
        """ヘルプに終了コード1の説明があること"""
        help_text = self._get_help_text()
        self.assertIn("1", help_text)
        self.assertIn("異常終了", help_text)


class TestExitCodeBehavior(unittest.TestCase):
    """実際の終了コードの動作検証"""

    def test_success_exits_with_0(self):
        """成功時にexit code 0で終了すること"""
        with patch('sys.argv', ['fukuoka_water_downloader.py',
                                '--email', 'test@example.com', '--password', 'test']), \
             patch('fukuoka_water_downloader.FukuokaWaterDownloader.run', return_value=True), \
             patch('sys.exit') as mock_exit:
            main()
        mock_exit.assert_called_with(0)

    def test_failure_exits_with_1(self):
        """失敗時にexit code 1で終了すること"""
        with patch('sys.argv', ['fukuoka_water_downloader.py',
                                '--email', 'test@example.com', '--password', 'test']), \
             patch('fukuoka_water_downloader.FukuokaWaterDownloader.run', return_value=False), \
             patch('sys.exit') as mock_exit:
            main()
        mock_exit.assert_called_with(1)


if __name__ == '__main__':
    unittest.main()
