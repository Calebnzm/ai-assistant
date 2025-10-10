from django.urls import path
from .views import ConversationAPIView, ActiveConversationAPIView,AgentToolAPIView

urlpatterns = [
    path("conversations/", ConversationAPIView.as_view(), name="conversations"),
    path("agent/execute-tool/", AgentToolAPIView.as_view(), name="agent-execute-tool"),
    path("conversations/active/", ActiveConversationAPIView.as_view(), name="conversation-active"),
    path("conversations/<int:conversation_id>/", ConversationAPIView.as_view(), name="conversation-detail"),
]
