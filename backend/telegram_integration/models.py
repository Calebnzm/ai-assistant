import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class TelegramLink(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="telegram_links")
    code = models.CharField(max_length=32, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)

    def mark_used(self, chat_id):
        self.is_used = True
        self.telegram_chat_id = str(chat_id)
        self.save()

    @classmethod
    def generate_for_user(cls, user, ttl_minutes=10):
        code = uuid.uuid4().hex[:10].upper()
        now = timezone.now()
        return cls.objects.create(
            user=user,
            code=code,
            expires_at = now + timedelta(minutes=ttl_minutes)
        )
    
    def is_expired(self):
        return timezone.now() > self.expires_at