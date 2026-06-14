from django.db import models
from django.conf import settings
from datetime import date, timedelta
from functools import lru_cache
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField, HnswIndex
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def _embedding_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


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
    completion_date = models.DateTimeField(null=True, blank=True)
    streak_dates = ArrayField(
        models.DateField(),
        default=list,
        blank=True,
        null=True
    )
    embedding = VectorField(dimensions=384, blank=True, null=True)

    def generate_embedding(self):
        "Generates a text block and its embedding"

        parts = [self.title]

        if self.description:
            parts.append(self.description)
        
        if self.tags and isinstance(self.tags, list):
            tag_string = " ".join(self.tags)
            parts.append(f"Tags: {tag_string}")

        combined_text = ". ".join(parts)

        return _embedding_model().encode(combined_text)
    
    def save(self, *args, **kwargs):
        "Generate embeddings before saving task"
        self.embedding = self.generate_embedding()
        super().save(*args, **kwargs)

    class Meta:
        "Index for faster similarity searches"
        indexes = [
            HnswIndex(
                name="task_embedding_index",
                fields=["embedding"],
                opclasses=["vector_cosine_ops"],
            )
        ]

    def mark_completed(self):
        today = timezone.localdate()
        if self.type == "task":
            self.is_completed = True
            self.completion_date = timezone.now()
            self.save()
        else:
            self.last_completed = today
            self.update_streak(today)
            self.save()

    def mark_incomplete(self):
        today = timezone.localdate()

        if self.type == "task":
            self.is_completed = False
            self.completion_date = None
            self.save()
            return

        if not isinstance(self.streak_dates, list):
            self.streak_dates = []

        if today in self.streak_dates:
            self.streak_dates.remove(today)

        self.last_completed = max(self.streak_dates) if self.streak_dates else None
        self.save(update_fields=["last_completed", "streak_dates", "updated_at"])


    def update_streak(self, today=None):
        today = today or timezone.localdate()

        if self.last_completed == today:
            return

        if not isinstance(self.streak_dates, list):
            self.streak_dates = []

        if self.last_completed == today - timedelta(days=1):
            self.streak = (self.streak or 0) + 1
        else:
            self.streak = 1

        self.last_completed = today
        if today not in self.streak_dates:
            self.streak_dates.append(today)

        self.save(update_fields=["streak", "last_completed", "streak_dates", "updated_at"])


    def __str__(self):
        return self.title
