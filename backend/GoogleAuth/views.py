import json
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.urls import reverse
from django.core.cache import cache 
from googleapiclient.discovery import build
from django.utils.crypto import get_random_string

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from google_auth_oauthlib.flow import Flow

from api.models import User
from .models import GoogleCredential

if settings.OAUTHLIB_INSECURE_TRANSPORT:
    os.environ.setdefault(
        "OAUTHLIB_INSECURE_TRANSPORT", settings.OAUTHLIB_INSECURE_TRANSPORT
    )

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/documents.readonly",
]


def _get_client_config():
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

class GoogleAuthStart(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        flow = Flow.from_client_config(
            _get_client_config(),
            scopes=SCOPES,
            redirect_uri=request.build_absolute_uri(reverse("google_oauth_callback")),
        )

        auth_url, returned_state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )

        cache_key = f"google_oauth_state_{returned_state}"
        cache.set(cache_key, user.id, timeout=600)

        return Response({"auth_url": auth_url, "state": returned_state})

class GoogleOAuthCallback(APIView):
    """
    Called by Google (no auth attached). We look up the state in cache to find the user,
    exchange the code for tokens and save credentials tied to that user.
    Then redirect the browser back to frontend (profile/success page).
    """
    permission_classes = [AllowAny] 

    def get(self, request):
        state = request.GET.get("state")
        if not state:
            return Response({"error": "Missing state"}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"google_oauth_state_{state}"
        user_id = cache.get(cache_key)
        if not user_id:
            return Response({"error": "Invalid or expired state"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

        flow = Flow.from_client_config(
            _get_client_config(),
            scopes=SCOPES,
            state=state,
            redirect_uri=request.build_absolute_uri(reverse("google_oauth_callback")),
        )

        try:
            flow.fetch_token(authorization_response=request.build_absolute_uri())
        except Exception as exc:
            return Response({"error": "Failed to fetch token", "details": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        creds = flow.credentials
        oauth2 = build('oauth2', 'v2', credentials=creds)
        userinfo = oauth2.userinfo().get().execute()
        email = userinfo.get('email')

        obj, created = GoogleCredential.objects.update_or_create(
            user=user,
            defaults={
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": json.dumps(list(creds.scopes or [])),
                "expiry": creds.expiry,
                "email": email
            },
        )

        try:
            gmail_service = build("gmail", "v1", credentials=creds)
            topic_name = "projects/plannora/topics/email"
            watch_request = {
                "labelIds": ["CATEGORY_PERSONAL"],
                "topicName": topic_name,
            }
            watch_response = gmail_service.users().watch(userId="me", body=watch_request).execute()
            print(f"Gmail Watch started for {email}, historyId: {watch_response.get('historyId')}")
        except Exception as watch_error:
            print(f"⚠️ Failed to start Gmail Watch for {email}: {watch_error}")

        cache.delete(cache_key)

        frontend_url = settings.FRONTEND_URL
        if not frontend_url:
            raise ImproperlyConfigured("Missing FRONTEND_URL environment variable")
        success_url = f"{frontend_url.rstrip('/')}/google/success"
        return redirect(success_url)
