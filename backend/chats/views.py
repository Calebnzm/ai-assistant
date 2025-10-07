
import google.generativeai as genai
from google.generativeai import types
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Conversation, ChatMessage
from .serializers import ConversationSerializer
from django.utils import timezone
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

class ConversationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, conversation_id=None):
        user = request.user
        message = request.data.get("message")
        timeout_seconds = 300
            
        conversation = (
            user.conversations.filter(active=True).order_by("-created_at").first()
        )

        if conversation and conversation.is_expired():
            conversation.active = False
            conversation.save()
            conversation = None

        if not conversation:
            conversation = Conversation.objects.create(
                user=user,
                expires_at = timezone.now() + timedelta(seconds=timeout_seconds)
            )

        system_prompt = f"""
            You are an AI Personal Assistant for {user.first_name}.

            These are your tasks:
                1. Provide the user with any assistance they might require
                2. Schedule activities for the user. They will have to give you all the neccessary info to do that.
                3. Monitor the user's email, calender, and inform them of any impending tasks and activities, as well as schedule them, as they come.
                4. Manage email correspondece for the user.

            When interacting with the client.
                1. Do not provide any code, or confidential information.
                2. Use emoji's as much as you deem neccessary.
                3. Do not lead the conversation except when notifying the user of new activities schedules.    
        """

        ChatMessage.objects.create(conversation=conversation, role="user", content=message)

        history = [
            {"role": msg.role, "parts": [{"text": msg.content}]}
            for msg in conversation.messages.all().order_by("created_at")
        ]

        # Add system prompt at the start
        contents = [{"role": "user", "parts": [{"text": system_prompt}]}] + history

        # Generate model response
        response = model.generate_content(
            contents=contents
        )

        assistant_message = response.text

        ChatMessage.objects.create(conversation=conversation, role="model", content=assistant_message)

        conversation.refresh_expiry(timeout=timeout_seconds)

        return Response({
            "role": "model",
            "content": assistant_message,
            "conversation_id": conversation.id,
            "conversation_expires_at": conversation.expires_at,
        })
    
class ActiveConversationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        timeout_seconds = 60

        conversation = (
            user.conversations.filter(active=True).order_by("-created_at").first()
        )

        if conversation and conversation.is_expired():
            conversation.active = False
            conversation.save()
            conversation = None

        if not conversation:
            conversation = Conversation.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(seconds=timeout_seconds),
            )

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)

