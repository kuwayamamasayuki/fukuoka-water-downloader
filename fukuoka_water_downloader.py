#!/usr/bin/env python3
"""
福岡市水道局アプリ料金データダウンローダー
Fukuoka City Water Bureau Billing Data Downloader

このスクリプトは福岡市水道局のWebアプリから料金データを自動でダウンロードします。
This script automatically downloads billing data from Fukuoka City Water Bureau web app.
"""

import argparse
import csv
import getpass
import json
import logging
import os
import re
import sys
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv


class FukuokaWaterDownloader:
    """福岡市水道局アプリからデータをダウンロードするクラス"""

    DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0'

    def __init__(self, debug: bool = False, debug_log_file: str = None,
                 quiet: bool = False, filename_only: bool = False,
                 verbose: bool = False):
        self.session = requests.Session()
        self.base_url = "https://www.suido-madoguchi-fukuoka.jp"
        self.api_base_url = "https://api.suido-madoguchi-fukuoka.jp"
        self.jwt_token = None
        self.user_id = None
        self.debug = debug
        self.verbose = verbose or debug
        self.debug_log_file = debug_log_file
        self.quiet = quiet
        self.filename_only = filename_only
        self.setup_session()
        if self.debug:
            self.setup_debug_logging()
        
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
        
        self.session.verify = True

        self.session.headers.update({
            'User-Agent': self.DEFAULT_USER_AGENT
        })

    def convert_date_to_kenyin_format(self, date_str: str) -> str:
        """日付を検針分形式（kenYm）に変換 - 全角数字を使用"""
        def to_fullwidth_number(num):
            """半角数字を全角数字に変換（2桁にパディング）"""
            fullwidth_digits = "０１２３４５６７８９"
            num_str = str(num)
            if len(num_str) == 1:
                return f"　{fullwidth_digits[int(num_str)]}"
            else:
                return ''.join(fullwidth_digits[int(d)] for d in num_str)
        
        def format_reiwa_date(reiwa_year, month):
            """令和年月を正しいスペーシングでフォーマット"""
            year_str = to_fullwidth_number(reiwa_year)
            month_str = to_fullwidth_number(month)
            return f"令和{year_str}年{month_str}月検針分"
        
        def format_heisei_date(heisei_year, month):
            """平成年月を正しいスペーシングでフォーマット"""
            year_str = to_fullwidth_number(heisei_year)
            month_str = to_fullwidth_number(month)
            return f"平成{year_str}年{month_str}月検針分"
        
        if not date_str:
            today = datetime.now()
            reiwa_year = today.year - 2018
            return format_reiwa_date(reiwa_year, today.month)
        
        reiwa_match = re.match(r'令和(\d+)年(\d+)月', date_str)
        if reiwa_match:
            year = int(reiwa_match.group(1))
            month = int(reiwa_match.group(2))
            return format_reiwa_date(year, month)
        
        heisei_match = re.match(r'平成(\d+)年(\d+)月', date_str)
        if heisei_match:
            year = int(heisei_match.group(1))
            month = int(heisei_match.group(2))
            return format_heisei_date(year, month)
        
        western_match = re.match(r'(\d{4})-(\d{1,2})', date_str)
        if western_match:
            year = int(western_match.group(1))
            month = int(western_match.group(2))
            reiwa_year = year - 2018
            if reiwa_year > 0:
                return format_reiwa_date(reiwa_year, month)
            else:
                heisei_year = year - 1988
                return format_heisei_date(heisei_year, month)
        
        western_match2 = re.match(r'(\d{4})年(\d{1,2})月', date_str)
        if western_match2:
            year = int(western_match2.group(1))
            month = int(western_match2.group(2))
            reiwa_year = year - 2018
            if reiwa_year > 0:
                return format_reiwa_date(reiwa_year, month)
            else:
                heisei_year = year - 1988
                return format_heisei_date(heisei_year, month)
        
        date_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if date_match:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            reiwa_year = year - 2018
            if reiwa_year > 0:
                return format_reiwa_date(reiwa_year, month)
            else:
                heisei_year = year - 1988
                return format_heisei_date(heisei_year, month)
        
        slash_dot_match = re.match(r'(\d{4})[/\.](\d{1,2})', date_str)
        if slash_dot_match:
            year = int(slash_dot_match.group(1))
            month = int(slash_dot_match.group(2))
            reiwa_year = year - 2018
            if reiwa_year > 0:
                return format_reiwa_date(reiwa_year, month)
            else:
                heisei_year = year - 1988
                return format_heisei_date(heisei_year, month)
        
        r_notation_match = re.match(r'[Rr](\d{1,2})[/\.](\d{1,2})', date_str)
        if r_notation_match:
            reiwa_year = int(r_notation_match.group(1))
            month = int(r_notation_match.group(2))
            return format_reiwa_date(reiwa_year, month)
        
        raise ValueError(f"サポートされていない日付形式です: {date_str}")

    @staticmethod
    def parse_date_to_year_month(date_str: str) -> Tuple[int, int]:
        """日付文字列を西暦の(year, month)タプルに変換（バリデーション用）"""
        if not date_str:
            today = datetime.now()
            return (today.year, today.month)

        reiwa_match = re.match(r'令和(\d+)年(\d+)月', date_str)
        if reiwa_match:
            return (int(reiwa_match.group(1)) + 2018, int(reiwa_match.group(2)))

        heisei_match = re.match(r'平成(\d+)年(\d+)月', date_str)
        if heisei_match:
            return (int(heisei_match.group(1)) + 1988, int(heisei_match.group(2)))

        western_match = re.match(r'(\d{4})[-年/\.](\d{1,2})', date_str)
        if western_match:
            return (int(western_match.group(1)), int(western_match.group(2)))

        r_notation_match = re.match(r'[Rr](\d{1,2})[/\.](\d{1,2})', date_str)
        if r_notation_match:
            return (int(r_notation_match.group(1)) + 2018, int(r_notation_match.group(2)))

        raise ValueError(f"サポートされていない日付形式です: {date_str}")

    def print_output(self, message: str, is_error: bool = False, is_filename: bool = False):
        """制御された出力（quiet/filename-onlyモードに対応）"""
        if is_error:
            print(message, file=sys.stderr)
        elif self.filename_only and is_filename:
            print(message)
        elif not self.quiet and not self.filename_only:
            print(message)

    def print_verbose(self, message: str):
        """verbose/debugモード時のみ出力（ステップごとの詳細進捗）"""
        if self.verbose and not self.quiet and not self.filename_only:
            print(message)

    def setup_debug_logging(self):
        """デバッグログの設定"""
        if self.debug_log_file:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(message)s',
                handlers=[
                    logging.FileHandler(self.debug_log_file, encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            try:
                os.chmod(self.debug_log_file, 0o600)
            except OSError:
                pass
        else:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """ファイル名をサニタイズしてパストラバーサルを防止"""
        filename = filename.replace('\\', '/')
        filename = os.path.basename(filename)
        if not filename:
            raise ValueError("ファイル名が空です")
        return filename

    def mask_email(self, email: str) -> str:
        """メールアドレスの一部をマスク"""
        if '@' in email:
            local, domain = email.split('@', 1)
            if len(local) > 3:
                masked_local = local[:2] + '*' * (len(local) - 2)
            else:
                masked_local = local[0] + '*' * (len(local) - 1)
            return f"{masked_local}@{domain}"
        return email

    def log_request(self, method: str, url: str, headers: dict = None, data: any = None):
        """Log HTTP request details for debugging"""
        if not self.debug:
            return
        
        message = f"\n=== HTTP REQUEST ===\nMethod: {method}\nURL: {url}\n"
        
        if headers:
            message += "Headers:\n"
            for key, value in headers.items():
                if key.lower() == 'authorization':
                    message += f"  {key}: [MASKED]\n"
                else:
                    message += f"  {key}: {value}\n"
        
        if data:
            message += "Request Body:\n"
            if isinstance(data, dict):
                masked_data = data.copy()
                if 'password' in masked_data:
                    masked_data['password'] = '[MASKED_PASSWORD]'
                if 'loginId' in masked_data:
                    masked_data['loginId'] = '[MASKED_EMAIL]'
                message += f"  {json.dumps(masked_data, indent=2, ensure_ascii=False)}\n"
            else:
                message += f"  {data}\n"
        message += "=" * 20
        
        if self.debug_log_file:
            logging.debug(message)
        else:
            self.print_output(message)

    def log_response(self, response: requests.Response):
        """Log HTTP response details for debugging"""
        if not self.debug:
            return
        
        message = f"\n=== HTTP RESPONSE ===\nStatus Code: {response.status_code}\nURL: {response.url}\n"
        
        message += "Response Headers:\n"
        for key, value in response.headers.items():
            message += f"  {key}: {value}\n"
        
        message += "Response Body:\n"
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                json_data = response.json()
                masked_data = json_data.copy() if isinstance(json_data, dict) else json_data
                if isinstance(masked_data, dict):
                    if 'token' in masked_data:
                        masked_data['token'] = '[MASKED]'
                    if 'data' in masked_data and isinstance(masked_data['data'], dict):
                        if 'mailAddress' in masked_data['data']:
                            masked_data['data']['mailAddress'] = '[MASKED_EMAIL]'
                message += f"  {json.dumps(masked_data, indent=2, ensure_ascii=False)}\n"
            else:
                content = response.text[:500]
                if len(response.text) > 500:
                    content += "... (truncated)"
                message += f"  {content}\n"
        except Exception as e:
            message += f"  Could not parse response: {e}\n"
        message += "=" * 22
        
        if self.debug_log_file:
            logging.debug(message)
        else:
            self.print_output(message)

    def send_cors_preflight(self, url: str, method: str, request_headers: list) -> bool:
        """Send CORS preflight OPTIONS request before actual API call"""
        try:
            preflight_headers = {
                'Access-Control-Request-Method': method,
                'Access-Control-Request-Headers': ','.join(request_headers),
                'Origin': self.base_url,
                'Referer': f'{self.base_url}/',
                'User-Agent': self.DEFAULT_USER_AGENT,
                'accept': '*/*',
                'accept-language': 'ja,en-US;q=0.7,en;q=0.3',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'priority': 'u=4',
                'te': 'trailers',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            self.print_verbose(f"CORS プリフライト送信中: {method} {url}")
            self.log_request("OPTIONS", url, preflight_headers)
            
            response = self.session.options(url, headers=preflight_headers)
            self.log_response(response)
            
            if response.status_code != 200:
                self.print_output("サーバーとの通信に失敗しました。ネットワーク接続を確認してください。", is_error=True)
                self.print_verbose(f"技術詳細: CORS プリフライト失敗 ステータスコード: {response.status_code}")
                return False

            allowed_methods = response.headers.get('Access-Control-Allow-Methods', '')
            allowed_headers = response.headers.get('Access-Control-Allow-Headers', '')

            if method.upper() not in allowed_methods.upper() and '*' not in allowed_methods:
                self.print_output("サーバーとの通信に失敗しました。サーバー側の設定に問題がある可能性があります。", is_error=True)
                self.print_verbose(f"技術詳細: サーバーが {method} メソッドを許可していません: {allowed_methods}")
                return False

            for header in request_headers:
                if header.lower() not in allowed_headers.lower() and '*' not in allowed_headers:
                    self.print_output("サーバーとの通信に失敗しました。サーバー側の設定に問題がある可能性があります。", is_error=True)
                    self.print_verbose(f"技術詳細: サーバーが {header} ヘッダーを許可していません: {allowed_headers}")
                    return False
            
            self.print_verbose("CORS プリフライト成功")
            return True
            
        except Exception as e:
            self.print_output("サーバーとの通信中にエラーが発生しました。ネットワーク接続を確認してください。", is_error=True)
            self.print_verbose(f"技術詳細: CORS プリフライトエラー: {e}")
            return False

    def get_user_data(self) -> bool:
        """ユーザーデータを取得してdwKeyを抽出"""
        try:
            if not self.jwt_token:
                self.print_output("JWTトークンが必要です", is_error=True)
                return False
            
            self.print_verbose("ユーザーデータを取得中...")
            
            userdata_url = f"{self.api_base_url}/user/userdata"
            
            if not self.send_cors_preflight(userdata_url, 'GET', ['authorization']):
                self.print_output("サーバーとの通信準備に失敗しました。処理を中止します。", is_error=True)
                return False
            
            headers = {
                'Authorization': self.jwt_token,
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'ja,en-US;q=0.7,en;q=0.3',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'priority': 'u=0',
                'te': 'trailers',
                'Origin': self.base_url,
                'Referer': f'{self.base_url}/',
                'User-Agent': self.DEFAULT_USER_AGENT,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            self.log_request("GET", userdata_url, headers)
            
            response = self.session.get(userdata_url, headers=headers)
            
            self.log_response(response)
            
            if response.status_code == 200:
                response_data = response.json()
                
                if 'token' in response_data:
                    self.jwt_token = response_data['token']
                    if self.debug:
                        debug_msg = "JWTトークンを更新しました (get_user_data)"
                        if self.debug_log_file:
                            logging.debug(debug_msg)
                        else:
                            self.print_output(debug_msg)
                
                if 'data' in response_data and 'dwKey' in response_data['data']:
                    self.user_id = response_data['data']['dwKey']
                    self.print_verbose(f"dwKeyを取得しました: {self.user_id}")
                    if self.debug:
                        debug_msg = f"ユーザーデータ取得成功: dwKey={self.user_id}"
                        if self.debug_log_file:
                            logging.debug(debug_msg)
                        else:
                            self.print_output(debug_msg)
                    return True
                else:
                    self.print_output("dwKeyが見つかりませんでした", is_error=True)
                    return False
            else:
                self.print_output(f"ユーザーデータ取得に失敗しました。ステータスコード: {response.status_code}", is_error=True)
                self.print_output(f"レスポンス: {response.text}", is_error=True)
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_output(f"ユーザーデータ取得中にエラーが発生しました: {e}", is_error=True)
            if self.debug:
                error_msg = f"ユーザーデータ取得詳細エラー: {str(e)}"
                if self.debug_log_file:
                    logging.debug(error_msg)
                else:
                    self.print_output(error_msg)
            return False

    def get_credentials(self, email: Optional[str] = None, password: Optional[str] = None) -> Tuple[str, str]:
        """認証情報を取得
        優先順位: CLI引数 → 環境変数(WATER_*) → .envファイル → 対話入力
        """
        load_dotenv()

        final_email = email
        final_password = password

        if not final_email:
            final_email = os.getenv('WATER_EMAIL')
        if not final_password:
            final_password = os.getenv('WATER_PASSWORD')

        if not final_email:
            final_email = input("メールアドレスを入力してください: ")
        if not final_password:
            final_password = getpass.getpass("パスワードを入力してください: ")
        
        if not final_email or not final_password:
            raise ValueError("メールアドレスとパスワードが必要です")
        
        return final_email, final_password

    def login(self, email: str, password: str) -> bool:
        """ログイン処理"""
        try:
            self.print_verbose("ログインページにアクセス中...")
            
            login_url = f"{self.base_url}/#/login"
            response = self.session.get(login_url)
            response.raise_for_status()
            
            self.print_verbose("ログイン試行中...")
            
            api_login_url = f"{self.api_base_url}/user/auth/login"
            
            login_data = {
                "loginId": email,
                "password": password
            }
            
            headers = {
                'Content-Type': 'application/json;charset=utf-8',
                'Content-Length': str(len(json.dumps(login_data)))
            }
            
            self.log_request("POST", api_login_url, headers, login_data)
            
            response = self.session.post(
                api_login_url,
                json=login_data,
                headers=headers
            )
            
            self.log_response(response)
            
            if response.status_code == 200:
                response_data = response.json()
                if 'token' in response_data:
                    self.jwt_token = response_data['token']
                    self.print_output("ログインに成功しました")
                    
                    if not self.get_user_data():
                        self.print_output("ユーザーデータの取得に失敗しました", is_error=True)
                        return False
                    
                    return True
                else:
                    self.print_output("認証トークンが取得できませんでした", is_error=True)
                    return False
            else:
                self.print_output(f"ログインに失敗しました。ステータスコード: {response.status_code}", is_error=True)
                self.print_output(f"レスポンス: {response.text}", is_error=True)
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_output(f"ログイン中にエラーが発生しました: {e}", is_error=True)
            if self.debug:
                error_msg = f"ログイン詳細エラー: {str(e)}"
                if self.debug_log_file:
                    logging.debug(error_msg)
                else:
                    self.print_output(error_msg)
            return False

    def download_billing_data(self, date_from: str, date_to: str, output_format: str = 'csv') -> Optional[Tuple[bytes, str]]:
        """料金データをダウンロード"""
        try:
            if not self.jwt_token or not self.user_id:
                self.print_output("認証が必要です", is_error=True)
                return None, None
            
            self.print_output("料金データをダウンロード中...")
            
            ken_ym_from = self.convert_date_to_kenyin_format(date_from)
            ken_ym_to = self.convert_date_to_kenyin_format(date_to)
            
            if not date_from and not date_to:
                ken_ym_from = ken_ym_to = self.convert_date_to_kenyin_format("")
            
            self.print_verbose(f"期間: {ken_ym_from} から {ken_ym_to}")
            
            create_url = f"{self.api_base_url}/user/file/create/payment/log/{self.user_id}"
            
            if not self.send_cors_preflight(create_url, 'POST', ['authorization', 'content-type']):
                self.print_output("サーバーとの通信準備に失敗しました。処理を中止します。", is_error=True)
                return None, None
            
            format_type = "2" if output_format.lower() == 'csv' else "1"  # CSV=2, PDF=1
            
            create_data = {
                "formatType": format_type,
                "kenYmFrom": ken_ym_from,
                "kenYmTo": ken_ym_to
            }
            
            json_body = json.dumps(create_data, separators=(',', ':'), ensure_ascii=False)
            json_bytes = json_body.encode('utf-8')
            
            headers = {
                'Content-Type': 'application/json;charset=utf-8',
                'Authorization': self.jwt_token,
                'Content-Length': str(len(json_bytes)),
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'ja,en-US;q=0.7,en;q=0.3',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'priority': 'u=0',
                'te': 'trailers',
                'Origin': self.base_url,
                'Referer': f'{self.base_url}/',
                'User-Agent': self.DEFAULT_USER_AGENT,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            self.print_verbose("ファイル作成要求中...")
            if self.debug and not self.quiet:
                self.print_output("=== AUTHENTICATION DEBUG INFO ===")
                self.print_output(f"User ID (dwKey): {self.user_id}")
                self.print_output(f"Create URL: {create_url}")
                self.print_output(f"Request body: {json_body}")
                self.print_output(f"Request body UTF-8 bytes: {len(json_bytes)}")
                self.print_output(f"Request body hex: {json_bytes.hex()}")
                self.print_output("=" * 40)
            
            self.log_request("POST", create_url, headers, create_data)
            response = self.session.post(create_url, data=json_bytes, headers=headers)
            self.log_response(response)
            response.raise_for_status()
            
            if response.status_code != 200:
                self.print_output(f"ファイル作成に失敗しました。ステータスコード: {response.status_code}", is_error=True)
                return None, None
            
            create_result = response.json()
            if self.debug and not self.quiet:
                self.print_output(f"ファイル作成結果: {create_result}")
            
            if 'token' in create_result:
                self.jwt_token = create_result['token']
                if self.debug:
                    debug_msg = "JWTトークンを更新しました (download_billing_data - create)"
                    if self.debug_log_file:
                        logging.debug(debug_msg)
                    else:
                        self.print_output(debug_msg)
            
            if create_result.get('result') == '27300':
                self.print_output("エラー 27300: ファイル作成に失敗しました。認証またはパラメータの問題の可能性があります。", is_error=True)
                return None, None
            elif create_result.get('result') != '00000':
                self.print_output(f"予期しないレスポンス: {create_result}", is_error=True)
                return None, None
            
            if 'data' in create_result and 'fileName' in create_result['data']:
                filename = self.sanitize_filename(create_result['data']['fileName'])
            else:
                import time
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"riyourireki_{self.user_id}_{timestamp}.csv"
            
            download_url_endpoint = f"{self.api_base_url}/user/file/download/paylog/{self.user_id}/{filename}"
            
            if not self.send_cors_preflight(download_url_endpoint, 'GET', ['authorization']):
                self.print_output("サーバーとの通信準備に失敗しました。処理を中止します。", is_error=True)
                return None, None
            
            download_headers = {
                'Authorization': self.jwt_token,
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'ja,en-US;q=0.7,en;q=0.3',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'priority': 'u=0',
                'te': 'trailers',
                'Origin': self.base_url,
                'Referer': f'{self.base_url}/',
                'User-Agent': self.DEFAULT_USER_AGENT,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            self.print_verbose("ダウンロードURL取得中...")
            self.log_request("GET", download_url_endpoint, download_headers)
            response = self.session.get(download_url_endpoint, headers=download_headers)
            self.log_response(response)
            response.raise_for_status()
            
            if response.status_code != 200:
                self.print_output(f"ダウンロードURL取得に失敗しました。ステータスコード: {response.status_code}", is_error=True)
                return None, None
            
            download_info = response.json()
            if self.debug and not self.quiet:
                self.print_output(f"ダウンロード情報: {download_info}")
            
            if 'token' in download_info:
                self.jwt_token = download_info['token']
                if self.debug:
                    debug_msg = "JWTトークンを更新しました (download_billing_data - download)"
                    if self.debug_log_file:
                        logging.debug(debug_msg)
                    else:
                        self.print_output(debug_msg)
            
            if download_info.get('result') == '21801':
                self.print_output("エラー 21801: ダウンロードURL取得に失敗しました。認証またはファイル作成の問題の可能性があります。", is_error=True)
                return None, None
            elif download_info.get('result') != '00000':
                self.print_output(f"予期しないレスポンス: {download_info}", is_error=True)
                return None, None
            
            if 'downloadUrl' in download_info:
                signed_url = download_info['downloadUrl']
            else:
                download_domain = self.base_url.replace('://www.', '://download.')
                signed_url = f"{download_domain}/paylog/{self.user_id}/{filename}"
            
            self.print_verbose("実際のファイルをダウンロード中...")
            self.log_request("GET", signed_url)
            response = self.session.get(signed_url)
            self.log_response(response)
            response.raise_for_status()
            
            if response.status_code == 200:
                self.print_verbose(f"データのダウンロードに成功しました（サイズ: {len(response.content)} bytes）")

                content_type = response.headers.get('content-type', '')
                self.print_verbose(f"Content-Type: {content_type}")
                
                return response.content, filename
            else:
                self.print_output(f"ダウンロードに失敗しました。ステータスコード: {response.status_code}", is_error=True)
                return None, None
                
        except requests.exceptions.RequestException as e:
            self.print_output(f"ダウンロード中にエラーが発生しました: {e}", is_error=True)
            if self.debug:
                error_msg = f"ダウンロード詳細エラー: {str(e)}"
                if self.debug_log_file:
                    logging.debug(error_msg)
                else:
                    self.print_output(error_msg)
            return None, None

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """バイト数を人間が読みやすい形式に変換"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def save_data(self, data: bytes, filename: str, output_format: str):
        """データをファイルに保存"""
        try:
            filename = self.sanitize_filename(filename)
            if output_format.lower() == 'csv':
                with open(filename, 'wb') as f:
                    f.write(data)
            else:
                with open(filename, 'wb') as f:
                    f.write(data)
            
            if self.filename_only:
                self.print_output(filename, is_filename=True)
            else:
                size_str = self.format_file_size(len(data))
                self.print_output(f"データを {filename} ({size_str}) に保存しました", is_filename=True)
            
        except Exception as e:
            self.print_output(f"ファイル保存中にエラーが発生しました: {e}", is_error=True)

    def run(self, email: Optional[str] = None, password: Optional[str] = None,
            date_from: Optional[str] = None, date_to: Optional[str] = None,
            output_format: str = 'csv', output_file: Optional[str] = None):
        """メイン実行処理"""
        try:
            email, password = self.get_credentials(email, password)
            
            if not self.login(email, password):
                self.print_output("ログインに失敗しました。処理を終了します。", is_error=True)
                return False
            
            if not date_from and not date_to:
                now = datetime.now()
                current_month = now.strftime("%Y-%m")
                date_from = date_to = current_month
                self.print_output(f"対象期間: {now.year}年{now.month}月（デフォルト: 当月）")
            else:
                if date_from and date_to and date_from == date_to:
                    self.print_output(f"対象期間: {date_from}")
                elif date_from and date_to:
                    self.print_output(f"対象期間: {date_from} ～ {date_to}")
                elif date_from:
                    self.print_output(f"対象期間: {date_from} ～")
                elif date_to:
                    self.print_output(f"対象期間: ～ {date_to}")

            if date_from and date_to:
                try:
                    from_ym = self.parse_date_to_year_month(date_from)
                    to_ym = self.parse_date_to_year_month(date_to)
                    if from_ym > to_ym:
                        self.print_output(
                            f"エラー: 開始期間({date_from})が終了期間({date_to})より後になっています",
                            is_error=True)
                        return False
                except ValueError as e:
                    self.print_output(f"日付の解析に失敗しました: {e}", is_error=True)
                    return False

            result = self.download_billing_data(date_from, date_to, output_format)
            
            if not result or not result[0]:
                self.print_output("データのダウンロードに失敗しました。", is_error=True)
                return False
            
            data, api_filename = result
            
            if not output_file:
                output_file = api_filename if api_filename else f"fukuoka_water_bill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format}"
            
            self.save_data(data, output_file, output_format)
            
            self.print_output("処理が正常に完了しました。")
            return True
            
        except Exception as e:
            self.print_output(f"処理中にエラーが発生しました: {e}", is_error=True)
            return False
        finally:
            self.jwt_token = None
            self.user_id = None


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='福岡市水道局アプリから料金データを自動ダウンロード',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 対話入力（最も安全 - パスワードは画面に表示されません）
  python fukuoka_water_downloader.py

  # .envファイル（推奨 - 自動化にも対応）
  cp .env.example .env  # .envを編集して認証情報を設定
  python fukuoka_water_downloader.py

  # 環境変数
  export WATER_EMAIL=user@example.com
  export WATER_PASSWORD=mypassword
  python fukuoka_water_downloader.py

  # 期間指定
  python fukuoka_water_downloader.py --date-from "令和5年1月" --date-to "令和5年12月"
  python fukuoka_water_downloader.py --date-from "2023-01" --date-to "2023-12"

  # 出力形式指定
  python fukuoka_water_downloader.py --format csv --output billing_data.csv

  # 詳細モード（ステップごとの進捗を表示）
  python fukuoka_water_downloader.py --verbose

  # デバッグモード（--verbose の内容に加え、HTTP通信の詳細を表示）
  python fukuoka_water_downloader.py --debug
  python fukuoka_water_downloader.py --debug-log debug.log

  # 静寂モード（--quiet と --filename-only は同時に指定できません）
  python fukuoka_water_downloader.py --quiet
  python fukuoka_water_downloader.py --filename-only --format csv

セキュリティに関する注意:
  --password引数はシェル履歴やpsコマンドの出力に残るため、
  .envファイル、環境変数、または対話入力の使用を推奨します。

終了コード:
  0  正常終了（ダウンロード成功）
  1  異常終了（認証失敗、パラメータエラー等）
        """
    )
    
    parser.add_argument('--email', '-e',
                        help='ログイン用メールアドレス（環境変数 WATER_EMAIL でも指定可能）')
    parser.add_argument('--password', '-p',
                        help='ログイン用パスワード（非推奨: シェル履歴に残ります。環境変数 WATER_PASSWORD または .envファイルを推奨）')
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
                        help='詳細な進捗を表示（ステップごとの状況）')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='デバッグ情報を表示（--verbose の内容に加え、HTTPリクエスト/レスポンスの詳細）')
    parser.add_argument('--debug-log',
                        help='デバッグ情報をファイルに保存（ファイル名を指定）')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='エラー以外の出力を抑制（静寂モード、--filename-only と同時指定不可）')
    parser.add_argument('--filename-only', action='store_true',
                        help='保存されたファイル名のみを出力（--quiet と同時指定不可）')
    
    args = parser.parse_args()
    
    if args.password:
        print("警告: --password引数はシェル履歴やpsコマンドの出力に残る可能性があります。"
              "環境変数、.envファイル、または対話入力の使用を推奨します。",
              file=sys.stderr)

    if args.quiet and args.filename_only:
        print("エラー: --quiet と --filename-only は同時に指定できません", file=sys.stderr)
        sys.exit(1)
    
    debug_enabled = args.debug or bool(args.debug_log)
    verbose_enabled = args.verbose or debug_enabled
    debug_log_file = args.debug_log if args.debug_log else None

    downloader = FukuokaWaterDownloader(debug=debug_enabled, debug_log_file=debug_log_file,
                                        quiet=args.quiet, filename_only=args.filename_only,
                                        verbose=verbose_enabled)
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
