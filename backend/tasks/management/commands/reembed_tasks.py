from django.core.management.base import BaseCommand
from django.db import transaction

from tasks.models import Task
from tools.embeddings import embed_texts


class Command(BaseCommand):
    help = "Rebuild task embeddings with the current embedding model."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=32,
            help="Number of tasks to embed per OpenAI request.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        queryset = Task.objects.all().order_by("id")

        updated = 0
        batch = []
        for task in queryset.iterator(chunk_size=batch_size):
            batch.append(task)
            if len(batch) == batch_size:
                updated += self._process_batch(batch)
                batch = []

        if batch:
            updated += self._process_batch(batch)

        if updated == 0:
            self.stdout.write(self.style.SUCCESS("No tasks found."))
            return

        self.stdout.write(self.style.SUCCESS(f"Re-embedded {updated} tasks."))

    def _process_batch(self, batch):
        texts = []
        for task in batch:
            parts = [task.title]
            if task.description:
                parts.append(task.description)
            if task.tags and isinstance(task.tags, list):
                parts.append(f"Tags: {' '.join(task.tags)}")
            texts.append('. '.join(parts))

        embeddings = embed_texts(texts)
        with transaction.atomic():
            for task, embedding in zip(batch, embeddings):
                task.embedding = embedding
                task.save(update_fields=["embedding"], recalculate_embedding=False)
                self.stdout.write(f"Re-embedded task {task.id}")
        return len(batch)
