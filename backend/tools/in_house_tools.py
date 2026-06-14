from django.db.models import Q
from tasks.models import Task
from api.models import User
from datetime import date, datetime
from rest_framework.exceptions import ValidationError
from sentence_transformers import SentenceTransformer
from pgvector.django import CosineDistance
from chats.models import Conversation, ChatMessage
from django.utils import timezone
from datetime import timedelta
from functools import lru_cache
import os, requests, json
from django.utils.dateparse import parse_datetime
from dotenv import load_dotenv

from jobs.models import Job

load_dotenv()


@lru_cache(maxsize=1)
def _embedding_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")

def list_activity(user_id, start_date_str: str, end_date_str: str) -> list:
    "A tool to get the task list for a given date"

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
    
    user = User.objects.get(pk=user_id)
    tasks = Task.objects.filter(user=user).filter(
        Q(due_date__range=(start_date, end_date)) |
        Q(created_at__range=(start_date, end_date)) |
        Q(created_at__lt=start_date) & Q(due_date__gt=end_date)
    ).distinct()

    task_list = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "created": task.created_at,
            "due_date": task.due_date.isoformat(),
            "completed": task.is_completed,
            "task type": task.type,
            "tags": task.tags or [],
            "streak": task.streak if task.type in ["habit", "project"] else "Not valid for a task",
            "Number of days Completed": len(task.streak_dates) if task.type in ["habit", "project"] else "Not valid for a task"
        } for task in tasks
    ]

    return {"tasks": task_list}

def create_activity(user_id, title: str, description: str, type: str, priority: str, due_date_str: date, tags: str) -> str:
    "A tool to create an activity"


    try:
        user = User.objects.get(pk=user_id)
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        activity = Task(user=user, title=title, description=description, type=type, priority=priority, due_date=due_date, tags=tags)
        activity.save()
        return {"status": "Task Created Succesfully"}

    except User.DoesNotExist:
        return {"status": "error", "message": "User account not found"}
    except ValueError:
        return {"status": "error", "message": "Invalid due date format. Please use YYYY-MM-DD"}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
    


def edit_activity(user_id: int, task_id: int, **updates) -> dict:
    """
    Edits an existing task for a user.
    Requires a task_id and a dictionary of fields to update.
    """
    try:

        if updates["due_date"]:
            updates["due_date"] = datetime.strptime(updates["due_date"], "%Y-%m-%d").date()

        user = User.objects.get(pk=user_id)

        task = Task.objects.get(pk=task_id, user=user)

        for key, value in updates.items():
            setattr(task, key, value)
        
        task.save()

        return {"status": "success", "updated_task_id": task.id}

    except ValidationError as e:
        return {"status": "error", "message": "Invalid input provided.", "details": e.detail}
    except Task.DoesNotExist:
        return {"status": "error", "message": f"Task with ID {task_id} not found for this user."}
    except User.DoesNotExist:
        return {"status": "error", "message": "User not found."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
    


def delete_activity(user_id, task_id: int) -> dict:
    "Deletes a task for a user"

    try:
        user = User.objects.get(pk=user_id)
        activity = Task.objects.get(pk=task_id, user=user)
        activity.delete()

        return {"status": "success", "message": "Task Deleted Succesfully"}

    except Task.DoesNotExist:
        return {"status": "error", "message": f"Task with ID {task_id} not found for this user."}
    except User.DoesNotExist:
        return {"status": "error", "message": "User not found."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}



def search_activities(user_id, search_phrase: str) -> dict:
    "A semantic search tool to search for a task using a phrase"

    try:

        user = User.objects.get(pk=user_id)
        if not search_phrase:
            return {"status": "error", "message": "A search parameter is required."}
        
        search_phrase_embedding = _embedding_model().encode(search_phrase)

        tasks = (
            Task.objects.filter(user=user).annotate(
                distance=CosineDistance("embedding", search_phrase_embedding)
            )
            .order_by('distance')[:5]
        )

        results = [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "created": task.created_at,
                "due_date": task.due_date.isoformat(),
                "completed": task.is_completed,
                "task type": task.type,
                "tags": task.tags or [],
                "streak": task.streak if task.type in ["habit", "project"] else "Not valid for a task",
                "Number of days Completed": len(task.streak_dates) if task.type in ["habit", "project"] else "Not valid for a task",
                "similarity": f"{(1 - task.distance) * 100}%"
            }
            for task in tasks
        ]

        return {"tasks": results}
    
    except User.DoesNotExist:
        return {"status": "error", "message": "User not found."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
    

def bot_send_message(user_id: str, message: str):
    "Sends a message to a telegram user."

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not TELEGRAM_BOT_TOKEN:
        return {"status": "error", "message": " DevError: Missing TELEGRAM_BOT_TOKEN in environment variables. Cannot send message."}
    

    try: 
        user = User.objects.get(pk=user_id)

        telegram_id = user.telegram_id

        if not telegram_id:
            return {"status": "error", "message": "User has not linked Telegram for correspondece."}

        if not message:
            return {"status": "error", "message": "Message cannot be empty"}
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": telegram_id, "text": message}
        response = requests.post(url, data=payload)
        response.raise_for_status()
        conversation = (
            user.conversations.filter(active=True).order_by("-created_at").first()
        )

        if conversation and conversation.is_expired():
            conversation.active = False
            conversation.save()
            conversation = None

        timeout_seconds = 600

        if not conversation:
            conversation = Conversation.objects.create(
                user=user,
                expires_at = timezone.now() + timedelta(seconds=timeout_seconds)
            )

        ChatMessage.objects.create(conversation=conversation, role="model", content=message)

        return {"status": "success", "message": "Message sent succesfully"}
    
    except User.DoesNotExist:
        return {"status": "error", "message": "User not found."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
    

def create_job_tool(user_id: int, title: str, description: str, steps: list, services: list = None, scheduled_at: str = None) -> dict:
    "A tool to create and schedule Jobs"


    try:
        from jobs.tasks import schedule_job

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return {"status": "error", "message": "User account not found"}

        if scheduled_at:
            dt = parse_datetime(scheduled_at)
            if dt is None:
                return {"status":"error","message":"Invalid scheduled_at ISO format"}
            scheduled_at_dt = timezone.make_aware(dt) if dt.tzinfo is None else dt
        else:
            scheduled_at_dt = timezone.now()

        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except json.JSONDecodeError:
                return {"status": "error", "message": "steps must be valid JSON or a Python list"}
        if not isinstance(steps, list):
            return {"status": "error", "message": "steps must be a list of step objects"}


        job = Job.objects.create(
            user=user,
            title=title,
            description=description,
            steps=steps,
            services=services or [],
            scheduled_at=scheduled_at_dt,
            status="SCHEDULED",
            max_retries=3,
        )

        if scheduled_at_dt <= timezone.now():
            schedule_job.apply_async(args=[str(job.id)])
        else:
            schedule_job.apply_async(args=[str(job.id)], eta=scheduled_at_dt)

        return {"status": "ok", "job_id": str(job.id), "scheduled_at": scheduled_at_dt.isoformat()}

    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}


def complete():
    return


