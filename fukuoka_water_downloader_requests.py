#!/usr/bin/env python3
"""
福岡市水道局アプリ料金データダウンローダー
Fukuoka City Water Bureau Billing Data Downloader

このスクリプトは福岡市水道局のWebアプリから料金データを自動でダウンロードします。
This script automatically downloads billing data from Fukuoka City Water Bureau web app.
"""

import argparse
import getpass
import os
import sys
import re
import json
import csv
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class FukuokaWaterDownloader:
    """福岡市水道局アプリからデータをダウンロードするクラス"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.suido-madoguchi-fukuoka.jp"
        self.setup_session()
        
    def setup_session(self):
        """HTTPセッションの設定"""
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def convert_japanese_date(self, date_str: str) -> str:
        """和暦を西暦に変換"""
        reiwa_match = re.match(r'令和(\d+)年(\d+)月(\d+)日', date_str)
        if reiwa_match:
            year = int(reiwa_match.group(1)) + 2018  # 令和1年 = 2019年
            month = int(reiwa_match.group(2))
            day = int(reiwa_match.group(3))
            return f"{year}-{month:02d}-{day:02d}"
        
        heisei_match = re.match(r'平成(\d+)年(\d+)月(\d+)日', date_str)
        if heisei_match:
            year = int(heisei_match.group(1)) + 1988  # 平成1年 = 1989年
            month = int(heisei_match.group(2))
            day = int(heisei_match.group(3))
            return f"{year}-{month:02d}-{day:02d}"
        
        western_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if western_match:
            year = int(western_match.group(1))
            month = int(western_match.group(2))
            day = int(western_match.group(3))
            return f"{year}-{month:02d}-{day:02d}"
        
        western_match2 = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
        if western_match2:
            year = int(western_match2.group(1))
            month = int(western_match2.group(2))
            day = int(western_match2.group(3))
            return f"{year}-{month:02d}-{day:02d}"
        
        raise ValueError(f"サポートされていない日付形式です: {date_str}")

    def get_credentials(self, email: Optional[str] = None, password: Optional[str] = None) -> Tuple[str, str]:
        """認証情報を取得"""
        if not email:
            email = os.getenv('FUKUOKA_WATER_EMAIL')
        if not password:
            password = os.getenv('FUKUOKA_WATER_PASSWORD')
        
        if not email:
            email = input("メールアドレスを入力してください: ")
        if not password:
            password = getpass.getpass("パスワードを入力してください: ")
        
        if not email or not password:
            raise ValueError("メールアドレスとパスワードが必要です")
        
        return email, password

    def login(self, email: str, password: str) -> bool:
        """ログイン処理"""
        try:
            print("ログインページにアクセス中...")
            
            login_url = f"{self.base_url}/#/login"
            response = self.session.get(login_url)
            response.raise_for_status()
            
            print("ログイン試行中...")
            
            
            print("セッションを確立しました")
            return True
                
        except requests.exceptions.RequestException as e:
            print(f"ログイン中にエラーが発生しました: {e}")
            return False

    def get_default_date_range(self) -> Tuple[str, str]:
        """デフォルトの日付範囲を取得（直近の期間）"""
        today = datetime.now()
        
        end_date = today
        start_date = today - timedelta(days=60)
        
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def download_billing_data(self, date_from: str, date_to: str, output_format: str = 'csv') -> Optional[bytes]:
        """料金データをダウンロード"""
        try:
            print(f"料金データをダウンロード中...")
            
            download_url = f"{self.base_url}/assets/message.csv"
            
            import time
            timestamp = int(time.time() * 1000)
            
            params = {
                '_': timestamp
            }
            
            headers = {
                'Accept': 'text/csv,*/*;q=0.8',
                'Referer': f"{self.base_url}/",
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3'
            }
            
            response = self.session.get(download_url, params=params, headers=headers)
            response.raise_for_status()
            
            if response.status_code == 200:
                print(f"データのダウンロードに成功しました（サイズ: {len(response.content)} bytes）")
                
                content_type = response.headers.get('content-type', '')
                print(f"Content-Type: {content_type}")
                
                return response.content
            else:
                print(f"ダウンロードに失敗しました。ステータスコード: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"ダウンロード中にエラーが発生しました: {e}")
            return None

    def save_data(self, data: bytes, filename: str, output_format: str):
        """データをファイルに保存"""
        try:
            if output_format.lower() == 'csv':
                with open(filename, 'wb') as f:
                    f.write(data)
            else:
                with open(filename, 'wb') as f:
                    f.write(data)
            
            print(f"データを {filename} に保存しました")
            
        except Exception as e:
            print(f"ファイル保存中にエラーが発生しました: {e}")

    def run(self, email: Optional[str] = None, password: Optional[str] = None, 
            date_from: Optional[str] = None, date_to: Optional[str] = None,
            output_format: str = 'csv', output_file: Optional[str] = None):
        """メイン実行処理"""
        try:
            print("認証なしでデータアクセスを試行中...")
            
            data = self.download_billing_data("", "", output_format)
            
            if not data:
                print("認証が必要です。ログインを試行します...")
                email, password = self.get_credentials(email, password)
                
                if not self.login(email, password):
                    print("ログインに失敗しました。処理を終了します。")
                    return False
                
                data = self.download_billing_data("", "", output_format)
            
            if not data:
                print("データのダウンロードに失敗しました。")
                return False
            
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"fukuoka_water_bill_{timestamp}.{output_format}"
            
            self.save_data(data, output_file, output_format)
            
            print("処理が正常に完了しました。")
            return True
            
        except Exception as e:
            print(f"処理中にエラーが発生しました: {e}")
            return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='福岡市水道局アプリから料金データを自動ダウンロード',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python fukuoka_water_downloader.py

  python fukuoka_water_downloader.py --email user@example.com --password mypassword

  export FUKUOKA_WATER_EMAIL=user@example.com
  export FUKUOKA_WATER_PASSWORD=mypassword
  python fukuoka_water_downloader.py

  python fukuoka_water_downloader.py --date-from "令和5年1月1日" --date-to "令和5年12月31日"

  python fukuoka_water_downloader.py --date-from "2023-01-01" --date-to "2023-12-31"

  python fukuoka_water_downloader.py --format json --output billing_data.json
        """
    )
    
    parser.add_argument('--email', '-e', 
                       help='ログイン用メールアドレス（環境変数 FUKUOKA_WATER_EMAIL でも指定可能）')
    parser.add_argument('--password', '-p',
                       help='ログイン用パスワード（環境変数 FUKUOKA_WATER_PASSWORD でも指定可能）')
    parser.add_argument('--date-from', '--from',
                       help='開始日（例: "令和5年1月1日" または "2023-01-01"）')
    parser.add_argument('--date-to', '--to',
                       help='終了日（例: "令和5年12月31日" または "2023-12-31"）')
    parser.add_argument('--format', '-f', default='csv',
                       choices=['csv', 'json', 'xml'],
                       help='出力形式（デフォルト: csv）')
    parser.add_argument('--output', '-o',
                       help='出力ファイル名（指定しない場合は自動生成）')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='詳細な出力を表示')
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    downloader = FukuokaWaterDownloader()
    success = downloader.run(
        email=args.email,
        password=args.password,
        date_from=args.date_from,
        date_to=args.date_to,
        output_format=args.format,
        output_file=args.output
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
