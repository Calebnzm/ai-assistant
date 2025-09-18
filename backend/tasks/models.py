from django.db import models
from django.conf import settings
from datetime import date, timedelta
from django.utils import timezone

class Task(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    due_date = models.DateField(blank=True, null=True)

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    TASK_TYPE_CHOICES = [
        ('task', 'Task'),
        ('habit', 'Habit'),
        ('project', 'Project'),
    ]
    type = models.CharField(max_length=10, choices=TASK_TYPE_CHOICES, default='task')
    streak = models.IntegerField(default=0, blank=True, null=True)
    last_completed = models.DateField(blank=True, null=True)
    tags = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completion_date = models.DateTimeField(null=True, blank=True)  # <-- new field

    def mark_completed(self):
        self.is_completed = True
        self.completion_date = timezone.now()
        self.save()

    def mark_incomplete(self):
        self.is_completed = False
        self.completion_date = None
        self.save()


    def update_streak(self):
        today = date.today()
        if self.last_completed == today:
            return
        
        if self.last_completed == today - timedelta(days=1):
            self.streak = (self.streak or 0) + 1

        else:
            self.streak = 1

        self.last_completed = today
        self.save
        
    def __str__(self):
        return self.title
