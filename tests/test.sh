#!/bin/sh -x

PYTHON=python3
SCRIPT=../fukuoka_water_downloader.py
OPTIONS="--from 2025/07 --to 2025/07"



# オプション無し（すべてデフォルト）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS}
sleep 10

# メールアドレスをオプションで指定
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --email yourmailaddress@yourdomain
sleep 10

# パスワードをオプションで指定
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --password XXX
sleep 10



export FUKUOKA_WATER_EMAIL=yourmailaddress@yourdomain
export FUKUOKA_WATER_PASSWORD=XXX


# 開始月をオプションで指定
## 和暦
### 年月
#### 全角（令和７年７月など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --date-from 令和７年５月
sleep 10

#### 半角（令和7年7月など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --date-from 令和7年03月
sleep 10

#### 混在（令和７年7月など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --from 令和７年1月
sleep 10

### ピリオド（R7.7など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS}
sleep 10

echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --from R6.11
sleep 10

### ハイフン（R7-7など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS}
sleep 10

echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --from R6-9
sleep 10



## 西暦
### ハイフン（2025-7など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS}
sleep 10

### スラッシュ（2025/7など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS}
sleep 10

### ピリオド（2025.7など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS}
sleep 10

### 年月
#### 全角（２０２５年７月など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS}
sleep 10

#### 半角（2025年7月など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS}
sleep 10

#### 混在（２０２５年7月など）
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS}
sleep 10


# 終了月をオプションで指定
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS}
sleep 10


# 出力形式をオプションで指定
## csv
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --format csv
sleep 10

## PDF
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} -f pdf
sleep 10

# 出力ファイル名をオプションで指定
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --output test-output.csv
sleep 10

echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --format pdf -o test-output.pdf
sleep 10

# 詳細な出力を表示するオプションを指定
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --verbose
sleep 10

# デバッグ情報を表示するオプションを指定
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --debug
sleep 10

# デバッグ情報をファイルに保存するオプションを指定
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --debug-log debug-log.txt
sleep 10

# --quietオプションを指定
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --quiet
sleep 10

# --filename-onlyオプションを指定
echo "===========================\n\n\n"
${PYTHON} ${SCRIPT} ${OPTIONS} --filename-only

