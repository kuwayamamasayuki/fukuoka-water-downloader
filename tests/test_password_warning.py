#!/usr/bin/env python3
"""--password引数使用時の警告メッセージを検証するテスト"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPasswordWarning(unittest.TestCase):
    """--password引数使用時のセキュリティ警告テスト"""

    def _run_main_with_args(self, args):
        """main()を指定引数で実行し、stderrの出力を返す"""
        from fukuoka_water_downloader import main
        stderr_capture = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py'] + args), \
             patch('sys.stderr', stderr_capture), \
             patch('fukuoka_water_downloader.FukuokaWaterDownloader.run', return_value=True), \
             patch('sys.exit'):
            main()
        return stderr_capture.getvalue()

    def test_warning_shown_when_password_argument_used(self):
        """--password引数使用時に警告がstderrに出力されること"""
        stderr_output = self._run_main_with_args(
            ['--email', 'test@example.com', '--password', 'secret123']
        )
        self.assertIn("警告", stderr_output)
        self.assertIn("シェル履歴", stderr_output)

    def test_warning_shown_with_short_flag(self):
        """-p短縮フラグ使用時にも警告が出力されること"""
        stderr_output = self._run_main_with_args(
            ['-e', 'test@example.com', '-p', 'secret123']
        )
        self.assertIn("警告", stderr_output)

    def test_no_warning_without_password_argument(self):
        """--password引数未使用時に警告が出力されないこと"""
        stderr_output = self._run_main_with_args(
            ['--email', 'test@example.com']
        )
        self.assertNotIn("警告", stderr_output)

    def test_no_warning_with_no_arguments(self):
        """引数なし実行時に警告が出力されないこと"""
        stderr_output = self._run_main_with_args([])
        self.assertNotIn("警告", stderr_output)

    def test_warning_recommends_alternatives(self):
        """警告メッセージが代替手段を案内すること"""
        stderr_output = self._run_main_with_args(
            ['--password', 'secret123', '--email', 'test@example.com']
        )
        self.assertIn(".env", stderr_output)
        self.assertIn("環境変数", stderr_output)

    def test_help_text_contains_security_note(self):
        """--passwordのヘルプテキストに非推奨である旨が記載されていること"""
        import argparse
        from fukuoka_water_downloader import main
        help_output = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--help']), \
             patch('sys.stdout', help_output), \
             self.assertRaises(SystemExit):
            main()
        help_text = help_output.getvalue()
        self.assertIn("非推奨", help_text)


if __name__ == '__main__':
    unittest.main()
