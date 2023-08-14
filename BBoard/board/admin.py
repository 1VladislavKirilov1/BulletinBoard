from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import gettext_lazy as _
from .models import Category, Post, User, Response, Subscription


class FlatPageAdmin(FlatPageAdmin):
    fieldsets = (
        (None, {'fields': ('url', 'title', 'content', 'sites')}),
        (_('Advanced options'), {
            'classes': ('collapse',),
            'fields': (
                'enable_comments',
                'registration_required',
                'template_name',
            ),
        }),
    )


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'text', 'user', 'upload',)
    list_filter = ('user',)
    search_fields = ('user', 'category',)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(User)
admin.site.register(Response)
admin.site.register(Subscription)