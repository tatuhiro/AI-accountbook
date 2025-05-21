#!/bin/bash

pip install --upgrade pip

# 依存関係のインストール
pip install -r requirements.txt

# データベースのマイグレーション
python manage.py migrate

# 静的ファイルの収集
python manage.py collectstatic --noinput