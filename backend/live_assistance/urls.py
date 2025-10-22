from django.urls import path
from . import views

urlpatterns = [
    path("pubsub/gmail/", views.pubsub_gmail_push, name="pubsub_gmail_push"),
]