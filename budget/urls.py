from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView
from .views import get_chat_history 
from .views import reset_chat_history

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    path('signup/', views.signup, name='signup'),
    path('index/', views.index, name='index'),
    path('budget/combined_graph/<int:year>/<int:month>/', views.combined_graph, name='combined_graph'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),  # ログアウト後はログインページにリダイレクト
    
    #支出関係
    path('expense/form/', views.expense_form, name='add_expense'),
    path('expense/form/', views.expense_form, name='expense_form'),
    path('expense/form/<int:pk>/', views.expense_form, name='edit_expense'),
    path('expense/<int:pk>/delete/', views.delete_expense_view, name='delete_expense'),
    path('expense/list/', views.expense_list, name='expense_list'),
    path('expense/graph/<int:year>/<int:month>/', views.expense_graph, name='expense_graph'), #エラーが出たらbudget/graphに戻す
    #収入関係
    path('income/form/', views.income_form, name='add_income'),
    path('income/form/<int:pk>/', views.income_form, name='edit_income'),
    path('income/<int:pk>/delete/', views.delete_income_view, name='delete_income'),
    path('income/list/', views.income_list, name="income_list"),
    path('income/graph/<int:year>/<int:month>/', views.income_graph, name='income_graph'),
    #カテゴリ関係
    path('main_category/form/', views.main_category_form, name='add_main_category'),
    path('main_category/form/<int:pk>/', views.main_category_form, name='edit_main_category'),
    path('main_category/<int:pk>/delete/', views.delete_main_category, name='delete_main_category'),
    path('main_category_list/', views.main_category_list, name='main_category_list'),
    path('sub_category/form/', views.sub_category_form, name='add_sub_category'),
    path('sub_category/form/<int:pk>/', views.sub_category_form, name='edit_sub_category'),
    path('sub_category/<int:pk>/delete/', views.delete_sub_category, name='delete_sub_category'),
    path('sub_category_list/', views.sub_category_list, name='sub_category_list'),
    path('api/subcategories/', views.get_subcategories, name='get_subcategories'),
    path('source/form/', views.source_form, name='add_source'),
    path('source/form/<int:pk>/', views.source_form, name='edit_source'),
    path('source/<int:pk>/delete/', views.delete_source, name='delete_source'),
    path('source_list/', views.source_list, name='source_list'),
    #CSV関係
    path('export_expense_csv/', views.export_expense_csv, name='export_expense_csv'),
    path('export_income_csv/', views.export_income_csv, name='export_income_csv'),

    path('user_info/', views.user_info, name='user_info'),
    path('submit_user_info/', views.submit_user_info, name='submit_user_info'),
    path('user_storage/', views.user_storage, name='user_storage'),
    path('<int:year>/<int:month>/', views.index, name='index'), 
    path('chat_api/', views.chat_api, name='chat_api'),
    path('export_user_info/', views.export_user_info_csv, name='export_user_info_csv'),
    path('chatbot/', views.chatbot, name='chatbot'), 
    path('api/chat-history/', views.get_chat_history, name='chat_history'),
    path('api/reset-chat-history/', views.reset_chat_history, name='reset_chat_history'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/threads/create/', views.create_thread, name='create_thread'),
    path('chatbot/threads/<int:thread_id>/', views.chatbot_thread, name='chatbot_thread'),
    path('chatbot/threads/<int:thread_id>/delete/', views.delete_thread, name='delete_thread'),
    path('chatbot/threads/<int:thread_id>/rename/', views.rename_thread, name='rename_thread'),
    path('api/thread-list/', views.get_thread_list, name='get_thread_list'),
]
