#!/usr/bin/env python3
"""
福岡市水道局アプリから水道料金データをダウンロードするスクリプト
Fukuoka City Water Bureau App - Water Bill Data Scraper
"""

import os
import time
import json
import argparse
import getpass
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fukuoka_water_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FukuokaWaterScraper:
    def __init__(self, headless=True, download_dir=None):
        """
        スクレイパーの初期化
        
        Args:
            headless (bool): ヘッドレスモードで実行するかどうか
            download_dir (str): ダウンロードディレクトリのパス
        """
        self.headless = headless
        self.download_dir = download_dir or os.path.join(os.getcwd(), 'downloads')
        self.driver = None
        self.wait = None
        
        os.makedirs(self.download_dir, exist_ok=True)
    
    def convert_western_to_japanese_era(self, period_str):
        """
        Convert various date formats to Japanese era format (e.g., '令和　６年　１月検針分')
        
        Supported formats:
        - 2024年1月, 2024年01月
        - 2024/1, 2024/01
        - R6.1, R6/1 (Reiwa era shorthand)
        - 令和６年１月, 令和6年1月 (Japanese era format)
        """
        if not period_str:
            return None
            
        try:
            western_year = None
            month = None
            
            def to_fullwidth(num):
                fullwidth_digits = "０１２３４５６７８９"
                return ''.join(fullwidth_digits[int(d)] for d in str(num))
            
            period_str = period_str.strip()
            
            match = re.match(r'(\d{4})年(\d{1,2})月?', period_str)
            if match:
                western_year = int(match.group(1))
                month = int(match.group(2))
            
            if not match:
                match = re.match(r'(\d{4})[/\.](\d{1,2})', period_str)
                if match:
                    western_year = int(match.group(1))
                    month = int(match.group(2))
            
            if not match:
                match = re.match(r'[Rr](\d{1,2})[/\.](\d{1,2})', period_str)
                if match:
                    reiwa_year = int(match.group(1))
                    month = int(match.group(2))
                    western_year = reiwa_year + 2018  # Convert Reiwa to Western year
            
            if not match:
                match = re.match(r'令和[　\s]*([０-９\d]{1,2})年[　\s]*([０-９\d]{1,2})月?', period_str)
                if match:
                    reiwa_year_str = match.group(1)
                    month_str = match.group(2)
                    
                    fullwidth_to_halfwidth = str.maketrans('０１２３４５６７８９', '0123456789')
                    reiwa_year = int(reiwa_year_str.translate(fullwidth_to_halfwidth))
                    month = int(month_str.translate(fullwidth_to_halfwidth))
                    western_year = reiwa_year + 2018
            
            # If no pattern matched, return None
            if western_year is None or month is None:
                logger.warning(f"Could not parse date format: '{period_str}'")
                return None
            
            if month < 1 or month > 12:
                logger.warning(f"Invalid month: {month}")
                return None
            
            if western_year >= 2019:
                reiwa_year = western_year - 2018
                
                if month < 10:
                    month_str = f"　{to_fullwidth(month)}月"
                else:
                    if month == 11:
                        month_str = f"{to_fullwidth(month)}月"  # 11月 has no leading space
                    else:
                        month_str = f"{to_fullwidth(month)}月"
                
                if reiwa_year < 10:
                    year_str = f"　{to_fullwidth(reiwa_year)}年"
                else:
                    year_str = f"{to_fullwidth(reiwa_year)}年"
                
                japanese_format = f"令和{year_str}{month_str}検針分"
                logger.info(f"Converted '{period_str}' to '{japanese_format}'")
                return japanese_format
            else:
                logger.warning(f"Year {western_year} is before Reiwa era (2019+)")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to convert period format '{period_str}': {e}")
            return None
        
    def setup_driver(self):
        """Chromeドライバーのセットアップ"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            prefs = {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            service = Service()
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("Chromeドライバーのセットアップが完了しました")
            
        except Exception as e:
            logger.error(f"ドライバーのセットアップに失敗しました: {e}")
            raise
    
    def login(self, email, password):
        """
        ログイン処理
        
        Args:
            email (str): メールアドレス
            password (str): パスワード
            
        Returns:
            bool: ログイン成功の場合True
        """
        try:
            logger.info("ログインページにアクセスしています...")
            self.driver.get("https://www.suido-madoguchi-fukuoka.jp/#/login")
            
            time.sleep(3)
            
            logger.info("メールアドレスを入力しています...")
            email_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_field.clear()
            email_field.send_keys(email)
            
            logger.info("パスワードを入力しています...")
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            logger.info("ログインボタンをクリックしています...")
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'ログイン')]")
            login_button.click()
            
            time.sleep(5)
            
            current_url = self.driver.current_url
            if "login" not in current_url:
                logger.info("ログインに成功しました")
                return True
            else:
                logger.error("ログインに失敗しました")
                return False
                
        except TimeoutException:
            logger.error("ログインページの要素が見つかりませんでした（タイムアウト）")
            return False
        except NoSuchElementException as e:
            logger.error(f"ログインページの要素が見つかりませんでした: {e}")
            return False
        except Exception as e:
            logger.error(f"ログイン処理中にエラーが発生しました: {e}")
            return False
    
    def navigate_to_billing_data(self):
        """料金データページへの遷移 - waterPrice ページに移動"""
        try:
            logger.info("料金データページ (waterPrice) を探しています...")
            
            time.sleep(5)
            
            try:
                logger.info("Looking for '料金' button on the left side...")
                
                billing_button_xpath = "/html/body/div/div[1]/div[1]/div/nav/ul/li[4]/div/span"
                
                try:
                    billing_button = self.driver.find_element(By.XPATH, billing_button_xpath)
                    logger.info(f"Found billing button using specific XPath: '{billing_button.text.strip()}'")
                    billing_button.click()
                    time.sleep(3)
                    
                    current_url = self.driver.current_url
                    if 'waterPrice' in current_url:
                        logger.info(f"Successfully navigated to waterPrice page: {current_url}")
                        return True
                    else:
                        logger.warning(f"Specific XPath click didn't navigate to waterPrice, current URL: {current_url}")
                        
                except Exception as e:
                    logger.warning(f"Specific XPath for billing button failed: {e}, trying fallback selectors")
                    
                    billing_button_selectors = [
                        "//a[contains(text(), '料金') and contains(@href, 'waterPrice')]",
                        "//a[@href='#/waterPrice']",
                        "//*[contains(@href, 'waterPrice')]",
                        "//a[contains(text(), '料金')]",
                        "//button[contains(text(), '料金')]",
                        "//*[contains(@class, 'nav') or contains(@class, 'menu')]//*[contains(text(), '料金')]"
                    ]
                    
                    for selector in billing_button_selectors:
                        try:
                            billing_buttons = self.driver.find_elements(By.XPATH, selector)
                            for button in billing_buttons:
                                try:
                                    button_text = button.text.strip()
                                    button_href = button.get_attribute('href') or ''
                                    logger.info(f"Found potential billing button: '{button_text}' -> {button_href}")
                                    
                                    button.click()
                                    time.sleep(3)
                                    
                                    current_url = self.driver.current_url
                                    if 'waterPrice' in current_url:
                                        logger.info(f"Successfully navigated to waterPrice page: {current_url}")
                                        return True
                                        
                                except Exception as e:
                                    logger.warning(f"Error clicking billing button: {e}")
                                    continue
                        except Exception as e:
                            logger.warning(f"Error with selector {selector}: {e}")
                            continue
                        
            except Exception as e:
                logger.warning(f"Failed to find billing button: {e}")
            
            try:
                current_url = self.driver.current_url
                base_url = current_url.split('#')[0]
                water_price_url = base_url + "#/waterPrice"
                logger.info(f"Trying direct navigation to: {water_price_url}")
                self.driver.get(water_price_url)
                time.sleep(3)
                
                current_url = self.driver.current_url
                if 'waterPrice' in current_url:
                    logger.info(f"Successfully navigated to waterPrice page: {current_url}")
                    return True
                else:
                    logger.warning(f"Direct navigation failed, current URL: {current_url}")
                    
            except Exception as e:
                logger.warning(f"Direct navigation to waterPrice failed: {e}")
            
            logger.warning("料金データページ (waterPrice) への遷移に失敗しました")
            return False
            
        except Exception as e:
            logger.error(f"料金データページへの遷移中にエラーが発生しました: {e}")
            return False
    
    
    def download_data(self, output_period=None, period_from=None, period_to=None, format_type="CSV"):
        """データのダウンロード処理
        
        Args:
            output_period (str): 出力期間 (単一期間指定、period_from/period_toと併用不可)
            period_from (str): 出力開始期間 (None の場合はデフォルト値を使用)
            period_to (str): 出力終了期間 (None の場合はデフォルト値を使用)
            format_type (str): フォーマット ("CSV", "PDF", "Excel" など)
        """
        try:
            logger.info("ダウンロード機能を探しています...")
            
            download_button_xpath = "/html/body/div/div[1]/div[2]/div/div/div/div[4]/h3/button"
            
            try:
                download_button = self.driver.find_element(By.XPATH, download_button_xpath)
                logger.info(f"Found download button using specific XPath: '{download_button.text.strip()}'")
                download_button.click()
                time.sleep(3)
                download_button_found = True
            except Exception as e:
                logger.warning(f"Specific XPath failed: {e}, trying fallback selectors")
                download_button_found = False
                download_selectors = [
                    "//button[contains(text(), 'ダウンロード')]",
                    "//a[contains(text(), 'ダウンロード')]",
                    "//*[contains(@class, 'download') or contains(@class, 'btn')]//*[contains(text(), 'ダウンロード')]",
                    "//input[@type='button' and contains(@value, 'ダウンロード')]"
                ]
                
                for selector in download_selectors:
                    try:
                        download_buttons = self.driver.find_elements(By.XPATH, selector)
                        for button in download_buttons:
                            try:
                                button_text = button.text.strip()
                                logger.info(f"Found download button: '{button_text}'")
                                button.click()
                                time.sleep(3)
                                download_button_found = True
                                break
                            except Exception as e:
                                logger.warning(f"Error clicking download button: {e}")
                                continue
                        if download_button_found:
                            break
                    except Exception as e:
                        logger.warning(f"Error with download selector {selector}: {e}")
                        continue
            
            if not download_button_found:
                logger.warning("ダウンロードボタンが見つかりませんでした")
                return False
            
            try:
                if output_period is None:
                    logger.info("Setting output period to latest...")
                    
                    period_selectors = [
                        "//select[contains(@name, 'period') or contains(@id, 'period')]",
                        "//input[contains(@name, 'period') or contains(@id, 'period')]",
                        "//*[contains(text(), '出力期間')]/following-sibling::*//select",
                        "//*[contains(text(), '出力期間')]/following-sibling::*//input"
                    ]
                    
                    for selector in period_selectors:
                        try:
                            period_elements = self.driver.find_elements(By.XPATH, selector)
                            if len(period_elements) >= 2:
                                from_element = period_elements[0]
                                to_element = period_elements[1]
                                
                                if to_element.tag_name == "select":
                                    to_value = to_element.get_attribute('value')
                                    if to_value:
                                        from_element.send_keys(to_value)
                                        logger.info(f"Set period from latest: {to_value}")
                                        break
                                elif to_element.tag_name == "input":
                                    to_value = to_element.get_attribute('value')
                                    if to_value:
                                        from_element.clear()
                                        from_element.send_keys(to_value)
                                        logger.info(f"Set period from latest: {to_value}")
                                        break
                        except Exception as e:
                            logger.warning(f"Error setting period with selector {selector}: {e}")
                            continue
                else:
                    logger.info(f"Setting custom output period: {output_period}")
                    period_inputs = self.driver.find_elements(By.XPATH, "//input[contains(@name, 'period') or contains(@id, 'period')]")
                    if period_inputs:
                        period_inputs[0].clear()
                        period_inputs[0].send_keys(output_period)
                        
            except Exception as e:
                logger.warning(f"Error setting output period: {e}")
            
            try:
                logger.info(f"Setting format to: {format_type}")
                
                format_selectors = [
                    f"//select[contains(@name, 'format') or contains(@id, 'format')]//option[contains(text(), '{format_type}')]",
                    f"//input[@type='radio' and contains(@value, '{format_type}')]",
                    f"//*[contains(text(), 'フォーマット')]/following-sibling::*//option[contains(text(), '{format_type}')]",
                    f"//*[contains(text(), 'フォーマット')]/following-sibling::*//input[@value='{format_type}']"
                ]
                
                format_set = False
                for selector in format_selectors:
                    try:
                        format_elements = self.driver.find_elements(By.XPATH, selector)
                        for element in format_elements:
                            try:
                                if element.tag_name == "option":
                                    element.click()
                                elif element.tag_name == "input":
                                    element.click()
                                logger.info(f"Selected format: {format_type}")
                                format_set = True
                                break
                            except Exception as e:
                                logger.warning(f"Error selecting format option: {e}")
                                continue
                        if format_set:
                            break
                    except Exception as e:
                        logger.warning(f"Error with format selector {selector}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Error setting format: {e}")
            
            try:
                logger.info("Clicking final download button...")
                time.sleep(2)  # Wait for form to be ready
                
                final_download_selectors = [
                    "//button[contains(text(), 'ダウンロード')]",
                    "//input[@type='submit' and contains(@value, 'ダウンロード')]",
                    "//input[@type='button' and contains(@value, 'ダウンロード')]",
                    "//*[contains(@class, 'download-btn') or contains(@class, 'submit-btn')]"
                ]
                
                final_download_clicked = False
                for selector in final_download_selectors:
                    try:
                        final_buttons = self.driver.find_elements(By.XPATH, selector)
                        for button in final_buttons:
                            try:
                                button_text = button.text.strip() or button.get_attribute('value') or ''
                                logger.info(f"Attempting to click final download button: '{button_text}'")
                                
                                click_strategies = [
                                    lambda: button.click(),
                                    lambda: self.driver.execute_script("arguments[0].click();", button),
                                    lambda: ActionChains(self.driver).move_to_element(button).click().perform(),
                                    lambda: (
                                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button),
                                        time.sleep(2),
                                        self.driver.execute_script("arguments[0].click();", button)
                                    )[-1],
                                    lambda: (
                                        self.driver.execute_script("""
                                            var overlapping = document.elementsFromPoint(arguments[0].getBoundingClientRect().left + arguments[0].getBoundingClientRect().width/2, 
                                                                                        arguments[0].getBoundingClientRect().top + arguments[0].getBoundingClientRect().height/2);
                                            overlapping.forEach(function(el) {
                                                if (el !== arguments[0] && el.tagName.toLowerCase() === 'label') {
                                                    el.style.pointerEvents = 'none';
                                                }
                                            });
                                            arguments[0].click();
                                        """, button)
                                    )
                                ]
                                
                                for i, strategy in enumerate(click_strategies):
                                    try:
                                        logger.info(f"Trying click strategy {i+1} for download button")
                                        strategy()
                                        logger.info(f"Successfully clicked download button with strategy {i+1}")
                                        final_download_clicked = True
                                        break
                                    except Exception as e:
                                        logger.warning(f"Click strategy {i+1} failed: {e}")
                                        continue
                                
                                if final_download_clicked:
                                    break
                                    
                            except Exception as e:
                                logger.warning(f"Error with download button: {e}")
                                continue
                        if final_download_clicked:
                            break
                    except Exception as e:
                        logger.warning(f"Error with final download selector {selector}: {e}")
                        continue
                
                if final_download_clicked:
                    logger.info("Download initiated, checking for additional steps...")
                    time.sleep(3)  # Wait for any additional UI to appear
                    
                    try:
                        alert = self.driver.switch_to.alert
                        alert_text = alert.text
                        logger.info(f"Found alert dialog: {alert_text}")
                        alert.accept()  # Accept the alert
                        time.sleep(2)
                    except:
                        logger.info("No alert dialog found")
                    
                    modal_handled = False
                    try:
                        download_modal = self.driver.find_element(By.XPATH, "//div[contains(@class, 'modal') and contains(., 'ダウンロード')]")
                        if download_modal:
                            logger.info("Found download modal dialog")
                            
                            try:
                                period_selects = download_modal.find_elements(By.XPATH, ".//select")
                                if len(period_selects) >= 2:
                                    from_select = period_selects[0]  # Left dropdown (from period)
                                    to_select = period_selects[1]    # Right dropdown (to period)
                                    
                                    logger.info("Available period options:")
                                    from_options = Select(from_select).options
                                    to_options = Select(to_select).options
                                    logger.info(f"From dropdown ({len(from_options)} options):")
                                    for i, option in enumerate(from_options):
                                        logger.info(f"  {i}: '{option.text}' (value='{option.get_attribute('value')}')")
                                    logger.info(f"To dropdown ({len(to_options)} options):")
                                    for i, option in enumerate(to_options):
                                        logger.info(f"  {i}: '{option.text}' (value='{option.get_attribute('value')}')")
                                    
                                    if output_period:
                                        logger.info(f"Setting single period: {output_period}")
                                        try:
                                            Select(from_select).select_by_visible_text(output_period)
                                            Select(to_select).select_by_visible_text(output_period)
                                            logger.info(f"Set both periods to: {output_period}")
                                        except Exception as e:
                                            logger.warning(f"Could not set single period '{output_period}': {e}")
                                    
                                    elif period_from or period_to:
                                        current_to = Select(to_select).first_selected_option.text
                                        
                                        if period_from:
                                            converted_from = self.convert_western_to_japanese_era(period_from)
                                            period_to_try = converted_from if converted_from else period_from
                                            
                                            try:
                                                Select(from_select).select_by_visible_text(period_to_try)
                                                logger.info(f"Set start period to: {period_to_try}")
                                            except Exception as e:
                                                logger.warning(f"Could not set start period '{period_from}' (tried '{period_to_try}'): {e}")
                                                logger.info("Available options in from dropdown:")
                                                for option in Select(from_select).options:
                                                    logger.info(f"  - {option.text}")
                                        else:
                                            try:
                                                Select(from_select).select_by_visible_text(current_to)
                                                logger.info(f"Set start period to default end period (most recent): {current_to}")
                                            except Exception as e:
                                                logger.warning(f"Could not set start period to default end period '{current_to}': {e}")
                                                current_from = Select(from_select).first_selected_option.text
                                                logger.info(f"Falling back to default start period: {current_from}")
                                        
                                        if period_to:
                                            converted_to = self.convert_western_to_japanese_era(period_to)
                                            period_to_try = converted_to if converted_to else period_to
                                            
                                            try:
                                                Select(to_select).select_by_visible_text(period_to_try)
                                                logger.info(f"Set end period to: {period_to_try}")
                                            except Exception as e:
                                                logger.warning(f"Could not set end period '{period_to}' (tried '{period_to_try}'): {e}")
                                                logger.info("Available options in to dropdown:")
                                                for option in Select(to_select).options:
                                                    logger.info(f"  - {option.text}")
                                        else:
                                            logger.info(f"Using default end period: {current_to}")
                                    
                                    else:
                                        current_to = Select(to_select).first_selected_option.text
                                        try:
                                            Select(from_select).select_by_visible_text(current_to)
                                            logger.info(f"Set start period to default end period (most recent): {current_to}")
                                        except Exception as e:
                                            logger.warning(f"Could not set start period to default end period '{current_to}': {e}")
                                            current_from = Select(from_select).first_selected_option.text
                                            logger.info(f"Falling back to default start period: {current_from}")
                                        logger.info(f"Using default end period: {current_to}")
                                    
                                    time.sleep(1)
                                else:
                                    logger.warning("Could not find period selection dropdowns in modal")
                            except Exception as e:
                                logger.warning(f"Error setting period in modal: {e}")
                            
                            try:
                                all_radios = download_modal.find_elements(By.XPATH, ".//input[@type='radio']")
                                logger.info(f"Found {len(all_radios)} radio buttons in modal")
                                for i, radio in enumerate(all_radios):
                                    value = radio.get_attribute('value') or 'no-value'
                                    name = radio.get_attribute('name') or 'no-name'
                                    logger.info(f"  Radio {i+1}: name='{name}', value='{value}'")
                                
                                if format_type.upper() == "PDF":
                                    target_value = "1"
                                    format_name = "PDF"
                                else:
                                    target_value = "2"
                                    format_name = "CSV"
                                
                                format_radio = None
                                format_selectors = [
                                    f".//input[@type='radio' and @value='{target_value}']",
                                    f".//input[@type='radio'][{target_value}]",
                                ]
                                
                                for selector in format_selectors:
                                    try:
                                        format_radio = download_modal.find_element(By.XPATH, selector)
                                        logger.info(f"Found {format_name} radio with selector: {selector}")
                                        break
                                    except:
                                        continue
                                
                                if format_radio:
                                    self.driver.execute_script("arguments[0].click();", format_radio)
                                    logger.info(f"Selected {format_name} format")
                                else:
                                    logger.warning(f"Could not find {format_name} radio button, proceeding with default format")
                                    
                            except Exception as e:
                                logger.warning(f"Error setting format in modal: {e}")
                            
                            try:
                                final_download_xpath = "/html/body/div/div[3]/div[2]/div/div/div[5]/button[2]"
                                
                                try:
                                    final_download_btn = self.driver.find_element(By.XPATH, final_download_xpath)
                                    logger.info("Found final download button using specific XPath")
                                except:
                                    final_download_btn = download_modal.find_element(By.CSS_SELECTOR, "button.btn")
                                    if not final_download_btn:
                                        final_download_btn = download_modal.find_element(By.XPATH, ".//button[contains(text(), 'ダウンロード')]")
                                    logger.info("Found final download button using fallback selector")
                                
                                logger.info("Clicking final download button in modal...")
                                
                                self.driver.execute_script("arguments[0].click();", final_download_btn)
                                logger.info("Successfully clicked final download button in modal")
                                modal_handled = True
                                time.sleep(3)
                                
                            except Exception as e:
                                logger.warning(f"Error clicking final download button in modal: {e}")
                                
                    except Exception as e:
                        logger.warning(f"Error handling download modal: {e}")
                    
                    if not modal_handled:
                        logger.warning("Could not properly handle download modal, trying alternative approach...")
                        try:
                            download_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'ダウンロード')]")
                            for btn in download_buttons:
                                try:
                                    self.driver.execute_script("arguments[0].click();", btn)
                                    logger.info("Clicked download button as fallback")
                                    time.sleep(2)
                                    break
                                except:
                                    continue
                        except Exception as e:
                            logger.warning(f"Fallback download button click failed: {e}")
                    
                    current_url = self.driver.current_url
                    logger.info(f"Current URL after download click: {current_url}")
                    
                    new_download_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'ダウンロード') or contains(text(), '完了') or contains(text(), '処理中')]")
                    if new_download_elements:
                        logger.info(f"Found {len(new_download_elements)} new download-related elements:")
                        for element in new_download_elements[:5]:  # Log first 5
                            try:
                                element_text = element.text.strip()
                                if element_text:
                                    logger.info(f"  - {element_text}")
                            except:
                                continue
                    
                    logger.info("Waiting for download completion...")
                    return self.wait_for_download()
                else:
                    logger.warning("Could not find final download button")
                    return False
                    
            except Exception as e:
                logger.error(f"Error clicking final download button: {e}")
                return False
            
        except Exception as e:
            logger.error(f"データダウンロード中にエラーが発生しました: {e}")
            return False
    
    def wait_for_download(self, timeout=120):
        """ダウンロードの完了を待機"""
        try:
            logger.info("ダウンロードの完了を待機しています...")
            
            download_locations = [
                self.download_dir,
                os.path.expanduser("~/Downloads"),
                "/tmp",
                os.getcwd()
            ]
            
            time.sleep(2)  # Give download a moment to start
            
            initial_files = {}
            for location in download_locations:
                if os.path.exists(location):
                    files = [f for f in os.listdir(location) 
                           if f.lower().endswith(('.csv', '.pdf', '.xlsx', '.xls')) 
                           and not f.startswith('.')]
                    initial_files[location] = set(files)
                else:
                    initial_files[location] = set()
            
            logger.info(f"初期ファイル数: {sum(len(files) for files in initial_files.values())}")
            
            start_time = time.time()
            check_interval = 3
            downloaded_files = []
            
            while time.time() - start_time < timeout:
                time.sleep(check_interval)
                
                for location in download_locations:
                    if os.path.exists(location):
                        current_files = set([f for f in os.listdir(location) 
                                           if f.lower().endswith(('.csv', '.pdf', '.xlsx', '.xls')) 
                                           and not f.startswith('.')])
                        
                        new_files = current_files - initial_files[location]
                        
                        if new_files:
                            logger.info(f"新しいファイルを検出: {len(new_files)} ファイル in {location}")
                            
                            for new_file in new_files:
                                file_path = os.path.join(location, new_file)
                                try:
                                    file_size = os.path.getsize(file_path)
                                    time.sleep(1)  # Wait a moment
                                    new_size = os.path.getsize(file_path)
                                    
                                    if file_size == new_size and file_size > 0:  # File is stable and not empty
                                        logger.info(f"安定したファイルを検出: {file_path} ({file_size} bytes)")
                                        
                                        final_path = file_path
                                        if location != self.download_dir:
                                            import shutil
                                            dest_path = os.path.join(self.download_dir, new_file)
                                            try:
                                                shutil.move(file_path, dest_path)
                                                logger.info(f"ファイルを移動しました: {dest_path}")
                                                final_path = dest_path
                                            except Exception as e:
                                                logger.warning(f"ファイル移動に失敗: {e}")
                                                try:
                                                    shutil.copy2(file_path, dest_path)
                                                    logger.info(f"ファイルをコピーしました: {dest_path}")
                                                    final_path = dest_path
                                                except Exception as e2:
                                                    logger.error(f"ファイルコピーも失敗: {e2}")
                                        
                                        downloaded_files.append(final_path)
                                        logger.info(f"ダウンロード完了: {final_path}")
                                        return downloaded_files
                                    else:
                                        logger.info(f"ファイル {new_file} はまだダウンロード中です...")
                                except Exception as e:
                                    logger.warning(f"ファイルサイズチェックエラー: {e}")
                
                if time.time() - start_time > 10:  # After 10 seconds, check for recent files
                    current_time = time.time()
                    for location in download_locations:
                        if os.path.exists(location):
                            try:
                                files = os.listdir(location)
                                for file in files:
                                    if (file.lower().endswith(('.csv', '.pdf', '.xlsx', '.xls')) 
                                        and not file.startswith('.')):
                                        file_path = os.path.join(location, file)
                                        file_mtime = os.path.getmtime(file_path)
                                        
                                        if file_mtime > start_time - 60:  # Allow 1 minute buffer
                                            file_size = os.path.getsize(file_path)
                                            if file_size > 0:
                                                final_path = file_path
                                                if location != self.download_dir:
                                                    import shutil
                                                    dest_path = os.path.join(self.download_dir, file)
                                                    try:
                                                        if not os.path.exists(dest_path):
                                                            shutil.copy2(file_path, dest_path)
                                                            logger.info(f"最近のファイルをコピー: {dest_path}")
                                                            final_path = dest_path
                                                    except Exception as e:
                                                        logger.warning(f"ファイルコピーエラー: {e}")
                                                
                                                if final_path not in downloaded_files:
                                                    downloaded_files.append(final_path)
                                                    logger.info(f"最近のファイルを検出: {final_path} ({file_size} bytes)")
                                                    return downloaded_files
                            except Exception as e:
                                logger.warning(f"最近のファイルチェックエラー: {e}")
                
                temp_files = []
                for location in download_locations:
                    if os.path.exists(location):
                        temp_files.extend([f for f in os.listdir(location) if f.endswith('.crdownload')])
                
                elapsed = time.time() - start_time
                if elapsed % 15 == 0:  # Log every 15 seconds
                    logger.info(f"ダウンロード待機中... ({elapsed:.1f}/{timeout}秒) - 一時ファイル: {len(temp_files)}")
            
            logger.warning("ダウンロードのタイムアウトが発生しました")
            
            for location in download_locations:
                if os.path.exists(location):
                    current_files = set([f for f in os.listdir(location) 
                                       if f.lower().endswith(('.csv', '.pdf', '.xlsx', '.xls')) 
                                       and not f.startswith('.')])
                    
                    new_files = current_files - initial_files[location]
                    if new_files:
                        logger.info(f"タイムアウト後に発見されたファイル: {new_files}")
                        for new_file in new_files:
                            file_path = os.path.join(location, new_file)
                            if os.path.exists(file_path):
                                file_size = os.path.getsize(file_path)
                                if file_size > 0:
                                    final_path = file_path
                                    if location != self.download_dir:
                                        import shutil
                                        dest_path = os.path.join(self.download_dir, new_file)
                                        try:
                                            shutil.move(file_path, dest_path)
                                            logger.info(f"ファイルを移動しました: {dest_path}")
                                            final_path = dest_path
                                        except Exception as e:
                                            logger.warning(f"ファイル移動に失敗: {e}")
                                    
                                    downloaded_files.append(final_path)
                                    logger.info(f"タイムアウト後にファイル検出: {final_path} ({file_size} bytes)")
            
            return downloaded_files
            
        except Exception as e:
            logger.error(f"ダウンロード待機中にエラーが発生しました: {e}")
            return []
    
    
    def check_billing_page_indicators(self):
        """Check if current page contains billing/usage data indicators"""
        try:
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()
            
            url_indicators = ['billing', 'usage', 'ryokin', 'shiyo', 'meisai', 'rireki']
            if any(indicator in current_url for indicator in url_indicators):
                return True
            
            content_indicators = [
                '料金', '使用量', '請求', '明細', '水道料金', 'ご使用量', 
                '請求金額', '上下水道', '検針', '使用実績', 'm³', '円'
            ]
            
            indicator_count = sum(1 for indicator in content_indicators if indicator in page_source)
            
            if indicator_count >= 3:
                logger.info(f"Found {indicator_count} billing indicators on current page")
                return True
            
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            if tables:
                for table in tables:
                    table_text = table.text.lower()
                    if any(indicator in table_text for indicator in content_indicators):
                        logger.info("Found billing data in table structure")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking billing page indicators: {e}")
            return False
    
    def log_page_structure(self):
        """Log current page structure for debugging"""
        try:
            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")
            
            clickable_elements = self.driver.find_elements(By.XPATH, "//a | //button")
            logger.info(f"Found {len(clickable_elements)} clickable elements:")
            
            for i, element in enumerate(clickable_elements[:20]):  # Log first 20
                try:
                    text = element.text.strip()
                    href = element.get_attribute('href') or ''
                    tag = element.tag_name
                    if text:
                        logger.info(f"  {i+1}. {tag}: '{text}' -> {href}")
                except:
                    continue
            
            try:
                title = self.driver.title
                logger.info(f"Page title: {title}")
            except:
                pass
                
        except Exception as e:
            logger.warning(f"Error logging page structure: {e}")

    
    def run(self, email, password, output_period=None, period_from=None, period_to=None, format_type="CSV"):
        """
        メイン実行処理
        
        Args:
            email (str): ログイン用メールアドレス
            password (str): ログイン用パスワード
            output_period (str): 出力期間 (単一期間指定、period_from/period_toと併用不可)
            period_from (str): 出力開始期間 (None の場合はデフォルト値を使用)
            period_to (str): 出力終了期間 (None の場合はデフォルト値を使用)
            format_type (str): フォーマット ("CSV", "PDF", "Excel" など)
            
        Returns:
            dict: 実行結果
        """
        result = {
            "success": False,
            "login_success": False,
            "files_downloaded": False,
            "downloaded_files": [],
            "error_message": None
        }
        
        try:
            self.setup_driver()
            
            if self.login(email, password):
                result["login_success"] = True
                
                self.log_page_structure()
                
                if self.navigate_to_billing_data():
                    
                    download_result = self.download_data(output_period, period_from, period_to, format_type)
                    if download_result:
                        result["files_downloaded"] = True
                        
                        downloaded_files = [
                            os.path.join(self.download_dir, f) 
                            for f in os.listdir(self.download_dir)
                            if os.path.isfile(os.path.join(self.download_dir, f))
                            and not f.endswith('.png')
                            and not f.endswith('.json')
                        ]
                        result["downloaded_files"].extend(downloaded_files)
                
                result["success"] = True
            else:
                result["error_message"] = "ログインに失敗しました"
                
        except Exception as e:
            result["error_message"] = str(e)
            logger.error(f"実行中にエラーが発生しました: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("ブラウザを終了しました")
        
        return result

def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(
        description='福岡市水道局アプリから水道料金ファイルをダウンロードするスクレイパー',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s --email user@example.com --password mypass
  %(prog)s --email user@example.com --password mypass --format PDF
  %(prog)s --email user@example.com --password mypass --period "2024年4月" --format CSV
  %(prog)s --email user@example.com --password mypass --period-from "2024年1月" --period-to "2025年3月" --format CSV
  %(prog)s --email user@example.com --password mypass --output-dir ./downloads
  
環境変数での認証情報指定:
  export mailaddress="user@example.com"
  export password="mypass"
  %(prog)s
        """
    )
    
    parser.add_argument('--email', '-e', 
                       help='ログイン用メールアドレス（環境変数 mailaddress でも指定可能）')
    parser.add_argument('--password', '-p', 
                       help='ログイン用パスワード（環境変数 password でも指定可能）')
    
    parser.add_argument('--period-from', 
                       help='ダウンロード開始期間（例: 2024年4月）')
    parser.add_argument('--period-to', 
                       help='ダウンロード終了期間（例: 2025年3月）')
    parser.add_argument('--period', 
                       help='ダウンロード期間（単一期間指定、--period-from/--period-toと併用不可）')
    parser.add_argument('--format', '-f', 
                       choices=['CSV', 'PDF'], 
                       default='CSV',
                       help='出力フォーマット（デフォルト: CSV）')
    
    parser.add_argument('--output-dir', '-o', 
                       help='ダウンロード先ディレクトリ（デフォルト: ./downloads）')
    
    parser.add_argument('--headful', 
                       action='store_true',
                       help='ブラウザを表示して実行（デバッグ用）')
    
    return parser.parse_args()

def main():
    """メイン関数"""
    args = parse_arguments()
    
    email = args.email or os.environ.get('mailaddress')
    password = args.password or os.environ.get('password')
    
    if not email:
        try:
            email = input("メールアドレスを入力してください: ").strip()
            if not email:
                print("エラー: メールアドレスが入力されませんでした")
                return 1
        except (KeyboardInterrupt, EOFError):
            print("\n処理が中断されました")
            return 1
    
    if not password:
        try:
            password = getpass.getpass("パスワードを入力してください: ").strip()
            if not password:
                print("エラー: パスワードが入力されませんでした")
                return 1
        except (KeyboardInterrupt, EOFError):
            print("\n処理が中断されました")
            return 1
    
    if args.period and (args.period_from or args.period_to):
        print("エラー: --period と --period-from/--period-to は同時に指定できません")
        return 1
    
    print("福岡市水道局アプリ - 水道料金データスクレイパー")
    print("=" * 60)
    print(f"メールアドレス: {email}")
    print(f"出力フォーマット: {args.format}")
    if args.period:
        print(f"出力期間: {args.period}")
    elif args.period_from or args.period_to:
        period_from = args.period_from or 'デフォルト'
        period_to = args.period_to or 'デフォルト'
        print(f"出力期間: {period_from} ～ {period_to}")
    else:
        print(f"出力期間: デフォルト期間")
    print(f"出力ディレクトリ: {args.output_dir or './downloads'}")
    print("=" * 60)
    
    try:
        scraper = FukuokaWaterScraper(
            headless=not args.headful,
            download_dir=args.output_dir
        )
        
        result = scraper.run(
            email=email,
            password=password,
            output_period=args.period,
            period_from=args.period_from,
            period_to=args.period_to,
            format_type=args.format
        )
        
        print("\n" + "=" * 60)
        print("実行結果:")
        print("=" * 60)
        print(f"ログイン成功: {'✓' if result['login_success'] else '✗'}")
        print(f"ファイルダウンロード成功: {'✓' if result['files_downloaded'] else '✗'}")
        
        if result['downloaded_files']:
            print(f"\nダウンロードされたファイル ({len(result['downloaded_files'])} 件):")
            for file_path in result['downloaded_files']:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"  ✓ {os.path.basename(file_path)} ({file_size:,} bytes)")
                    print(f"    {file_path}")
                else:
                    print(f"  ✗ {file_path} (ファイルが見つかりません)")
        
        
        if result['error_message']:
            print(f"\nエラー: {result['error_message']}")
            return 1
        
        if result['success']:
            print("\n🎉 処理が正常に完了しました！")
            return 0
        else:
            print("\n❌ 処理中にエラーが発生しました")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n処理が中断されました")
        return 1
    except Exception as e:
        print(f"\n予期しないエラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
