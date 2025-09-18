from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import SignupView, ProfileView

urlpatterns = [
    path('auth/register/', SignupView.as_view(), name='register'),  # signup
    path('auth/login/', TokenObtainPairView.as_view(), name='login'), # login
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # refresh
    path('auth/profile/', ProfileView.as_view(), name='profile'),
]