#!/usr/bin/env python3
"""--quiet と --filename-only の排他制約のヘルプ表示を検証するテスト"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fukuoka_water_downloader import main


class TestQuietFilenameOnlyHelpText(unittest.TestCase):
    """ヘルプテキストに排他制約が明記されていることの検証"""

    def _get_help_text(self):
        help_output = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--help']), \
             patch('sys.stdout', help_output), \
             self.assertRaises(SystemExit):
            main()
        return help_output.getvalue()

    def test_quiet_help_mentions_filename_only(self):
        """--quietのヘルプ説明に--filename-onlyと同時指定不可が記載されていること"""
        help_text = self._get_help_text()
        # --quiet, -q の説明部分を抽出（次の--引数まで）
        import re
        quiet_section = re.search(r'--quiet.*?(?=\n\s*--|$)', help_text, re.DOTALL)
        self.assertIsNotNone(quiet_section, "--quietの説明セクションが見つかりません")
        self.assertIn('--filename-only', quiet_section.group(),
                      "--quietのヘルプに--filename-onlyとの排他制約が記載されていません")

    def test_filename_only_help_mentions_quiet(self):
        """--filename-onlyのヘルプ説明に--quietと同時指定不可が記載されていること"""
        help_text = self._get_help_text()
        # 引数説明セクション内の--filename-onlyの説明行を探す
        lines = help_text.split('\n')
        for i, line in enumerate(lines):
            if '  --filename-only' in line and '保存' in line:
                self.assertIn('--quiet', line,
                              "--filename-onlyのヘルプに--quietとの排他制約が記載されていません")
                return
        self.fail("--filename-onlyの説明行が見つかりません")

    def test_epilog_mentions_mutual_exclusion(self):
        """使用例のセクションに排他制約の説明があること"""
        help_text = self._get_help_text()
        self.assertIn("同時に指定できません", help_text)


class TestQuietFilenameOnlyMutualExclusion(unittest.TestCase):
    """--quiet と --filename-only の同時指定時のエラー動作の検証"""

    def test_both_flags_exits_with_error(self):
        """同時指定時にエラー終了すること"""
        stderr = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--quiet', '--filename-only',
                                '--email', 'test@example.com', '--password', 'test']), \
             patch('sys.stderr', stderr), \
             self.assertRaises(SystemExit) as ctx:
            main()
        self.assertEqual(ctx.exception.code, 1)

    def test_both_flags_shows_error_message(self):
        """同時指定時にエラーメッセージが出力されること"""
        stderr = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--quiet', '--filename-only',
                                '--email', 'test@example.com', '--password', 'test']), \
             patch('sys.stderr', stderr):
            try:
                main()
            except SystemExit:
                pass
        self.assertIn("--quiet", stderr.getvalue())
        self.assertIn("--filename-only", stderr.getvalue())

    def test_quiet_alone_works(self):
        """--quiet単独は正常動作すること"""
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--quiet',
                                '--email', 'test@example.com', '--password', 'test']), \
             patch('fukuoka_water_downloader.FukuokaWaterDownloader.run', return_value=True), \
             patch('sys.exit') as mock_exit:
            main()
        # sys.exit(1)が呼ばれていないこと（exit(0)のみ）
        mock_exit.assert_called_with(0)

    def test_filename_only_alone_works(self):
        """--filename-only単独は正常動作すること"""
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--filename-only',
                                '--email', 'test@example.com', '--password', 'test']), \
             patch('fukuoka_water_downloader.FukuokaWaterDownloader.run', return_value=True), \
             patch('sys.exit') as mock_exit:
            main()
        mock_exit.assert_called_with(0)


if __name__ == '__main__':
    unittest.main()
