#!/usr/bin/env python3
"""ダウンロード完了時のファイルサイズ表示を検証するテスト"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fukuoka_water_downloader import FukuokaWaterDownloader


class TestFormatFileSize(unittest.TestCase):
    """format_file_sizeメソッドのテスト"""

    def test_bytes(self):
        self.assertEqual(FukuokaWaterDownloader.format_file_size(0), "0 B")
        self.assertEqual(FukuokaWaterDownloader.format_file_size(512), "512 B")
        self.assertEqual(FukuokaWaterDownloader.format_file_size(1023), "1023 B")

    def test_kilobytes(self):
        self.assertEqual(FukuokaWaterDownloader.format_file_size(1024), "1.0 KB")
        self.assertEqual(FukuokaWaterDownloader.format_file_size(2355), "2.3 KB")
        self.assertEqual(FukuokaWaterDownloader.format_file_size(1024 * 100), "100.0 KB")

    def test_megabytes(self):
        self.assertEqual(FukuokaWaterDownloader.format_file_size(1024 * 1024), "1.0 MB")
        self.assertEqual(FukuokaWaterDownloader.format_file_size(1024 * 1024 * 5), "5.0 MB")


class TestSaveDataFileSize(unittest.TestCase):
    """save_dataメソッドでファイルサイズが表示されることの検証"""

    def test_save_shows_file_size(self):
        """保存完了メッセージにファイルサイズが含まれること"""
        downloader = FukuokaWaterDownloader()
        data = b'x' * 2355  # 2.3 KB
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout, \
             patch('builtins.open', unittest.mock.mock_open()):
            downloader.save_data(data, 'test.csv', 'csv')
        output = mock_stdout.getvalue()
        self.assertIn("2.3 KB", output)
        self.assertIn("test.csv", output)

    def test_save_shows_bytes_for_small_files(self):
        """小さいファイルはバイト表示されること"""
        downloader = FukuokaWaterDownloader()
        data = b'x' * 100
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout, \
             patch('builtins.open', unittest.mock.mock_open()):
            downloader.save_data(data, 'test.csv', 'csv')
        self.assertIn("100 B", mock_stdout.getvalue())

    def test_filename_only_mode_no_size(self):
        """filename_onlyモードではファイルサイズを表示しないこと"""
        downloader = FukuokaWaterDownloader(filename_only=True)
        data = b'x' * 2355
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout, \
             patch('builtins.open', unittest.mock.mock_open()):
            downloader.save_data(data, 'test.csv', 'csv')
        output = mock_stdout.getvalue()
        self.assertNotIn("KB", output)
        self.assertIn("test.csv", output)


if __name__ == '__main__':
    unittest.main()
