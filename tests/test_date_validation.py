#!/usr/bin/env python3
"""date_from > date_to の日付バリデーションを検証するテスト"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fukuoka_water_downloader import FukuokaWaterDownloader


class TestParseDateToYearMonth(unittest.TestCase):
    """parse_date_to_year_monthメソッドのテスト"""

    def test_western_yyyy_mm(self):
        result = FukuokaWaterDownloader.parse_date_to_year_month("2024-01")
        self.assertEqual(result, (2024, 1))

    def test_western_yyyy_mm_two_digit_month(self):
        result = FukuokaWaterDownloader.parse_date_to_year_month("2024-12")
        self.assertEqual(result, (2024, 12))

    def test_slash_format(self):
        result = FukuokaWaterDownloader.parse_date_to_year_month("2024/3")
        self.assertEqual(result, (2024, 3))

    def test_dot_format(self):
        result = FukuokaWaterDownloader.parse_date_to_year_month("2024.6")
        self.assertEqual(result, (2024, 6))

    def test_japanese_year_format(self):
        result = FukuokaWaterDownloader.parse_date_to_year_month("2024年1月")
        self.assertEqual(result, (2024, 1))

    def test_reiwa_format(self):
        result = FukuokaWaterDownloader.parse_date_to_year_month("令和6年1月")
        self.assertEqual(result, (2024, 1))

    def test_reiwa_format_double_digit(self):
        result = FukuokaWaterDownloader.parse_date_to_year_month("令和7年12月")
        self.assertEqual(result, (2025, 12))

    def test_heisei_format(self):
        result = FukuokaWaterDownloader.parse_date_to_year_month("平成31年4月")
        self.assertEqual(result, (2019, 4))

    def test_r_notation_uppercase(self):
        result = FukuokaWaterDownloader.parse_date_to_year_month("R6.1")
        self.assertEqual(result, (2024, 1))

    def test_r_notation_lowercase(self):
        result = FukuokaWaterDownloader.parse_date_to_year_month("r6/12")
        self.assertEqual(result, (2024, 12))

    def test_empty_string_returns_current_month(self):
        from datetime import datetime
        now = datetime.now()
        result = FukuokaWaterDownloader.parse_date_to_year_month("")
        self.assertEqual(result, (now.year, now.month))

    def test_unsupported_format_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            FukuokaWaterDownloader.parse_date_to_year_month("abc")
        self.assertIn("サポートされていない日付形式", str(ctx.exception))


class TestDateRangeValidation(unittest.TestCase):
    """run()メソッドでの日付範囲バリデーションテスト"""

    def _create_downloader(self):
        downloader = FukuokaWaterDownloader(quiet=True)
        downloader.jwt_token = "test_token"
        downloader.user_id = "test_user"
        return downloader

    def test_valid_range_same_month(self):
        """同じ月の場合はバリデーションを通過すること"""
        downloader = self._create_downloader()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch.object(downloader, 'download_billing_data', return_value=(b'data', 'test.csv')), \
             patch.object(downloader, 'save_data'):
            result = downloader.run(email='e', password='p',
                                    date_from='2024-01', date_to='2024-01')
        self.assertTrue(result)

    def test_valid_range_from_before_to(self):
        """from < to の場合はバリデーションを通過すること"""
        downloader = self._create_downloader()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch.object(downloader, 'download_billing_data', return_value=(b'data', 'test.csv')), \
             patch.object(downloader, 'save_data'):
            result = downloader.run(email='e', password='p',
                                    date_from='2024-01', date_to='2024-12')
        self.assertTrue(result)

    def test_invalid_range_from_after_to(self):
        """from > to の場合はFalseを返すこと"""
        downloader = self._create_downloader()
        stderr = StringIO()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch('sys.stderr', stderr):
            result = downloader.run(email='e', password='p',
                                    date_from='2025-03', date_to='2024-01')
        self.assertFalse(result)

    def test_invalid_range_shows_error_message(self):
        """from > to の場合にエラーメッセージが出力されること"""
        downloader = FukuokaWaterDownloader()
        stderr = StringIO()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch('sys.stderr', stderr):
            downloader.run(email='e', password='p',
                           date_from='2025-03', date_to='2024-01')
        self.assertIn("開始期間", stderr.getvalue())
        self.assertIn("終了期間", stderr.getvalue())

    def test_invalid_range_reiwa_format(self):
        """令和形式でも逆順を検出すること"""
        downloader = self._create_downloader()
        stderr = StringIO()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch('sys.stderr', stderr):
            result = downloader.run(email='e', password='p',
                                    date_from='令和7年3月', date_to='令和6年1月')
        self.assertFalse(result)

    def test_invalid_range_mixed_format(self):
        """異なる日付形式の混在でもバリデーションが動作すること"""
        downloader = self._create_downloader()
        stderr = StringIO()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch('sys.stderr', stderr):
            result = downloader.run(email='e', password='p',
                                    date_from='令和7年1月', date_to='2024-06')
        self.assertFalse(result)

    def test_valid_range_mixed_format(self):
        """異なる日付形式の混在でも正しい順序は通過すること"""
        downloader = self._create_downloader()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch.object(downloader, 'download_billing_data', return_value=(b'data', 'test.csv')), \
             patch.object(downloader, 'save_data'):
            result = downloader.run(email='e', password='p',
                                    date_from='R6.1', date_to='2025-03')
        self.assertTrue(result)

    def test_invalid_range_year_difference(self):
        """年が異なる逆順を検出すること"""
        downloader = self._create_downloader()
        stderr = StringIO()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch('sys.stderr', stderr):
            result = downloader.run(email='e', password='p',
                                    date_from='2025-01', date_to='2023-12')
        self.assertFalse(result)

    def test_no_date_specified_uses_default(self):
        """日付未指定時はデフォルト（当月）が使われバリデーションエラーにならないこと"""
        downloader = self._create_downloader()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch.object(downloader, 'download_billing_data', return_value=(b'data', 'test.csv')), \
             patch.object(downloader, 'save_data'):
            result = downloader.run(email='e', password='p')
        self.assertTrue(result)

    def test_only_from_specified_no_validation_error(self):
        """fromのみ指定時にバリデーションエラーにならないこと"""
        downloader = self._create_downloader()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch.object(downloader, 'download_billing_data', return_value=(b'data', 'test.csv')), \
             patch.object(downloader, 'save_data'):
            result = downloader.run(email='e', password='p',
                                    date_from='2024-01')
        self.assertTrue(result)

    def test_invalid_date_format_shows_error(self):
        """不正な日付形式の場合にエラーメッセージが出力されること"""
        downloader = FukuokaWaterDownloader()
        stderr = StringIO()
        with patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch('sys.stderr', stderr):
            result = downloader.run(email='e', password='p',
                                    date_from='invalid', date_to='2024-01')
        self.assertFalse(result)
        self.assertIn("日付の解析に失敗しました", stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
