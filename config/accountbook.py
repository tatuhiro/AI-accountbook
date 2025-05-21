from .settings import *  # 既存の設定をすべてインポート
import dj_database_url

DEBUG = False

# ALLOWED_HOSTS に render.com から提供されるドメインを追加
ALLOWED_HOSTS = [
    "*.onrender.com",  # ワイルドカードを使用して、すべてのサブドメインを許可
    # 必要に応じて、カスタムドメインを追加
]

# 静的ファイルの設定
STATIC_ROOT = BASE_DIR / "staticfiles"  # 本番環境の静的ファイルのパス
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # WhiteNoise を使用

# データベースの設定 (本番環境では PostgreSQL を推奨)
import dj_database_url
DATABASES = {
    "default": dj_database_url.config(conn_max_age=600, ssl_require=True),  # 環境変数からデータベース設定を読み込み
}