import json
import os
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from chats.views import ConversationAPIView
from dotenv import load_dotenv
from .models import TelegramLink

load_dotenv()
User = get_user_model()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def send_telegram_message(chat_id, text):
    """Sends a message back to a Telegram User."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = { "chat_id": chat_id, "text": text }
    requests.post(url, data=payload)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_telegram_link(request):
    """
    Called by logged-in web user to generate a one-time code.
    Returns code and instructions to send /link <CODE> to the bot.
    """
    user = request.user
    link = TelegramLink.generate_for_user(user, ttl_minutes=10)
    return JsonResponse({
        "code": link.code,
        "expires_at": link.expires_at,
        "instructions": f"Open Telegram and send the message: /link {link.code} to @{os.getenv('TELEGRAM_BOT_USERNAME')}"
    }, status=201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_telegram_link_status(request):
    """
    Returns whether the user has a telegram_id linked.
    """
    user = request.user
    return JsonResponse({
        "linked": bool(user.telegram_id),
        "telegram_id": user.telegram_id
    })

@csrf_exempt
def telegram_webhook(request):
    try:
        data = json.loads(request.body)
        message = data.get("message")
        if not message:
            return JsonResponse({"error": "No Message"}, status=400)
        
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        user = User.objects.filter(telegram_id=str(chat_id)).first()
        if not user:
            return JsonResponse({"error": "No linked account. You are required to have an account and link it through the profile page"})
        
        fake_request = type("FakeRequest", (), {"user": user, "data": {"message": text}})()
        response = ConversationAPIView().post(fake_request)
        reply = response.data.get("content", "Unable to get response")

        send_telegram_message(chat_id, reply)

        return JsonResponse({"ok": True})
    
    except Exception as e:
        print("Error in telegram_webhook", e)
        return JsonResponse({"error": str(e)}, status=500)