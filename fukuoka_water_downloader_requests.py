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
from bs4 import BeautifulSoup


class FukuokaWaterDownloader:
    """福岡市水道局アプリからデータをダウンロードするクラス"""
    
    def __init__(self, debug: bool = False, debug_log_file: str = None):
        self.session = requests.Session()
        self.base_url = "https://www.suido-madoguchi-fukuoka.jp"
        self.api_base_url = "https://api.suido-madoguchi-fukuoka.jp"
        self.jwt_token = None
        self.user_id = None
        self.debug = debug
        self.debug_log_file = debug_log_file
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
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0'
        })

    def convert_date_to_kenyin_format(self, date_str: str) -> str:
        """日付を検針分形式（kenYm）に変換 - 全角数字を使用"""
        def to_fullwidth_number(num):
            """半角数字を全角数字に変換"""
            fullwidth_digits = "０１２３４５６７８９"
            return ''.join(fullwidth_digits[int(d)] for d in str(num))
        
        if not date_str:
            today = datetime.now()
            reiwa_year = today.year - 2018
            return f"令和　{to_fullwidth_number(reiwa_year)}年　{to_fullwidth_number(today.month)}月検針分"
        
        reiwa_match = re.match(r'令和(\d+)年(\d+)月', date_str)
        if reiwa_match:
            year = int(reiwa_match.group(1))
            month = int(reiwa_match.group(2))
            return f"令和　{to_fullwidth_number(year)}年　{to_fullwidth_number(month)}月検針分"
        
        heisei_match = re.match(r'平成(\d+)年(\d+)月', date_str)
        if heisei_match:
            year = int(heisei_match.group(1))
            month = int(heisei_match.group(2))
            return f"平成　{to_fullwidth_number(year)}年　{to_fullwidth_number(month)}月検針分"
        
        western_match = re.match(r'(\d{4})-(\d{1,2})', date_str)
        if western_match:
            year = int(western_match.group(1))
            month = int(western_match.group(2))
            reiwa_year = year - 2018
            if reiwa_year > 0:
                return f"令和　{to_fullwidth_number(reiwa_year)}年　{to_fullwidth_number(month)}月検針分"
            else:
                heisei_year = year - 1988
                return f"平成　{to_fullwidth_number(heisei_year)}年　{to_fullwidth_number(month)}月検針分"
        
        western_match2 = re.match(r'(\d{4})年(\d{1,2})月', date_str)
        if western_match2:
            year = int(western_match2.group(1))
            month = int(western_match2.group(2))
            reiwa_year = year - 2018
            if reiwa_year > 0:
                return f"令和　{to_fullwidth_number(reiwa_year)}年　{to_fullwidth_number(month)}月検針分"
            else:
                heisei_year = year - 1988
                return f"平成　{to_fullwidth_number(heisei_year)}年　{to_fullwidth_number(month)}月検針分"
        
        date_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if date_match:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            reiwa_year = year - 2018
            if reiwa_year > 0:
                return f"令和　{to_fullwidth_number(reiwa_year)}年　{to_fullwidth_number(month)}月検針分"
            else:
                heisei_year = year - 1988
                return f"平成　{to_fullwidth_number(heisei_year)}年　{to_fullwidth_number(month)}月検針分"
        
        raise ValueError(f"サポートされていない日付形式です: {date_str}")

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
        else:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')

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
            print(message)

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
            print(message)

    def send_cors_preflight(self, url: str, method: str, request_headers: list) -> bool:
        """Send CORS preflight OPTIONS request before actual API call"""
        try:
            preflight_headers = {
                'Access-Control-Request-Method': method,
                'Access-Control-Request-Headers': ','.join(request_headers),
                'Origin': 'https://www.suido-madoguchi-fukuoka.jp',
                'Referer': 'https://www.suido-madoguchi-fukuoka.jp/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
                'accept': '*/*',
                'accept-language': 'ja,en-US;q=0.7,en;q=0.3',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'priority': 'u=4',
                'te': 'trailers',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            print(f"CORS プリフライト送信中: {method} {url}")
            self.log_request("OPTIONS", url, preflight_headers)
            
            response = self.session.options(url, headers=preflight_headers)
            self.log_response(response)
            
            if response.status_code != 200:
                print(f"CORS プリフライト失敗: {response.status_code}")
                return False
            
            allowed_methods = response.headers.get('Access-Control-Allow-Methods', '')
            allowed_headers = response.headers.get('Access-Control-Allow-Headers', '')
            
            if method.upper() not in allowed_methods.upper() and '*' not in allowed_methods:
                print(f"サーバーが {method} メソッドを許可していません: {allowed_methods}")
                return False
            
            for header in request_headers:
                if header.lower() not in allowed_headers.lower() and '*' not in allowed_headers:
                    print(f"サーバーが {header} ヘッダーを許可していません: {allowed_headers}")
                    return False
            
            print("CORS プリフライト成功")
            return True
            
        except Exception as e:
            print(f"CORS プリフライトエラー: {e}")
            return False

    def get_user_data(self) -> bool:
        """ユーザーデータを取得してdwKeyを抽出"""
        try:
            if not self.jwt_token:
                print("JWTトークンが必要です")
                return False
            
            print("ユーザーデータを取得中...")
            
            userdata_url = f"{self.api_base_url}/user/userdata"
            
            if not self.send_cors_preflight(userdata_url, 'GET', ['authorization']):
                print("CORS プリフライトに失敗しました。処理を中止します。")
                return False
            
            headers = {
                'Authorization': self.jwt_token,
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'ja,en-US;q=0.7,en;q=0.3',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'priority': 'u=0',
                'te': 'trailers',
                'Origin': 'https://www.suido-madoguchi-fukuoka.jp',
                'Referer': 'https://www.suido-madoguchi-fukuoka.jp/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
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
                            print(debug_msg)
                
                if 'data' in response_data and 'dwKey' in response_data['data']:
                    self.user_id = response_data['data']['dwKey']
                    print(f"dwKeyを取得しました: {self.user_id}")
                    if self.debug:
                        debug_msg = f"ユーザーデータ取得成功: dwKey={self.user_id}"
                        if self.debug_log_file:
                            logging.debug(debug_msg)
                        else:
                            print(debug_msg)
                    return True
                else:
                    print("dwKeyが見つかりませんでした")
                    return False
            else:
                print(f"ユーザーデータ取得に失敗しました。ステータスコード: {response.status_code}")
                print(f"レスポンス: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"ユーザーデータ取得中にエラーが発生しました: {e}")
            if self.debug:
                error_msg = f"ユーザーデータ取得詳細エラー: {str(e)}"
                if self.debug_log_file:
                    logging.debug(error_msg)
                else:
                    print(error_msg)
            return False

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
                    print("ログインに成功しました")
                    
                    try:
                        payload = self.jwt_token.split('.')[1]
                        payload += '=' * (4 - len(payload) % 4)
                        decoded = base64.b64decode(payload)
                        jwt_data = json.loads(decoded)
                        if self.debug:
                            masked_jwt_data = jwt_data.copy()
                            if self.debug_log_file:
                                logging.debug(f"JWT Payload: {json.dumps(masked_jwt_data, indent=2, ensure_ascii=False)}")
                            else:
                                print(f"JWT Payload: {json.dumps(masked_jwt_data, indent=2, ensure_ascii=False)}")
                    except Exception as e:
                        print(f"JWT解析エラー: {e}")
                        if self.debug:
                            error_msg = f"JWT解析詳細エラー: {str(e)}"
                            if self.debug_log_file:
                                logging.debug(error_msg)
                            else:
                                print(error_msg)
                    
                    if not self.get_user_data():
                        print("ユーザーデータの取得に失敗しました")
                        return False
                    
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
            if self.debug:
                error_msg = f"ログイン詳細エラー: {str(e)}"
                if self.debug_log_file:
                    logging.debug(error_msg)
                else:
                    print(error_msg)
            return False

    def get_default_date_range(self) -> Tuple[str, str]:
        """デフォルトの日付範囲を取得（Webページのドロップダウンから）"""
        try:
            waterPrice_url = f"{self.base_url}/#/waterPrice"
            
            headers = {
                'Authorization': self.jwt_token,
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'accept-language': 'ja,en-US;q=0.7,en;q=0.3',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
                'Referer': f"{self.base_url}/",
            }
            
            if self.debug:
                print(f"[DEBUG] デフォルト期間取得: リクエスト送信中...")
                print(f"[DEBUG] URL: {waterPrice_url}")
                print(f"[DEBUG] Authorization: {self.jwt_token[:20]}..." if self.jwt_token else "[DEBUG] Authorization: None")
            
            response = self.session.get(waterPrice_url, headers=headers)
            
            if self.debug:
                print(f"[DEBUG] レスポンス受信: ステータスコード {response.status_code}")
                print(f"[DEBUG] Content-Type: {response.headers.get('content-type', 'Unknown')}")
                print(f"[DEBUG] Content-Length: {len(response.content)} bytes")
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if self.debug:
                print(f"[DEBUG] HTML解析完了")
                html_preview = str(response.content[:500])
                print(f"[DEBUG] HTML先頭500文字: {html_preview}")
                
                if b'waterPrice' in response.content:
                    print(f"[DEBUG] ページ内容確認: 'waterPrice'文字列が見つかりました")
                else:
                    print(f"[DEBUG] ページ内容確認: 'waterPrice'文字列が見つかりません")
            
            css_selector = 'body > div > div:nth-child(3) > div:nth-child(2) > div > div > div:nth-child(2) > div:nth-child(3) > select'
            
            if self.debug:
                print(f"[DEBUG] CSSセレクター検索: {css_selector}")
            
            dropdown = soup.select_one(css_selector)
            
            if self.debug:
                if dropdown:
                    print(f"[DEBUG] ドロップダウン要素発見: {dropdown.name}")
                    print(f"[DEBUG] ドロップダウン属性: {dropdown.attrs}")
                else:
                    print(f"[DEBUG] ドロップダウン要素が見つかりません")
                    
                    all_selects = soup.find_all('select')
                    print(f"[DEBUG] ページ内のselect要素数: {len(all_selects)}")
                    for i, select in enumerate(all_selects):
                        print(f"[DEBUG] select[{i}]: {select.attrs}")
                        options = select.find_all('option')
                        print(f"[DEBUG] select[{i}] options数: {len(options)}")
                        if options:
                            print(f"[DEBUG] select[{i}] 最初のoption: {options[0].get_text().strip()}")
                            print(f"[DEBUG] select[{i}] 最後のoption: {options[-1].get_text().strip()}")
            
            if dropdown:
                options = dropdown.find_all('option')
                if self.debug:
                    print(f"[DEBUG] オプション数: {len(options)}")
                    for i, option in enumerate(options):
                        print(f"[DEBUG] option[{i}]: '{option.get_text().strip()}'")
                
                if options:
                    latest_option = options[-1].get_text().strip()
                    if self.debug:
                        print(f"[DEBUG] 選択された期間: {latest_option}")
                    return latest_option, latest_option
            
            if self.debug:
                print("[DEBUG] Webスクレイピング失敗: フォールバック期間を使用")
            print("Webページからの期間取得に失敗しました。デフォルト期間を使用します。")
            today = datetime.now()
            end_date = today
            start_date = today - timedelta(days=60)
            fallback_start = start_date.strftime("%Y-%m-%d")
            fallback_end = end_date.strftime("%Y-%m-%d")
            if self.debug:
                print(f"[DEBUG] フォールバック期間: {fallback_start} から {fallback_end}")
            return fallback_start, fallback_end
            
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] 例外発生: {type(e).__name__}: {e}")
                import traceback
                print(f"[DEBUG] スタックトレース:")
                traceback.print_exc()
            print(f"期間取得中にエラーが発生しました: {e}")
            today = datetime.now()
            end_date = today
            start_date = today - timedelta(days=60)
            fallback_start = start_date.strftime("%Y-%m-%d")
            fallback_end = end_date.strftime("%Y-%m-%d")
            if self.debug:
                print(f"[DEBUG] 例外後フォールバック期間: {fallback_start} から {fallback_end}")
            return fallback_start, fallback_end

    def download_billing_data(self, date_from: str, date_to: str, output_format: str = 'csv') -> Optional[Tuple[bytes, str]]:
        """料金データをダウンロード"""
        try:
            if not self.jwt_token or not self.user_id:
                print("認証が必要です")
                return None, None
            
            print("料金データをダウンロード中...")
            
            ken_ym_from = self.convert_date_to_kenyin_format(date_from)
            ken_ym_to = self.convert_date_to_kenyin_format(date_to)
            
            if not date_from and not date_to:
                ken_ym_from = ken_ym_to = self.convert_date_to_kenyin_format("")
            
            print(f"期間: {ken_ym_from} から {ken_ym_to}")
            
            create_url = f"{self.api_base_url}/user/file/create/payment/log/{self.user_id}"
            
            if not self.send_cors_preflight(create_url, 'POST', ['authorization', 'content-type']):
                print("CORS プリフライトに失敗しました。処理を中止します。")
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
                'Origin': 'https://www.suido-madoguchi-fukuoka.jp',
                'Referer': 'https://www.suido-madoguchi-fukuoka.jp/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            print("ファイル作成要求中...")
            if self.debug:
                print(f"=== AUTHENTICATION DEBUG INFO ===")
                print(f"JWT Token (first 100 chars): {self.jwt_token[:100]}...")
                print(f"User ID (dwKey): {self.user_id}")
                print(f"Create URL: {create_url}")
                print(f"Request body: {json_body}")
                print(f"Request body UTF-8 bytes: {len(json_bytes)}")
                print(f"Request body hex: {json_bytes.hex()}")
                print(f"Authorization header: {headers.get('Authorization', 'NOT SET')[:100]}...")
                print("=" * 40)
            
            self.log_request("POST", create_url, headers, create_data)
            response = self.session.post(create_url, data=json_bytes, headers=headers)
            self.log_response(response)
            response.raise_for_status()
            
            if response.status_code != 200:
                print(f"ファイル作成に失敗しました。ステータスコード: {response.status_code}")
                return None, None
            
            create_result = response.json()
            print("ファイル作成結果:", create_result)
            
            if 'token' in create_result:
                self.jwt_token = create_result['token']
                if self.debug:
                    debug_msg = "JWTトークンを更新しました (download_billing_data - create)"
                    if self.debug_log_file:
                        logging.debug(debug_msg)
                    else:
                        print(debug_msg)
            
            if create_result.get('result') == '27300':
                print("エラー 27300: ファイル作成に失敗しました。認証またはパラメータの問題の可能性があります。")
                return None, None
            elif create_result.get('result') != '00000':
                print(f"予期しないレスポンス: {create_result}")
                return None, None
            
            if 'data' in create_result and 'fileName' in create_result['data']:
                filename = create_result['data']['fileName']
            else:
                import time
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"riyourireki_{self.user_id}_{timestamp}.csv"
            
            download_url_endpoint = f"{self.api_base_url}/user/file/download/paylog/{self.user_id}/{filename}"
            
            if not self.send_cors_preflight(download_url_endpoint, 'GET', ['authorization']):
                print("CORS プリフライトに失敗しました。処理を中止します。")
                return None, None
            
            download_headers = {
                'Authorization': self.jwt_token,
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'ja,en-US;q=0.7,en;q=0.3',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'priority': 'u=0',
                'te': 'trailers',
                'Origin': 'https://www.suido-madoguchi-fukuoka.jp',
                'Referer': 'https://www.suido-madoguchi-fukuoka.jp/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            print("ダウンロードURL取得中...")
            self.log_request("GET", download_url_endpoint, download_headers)
            response = self.session.get(download_url_endpoint, headers=download_headers)
            self.log_response(response)
            response.raise_for_status()
            
            if response.status_code != 200:
                print(f"ダウンロードURL取得に失敗しました。ステータスコード: {response.status_code}")
                return None, None
            
            download_info = response.json()
            print(f"ダウンロード情報: {download_info}")
            
            if 'token' in download_info:
                self.jwt_token = download_info['token']
                if self.debug:
                    debug_msg = "JWTトークンを更新しました (download_billing_data - download)"
                    if self.debug_log_file:
                        logging.debug(debug_msg)
                    else:
                        print(debug_msg)
            
            if download_info.get('result') == '21801':
                print("エラー 21801: ダウンロードURL取得に失敗しました。認証またはファイル作成の問題の可能性があります。")
                return None, None
            elif download_info.get('result') != '00000':
                print(f"予期しないレスポンス: {download_info}")
                return None, None
            
            if 'downloadUrl' in download_info:
                signed_url = download_info['downloadUrl']
            else:
                signed_url = f"https://download.suido-madoguchi-fukuoka.jp/paylog/{self.user_id}/{filename}"
            
            print("実際のファイルをダウンロード中...")
            self.log_request("GET", signed_url)
            response = self.session.get(signed_url)
            self.log_response(response)
            response.raise_for_status()
            
            if response.status_code == 200:
                print(f"データのダウンロードに成功しました（サイズ: {len(response.content)} bytes）")
                
                content_type = response.headers.get('content-type', '')
                print(f"Content-Type: {content_type}")
                
                return response.content, filename
            else:
                print(f"ダウンロードに失敗しました。ステータスコード: {response.status_code}")
                return None, None
                
        except requests.exceptions.RequestException as e:
            print(f"ダウンロード中にエラーが発生しました: {e}")
            if self.debug:
                error_msg = f"ダウンロード詳細エラー: {str(e)}"
                if self.debug_log_file:
                    logging.debug(error_msg)
                else:
                    print(error_msg)
            return None, None

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
                print("デフォルトの期間を取得中...")
                date_from, date_to = self.get_default_date_range()
                print(f"デフォルト期間を使用: {date_from} から {date_to}")
            else:
                if date_from:
                    print(f"開始期間: {date_from}")
                if date_to:
                    print(f"終了期間: {date_to}")
            
            result = self.download_billing_data(date_from, date_to, output_format)
            
            if not result or not result[0]:
                print("データのダウンロードに失敗しました。")
                return False
            
            data, api_filename = result
            
            if not output_file:
                output_file = api_filename if api_filename else f"fukuoka_water_bill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format}"
            
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

  python fukuoka_water_downloader_requests.py --debug --email user@example.com --password mypassword
  python fukuoka_water_downloader_requests.py -d -e user@example.com -p mypassword
  
  python fukuoka_water_downloader_requests.py --debug-log debug.log --email user@example.com --password mypassword
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
    parser.add_argument('--debug', '-d', action='store_true',
                       help='デバッグ情報を表示（HTTPリクエスト/レスポンスの詳細）')
    parser.add_argument('--debug-log', 
                       help='デバッグ情報をファイルに保存（ファイル名を指定）')
    
    args = parser.parse_args()
    
    debug_enabled = args.verbose or args.debug or args.debug_log
    debug_log_file = args.debug_log if args.debug_log else None
    
    downloader = FukuokaWaterDownloader(debug=debug_enabled, debug_log_file=debug_log_file)
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
