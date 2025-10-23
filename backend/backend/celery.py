import os
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'enqueue-pending-jobs': {
        'task': 'jobs.tasks.check_and_enqueue_pending_jobs',
        'schedule': 300.0,
    },
}