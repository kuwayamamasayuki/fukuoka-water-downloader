# 福岡市水道局アプリ - 水道料金データスクレイパー

福岡市水道局のWebアプリケーション（https://www.suido-madoguchi-fukuoka.jp/#/login）から水道料金ファイルを自動的にダウンロードするPythonスクリプトです。

## 機能

- 自動ログイン
- CSV/PDF形式でのファイルダウンロード
- 期間指定でのダウンロード
- コマンドライン引数による柔軟な操作
- エラーハンドリング

## 必要な環境

- Python 3.7以上
- Chrome/Chromiumブラウザ
- ChromeDriver

## インストール

1. 必要なパッケージをインストール：
```bash
pip install -r requirements.txt
```

2. ChromeDriverをインストール（Ubuntu/Debian）：
```bash
sudo apt-get update
sudo apt-get install chromium-chromedriver
```

## 使用方法

### コマンドライン実行（推奨）

#### 基本的な使用方法
```bash
# 環境変数で認証情報を設定
export mailaddress="your_email@example.com"
export password="your_password"

# デフォルト設定で実行（CSV形式、最新期間）
python3 fukuoka_water_scraper.py

# または直接認証情報を指定
python3 fukuoka_water_scraper.py --email your_email@example.com --password your_password
```

#### 詳細オプション
```bash
# PDF形式でダウンロード
python3 fukuoka_water_scraper.py --format PDF

# 期間範囲を指定（推奨）
python3 fukuoka_water_scraper.py --period-from "2024年1月" --period-to "2025年3月" --format CSV

# 従来の単一期間指定も引き続き利用可能
python3 fukuoka_water_scraper.py --period "2024年4月" --format CSV

# カスタム出力ディレクトリを指定
python3 fukuoka_water_scraper.py --output-dir ./my_downloads

# ブラウザを表示して実行（デバッグ用）
python3 fukuoka_water_scraper.py --headful
```

#### ヘルプ表示
```bash
python3 fukuoka_water_scraper.py --help
```

### コマンドライン引数

| 引数 | 短縮形 | 説明 | デフォルト |
|------|--------|------|------------|
| `--email` | `-e` | ログイン用メールアドレス | 環境変数 `mailaddress` |
| `--password` | `-p` | ログイン用パスワード | 環境変数 `password` |
| `--period` | | ダウンロード期間（単一期間） | 最新期間 |
| `--period-from` | | ダウンロード開始期間 | Webサイトのデフォルト値 |
| `--period-to` | | ダウンロード終了期間 | Webサイトのデフォルト値 |
| `--format` | `-f` | 出力フォーマット（CSV/PDF） | CSV |
| `--output-dir` | `-o` | ダウンロード先ディレクトリ | ./downloads |
| `--headful` | | ブラウザを表示して実行 | ヘッドレス |
| `--help` | `-h` | ヘルプを表示 | |

### 期間指定の詳細

#### 対応している日付フォーマット

スクリプトは以下の様々な日付フォーマットに対応しています：

```bash
# 標準的な日本語形式
python3 fukuoka_water_scraper.py --period-from "2024年1月"

# 西暦スラッシュ形式
python3 fukuoka_water_scraper.py --period-from "2024/1"

# 西暦ドット形式  
python3 fukuoka_water_scraper.py --period-from "2024.1"

# 令和年号省略形式（ドット）
python3 fukuoka_water_scraper.py --period-from "R6.1"

# 令和年号省略形式（スラッシュ）
python3 fukuoka_water_scraper.py --period-from "R6/1"

# 完全な日本語年号形式
python3 fukuoka_water_scraper.py --period-from "令和６年１月"

# 混合形式（半角・全角数字）
python3 fukuoka_water_scraper.py --period-from "令和6年1月"
```

#### 令和年号対応表

- R1 = 2019年（令和元年）
- R2 = 2020年（令和2年）  
- R3 = 2021年（令和3年）
- R4 = 2022年（令和4年）
- R5 = 2023年（令和5年）
- R6 = 2024年（令和6年）
- R7 = 2025年（令和7年）

#### 異なるフォーマットの組み合わせ

開始期間と終了期間で異なるフォーマットを使用することも可能です：

```bash
# 西暦形式と令和省略形式の組み合わせ
python3 fukuoka_water_scraper.py --period-from "2024/1" --period-to "R7.3"

# 日本語形式と西暦形式の組み合わせ  
python3 fukuoka_water_scraper.py --period-from "令和６年１月" --period-to "2025年3月"

# 省略形式と標準形式の組み合わせ
python3 fukuoka_water_scraper.py --period-from "R6.1" --period-to "2024年12月"
```

### 環境変数での認証情報設定

```bash
# 認証情報を環境変数に設定
export mailaddress="your_email@example.com"
export password="your_password"

# 設定後はメールアドレスとパスワードの指定不要
python3 fukuoka_water_scraper.py --format PDF
```

### Pythonスクリプトとしての使用

```python
from fukuoka_water_scraper import FukuokaWaterScraper

# スクレイパーのインスタンスを作成
scraper = FukuokaWaterScraper(
    headless=True,
    download_dir="./downloads"
)

# スクレイピング実行
result = scraper.run(
    email="your_email@example.com",
    password="your_password",
    output_period=None,  # 最新期間
    format_type="CSV"    # CSV形式
)

if result['success']:
    print("ファイルのダウンロードに成功しました")
    print(f"ダウンロードファイル: {result['downloaded_files']}")
else:
    print(f"エラー: {result['error_message']}")
```

## 出力ファイル

### ダウンロードファイル
- **CSV形式**: `riyourireki_*.csv` - 利用履歴データ
- **PDF形式**: `riyourireki_*.pdf` - 利用履歴PDF


## 設定オプション

### FukuokaWaterScraperクラスのパラメータ

- `headless` (bool): ヘッドレスモードで実行するかどうか（デフォルト: True）
- `download_dir` (str): ダウンロードディレクトリのパス（デフォルト: "./downloads"）

### runメソッドのパラメータ

- `email` (str): ログイン用メールアドレス
- `password` (str): ログイン用パスワード
- `output_period` (str): ダウンロード期間（None で最新期間）
- `format_type` (str): 出力フォーマット（"CSV" または "PDF"）

## エラーハンドリング

スクリプトは以下のエラーを適切に処理します：

- ネットワーク接続エラー
- ログイン失敗
- ページ読み込みタイムアウト
- 要素が見つからない場合
- ダウンロード失敗

## トラブルシューティング

### よくある問題

1. **ChromeDriverが見つからない**
   ```bash
   sudo apt-get install chromium-chromedriver
   ```

2. **ログインに失敗する**
   - メールアドレスとパスワードを確認してください
   - アカウントがロックされていないか確認してください

3. **タイムアウトエラー**
   - インターネット接続を確認してください
   - サイトがメンテナンス中でないか確認してください

4. **ダウンロードが完了しない**
   - ブラウザを表示して実行し、動作を確認してください
   ```bash
   python3 fukuoka_water_scraper.py --headful
   ```

### デバッグ方法

```bash
# ブラウザを表示して詳細ログを確認
python3 fukuoka_water_scraper.py --headful

# ログファイルを確認
tail -f fukuoka_water_scraper.log
```

## 使用例

### 毎月の料金ファイルを自動取得
```bash
#!/bin/bash
# monthly_download.sh

export mailaddress="your_email@example.com"
export password="your_password"

# CSV形式で最新ファイルをダウンロード
python3 fukuoka_water_scraper.py --format CSV --output-dir ./monthly_data

# PDF形式でも保存
python3 fukuoka_water_scraper.py --format PDF --output-dir ./monthly_data
```

### 特定期間のファイル取得
```bash
# 2024年4月のファイルを取得
python3 fukuoka_water_scraper.py --period "2024年4月" --format CSV

# 複数期間のファイルを順次取得
for period in "2024年1月" "2024年2月" "2024年3月"; do
    python3 fukuoka_water_scraper.py --period "$period" --format CSV
    sleep 5  # サーバー負荷軽減のため待機
done
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 注意事項

- このスクリプトは教育目的で作成されています
- 利用規約を遵守してください
- 過度なアクセスは避けてください

## 更新履歴

- v0.5.0: Devinが作成していた変な変更履歴を修正した。
- v0.4.0: スクリーンショットを取らないようにした。
- v0.3.0: 拡張日付フォーマット対応
  - 複数の日付入力フォーマットに対応（2024/1, R6.1, R6/1, 令和６年１月など）
  - 期間範囲指定機能（--period-from, --period-to）
  - 令和年号省略形式対応（R6.1 = 令和6年1月）
  - 異なるフォーマットの組み合わせ対応
  - 全角・半角数字の自動変換
  - 包括的な日付解析エラーハンドリング
- v0.2.0: CLI機能追加
  - コマンドライン引数による柔軟な操作
  - --help/-h オプション
  - --period, --format オプション
  - 環境変数による認証情報設定
- v0.1.0: 初回リリース
  - 基本的なログイン・ファイルダウンロード機能
  - エラーハンドリング
