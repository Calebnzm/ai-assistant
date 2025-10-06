from django.urls import path
from .views import ConversationAPIView, ActiveConversationAPIView

urlpatterns = [
    path("conversations/", ConversationAPIView.as_view(), name="conversations"),
    path("conversations/active/", ActiveConversationAPIView.as_view(), name="conversation-active"),
    path("conversations/<int:conversation_id>/", ConversationAPIView.as_view(), name="conversation-detail"),
]
