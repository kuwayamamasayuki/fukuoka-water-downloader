#!/usr/bin/env python3
"""パストラバーサル防止のテスト"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fukuoka_water_downloader import FukuokaWaterDownloader


class TestSanitizeFilename(unittest.TestCase):
    """sanitize_filenameメソッドのテスト"""

    def test_normal_filename(self):
        """通常のファイル名はそのまま返される"""
        self.assertEqual(
            FukuokaWaterDownloader.sanitize_filename("riyourireki_123.csv"),
            "riyourireki_123.csv"
        )

    def test_path_traversal_relative(self):
        """相対パストラバーサルが除去される"""
        self.assertEqual(
            FukuokaWaterDownloader.sanitize_filename("../../etc/passwd"),
            "passwd"
        )

    def test_path_traversal_deep(self):
        """深い相対パストラバーサルが除去される"""
        self.assertEqual(
            FukuokaWaterDownloader.sanitize_filename("../../../.ssh/authorized_keys"),
            "authorized_keys"
        )

    def test_absolute_path_unix(self):
        """Unix絶対パスからファイル名のみ抽出される"""
        self.assertEqual(
            FukuokaWaterDownloader.sanitize_filename("/etc/cron.d/malicious"),
            "malicious"
        )

    def test_path_with_backslash(self):
        """バックスラッシュを含むパスが処理される"""
        result = FukuokaWaterDownloader.sanitize_filename("..\\..\\Windows\\System32\\evil.exe")
        self.assertNotIn("..", result)
        self.assertNotIn("\\", result)

    def test_empty_filename_raises(self):
        """空のファイル名でValueErrorが発生する"""
        with self.assertRaises(ValueError):
            FukuokaWaterDownloader.sanitize_filename("")

    def test_only_traversal_raises(self):
        """パス部分のみ（ファイル名なし）でValueErrorが発生する"""
        with self.assertRaises(ValueError):
            FukuokaWaterDownloader.sanitize_filename("../../")

    def test_dot_filename(self):
        """ドットで始まるファイル名は許可される"""
        self.assertEqual(
            FukuokaWaterDownloader.sanitize_filename(".bashrc"),
            ".bashrc"
        )

    def test_filename_with_spaces(self):
        """スペースを含むファイル名はそのまま返される"""
        self.assertEqual(
            FukuokaWaterDownloader.sanitize_filename("my file.csv"),
            "my file.csv"
        )

    def test_subdirectory_stripped(self):
        """サブディレクトリが除去されファイル名のみ返される"""
        self.assertEqual(
            FukuokaWaterDownloader.sanitize_filename("subdir/file.csv"),
            "file.csv"
        )


class TestSaveDataPathTraversal(unittest.TestCase):
    """save_dataメソッドがパストラバーサルを防止することのテスト"""

    def setUp(self):
        self.downloader = FukuokaWaterDownloader(debug=False, quiet=True)
        self.test_data = b"test,data\n1,2\n"

    def test_save_data_strips_path(self):
        """save_dataがパストラバーサルを含むファイル名をサニタイズして保存する"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                self.downloader.save_data(self.test_data, "../../evil.csv", "csv")
                # カレントディレクトリに"evil.csv"として保存されること
                self.assertTrue(os.path.exists(os.path.join(tmpdir, "evil.csv")))
                # 親ディレクトリには書き込まれていないこと
                self.assertFalse(os.path.exists(os.path.join(tmpdir, "..", "evil.csv")))
            finally:
                os.chdir(original_cwd)

    def test_save_data_normal_filename(self):
        """save_dataが通常のファイル名で正常に保存する"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                self.downloader.save_data(self.test_data, "riyourireki_123.csv", "csv")
                saved_path = os.path.join(tmpdir, "riyourireki_123.csv")
                self.assertTrue(os.path.exists(saved_path))
                with open(saved_path, 'rb') as f:
                    self.assertEqual(f.read(), self.test_data)
            finally:
                os.chdir(original_cwd)


if __name__ == '__main__':
    unittest.main()
