from django import forms
from .models import MainCategory, SubCategory, Source, Expense, Income, ChatHistory, Thread
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import UserInfo

class MainCategoryForm(forms.ModelForm):
    class Meta:
        model = MainCategory
        fields = ['name']

class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['main_category', 'name']

class SourceForm(forms.ModelForm):
    class Meta:
        model = Source
        fields = ['name']

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'amount', 'main_category', 'sub_category', 'description', 'payment_method', 'rating']
        widgets = {
            'date' : forms.DateInput(attrs={'type': 'date'}),
        }

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['date', 'amount', 'source']
        widgets = {
            'date' : forms.DateInput(attrs={'type': 'date'}),
        }

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="ユーザー名", max_length=30,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザー名'}))
    password = forms.CharField(label="パスワード",
                               widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'パスワード'}))

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
    
    username = forms.CharField(label="ユーザー名", max_length=30,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザー名'}))
    password1 = forms.CharField(label="パスワード",
                               widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'パスワード'}))
    password2 = forms.CharField(label="パスワード（確認用）",
                               widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'もう一度パスワードを入力'}))


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = ['mbti', 'occupation', 'income', 'expenses', 'payment', 'savings', 'goal', 'personality', 'awareness']

class ChatHistoryForm(forms.ModelForm):
    class Meta:
        model = ChatHistory
        fields = ['user_message', 'ai_message']

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title']
