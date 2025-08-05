# 福岡市水道局アプリ - 水道料金データダウンローダー

[福岡市水道局アプリWeb版](https://www.suido-madoguchi-fukuoka.jp/#/login)から水道料金ファイルを自動的にダウンロードするPythonスクリプトです。

家計簿アプリ／サービスとの連携などに利用することを想定しています。

## 機能

- 自動ログイン
- CSV/PDF形式でのファイルダウンロード
- 期間指定でのダウンロード（現在の月がデフォルト）
- コマンドライン引数による柔軟な操作
- 詳細なデバッグログ機能
- エラーハンドリング
- CORS プリフライト対応

## 必要な環境

- Python 3.7以上
- インターネット接続

## インストール

必要なパッケージをインストール：
```bash
pip install -r requirements.txt
```

## 使用方法

### コマンドライン実行（推奨）

#### 基本的な使用方法
```bash
# 環境変数で認証情報を設定
export FUKUOKA_WATER_EMAIL="your_email@example.com"
export FUKUOKA_WATER_PASSWORD="your_password"

# デフォルト設定で実行（CSV形式、現在の月）
python3 fukuoka_water_downloader.py

# または直接認証情報を指定
python3 fukuoka_water_downloader.py --email your_email@example.com --password your_password
```

#### 詳細オプション
```bash
# PDF形式でダウンロード
python3 fukuoka_water_downloader.py --format pdf

# 期間範囲を指定
python3 fukuoka_water_downloader.py --date-from "2024-01" --date-to "2025-03" --format csv

# カスタム出力ファイル名を指定
python3 fukuoka_water_downloader.py --output custom_filename.csv

# デバッグモードで実行
python3 fukuoka_water_downloader.py --debug

# デバッグログをファイルに保存
python3 fukuoka_water_downloader.py --debug-log debug.log
```

#### ヘルプ表示
```bash
python3 fukuoka_water_downloader.py --help
```

### コマンドライン引数

| 引数 | 短縮形 | 説明 | デフォルト |
|------|--------|------|------------|
| `--email` | `-e` | ログイン用メールアドレス | 環境変数 `FUKUOKA_WATER_EMAIL` |
| `--password` | `-p` | ログイン用パスワード | 環境変数 `FUKUOKA_WATER_PASSWORD` |
| `--date-from` | `--from` | ダウンロード開始期間（YYYY-MM形式） | 現在の月 |
| `--date-to` | `--to` | ダウンロード終了期間（YYYY-MM形式） | 現在の月 |
| `--format` | `-f` | 出力フォーマット（csv/pdf） | csv |
| `--output` | `-o` | 出力ファイル名 | APIから返されるファイル名 |
| `--verbose` | `-v` | 詳細な出力を表示 | False |
| `--debug` | `-d` | デバッグ情報を表示 | False |
| `--debug-log` | | デバッグ情報をファイルに保存 | なし |
| `--help` | `-h` | ヘルプを表示 | |

### 期間指定の詳細

#### 対応している日付フォーマット

スクリプトは以下の様々な日付フォーマットに対応しています：

```bash
# 標準的なYYYY-MM形式（推奨）
python3 fukuoka_water_downloader.py --date-from "2024-01" --date-to "2024-12"

# 日本語形式
python3 fukuoka_water_downloader.py --date-from "2024年1月"

# 西暦スラッシュ形式
python3 fukuoka_water_downloader.py --date-from "2024/1"

# 西暦ドット形式  
python3 fukuoka_water_downloader.py --date-from "2024.1"

# 令和年号省略形式（ドット）
python3 fukuoka_water_downloader.py --date-from "R6.1"

# 令和年号省略形式（スラッシュ）
python3 fukuoka_water_downloader.py --date-from "R6/1"

# 完全な日本語年号形式
python3 fukuoka_water_downloader.py --date-from "令和６年１月"

# 混合形式（半角・全角数字）
python3 fukuoka_water_downloader.py --date-from "令和6年1月"
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
python3 fukuoka_water_downloader_requests.py --date-from "2024/1" --date-to "R7.3"

# 日本語形式と西暦形式の組み合わせ  
python3 fukuoka_water_downloader_requests.py --date-from "令和６年１月" --date-to "2025年3月"

# 省略形式と標準形式の組み合わせ
python3 fukuoka_water_downloader_requests.py --date-from "R6.1" --date-to "2024年12月"
```

### 環境変数での認証情報設定

```bash
# 認証情報を環境変数に設定
export FUKUOKA_WATER_EMAIL="your_email@example.com"
export FUKUOKA_WATER_PASSWORD="your_password"

# 設定後はメールアドレスとパスワードの指定不要
python3 fukuoka_water_downloader_requests.py --format pdf
```

### Pythonスクリプトとしての使用

```python
from fukuoka_water_downloader_requests import FukuokaWaterDownloader

# ダウンローダーのインスタンスを作成
downloader = FukuokaWaterDownloader(debug=True)

# ダウンロード実行
success = downloader.run(
    email="your_email@example.com",
    password="your_password",
    date_from=None,      # 現在の月
    date_to=None,        # 現在の月
    output_format="csv", # CSV形式
    output_file=None     # APIから返されるファイル名を使用
)

if success:
    print("ファイルのダウンロードに成功しました")
else:
    print("ダウンロードに失敗しました")
```

## 出力ファイル

### ダウンロードファイル
- **CSV形式**: APIから返されるファイル名（例：`riyourireki_*.csv`）- 利用履歴データ
- **PDF形式**: APIから返されるファイル名（例：`riyourireki_*.pdf`）- 利用履歴PDF

ファイル名は福岡市水道局のAPIから自動的に取得され、そのまま使用されます。

## 設定オプション

### FukuokaWaterDownloaderクラスのパラメータ

- `debug` (bool): デバッグモードで実行するかどうか（デフォルト: False）
- `debug_log_file` (str): デバッグログファイルのパス（デフォルト: None）

### runメソッドのパラメータ

- `email` (str): ログイン用メールアドレス
- `password` (str): ログイン用パスワード
- `date_from` (str): ダウンロード開始期間（None で現在の月）
- `date_to` (str): ダウンロード終了期間（None で現在の月）
- `output_format` (str): 出力フォーマット（"csv" または "pdf"）
- `output_file` (str): 出力ファイル名（None でAPIから返されるファイル名を使用）

## エラーハンドリング

スクリプトは以下のエラーを適切に処理します：

- ネットワーク接続エラー
- JWT認証エラー
- ログイン失敗
- API呼び出しエラー
- ファイルダウンロード失敗
- CORS プリフライトエラー

## トラブルシューティング

### よくある問題

1. **ログインに失敗する**
   - メールアドレスとパスワードを確認してください
   - アカウントがロックされていないか確認してください
   - 環境変数が正しく設定されているか確認してください

2. **ネットワークエラー**
   - インターネット接続を確認してください
   - サイトがメンテナンス中でないか確認してください
   - プロキシ設定を確認してください

3. **API呼び出しエラー**
   - JWT トークンの有効期限が切れている可能性があります
   - 再度ログインを試してください

4. **ファイルダウンロードが失敗する**
   - デバッグモードで詳細なログを確認してください
   ```bash
   python3 fukuoka_water_downloader_requests.py --debug
   ```

### デバッグ方法

```bash
# デバッグモードで実行
python3 fukuoka_water_downloader_requests.py --debug

# デバッグログをファイルに保存
python3 fukuoka_water_downloader_requests.py --debug-log debug.log

# ログファイルを確認
tail -f debug.log
```

## 使用例

### 毎月の料金ファイルを自動取得
```bash
#!/bin/bash
# monthly_download.sh

export FUKUOKA_WATER_EMAIL="your_email@example.com"
export FUKUOKA_WATER_PASSWORD="your_password"

# CSV形式で現在の月のファイルをダウンロード
python3 fukuoka_water_downloader_requests.py --format csv

# PDF形式でも保存
python3 fukuoka_water_downloader_requests.py --format pdf
```

### 特定期間のファイル取得
```bash
# 2024年4月のファイルを取得
python3 fukuoka_water_downloader_requests.py --date-from "2024-04" --date-to "2024-04" --format csv

# 複数期間のファイルを順次取得
for month in "2024-01" "2024-02" "2024-03"; do
    python3 fukuoka_water_downloader_requests.py --date-from "$month" --date-to "$month" --format csv
    sleep 5  # サーバー負荷軽減のため待機
done

# 期間範囲でのダウンロード
python3 fukuoka_water_downloader_requests.py --date-from "2024-01" --date-to "2024-12" --format csv
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 注意事項

- 利用規約を遵守してください
- 過度なアクセスは避けてください

## テスト

テストスクリプトは `tests/` ディレクトリに配置されています：

```bash
# テストディレクトリの内容を確認
ls tests/

# 特定のテストを実行
python3 tests/test_date_conversion.py
python3 tests/test_requests_implementation.py
```



## 更新履歴

- v1.1.0:
  - スクリプト名をfukuoka_water_downloader.pyへ変更した。
  - --quietオプションを追加した。
  - --filename-onlyオプションを追加した。
- v1.0.0: Requests ベース実装への移行
  - Selenium から requests ライブラリへの完全移行
  - JWT 認証による自動ログイン
  - CORS プリフライト対応
  - APIから返されるファイル名の自動使用
  - デフォルト日付範囲を現在の月に簡素化
  - 詳細なデバッグログ機能
  - 16進数ログ出力によるデバッグ支援
- v0.5.0: Devinが作成していた変な変更履歴を修正した。
- v0.4.0: スクリーンショットを取らないようにした。
- v0.3.0: 拡張日付フォーマット対応
  - 複数の日付入力フォーマットに対応（2024/1, R6.1, R6/1, 令和６年１月など）
  - 期間範囲指定機能（--period-from, --period-to → --date-from, --date-to）
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
