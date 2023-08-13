from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Post, Category


@receiver(post_migrate)
def add_initial_categories(sender, **kwargs):
    if sender.name == 'board':
        for category_code, category_name in Post.TYPE:
            Category.objects.get_or_create(name=category_name)