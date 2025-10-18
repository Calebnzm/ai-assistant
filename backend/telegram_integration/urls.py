from django.urls import path
from . import views

urlpatterns = [
    path("webhook/", views.telegram_webhook, name="telegram_webhook"),
    path("link/start/", views.start_telegram_link, name="start_telegram_link"),
    path("link/status/", views.check_telegram_link_status, name="check_telegram_link_status"),
]