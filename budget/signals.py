from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import MainCategory, Source

@receiver(post_migrate)
def create_initial_categories(sender, **kwargs):
    categories = ['食費', '日用品', '交通費', '娯楽', '美容・衣服', '医療・保険', '通信', '住まい']
    for category in categories:
        MainCategory.objects.get_or_create(name=category)
    
    # 給与・賞与などでもあり、要検討
    sources = ['仕事', 'パート', 'アルバイト']
    for source in sources:
        Source.objects.get_or_create(name=source)