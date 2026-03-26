#!/usr/bin/env python3
"""デフォルト期間（当月）の通常モード表示を検証するテスト"""

import os
import sys
import unittest
from datetime import datetime
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fukuoka_water_downloader import FukuokaWaterDownloader


class TestDefaultPeriodDisplay(unittest.TestCase):
    """デフォルト期間表示のテスト"""

    def _create_downloader(self, **kwargs):
        downloader = FukuokaWaterDownloader(**kwargs)
        downloader.jwt_token = "test_token"
        downloader.user_id = "test_user"
        return downloader

    def _run_with_capture(self, downloader, **run_kwargs):
        stdout = StringIO()
        with patch('sys.stdout', stdout), \
             patch.object(downloader, 'get_credentials', return_value=('e', 'p')), \
             patch.object(downloader, 'login', return_value=True), \
             patch.object(downloader, 'download_billing_data', return_value=(b'data', 'test.csv')), \
             patch.object(downloader, 'save_data'):
            downloader.run(email='e', password='p', **run_kwargs)
        return stdout.getvalue()

    def test_default_period_shows_current_month(self):
        """日付未指定時に当月が対象期間として表示されること"""
        downloader = self._create_downloader()
        output = self._run_with_capture(downloader)
        now = datetime.now()
        self.assertIn(f"{now.year}年{now.month}月", output)

    def test_default_period_shows_default_label(self):
        """日付未指定時に「デフォルト」の表記があること"""
        downloader = self._create_downloader()
        output = self._run_with_capture(downloader)
        self.assertIn("デフォルト", output)

    def test_default_period_shows_target_period_label(self):
        """日付未指定時に「対象期間」の表記があること"""
        downloader = self._create_downloader()
        output = self._run_with_capture(downloader)
        self.assertIn("対象期間", output)

    def test_specified_range_shows_period(self):
        """期間指定時に対象期間が表示されること"""
        downloader = self._create_downloader()
        output = self._run_with_capture(downloader,
                                        date_from='2024-01', date_to='2024-12')
        self.assertIn("対象期間", output)
        self.assertIn("2024-01", output)
        self.assertIn("2024-12", output)

    def test_same_month_range(self):
        """同じ月指定時に1つだけ表示されること"""
        downloader = self._create_downloader()
        output = self._run_with_capture(downloader,
                                        date_from='2024-06', date_to='2024-06')
        self.assertIn("対象期間: 2024-06", output)
        self.assertNotIn("～", output)

    def test_quiet_mode_no_period(self):
        """quietモードでは対象期間が表示されないこと"""
        downloader = self._create_downloader(quiet=True)
        output = self._run_with_capture(downloader)
        self.assertNotIn("対象期間", output)

    def test_filename_only_mode_no_period(self):
        """filename_onlyモードでは対象期間が表示されないこと"""
        downloader = self._create_downloader(filename_only=True)
        output = self._run_with_capture(downloader)
        self.assertNotIn("対象期間", output)


if __name__ == '__main__':
    unittest.main()
