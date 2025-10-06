from rest_framework import serializers
from .models import Conversation, ChatMessage

class ChatMessageSeriaizer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]

class ConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSeriaizer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "messages"]