# account_book
 djangoを用いて、Web上にて家計簿としての基本的機能がある他、「AIパートナー」として家計簿のデータから無駄な出費といったサポートをしてくれるチャット形式の機能を追加する。 この「AIパートナー」では、GPT4o-miniのAPIキーを用いて出力するものとする。

## マイグレーション
`python manage.py makemigrations`</br>
`python manage.py migrate`</br>

## 環境構築
`python -m venv venv` 仮想環境を作成</br>
`.\venv\Scripts\activate` アクティベート</br>
`pip install django pandas matplotlib langchain langchain-community openai langchain_openai japanize_matplotlib`


python manage.py createsuperuser

http://127.0.0.1:8000/admin/

pip install -U langchain-openai

# 旧コード
chain = LLMChain(llm=chat, prompt=prompt)

# 推奨される新しい書き方
chain = prompt | chat

# 現在のインポート
from langchain import ChatOpenAI

# 変更後のインポート
from langchain_openai import ChatOpenAI
