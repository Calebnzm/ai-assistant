import json
import os
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from chats.views import ConversationAPIView
from dotenv import load_dotenv
from .models import TelegramLink
import re

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
    """Handle incoming Telegram updates:
       - /link CODE -> use TelegramLink to attach telegram_id to user
       - otherwise if chat is linked -> forward to ConversationAPIView
       - otherwise instruct user to create a code in profile
    """
    try:
        payload = json.loads(request.body)
    except Exception as e:
        print("telegram_webhook: bad json", e)
        return HttpResponse(status=400)

    message = payload.get("message") or payload.get("edited_message")
    if not message:
        return HttpResponse(status=200)

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    reply_to_message = message.get("reply_to_message", None)
    if reply_to_message:
        reply_to_message_text = reply_to_message.get("text", None)
    if reply_to_message and reply_to_message_text:
        reply_text = (message.get("text") or "").strip()
        text = f"{reply_text} The user is replying to the message: {reply_to_message_text}"
    else:
        text = (message.get("text") or "").strip()


    if not text:
        send_telegram_message(chat_id, "I can only process text messages right now. Send /link <CODE> to link this chat.")
        return JsonResponse({"ok": True})

    m = re.match(r"^/link\s+([A-Za-z0-9]+)$", text)
    if m:
        code = m.group(1).upper()
        try:
            link = TelegramLink.objects.get(code=code)
        except TelegramLink.DoesNotExist:
            send_telegram_message(chat_id, "That link code was not found. Generate a new code on your profile page and try again.")
            return JsonResponse({"ok": True})

        if link.is_used:
            send_telegram_message(chat_id, "This link code has already been used.")
            return JsonResponse({"ok": True})
        if link.is_expired():
            send_telegram_message(chat_id, "This link code has expired. Please generate a new code on your profile page.")
            return JsonResponse({"ok": True})

        user = link.user
        user.telegram_id = str(chat_id)
        user.save(update_fields=["telegram_id"])
        try:
            link.mark_used(chat_id)
        except Exception:
            link.is_used = True
            link.telegram_chat_id = str(chat_id)
            link.save(update_fields=["is_used", "telegram_chat_id"])

        send_telegram_message(chat_id, f"Success — this Telegram chat is now linked to {user.email}. You can now chat with your assistant from Telegram.")
        return JsonResponse({"ok": True})

    user = User.objects.filter(telegram_id=str(chat_id)).first()
    if not user:
        send_telegram_message(chat_id, "No linked account found. Visit your profile in the web app, click 'Link Telegram' and send /link <CODE> to this bot.")
        return JsonResponse({"ok": True})

    try:
        fake_request = type("FakeRequest", (), {"user": user, "data": {"message": text}})()
        response = ConversationAPIView().post(fake_request)
        reply = response.data.get("content", "Unable to get response from assistant.")
    except Exception as e:
        print("Error forwarding to conversation view:", e)
        reply = "Internal error while processing your message."

    send_telegram_message(chat_id, reply)
    return JsonResponse({"ok": True})