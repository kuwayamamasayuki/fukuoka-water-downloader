#!/usr/bin/env python3
"""--verbose フラグと --debug フラグの出力レベル分離を検証するテスト"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fukuoka_water_downloader import FukuokaWaterDownloader, main


class TestVerboseFlag(unittest.TestCase):
    """verbose/debug出力レベルの分離テスト"""

    def test_verbose_attribute_defaults_to_false(self):
        """デフォルトでverboseがFalseであること"""
        downloader = FukuokaWaterDownloader()
        self.assertFalse(downloader.verbose)

    def test_verbose_true_when_verbose_set(self):
        """verbose=Trueを指定するとverboseがTrueになること"""
        downloader = FukuokaWaterDownloader(verbose=True)
        self.assertTrue(downloader.verbose)
        self.assertFalse(downloader.debug)

    def test_verbose_true_when_debug_set(self):
        """debug=Trueを指定するとverboseも自動的にTrueになること"""
        downloader = FukuokaWaterDownloader(debug=True)
        self.assertTrue(downloader.verbose)
        self.assertTrue(downloader.debug)

    def test_verbose_false_debug_false_by_default(self):
        """デフォルトではverboseもdebugもFalseであること"""
        downloader = FukuokaWaterDownloader()
        self.assertFalse(downloader.verbose)
        self.assertFalse(downloader.debug)


class TestPrintVerbose(unittest.TestCase):
    """print_verboseメソッドのテスト"""

    def test_print_verbose_outputs_when_verbose(self):
        """verbose=True時にprint_verboseが出力すること"""
        downloader = FukuokaWaterDownloader(verbose=True)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.print_verbose("テストメッセージ")
        self.assertIn("テストメッセージ", mock_stdout.getvalue())

    def test_print_verbose_silent_when_not_verbose(self):
        """verbose=False時にprint_verboseが出力しないこと"""
        downloader = FukuokaWaterDownloader(verbose=False)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.print_verbose("テストメッセージ")
        self.assertEqual("", mock_stdout.getvalue())

    def test_print_verbose_silent_when_quiet(self):
        """quiet=True時にprint_verboseが出力しないこと"""
        downloader = FukuokaWaterDownloader(verbose=True, quiet=True)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.print_verbose("テストメッセージ")
        self.assertEqual("", mock_stdout.getvalue())

    def test_print_verbose_silent_when_filename_only(self):
        """filename_only=True時にprint_verboseが出力しないこと"""
        downloader = FukuokaWaterDownloader(verbose=True, filename_only=True)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.print_verbose("テストメッセージ")
        self.assertEqual("", mock_stdout.getvalue())

    def test_print_verbose_outputs_when_debug(self):
        """debug=True時にもprint_verboseが出力すること"""
        downloader = FukuokaWaterDownloader(debug=True)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.print_verbose("テストメッセージ")
        self.assertIn("テストメッセージ", mock_stdout.getvalue())


class TestOutputLevelSeparation(unittest.TestCase):
    """通常/verbose/debugモードの出力レベル分離テスト"""

    def _capture_output(self, downloader, method_name, *args, **kwargs):
        """指定メソッドの標準出力をキャプチャ"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            method = getattr(downloader, method_name)
            method(*args, **kwargs)
        return mock_stdout.getvalue()

    def test_normal_mode_no_cors_messages(self):
        """通常モードでCORSプリフライトメッセージが出力されないこと"""
        downloader = FukuokaWaterDownloader()
        downloader.jwt_token = "test_token"
        downloader.user_id = "test_user"

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.print_verbose("CORS プリフライト送信中: POST https://example.com")
        self.assertEqual("", mock_stdout.getvalue())

    def test_verbose_mode_shows_cors_messages(self):
        """verboseモードでCORSプリフライトメッセージが出力されること"""
        downloader = FukuokaWaterDownloader(verbose=True)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.print_verbose("CORS プリフライト送信中: POST https://example.com")
        self.assertIn("CORS プリフライト", mock_stdout.getvalue())

    def test_normal_mode_shows_print_output(self):
        """通常モードでprint_outputのメッセージは出力されること"""
        downloader = FukuokaWaterDownloader()

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.print_output("ログインに成功しました")
        self.assertIn("ログインに成功しました", mock_stdout.getvalue())

    def test_normal_mode_no_verbose_messages(self):
        """通常モードでverboseメッセージが出力されないこと"""
        downloader = FukuokaWaterDownloader()

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.print_verbose("ユーザーデータを取得中...")
            downloader.print_verbose("dwKeyを取得しました: 12345")
            downloader.print_verbose("ファイル作成要求中...")
        self.assertEqual("", mock_stdout.getvalue())

    def test_verbose_mode_no_debug_http_logs(self):
        """verboseモード（debug=False）でHTTPログが出力されないこと"""
        downloader = FukuokaWaterDownloader(verbose=True, debug=False)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.log_request("GET", "https://example.com", {"Authorization": "test"})
            downloader.log_response(MagicMock(
                status_code=200, url="https://example.com",
                headers={"content-type": "application/json"},
                json=lambda: {"result": "00000"},
                text="{}"
            ))
        self.assertEqual("", mock_stdout.getvalue())

    def test_debug_mode_shows_http_logs(self):
        """debugモードでHTTPログが出力されること"""
        downloader = FukuokaWaterDownloader(debug=True)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            downloader.log_request("GET", "https://example.com")
        self.assertIn("HTTP REQUEST", mock_stdout.getvalue())


class TestMainFlagParsing(unittest.TestCase):
    """main()でのフラグパース検証"""

    def _run_main_with_args(self, args):
        """main()を指定引数で実行し、作成されたdownloaderの属性を返す"""
        captured_downloader = {}

        original_init = FukuokaWaterDownloader.__init__

        def capture_init(self, **kwargs):
            captured_downloader.update(kwargs)
            original_init(self, **kwargs)

        with patch('sys.argv', ['fukuoka_water_downloader.py'] + args), \
             patch.object(FukuokaWaterDownloader, '__init__', capture_init), \
             patch.object(FukuokaWaterDownloader, 'run', return_value=True), \
             patch('sys.exit'):
            main()
        return captured_downloader

    def test_no_flags_neither_verbose_nor_debug(self):
        """フラグなしでverbose=False, debug=Falseであること"""
        params = self._run_main_with_args(
            ['--email', 'test@example.com', '--password', 'test']
        )
        self.assertFalse(params.get('verbose', False))
        self.assertFalse(params.get('debug', False))

    def test_verbose_flag_sets_verbose_only(self):
        """-v指定でverbose=True, debug=Falseであること"""
        params = self._run_main_with_args(
            ['--email', 'test@example.com', '--password', 'test', '-v']
        )
        self.assertTrue(params.get('verbose'))
        self.assertFalse(params.get('debug', False))

    def test_debug_flag_sets_both(self):
        """-d指定でdebug=True, verbose=Trueであること"""
        params = self._run_main_with_args(
            ['--email', 'test@example.com', '--password', 'test', '-d']
        )
        self.assertTrue(params.get('debug'))
        self.assertTrue(params.get('verbose'))

    def test_debug_log_sets_both(self):
        """--debug-log指定でdebug=True, verbose=Trueであること"""
        params = self._run_main_with_args(
            ['--email', 'test@example.com', '--password', 'test', '--debug-log', 'test.log']
        )
        self.assertTrue(params.get('debug'))
        self.assertTrue(params.get('verbose'))

    def test_verbose_and_debug_together(self):
        """-v -d同時指定でどちらもTrueであること"""
        params = self._run_main_with_args(
            ['--email', 'test@example.com', '--password', 'test', '-v', '-d']
        )
        self.assertTrue(params.get('verbose'))
        self.assertTrue(params.get('debug'))


class TestHelpText(unittest.TestCase):
    """ヘルプテキストの内容検証"""

    def test_verbose_help_describes_step_progress(self):
        """--verboseのヘルプにステップごとの進捗表示の説明があること"""
        help_output = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--help']), \
             patch('sys.stdout', help_output), \
             self.assertRaises(SystemExit):
            main()
        help_text = help_output.getvalue()
        self.assertIn("ステップごと", help_text)

    def test_debug_help_mentions_http_details(self):
        """--debugのヘルプにHTTP詳細の説明があること"""
        help_output = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--help']), \
             patch('sys.stdout', help_output), \
             self.assertRaises(SystemExit):
            main()
        help_text = help_output.getvalue()
        self.assertIn("HTTP", help_text)

    def test_help_shows_verbose_example(self):
        """ヘルプの使用例に--verboseの例があること"""
        help_output = StringIO()
        with patch('sys.argv', ['fukuoka_water_downloader.py', '--help']), \
             patch('sys.stdout', help_output), \
             self.assertRaises(SystemExit):
            main()
        help_text = help_output.getvalue()
        self.assertIn("--verbose", help_text)
        self.assertIn("詳細モード", help_text)


if __name__ == '__main__':
    unittest.main()
