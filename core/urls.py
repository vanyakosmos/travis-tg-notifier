from django.conf import settings
from django.urls import path

from core import views

app_name = 'core'
urlpatterns = [
    path('', views.index_view, name='index'),
    path('login_success', views.login_success_view, name='login_success'),
    path('logout', views.logout_view, name='logout'),
    path('u/<str:chat_id>', views.hook_view, name='hook'),
    path('u/<str:chat_id>/force', views.deprecated_forced_hook_view, name='forced'),
    path(f'webhook/{settings.TELEGRAM_BOT_TOKEN}', views.bot_webhook_view, name='webhook'),
]
