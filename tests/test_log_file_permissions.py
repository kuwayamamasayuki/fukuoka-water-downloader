#!/usr/bin/env python3
"""デバッグログファイルのパーミッションが制限されることを検証するテスト"""

import os
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fukuoka_water_downloader import FukuokaWaterDownloader


class TestLogFilePermissions(unittest.TestCase):
    """デバッグログファイルのパーミッションテスト"""

    def test_log_file_permission_is_600(self):
        """デバッグログファイルが0o600（所有者のみ読み書き可能）で作成されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_debug.log")
            FukuokaWaterDownloader(
                debug=True, debug_log_file=log_path, quiet=False
            )
            self.assertTrue(os.path.exists(log_path))
            mode = stat.S_IMODE(os.stat(log_path).st_mode)
            self.assertEqual(mode, 0o600,
                             f"期待: 0o600, 実際: {oct(mode)}")

    def test_log_file_not_group_readable(self):
        """デバッグログファイルがグループから読み取り不可であること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_debug.log")
            FukuokaWaterDownloader(
                debug=True, debug_log_file=log_path, quiet=False
            )
            mode = stat.S_IMODE(os.stat(log_path).st_mode)
            self.assertFalse(mode & stat.S_IRGRP,
                             "グループ読み取り権限が付与されています")

    def test_log_file_not_other_readable(self):
        """デバッグログファイルが他ユーザーから読み取り不可であること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_debug.log")
            FukuokaWaterDownloader(
                debug=True, debug_log_file=log_path, quiet=False
            )
            mode = stat.S_IMODE(os.stat(log_path).st_mode)
            self.assertFalse(mode & stat.S_IROTH,
                             "他ユーザー読み取り権限が付与されています")

    def test_no_log_file_without_debug_log_option(self):
        """debug_log_file未指定時にログファイルが作成されないこと"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "should_not_exist.log")
            FukuokaWaterDownloader(
                debug=True, debug_log_file=None, quiet=False
            )
            self.assertFalse(os.path.exists(log_path))

    def test_source_contains_chmod(self):
        """ソースコードにos.chmod呼び出しが含まれること"""
        import inspect
        source = inspect.getsource(FukuokaWaterDownloader.setup_debug_logging)
        self.assertIn("os.chmod", source)
        self.assertIn("0o600", source)


if __name__ == '__main__':
    unittest.main()
