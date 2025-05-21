from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from .models import MainCategory, SubCategory, Source, Expense, Income, ChatHistory, Thread
from .forms import MainCategoryForm, SubCategoryForm, SourceForm, ExpenseForm, IncomeForm, ThreadForm
from io import BytesIO
# MatplotlibのバックエンドをAggに設定する
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
from datetime import datetime, timedelta
from django.contrib.auth.views import LoginView
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm
import csv
from django.http import HttpResponse
from .models import UserInfo
from .forms import UserInfoForm
from django.contrib.auth import logout
import japanize_matplotlib
import traceback


# Create your views here.
def get_month_range(year=None, month=None):
    # 指定された年と月がなければ現在の年月を使う
    if year is None or month is None:
        today = datetime.today()
        year = today.year
        month = today.month
    
    # 指定された月の最初の日
    first_day = datetime(year, month, 1)
    # 来月の1日を取得し、そこから1日引いて今月の最終日を取得
    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    return first_day, last_day

@login_required(login_url='/')
def index(request, year=None, month=None):
    if year and month:
        year = int(year)
        month = int(month)
    else:
        today = datetime.today()
        year = today.year
        month = today.month

    first_day, last_day = get_month_range(year, month)
    
    total_expense = Expense.objects.filter(user=request.user, date__range=[first_day, last_day]).aggregate(Sum('amount'))['amount__sum'] or 0
    total_income = Income.objects.filter(user=request.user, date__range=[first_day, last_day]).aggregate(Sum('amount'))['amount__sum'] or 0

    previous_month_date = first_day - timedelta(days=1)
    next_month_date = last_day + timedelta(days=1)
    previous_month = (previous_month_date.year, previous_month_date.month)
    next_month = (next_month_date.year, next_month_date.month)

    # カラー定義を再設定
    colors = {
        '食費': '#FF9F80',       # ソフトオレンジ
        '日用品': '#80FF9F',     # ソフトグリーン
        '交通費': '#80AFFF',     # ソフトブルー
        '娯楽': '#FFD480',       # ソフトイエロー
        '美容・衣服': '#FF809F', # ソフトレッド
        '医療・保険': '#B580A5', # ソフトパープル
        '通信': '#9973A7',       # ソフトダークパープル
        '住まい': '#CFFFCF',     # ソフトライトグリーン
        '旅行': '#A0FFFF',       # ソフトシアン
    }

    expenses_by_category = Expense.objects.filter(
        user=request.user, 
        date__range=[first_day, last_day]
    ).values('main_category__name', 'main_category').annotate(total=Sum('amount'))
    
    expenses_by_category_dict = {
        item['main_category']: item['total'] for item in expenses_by_category
    }

    categories_data = [

        {
            'name': category.name,
            'total': expenses_by_category_dict.get(category.id, 0),
            'percentage': max((expenses_by_category_dict.get(category.id, 0) / total_expense) * 100, 0) if total_expense > 0 else 0,
            'color': colors.get(category.name, '#CCCCCC')
        }
        for category in MainCategory.objects.all()
    ]

    context = {
        'total_expense': total_expense,
        'total_income': total_income,
        'current_month': first_day.strftime("%Y年%m月"),
        'previous_month': previous_month,
        'next_month': next_month,
        'year': year,
        'month': month,
        'categories_data': categories_data,
    }

    return render(request, 'budget/index.html', context)


def redirect_index(request):
    return redirect(index)

def expense_form(request, pk=None):
    if pk:
        expense = get_object_or_404(Expense, pk=pk, user=request.user)
        # 編集モード
        title = "支出を編集"
        submit_button_label = "更新"
    else:
        # 追加モード
        expense = None
        title = "支出を追加"
        submit_button_label = "追加"

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            new_expense = form.save(commit=False)
            new_expense.user = request.user  # ログインしているユーザーを設定
            new_expense.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)

    # 追加と編集に共通してメインカテゴリのリストを渡す
    main_categories = MainCategory.objects.all()
    
    return render(request, 'budget/expense_form.html', {
        'form': form,
        'title': title,
        'submit_button_label': submit_button_label,
        'mode': 'edit' if pk else 'add',
        'main_categories': main_categories,  # メインカテゴリ情報をテンプレートに渡す
    })

def delete_expense_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == "POST":
        expense.delete()
        return redirect('expense_list')
    return render(request, 'budget/confirm_delete.html', {'expense': expense})

def expense_list(request):
    # URLパラメータから月を取得、無ければ現在の月を使用
    month = request.GET.get('month')
    if month:
        current_date = datetime.strptime(month, '%Y-%m')
    else:
        current_date = datetime.now()

    # 月の最初の日と最後の日を計算
    first_day = current_date.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # ログインユーザーの指定された月の支出データのみを取得
    expenses = Expense.objects.filter(user=request.user, date__range=[first_day, last_day]).order_by('date')

    # 前月と次月のためのパラメータを計算
    previous_month = (first_day - timedelta(days=1)).strftime('%Y-%m')
    next_month = (last_day + timedelta(days=1)).strftime('%Y-%m')

    context = {
        'expenses': expenses,
        'current_month': current_date.strftime('%Y年%m月'),
        'current_year': current_date.year,  # 追加
        'current_month_number': current_date.month,  # 追加
        'previous_month': previous_month,
        'next_month': next_month,
    }
    return render(request, 'budget/expense_list.html', context)

def income_form(request, pk=None, action=None):
    if pk:
        income = get_object_or_404(Income, pk=pk, user=request.user)
        # 編集モード
        title = "収入を編集"
        submit_button_label = "更新"
    else:
        # 追加モード
        income = None
        title = "収入を追加"
        submit_button_label = "追加"

    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            new_income = form.save(commit=False)
            new_income.user = request.user  # ログインしているユーザーを設定
            new_income.save()
            return redirect('income_list')
    else:
        form = IncomeForm(instance=income)

    return render(request, 'budget/income_form.html', {
        'form': form,
        'title': title,
        'submit_button_label': submit_button_label,
        'mode': 'edit' if pk else 'add'
    })

def delete_income_view(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == "POST":
        income.delete()
        return redirect('income_list')
    return render(request, 'budget/confirm_delete.html', {'income': income})

def income_list(request):
    # URLパラメータから月を取得、無ければ現在の月を使用
    month = request.GET.get('month')
    if month:
        current_date = datetime.strptime(month, '%Y-%m')
    else:
        current_date = datetime.now()

    current_year = current_date.year##
    current_month_number = current_date.month##

    # 月の最初の日と最後の日を計算
    first_day = current_date.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # ログインユーザーの指定された月の収入データのみを取得
    incomes = Income.objects.filter(user=request.user, date__range=[first_day, last_day]).order_by('date')

    # 前月と次月のためのパラメータを計算
    previous_month = (first_day - timedelta(days=1)).strftime('%Y-%m')
    next_month = (last_day + timedelta(days=1)).strftime('%Y-%m')

    context = {
        'incomes': incomes,
        'current_month': current_date.strftime('%Y年%m月'),
        'previous_month': previous_month,
        'next_month': next_month,
        'current_year': current_date.year,            # 年を追加
        'current_month_number': current_date.month,   # 月を追加
    }
    return render(request, 'budget/income_list.html', context)

def main_category_form(request, pk=None, action=None):
    if pk:
        try:
            main_category = MainCategory.objects.get(pk=pk)
        except MainCategory.DoesNotExist:
            main_category = None
    else:
        main_category = None

    # 削除処理の修正
    if action == 'delete' and main_category:
        if request.method == 'POST':
            main_category.delete()
            return redirect('main_category_list')  # 削除後はリストページにリダイレクト

        return redirect('main_category_list')  # GETリクエスト時もリストページへ

    # 編集 or 追加処理
    elif main_category:
        title = "メインカテゴリを編集"
        submit_button_label = "更新"
    else:
        title = "メインカテゴリを追加"
        submit_button_label = "追加"

    if request.method == 'POST':
        form = MainCategoryForm(request.POST, instance=main_category)
        if form.is_valid():
            form.save()
            return redirect('main_category_list')
    else:
        form = MainCategoryForm(instance=main_category)

    return render(request, 'budget/main_category_form.html', {
        'form': form,
        'title': title,
        'submit_button_label': submit_button_label,
        'mode': 'edit' if pk else 'add',
        'main_category': main_category  # main_category を明示的に渡す
    })

def delete_main_category(request, pk):
    main_category = get_object_or_404(MainCategory, pk=pk)

    if request.method == "POST":
        main_category.delete()
        return redirect('main_category_list')  # 削除後はリストページへリダイレクト

    return redirect('main_category_list')  # GETリクエスト時もリストページへ



def main_category_list(request):
    categories = MainCategory.objects.all()
    return render(request, 'budget/main_category_list.html', {'categories': categories})



def sub_category_form(request, pk=None, action=None):
    if pk:
        sub_category = get_object_or_404(SubCategory, pk=pk)
        if action == 'delete':
            title = "サブカテゴリを削除"
            submit_button_label = "削除"
            if request.method == 'POST':
                sub_category.delete()
                return redirect('sub_category_list')
            return render(request, 'budget/sub_category_form.html', {
                'form': SubCategoryForm(instance=sub_category),
                'title': title,
                'submit_button_label': submit_button_label,
                'mode': 'delete'
            })

        # 編集モード
        title = "サブカテゴリを編集"
        submit_button_label = "更新"
    else:
        # 追加モード
        sub_category = None
        title = "サブカテゴリを追加"
        submit_button_label = "追加"

    if request.method == 'POST':
        form = SubCategoryForm(request.POST, instance=sub_category)
        if form.is_valid():
            form.save()
            return redirect('sub_category_list')
    else:
        form = SubCategoryForm(instance=sub_category)

    return render(request, 'budget/sub_category_form.html', {
        'form': form,
        'title': title,
        'submit_button_label': submit_button_label,
        'mode': 'edit' if pk else 'add'
    })

def delete_sub_category(request, pk):
    sub_category = get_object_or_404(SubCategory, pk=pk)

    if request.method == "POST":
        sub_category.delete()
        return redirect('sub_category_list')  # 削除後はリストページへリダイレクト

    return redirect('sub_category_list')  # GETリクエスト時もリストページへ


def sub_category_list(request):
    categories = SubCategory.objects.all()
    return render(request, 'budget/sub_category_list.html', {'categories': categories})

def get_subcategories(request):
    main_category_id = request.GET.get('main_category')
    subcategories = SubCategory.objects.filter(main_category_id=main_category_id)
    data = {'subcategories': [{'id': sub.id, 'name': sub.name} for sub in subcategories]}
    return JsonResponse(data)

def source_form(request, pk=None, action=None):
    if pk:
        source = get_object_or_404(Source, pk=pk)
        if action == 'delete':
            title = "収入カテゴリを削除"
            submit_button_label = "削除"
            if request.method == 'POST':
                source.delete()
                return redirect('source_list')
            return render(request, 'budget/source_form.html', {
                'form': SourceForm(instance=source),
                'title': title,
                'submit_button_label': submit_button_label,
                'mode': 'delete'
            })

        # 編集モード
        title = "収入カテゴリを編集"
        submit_button_label = "更新"
    else:
        # 追加モード
        source = None
        title = "収入カテゴリを追加"
        submit_button_label = "追加"

    if request.method == 'POST':
        form = SourceForm(request.POST, instance=source)
        if form.is_valid():
            form.save()
            return redirect('source_list')
    else:
        form = SourceForm(instance=source)

    return render(request, 'budget/source_form.html', {
        'form': form,
        'title': title,
        'submit_button_label': submit_button_label,
        'mode': 'edit' if pk else 'add'
    })

def source_list(request):
    sources = Source.objects.all()
    return render(request, 'budget/source_list.html', {'sources': sources})

def delete_source(request, pk):
    source = get_object_or_404(Source, pk=pk)
    if request.method == "POST":
        source.delete()
        return redirect('source_list')  # 削除後に `source_list` にリダイレクト
    return render(request, 'budget/confirm_delete.html', {'source': source})


import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.db.models import Sum

def expense_graph(request, year, month):
    # 指定された年月の初日と末日を取得
    start_date = datetime(year, month, 1)
    next_month = start_date.replace(day=28) + timedelta(days=4)  # 翌月1日を取得
    end_date = next_month - timedelta(days=next_month.day)  # 当月末日を取得

    # ログインユーザーの支出データを取得
    expenses = Expense.objects.filter(user=request.user, date__range=[start_date, end_date])

    # デバッグ: 支出データを確認
    print(f"Expenses for the period: {expenses}")

    # 日付ごとの支出合計を計算
    daily_totals = {}
    for expense in expenses:
        date = expense.date
        amount = float(expense.amount)
        print(f"Adding to daily_totals: Date: {date}, Amount: {amount}")  # 各支出の日付と金額を確認
        if date in daily_totals:
            daily_totals[date] += amount  # 同じ日付に既に値がある場合は加算
        else:
            daily_totals[date] = amount   # 新しい日付の場合は初期化


    # 日付と合計金額のリストを作成
    all_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    # 日付を `datetime.date` 型に変換して、`daily_totals` から金額を取得
    amounts = [daily_totals.get(date.date(), 0) for date in all_dates]

    

    # 支出グラフ作成（棒グラフ）
    plt.figure(figsize=(10, 5))
    plt.bar(all_dates, amounts, width=0.8, color='#F89EA0')  # 幅を調整して棒グラフに変更

    plt.title('支出')
    plt.xlabel('日付')
    plt.ylabel('金額', rotation=0)

    # Y軸の範囲を設定
    max_amount = max(amounts) if amounts else 0
    if max_amount == 0:
        plt.ylim(0, 1000)  # もし金額が0の場合、1000円までの範囲で設定
    else:
        plt.ylim(0, max_amount + max_amount * 0.1)  # 最大値に余裕を持たせる

    # 日付表示を調整（ラベルを45度回転）
    plt.xticks(rotation=0)
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))  # 2日ごとにラベルを表示
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d'))

    # グラフ全体のレイアウトを自動調整
    

    # 横線（Y軸のグリッド）のみ表示
    plt.grid(axis='y', linestyle='--', alpha=0.7)  # 横線は破線で薄く

    # グラフの背景色を薄い灰色に設定
    plt.gca().set_facecolor('#f0f0f0')  # 色コードで薄い灰色を指定
    
    # 画像をバイナリデータとして保存
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    return HttpResponse(buffer, content_type='image/png')


def income_graph(request, year, month):
    # 指定された年月の初日と末日を取得
    start_date = datetime(year, month, 1)
    next_month = start_date.replace(day=28) + timedelta(days=4)  # 翌月1日を取得
    end_date = next_month - timedelta(days=next_month.day)  # 当月末日を取得

    # ログインユーザーの支出データを取得
    incomes = Income.objects.filter(user=request.user, date__range=[start_date, end_date])

    # デバッグ: 収入データを確認
    print(f"Incomes for the period: {incomes}")

    # 日付ごとの支出合計を計算
    daily_totals = {}
    for income in incomes:
        date = income.date
        amount = float(income.amount)
        print(f"Adding to daily_totals: Date: {date}, Amount: {amount}")  # 各支出の日付と金額を確認
        if date in daily_totals:
            daily_totals[date] += amount  # 同じ日付に既に値がある場合は加算
        else:
            daily_totals[date] = amount   # 新しい日付の場合は初期化


    # 日付と合計金額のリストを作成
    all_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    # 日付を `datetime.date` 型に変換して、`daily_totals` から金額を取得
    amounts = [daily_totals.get(date.date(), 0) for date in all_dates]

    

    # 収入グラフ作成（棒グラフ）
    plt.figure(figsize=(10, 5))
    plt.bar(all_dates, amounts, width=0.8, color='#A0E8F2')  # 幅を調整して棒グラフに変更

    plt.title('収入')
    plt.xlabel('日付')
    plt.ylabel('金額', rotation=0)

    # Y軸の範囲を設定
    max_amount = max(amounts) if amounts else 0
    if max_amount == 0:
        plt.ylim(0, 1000)  # もし金額が0の場合、1000円までの範囲で設定
    else:
        plt.ylim(0, max_amount + max_amount * 0.1)  # 最大値に余裕を持たせる

    # 日付表示を調整（ラベルを45度回転）
    plt.xticks(rotation=0)
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))  # 2日ごとにラベルを表示
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d'))

    # グラフ全体のレイアウトを自動調整
    

    # 横線（Y軸のグリッド）のみ表示
    plt.grid(axis='y', linestyle='--', alpha=0.7)  # 横線は破線で薄く   

    # グラフの背景色を薄い灰色に設定
    plt.gca().set_facecolor('#f0f0f0')  # 色コードで薄い灰色を指定
    # 画像をバイナリデータとして保存
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    return HttpResponse(buffer, content_type='image/png')

# ・expence_graphとincome_graphを使って、一つのグラフをつくる

def combined_graph(request, year, month):
    # 指定された年月の初日と末日を取得
    start_date = datetime(year, month, 1)
    next_month = start_date.replace(day=28) + timedelta(days=4)  # 翌月1日を取得
    end_date = next_month - timedelta(days=next_month.day)  # 当月末日を取得

    # ログインユーザーの支出と収入データを取得
    expenses = Expense.objects.filter(user=request.user, date__range=[start_date, end_date])
    incomes = Income.objects.filter(user=request.user, date__range=[start_date, end_date])

    # 日付ごとの支出と収入の合計を計算
    expense_totals = {}
    income_totals = {}
    
    for expense in expenses:
        date = expense.date
        amount = float(expense.amount)
        expense_totals[date] = expense_totals.get(date, 0) + amount

    for income in incomes:
        date = income.date
        amount = float(income.amount)
        income_totals[date] = income_totals.get(date, 0) + amount

    # グラフ用の日付と金額リストを作成
    all_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    expense_amounts = [-expense_totals.get(date.date(), 0) for date in all_dates]  # 支出はマイナス
    income_amounts = [income_totals.get(date.date(), 0) for date in all_dates]     # 収入はプラス

    # グラフ作成（棒グラフ）
    plt.figure(figsize=(10, 5))
    plt.bar(all_dates, expense_amounts, width=0.8, color='#F89EA0', label="支出")   # 支出は赤
    plt.bar(all_dates, income_amounts, width=0.8, color='#A0E8F2', label="収入")    # 収入は青

    plt.title('支出と収入')
    plt.xlabel('日付')
    plt.ylabel('金額', rotation=0)

    # Y軸の範囲を設定
    max_amount = max(max(income_amounts), -min(expense_amounts)) if expense_amounts or income_amounts else 1000
    plt.ylim(-max_amount - max_amount * 0.1, max_amount + max_amount * 0.1)

    # 日付表示を調整
    # X軸ラベルのサイズを調整
    plt.xticks(rotation=0, fontsize=8)  # 8はフォントサイズ（例）

    # その他のコード
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d'))
    # グラフ全体のレイアウトを自動調整
    
    plt.legend()
    # 横線（Y軸のグリッド）のみ表示
    plt.grid(axis='y', linestyle='--', alpha=0.7)  # 横線は破線で薄く
    
    # グラフ全体の余白を左寄せに調整
    plt.subplots_adjust(left=0.1, right=0.9)

    # グラフの背景色を薄い灰色に設定
    plt.gca().set_facecolor('#f0f0f0')  # 色コードで薄い灰色を指定

    # 画像をバイナリデータとして保存
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    return HttpResponse(buffer, content_type='image/png')


class CustomLoginView(LoginView):
    template_name = 'budget/login.html'  # ログイン用テンプレート
    redirect_authenticated_user = True  # ログイン済みの場合リダイレクト
    next_page = 'index'  # ログイン成功後に移動するURL名


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 登録後すぐにログイン
            return redirect('index')  # サインアップ後にindexページにリダイレクト
    else:
        form = SignUpForm()
    return render(request, 'budget/signup.html', {'form': form})


# 支出データのCSV作成
def export_expense_csv(request):
    user = request.user  # 現在ログインしているユーザーを取得
    response = HttpResponse(content_type='text/csv; charset=UTF-8')
    response['Content-Disposition'] = f'attachment; filename="{user.username}_expense.csv"'
    response.write('\ufeff'.encode('utf8'))  # BOM（Byte Order Mark）を追加してExcelでの文字化けを防ぐ
    writer = csv.writer(response)
    writer.writerow(['date', 'amount', 'main_category', 'sub_category', 'payment_method', 'description', 'rating'
])  # ヘッダー行

    # 支出データを取得してCSVに書き込む
    expenses = Expense.objects.filter(user=user)
    for expense in expenses:
        writer.writerow([expense.date, expense.amount, expense.main_category, expense.sub_category, expense.payment_method,expense.description, expense.rating])

    return response

# 収入データのCSV作成
def export_income_csv(request):
    user = request.user  # 現在ログインしているユーザーを取得
    response = HttpResponse(content_type='text/csv; charset=UTF-8')
    response['Content-Disposition'] = f'attachment; filename="{user.username}_income.csv"'
    response.write('\ufeff'.encode('utf8'))  # BOM（Byte Order Mark）を追加してExcelでの文字化けを防ぐ
    writer = csv.writer(response)
    writer.writerow(['Date', 'Amount','Source'])  # ヘッダー行

    # 収入データを取得してCSVに書き込む
    incomes = Income.objects.filter(user=user)
    for income in incomes:
        writer.writerow([income.date, income.amount,income.source])

    return response

def user_info(request):
    # 既存のユーザー情報を取得
    try:
        user_info = UserInfo.objects.get(user=request.user)
        form = UserInfoForm(instance=user_info)
    except UserInfo.DoesNotExist:
        form = UserInfoForm()

    return render(request, 'budget/user_info.html', {'form': form})

def submit_user_info(request):
    if request.method == 'POST':
        form = UserInfoForm(request.POST)
        if form.is_valid():
            # 既にそのユーザーの情報が存在するか確認
            try:
                user_info = UserInfo.objects.get(user=request.user)
                # 既存の情報を更新する
                form = UserInfoForm(request.POST, instance=user_info)
                form.save()
            except UserInfo.DoesNotExist:
                # 存在しない場合は新しい情報を作成する
                user_info = form.save(commit=False)
                user_info.user = request.user
                user_info.save()
            
            return redirect('user_storage')
    else:
        form = UserInfoForm()

    return render(request, 'budget/user_info.html', {'form': form})

def user_storage(request):
    try:
        # UserInfoを取得
        user_info = UserInfo.objects.get(user=request.user)
    except UserInfo.DoesNotExist:
        # 存在しない場合は新規登録ページにリダイレクト
        return redirect('user_info')  # 'user_info'は新規登録ページのURL名
    
    return render(request, 'budget/user_storage.html', {'user_info': user_info})

def user_info_form(request):
    # 既存のユーザー情報を取得
    user_info, created = UserInfo.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserInfoForm(request.POST, instance=user_info)
        if form.is_valid():
            form.save()
            return redirect('user_storage')  # 確認ページにリダイレクト
    else:
        form = UserInfoForm(instance=user_info)  # 既存の情報をフォームに表示

    return render(request, 'budget/user_info.html', {'form': form})

def logout_view(request):
    logout(request)
    request.session.flush()  # セッションをクリア
    return redirect('login')  # ログインページにリダイレクト

 # UserInfoモデルをインポート

def export_user_info_csv(request):
    user = request.user  # 現在ログインしているユーザーを取得
    response = HttpResponse(content_type='text/csv; charset=UTF-8')
    response['Content-Disposition'] = f'attachment; filename="{user.username}_user_info.csv"'
    response.write('\ufeff'.encode('utf8'))  # BOM（Byte Order Mark）を追加してExcelでの文字化けを防ぐ

    writer = csv.writer(response)
    
    # ヘッダー行
    writer.writerow(['MBTIタイプ', '職業', '年収', '月ごとの支出項目', '支払い方法', '貯金額', '目標貯金額と目的', '性格タイプ', '節約意識'])

    try:
        # ログイン中のユーザーの情報を取得
        user_info = UserInfo.objects.get(user=user)
        # データをCSVに書き込む
        writer.writerow([
            user_info.mbti,
            user_info.occupation,
            user_info.income,
            user_info.expenses,
            user_info.payment,
            user_info.savings,
            user_info.goal,
            user_info.personality,
            user_info.awareness
        ])
    except UserInfo.DoesNotExist:
        # 情報が存在しない場合は、エラーメッセージを追加する
        writer.writerow(['情報が存在しません'])

    return response

# チャットボット実装
import os
import csv
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
from io import StringIO

from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain
from .models import Expense, Income, UserInfo, ChatHistory  # Expense, Income, UserInfoモデルをインポート

# Chat Model の定義
url = "https://api.openai.iniad.org/api/v1/"
chat = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, openai_api_base=url)

# データベースから支出データをCSV形式でエクスポート
def export_expense_csv(user):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['date', 'amount', 'main_category', 'sub_category', 'payment_method', 'description', 'rating'])
    
    expenses = Expense.objects.filter(user=user)
    if expenses.exists():
        for expense in expenses:
            writer.writerow([expense.date, expense.amount, expense.main_category, expense.sub_category, expense.payment_method, expense.description, expense.rating])
    else:
        writer.writerow(['支出データがありません'])

    output.seek(0)
    return output

# データベースから収入データをCSV形式でエクスポート
def export_income_csv(user):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Amount', 'Source'])
    
    incomes = Income.objects.filter(user=user)
    if incomes.exists():
        for income in incomes:
            writer.writerow([income.date, income.amount, income.source])
    else:
        writer.writerow(['収入データがありません'])

    output.seek(0)
    return output

# データベースからユーザー情報をCSV形式でエクスポート
def export_user_info_csv(user):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['MBTIタイプ', '職業', '年収', '月ごとの支出項目', '支払い方法', '貯金額', '目標貯金額と目的', '性格タイプ', '節約意識'])

    try:
        user_info = UserInfo.objects.get(user=user)
        writer.writerow([
            user_info.mbti,
            user_info.occupation,
            user_info.income,
            user_info.expenses,
            user_info.payment,
            user_info.savings,
            user_info.goal,
            user_info.personality,
            user_info.awareness
        ])
    except UserInfo.DoesNotExist:
        writer.writerow(['ユーザー情報がまだ登録されていません'])

    output.seek(0)
    return output

# データベースから会話ログをCSV形式でエクスポート
def export_chat_history_csv(user):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['user_message', 'ai_message'])
    
    # ChatHistoryをスレッドのユーザーでフィルタリング
    chat_histories = ChatHistory.objects.filter(thread__user=user)
    if chat_histories.exists():
        for chat_history in chat_histories:
            writer.writerow([chat_history.user_message, chat_history.ai_message])
    # 後々
    else:
        writer.writerow(['会話ログがありません'])

    output.seek(0)
    return output

# プロンプトのテンプレート文章
template = """
求められていること以上に話してはいけない
あなたは家計のサポートを行うアシスタントです。
以下の支出情報、収入情報、ユーザー情報を元に返信して
文章は基本的に1行か2行
詳細情報も参照にした返答を生成する
貯金額は全体の収入から全体の支出を引いた金額とする
支出情報: {expense_data}
収入情報: {income_data}
ユーザー情報: {user_info_data}
会話ログ: {chat_history}
会話ログのuser_messageはユーザーからのメッセージで、ai_messageはAIからの回答です。この会話ログを基に回答してください。
ユーザーのメッセージ: {user_message}
リストにするときは行を区切って
 - ** **この表示を使わないで。代わりに・で区切って
アドバイス:
"""

prompt = PromptTemplate(
    input_variables=["expense_data", "income_data", "user_info_data", "chat_history", "user_message"],
    template=template,
)

chain = LLMChain(llm=chat, prompt=prompt)


@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        thread_id = data.get('thread_id')

        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        try:
            thread_id = int(thread_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid thread ID'}, status=400)

        # スレッド取得
        thread = get_object_or_404(Thread, id=thread_id, user=request.user)

        # 各データをCSV形式で生成
        expense_csv = export_expense_csv(request.user)
        income_csv = export_income_csv(request.user)
        chat_history_csv = export_chat_history_csv(request.user)
        user_info_csv = export_user_info_csv(request.user)

        # 各データを文字列に変換
        expense_data_str = expense_csv.getvalue().strip() or "支出データがありません"
        income_data_str = income_csv.getvalue().strip() or "収入データがありません"
        chat_history_str = chat_history_csv.getvalue().strip()
        user_info_data_str = user_info_csv.getvalue().strip() or "ユーザー情報がありません"

        # AI応答を生成
        response = chain.run(
            expense_data=expense_data_str,
            income_data=income_data_str,
            chat_history=chat_history_str,
            user_info_data=user_info_data_str,
            user_message=user_message
        )

        # チャット履歴を保存
        ChatHistory.objects.create(
            thread=thread,
            user_message=user_message,
            ai_message=response,
        )

        return JsonResponse({'message': response})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # エラー詳細を出力
        if settings.DEBUG:
            return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)



from django.http import JsonResponse
from .models import ChatHistory

def get_chat_history(request):
    thread_id = request.GET.get('thread_id')
    if not thread_id:
        return JsonResponse({'error': 'Thread ID is required.'}, status=400)
    
    try:
        thread = Thread.objects.get(id=thread_id, user=request.user)  # ユーザーが所有するスレッドか確認
    except Thread.DoesNotExist:
        return JsonResponse({'error': 'Thread not found or not accessible.'}, status=404)
    
    chat_history = ChatHistory.objects.filter(thread=thread).order_by('id')
    data = [
        {'user_message': chat.user_message, 'ai_message': chat.ai_message}
        for chat in chat_history
    ]
    return JsonResponse({'chat_history': data})


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def reset_chat_history(request):
    if request.method == 'POST':
        try:
            # リクエストからスレッドIDを取得
            data = json.loads(request.body)
            thread_id = data.get('thread_id')

            if not thread_id:
                return JsonResponse({'status': 'error', 'message': 'Thread ID is required.'}, status=400)

            # スレッドが現在のユーザーに属しているか確認して取得
            thread = Thread.objects.get(id=thread_id, user=request.user)

            # スレッドに関連付けられたチャット履歴を削除
            ChatHistory.objects.filter(thread=thread).delete()

            return JsonResponse({'status': 'success', 'message': 'Chat history cleared for the selected thread.'})
        except Thread.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Thread not found or not accessible.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


@login_required
def chatbot(request):
    threads = Thread.objects.filter(user=request.user).order_by('-updated_at')
    selected_thread = None

    thread_id = request.GET.get('thread_id')
    if thread_id:
        selected_thread = get_object_or_404(Thread, id=thread_id, user=request.user)

    return render(request, 'budget/chatbot.html', {
        'threads': threads,
        'selected_thread': selected_thread,
    })

@login_required
def create_thread(request):
    if request.method == 'POST':  # POSTメソッドのみ処理
        thread = Thread.objects.create(user=request.user)
        thread.title = f"会話{thread.id}"  # 動的なタイトルを設定
        thread.save() # 更新を保存
        return JsonResponse({'thread_id': thread.id})
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def chatbot_thread(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id, user=request.user)
    threads = Thread.objects.filter(user=request.user).order_by('-updated_at')  # サイドバー用スレッド一覧
    return render(request, 'budget/chatbot.html', {
        'selected_thread': thread,
        'threads': threads,  # スレッド一覧
    })


@login_required
def get_thread_list(request):
    threads = Thread.objects.filter(user=request.user).order_by('-created_at')
    thread_data = [{'id': thread.id, 'title': thread.title} for thread in threads]
    return JsonResponse({'threads': thread_data})

@login_required
def delete_thread(request, thread_id):
    if request.method == 'POST':
        thread = get_object_or_404(Thread, id=thread_id, user=request.user)
        thread.delete()
        # スレッド削除後にリダイレクトするURLを返す
        return JsonResponse({'status': 'success', 'redirect_url': '/chatbot/'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def rename_thread(request, thread_id):
    if request.method == 'POST':
        try:
            thread = Thread.objects.get(id=thread_id, user=request.user)
            data = json.loads(request.body)
            new_title = data.get('title')
            if new_title:
                thread.title = new_title
                thread.save()
                return JsonResponse({'status': 'success', 'message': 'タイトルが変更されました。'})
            return JsonResponse({'status': 'error', 'message': 'タイトルが無効です。'})
        except Thread.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'スレッドが見つかりません。'})
    return JsonResponse({'status': 'error', 'message': '無効なリクエストです。'})

