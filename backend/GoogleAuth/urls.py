from django.urls import path
from .views import GoogleAuthStart, GoogleOAuthCallback

urlpatterns = [
    path('start/', GoogleAuthStart.as_view(), name='google_oauth_start'),
    path('oauth2callback/', GoogleOAuthCallback.as_view(), name='google_oauth_callback'),
]