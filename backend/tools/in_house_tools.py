from django.db.models import Q
from tasks.models import Task
from api.models import User
from datetime import date, datetime
from tasks.serializers import ActivityUpdateValidatorSerializer, ActivityValidatorSerializer
from rest_framework.exceptions import ValidationError

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
            "due_date": task.due_date,
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

