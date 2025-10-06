from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    active = models.BooleanField(default=True) 

    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def refresh_expiry(self, timeout=60):
        self.expires_at = timezone.now() + timedelta(seconds=timeout)
        self.save()
    

class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=[("user", "User"), ("model", "Model")])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content}"