#!/usr/bin/env python3
"""TLS証明書検証が明示的に有効化されていることを検証するテスト"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fukuoka_water_downloader import FukuokaWaterDownloader


class TestTLSVerify(unittest.TestCase):
    """セッションのTLS証明書検証設定のテスト"""

    def test_session_verify_is_true(self):
        """セッションのverify属性がTrueに設定されていること"""
        downloader = FukuokaWaterDownloader(debug=False, quiet=True)
        self.assertTrue(downloader.session.verify)

    def test_session_verify_is_explicitly_true(self):
        """verify属性がbool型のTrueであること（文字列やパス指定ではない）"""
        downloader = FukuokaWaterDownloader(debug=False, quiet=True)
        self.assertIs(downloader.session.verify, True)

    def test_source_contains_explicit_verify(self):
        """ソースコードにverify = Trueが明示的に記述されていること"""
        import inspect
        source = inspect.getsource(FukuokaWaterDownloader.setup_session)
        self.assertIn("verify = True", source)


if __name__ == '__main__':
    unittest.main()
