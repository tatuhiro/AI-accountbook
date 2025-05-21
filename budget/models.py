from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth.models import User

# Create your models here.

class MainCategory(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    main_category = models.ForeignKey(MainCategory, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

class Source(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name

class Expense(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', '現金'),
        ('credit', 'クレジットカード'),
        ('cashless', 'キャッシュレス決済'),
    ]
    RATING_CHOICES = [
        (1, 'よかった'),
        (2, 'ふつう'),
        (3, '必要なかった'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # ユーザーと紐付ける
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    main_category = models.ForeignKey(MainCategory, on_delete=models.SET_NULL, null=True)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash')
    description = models.TextField(blank=True, null=True)
    rating = models.IntegerField(choices=RATING_CHOICES, default=2)

    def __str__(self):
        return f"{self.amount} - {self.main_category} - {self.date}"

class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # ユーザーと紐付ける
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)

class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # ユーザー名を他のモデルから持ってくる
    mbti = models.CharField(max_length=4)
    occupation = models.CharField(max_length=100)
    income = models.CharField(max_length=100)
    expenses = models.TextField()
    payment = models.CharField(max_length=50)
    savings = models.CharField(max_length=100)
    goal = models.CharField(max_length=255)
    personality = models.CharField(max_length=50)
    awareness = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.user.username} - {self.occupation}'

class Thread(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="threads")
    title = models.CharField(max_length=255, default="Untitled Thread")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}"

class ChatHistory(models.Model):
    thread = models.ForeignKey('Thread', on_delete=models.CASCADE, related_name="chathistories")
    # ユーザーのメッセージ
    user_message = models.TextField()  # ユーザーのメッセージ内容
    # AIのメッセージ
    ai_message = models.TextField(null=True, blank=True)  # AIからの応答内容
    created_at = models.DateTimeField(auto_now_add=True)

