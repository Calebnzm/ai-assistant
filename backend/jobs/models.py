from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from django.contrib.postgres.fields import JSONField

User = get_user_model()

class Job(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SCHEDULED", "Scheduled"),
        ("IN_PROGRESS", "In progress"),
        ("SUCCEEDED", "Succeeded"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    steps = models.JSONField(default=list) 
    services = models.JSONField(default=list) 
    scheduled_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    result = models.JSONField(null=True, blank=True)
    logs = models.TextField(blank=True)
    retries = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

class JobTaskLog(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="task_logs")
    step_index = models.IntegerField()
    tool_name = models.CharField(max_length=255)
    args = models.JSONField(default=dict)
    response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
