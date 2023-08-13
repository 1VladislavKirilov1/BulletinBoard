from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from allauth.account.views import ConfirmEmailView
from .views import ConfirmEmailInvalidView

urlpatterns = [
    path('post/create/', views.post_create, name='post_create'),
    path('post/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:post_id>/delete/', views.post_delete, name='post_delete'),
    path('post/list/', views.all_posts, name='post_list'),
    path('response/create/<int:post_id>/', views.response_create, name='response_create'),
    path('response/list/', views.response_list, name='response_list'),
    path('response/accept/<int:response_id>/', views.response_accept, name='response_accept'),
    path('accounts/confirm_email/<str:key>/', ConfirmEmailView.as_view(), name='account_confirm_email'),
    path('accounts/confirm_email_invalid/', ConfirmEmailInvalidView.as_view(), name='confirm_email_invalid'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)