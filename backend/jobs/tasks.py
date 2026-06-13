from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Job, JobTaskLog
from tools.openai_runner import run_openai_tool_agent
from tools.tool_registry import fetch_schemas, fetch_tools
from dotenv import load_dotenv
import traceback
from datetime import timedelta, datetime

load_dotenv()
User = get_user_model()

@shared_task
def check_and_enqueue_pending_jobs():
    """Finds all pending jobs and queues them for execution."""
    now = timezone.now()

    with transaction.atomic():
        jobs_to_run = (
            Job.objects.select_for_update(skip_locked=True)
            .filter(status="PENDING", scheduled_at__lte=now)
        )

        for job in jobs_to_run:
            job.status = "SCHEDULED"
            job.save(update_fields=["status"])
            schedule_job.delay(job.id)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def schedule_job(self, job_id):
    "Simple wrapper to enque a job"

    return execute_job.apply_async(args=[job_id])

@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def execute_job(self, job_id):
    "Main worker agent for executing the job (corrected + safer)"
    try:
        with transaction.atomic():
            job = Job.objects.select_for_update(nowait=True).get(id=job_id)

            if job.status in ("IN_PROGRESS", "SUCCEEDED", "CANCELLED"):
                return {"skipped": job.status}

            job.status = "IN_PROGRESS"
            job.started_at = timezone.now()
            job.save()

        user = job.user

        TOOL_REGISTRY = fetch_tools(tier="core", services=job.services or [])
        TOOL_SCHEMAS = fetch_schemas(tier="core", services=job.services or [])

        current_time = timezone.now()
        formatted_time = current_time.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        system_prompt = system_prompt = f"""
            Role and Prime Directive
            You are a Personal AI Assistant for a user named {user.first_name}. Your prime directive is to process the user's request, take intelligent actions using your tools, and operate without direct user supervision.
            The current date and time is {formatted_time}. Use this for all date and time context unless the user specifies a different one.

            Context: Jobs
            The user will schedule jobs that they expect you to execute. They will provide the Title, description and steps for what they need you to do. 
            You have also been provided with a number of tools to aid your execution of the user's task/job.

            Standard Operating Procedure (SOP)
            You MUST follow this procedure for each job/task:

            1.  **Analyze and Understand:** First, silently analyze Job Description to determine its primary category. Is it a **Scheduling Request**, an **Research and Analysis Request**, **Correspondece Request**, as 
                well as the steps you will be required to take to accomplish the task.

            2.  **Gather necessary information:** Gather all the neccesary information from the user's account that will be necessary for you to accomplish the task or job.

            3.  **Determine if all actions may be required:** Not all the steps in a task/job will require execution, some steps might already be complete or done before. Example: Before scheduling an event, check to confirm
                if the event already exists in the first place. If it exists, no need to create it once again. This applies to all the tasks you will be expected to execute.

            4.  **Execute Tasks:** If an action is required, use one or more of your available tools to execute it.

            5.  **Confirm Execution:** After taking any actions, you will be required to confirm the results of your actions are what is expected. If not, you are required to redo the entire task once again,
                to accomplish the objective and acheive the desired/required results.
            
            6.  **Notify the user:** After satisfactorily accomplishing your tasks, you are required to breif the user on all the JD, the actions taken, and the accomplishments or results.
            ---
            ### Critical Directives
            -   **Be Conservative:** If you are ever unsure about the user's intent or the , it is always better to **do nothing** than to take the wrong action.
            -   **Act Autonomously:** Do not ask for permission. Follow the SOP and Action Matrix directly.
            -   **Inform the user:** Upon the completion of the job, you will be required to brief the user.
            
            Upon Completion of the task, use the complete tool.
        """

        jd = "Title: " + (job.title or "") + " Description: " + (job.description or "") + " Steps: " + str(job.steps or [])

        history = [
            {"role": "user", "content": jd}
        ]

        def log_tool_result(tool_name, tool_args, tool_result, step_index):
            try:
                JobTaskLog.objects.create(
                    job=job,
                    step_index=step_index,
                    tool_name=tool_name,
                    args=tool_args,
                    response=tool_result,
                    success=(tool_result.get("status") != "error"),
                    error_message=tool_result.get("message", "")
                    if tool_result.get("status") == "error"
                    else "",
                )
            except Exception:
                job.logs = (job.logs or "") + (
                    f"\nWarning: failed to write JobTaskLog for step {step_index}"
                )

        try:
            agent_result = run_openai_tool_agent(
                messages=history,
                system_prompt=system_prompt,
                tool_schemas=TOOL_SCHEMAS,
                tool_registry=TOOL_REGISTRY,
                user_id=user.id,
                max_iterations=20,
                on_tool_result=log_tool_result,
            )
            step_results = agent_result["tool_results"]
            iter_count = agent_result["iterations"]

        except Exception as e:
            job.retries = job.retries + 1
            if job.retries <= job.max_retries:
                backoff_seconds = 60 * (2 ** (job.retries - 1))
                job.status = "SCHEDULED"
                job.scheduled_at = timezone.now() + timedelta(seconds=backoff_seconds)
                job.save()
                execute_job.apply_async(args=[str(job.id)], eta=job.scheduled_at)
                return {"retrying": True, "next_try_at": job.scheduled_at.isoformat()}
            else:
                job.status = "FAILED"
                job.finished_at = timezone.now()
                job.logs = (job.logs or "") + f"\nModel error after retries: {str(e)}\n{traceback.format_exc()}"
                job.save()
                return {"error": str(e)}


        job.status = "SUCCEEDED"
        job.finished_at = timezone.now()
        job.result = {"steps": step_results}
        job.logs = (job.logs or "") + f"\nCompleted {len(step_results)} steps. Iterations: {iter_count}"
        job.save()
        return {"ok": True}

    except Job.DoesNotExist:
        return {"error": "job not found"}

    except transaction.DatabaseError as e:
        raise self.retry(exc=e)

    except Exception as exc:
        try:
            raise self.retry(exc=exc)
        except Exception:
            try:
                job = Job.objects.get(id=job_id)
                job.status = "FAILED"
                job.finished_at = timezone.now()
                job.logs = (job.logs or "") + f"\nUnexpected error: {str(exc)}\n{traceback.format_exc()}"
                job.save()
            except Exception:
                pass
            return {"error": str(exc)}