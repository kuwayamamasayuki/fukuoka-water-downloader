#!/usr/bin/env python3
"""
福岡市水道局アプリ料金データダウンローダー
Fukuoka City Water Bureau Billing Data Downloader

このスクリプトは福岡市水道局のWebアプリから料金データを自動でダウンロードします。
This script automatically downloads billing data from Fukuoka City Water Bureau web app.
"""

import argparse
import base64
import csv
import getpass
import json
import os
import re
import sys
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
        self.api_base_url = "https://api.suido-madoguchi-fukuoka.jp"
        self.jwt_token = None
        self.user_id = None
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://www.suido-madoguchi-fukuoka.jp',
            'Referer': 'https://www.suido-madoguchi-fukuoka.jp/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=0',
            'Te': 'trailers'
        })

    def convert_date_to_kenyin_format(self, date_str: str) -> str:
        """日付を検針分形式（kenYm）に変換"""
        if not date_str:
            today = datetime.now()
            reiwa_year = today.year - 2018
            return f"令和　{reiwa_year}年　{today.month}月検針分"
        
        reiwa_match = re.match(r'令和(\d+)年(\d+)月', date_str)
        if reiwa_match:
            year = int(reiwa_match.group(1))
            month = int(reiwa_match.group(2))
            return f"令和　{year}年　{month}月検針分"
        
        heisei_match = re.match(r'平成(\d+)年(\d+)月', date_str)
        if heisei_match:
            year = int(heisei_match.group(1))
            month = int(heisei_match.group(2))
            return f"平成　{year}年　{month}月検針分"
        
        western_match = re.match(r'(\d{4})-(\d{1,2})', date_str)
        if western_match:
            year = int(western_match.group(1))
            month = int(western_match.group(2))
            reiwa_year = year - 2018
            if reiwa_year > 0:
                return f"令和　{reiwa_year}年　{month}月検針分"
            else:
                heisei_year = year - 1988
                return f"平成　{heisei_year}年　{month}月検針分"
        
        western_match2 = re.match(r'(\d{4})年(\d{1,2})月', date_str)
        if western_match2:
            year = int(western_match2.group(1))
            month = int(western_match2.group(2))
            reiwa_year = year - 2018
            if reiwa_year > 0:
                return f"令和　{reiwa_year}年　{month}月検針分"
            else:
                heisei_year = year - 1988
                return f"平成　{heisei_year}年　{month}月検針分"
        
        date_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if date_match:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            reiwa_year = year - 2018
            if reiwa_year > 0:
                return f"令和　{reiwa_year}年　{month}月検針分"
            else:
                heisei_year = year - 1988
                return f"平成　{heisei_year}年　{month}月検針分"
        
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
            
            api_login_url = f"{self.api_base_url}/user/auth/login"
            
            login_data = {
                "loginId": email,
                "password": password
            }
            
            headers = {
                'Content-Type': 'application/json;charset=utf-8',
                'Content-Length': str(len(json.dumps(login_data)))
            }
            
            response = self.session.post(
                api_login_url,
                json=login_data,
                headers=headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if 'token' in response_data:
                    self.jwt_token = response_data['token']
                    print("ログインに成功しました")
                    
                    try:
                        payload = self.jwt_token.split('.')[1]
                        payload += '=' * (4 - len(payload) % 4)
                        decoded = base64.b64decode(payload)
                        jwt_data = json.loads(decoded)
                        self.user_id = jwt_data.get('userId')
                        print(f"ユーザーID: {self.user_id}")
                    except Exception as e:
                        print(f"JWT解析エラー: {e}")
                    
                    return True
                else:
                    print("認証トークンが取得できませんでした")
                    return False
            else:
                print(f"ログインに失敗しました。ステータスコード: {response.status_code}")
                print(f"レスポンス: {response.text}")
                return False
                
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
            if not self.jwt_token or not self.user_id:
                print("認証が必要です")
                return None
            
            print(f"料金データをダウンロード中...")
            
            ken_ym_from = self.convert_date_to_kenyin_format(date_from)
            ken_ym_to = self.convert_date_to_kenyin_format(date_to)
            
            if not date_from and not date_to:
                ken_ym_from = ken_ym_to = self.convert_date_to_kenyin_format("")
            
            print(f"期間: {ken_ym_from} から {ken_ym_to}")
            
            create_url = f"{self.api_base_url}/user/file/create/payment/log/{self.user_id}"
            
            format_type = "2" if output_format.lower() == 'csv' else "1"  # CSV=2, PDF=1
            
            create_data = {
                "formatType": format_type,
                "kenYmFrom": ken_ym_from,
                "kenYmTo": ken_ym_to
            }
            
            headers = {
                'Content-Type': 'application/json;charset=utf-8',
                'Authorization': self.jwt_token,
                'Content-Length': str(len(json.dumps(create_data)))
            }
            
            print("ファイル作成要求中...")
            response = self.session.post(create_url, json=create_data, headers=headers)
            response.raise_for_status()
            
            if response.status_code != 200:
                print(f"ファイル作成に失敗しました。ステータスコード: {response.status_code}")
                return None
            
            create_result = response.json()
            print(f"ファイル作成結果: {create_result}")
            
            if 'filename' in create_result:
                filename = create_result['filename']
            else:
                import time
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"riyourireki_{self.user_id.replace('000', '3-0-').replace('0', '-0-')}-{timestamp}.csv"
            
            download_url_endpoint = f"{self.api_base_url}/user/file/download/paylog/{self.user_id}/{filename}"
            
            print("ダウンロードURL取得中...")
            response = self.session.get(download_url_endpoint, headers={'Authorization': self.jwt_token})
            response.raise_for_status()
            
            if response.status_code != 200:
                print(f"ダウンロードURL取得に失敗しました。ステータスコード: {response.status_code}")
                return None
            
            download_info = response.json()
            print(f"ダウンロード情報: {download_info}")
            
            if 'downloadUrl' in download_info:
                signed_url = download_info['downloadUrl']
            else:
                signed_url = f"https://download.suido-madoguchi-fukuoka.jp/paylog/{self.user_id}/{filename}"
            
            print("実際のファイルをダウンロード中...")
            response = self.session.get(signed_url)
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
            email, password = self.get_credentials(email, password)
            
            if not self.login(email, password):
                print("ログインに失敗しました。処理を終了します。")
                return False
            
            if not date_from and not date_to:
                print("デフォルトの期間を使用: 最新のデータのみ")
            else:
                if date_from:
                    print(f"開始期間: {date_from}")
                if date_to:
                    print(f"終了期間: {date_to}")
            
            data = self.download_billing_data(date_from, date_to, output_format)
            
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
  python fukuoka_water_downloader_requests.py

  python fukuoka_water_downloader_requests.py --email user@example.com --password mypassword

  export FUKUOKA_WATER_EMAIL=user@example.com
  export FUKUOKA_WATER_PASSWORD=mypassword
  python fukuoka_water_downloader_requests.py

  python fukuoka_water_downloader_requests.py --date-from "令和5年1月" --date-to "令和5年12月"

  python fukuoka_water_downloader_requests.py --date-from "2023-01" --date-to "2023-12"
  python fukuoka_water_downloader_requests.py --date-from "2023年1月" --date-to "2023年12月"

  python fukuoka_water_downloader_requests.py --format csv --output billing_data.csv
        """
    )
    
    parser.add_argument('--email', '-e', 
                       help='ログイン用メールアドレス（環境変数 FUKUOKA_WATER_EMAIL でも指定可能）')
    parser.add_argument('--password', '-p',
                       help='ログイン用パスワード（環境変数 FUKUOKA_WATER_PASSWORD でも指定可能）')
    parser.add_argument('--date-from', '--from',
                       help='開始期間（例: "令和5年1月", "2023-01", "2023年1月"）')
    parser.add_argument('--date-to', '--to',
                       help='終了期間（例: "令和5年12月", "2023-12", "2023年12月"）')
    parser.add_argument('--format', '-f', default='csv',
                       choices=['csv', 'pdf'],
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
