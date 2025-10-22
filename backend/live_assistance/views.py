import json, os
import base64
import logging
import threading
import traceback
from typing import List, Dict
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from googleapiclient.discovery import build

from google import genai
from google.genai import types
from googleapiclient.errors import HttpError

User = get_user_model()
from GoogleAuth.models import GoogleCredential
from GoogleAuth.utils import get_credentials_for_user
from chats.views import ConversationAPIView
from tools.tool_registry import fetch_schemas, fetch_tools
from chats.models import Conversation


MAX_MESSAGES_PER_PUSH = 10

logger = logging.getLogger(__name__)

def decode_mime_body(payload: dict) -> str:
    """Extract a readable text body from Gmail message payload."""
    from bs4 import BeautifulSoup

    def get_part(parts):
        if not parts:
            return ""
        for part in parts:
            mime_type = part.get("mimeType", "")
            body_data = part.get("body", {}).get("data")
            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
                if mime_type == "text/html":
                    return BeautifulSoup(decoded, "html.parser").get_text()
                else:
                    return decoded
            if "parts" in part:
                nested = get_part(part["parts"])
                if nested:
                    return nested
        return ""

    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    return get_part(payload.get("parts", [])) or ""


def fetch_history_and_message_ids(gmail_service, start_history_id: str, user_cred: GoogleCredential) -> List[str]:
    """
    Robustly fetch message IDs using history.list(startHistoryId=...).
    Falls back to messages.list if history fails or contains no new messages.
    Returns up to MAX_MESSAGES_PER_PUSH unique message IDs.
    """
    logger.debug("fetch_history_and_message_ids: start_history_id=%s for user=%s", start_history_id, getattr(user_cred, "email", "<no-email>"))
    message_ids = []

    # helper to dedupe and cap
    def add_id(mid):
        if mid and mid not in message_ids and len(message_ids) < MAX_MESSAGES_PER_PUSH:
            message_ids.append(mid)

    # Try history.list first
    try:
        resp = gmail_service.users().history().list(
            userId="me",
            startHistoryId=start_history_id,
            historyTypes=["messageAdded"]
        ).execute()

        # debug dump for offline inspection
        try:
            with open("/tmp/gmail_api_debug.json", "a") as fh:
                fh.write(json.dumps({"kind": "history.list", "resp": resp, "ts": timezone.now().isoformat()}) + "\n")
        except Exception:
            logger.debug("Could not write gmail_api_debug.json")

        logger.debug("history.list response keys: %s", list(resp.keys()))
        for h in resp.get("history", []):
            # messagesAdded is the typical key
            for added in h.get("messagesAdded", []) or h.get("messages", []) or []:
                # messagesAdded entries sometimes come in the shape { "message": { "id": "..." } }
                mid = None
                if isinstance(added, dict):
                    if "message" in added and isinstance(added["message"], dict):
                        mid = added["message"].get("id")
                    else:
                        # sometimes history entries include direct message dicts
                        mid = added.get("id") or added.get("messageId")
                if mid:
                    add_id(mid)

    except HttpError as e:
        # history may be too old or startHistoryId invalid -> fallback
        status = getattr(e, "status_code", None) or getattr(e, "resp", {}).get("status") if hasattr(e, "resp") else "?"
        logger.warning("history.list failed (status=%s): %s. Falling back to messages.list.", status, str(e))
    except Exception as e:
        logger.exception("Unexpected error calling history.list: %s", e)

    # If history returned nothing, fallback to messages.list (support paging)
    if not message_ids:
        logger.debug("No message ids from history.list — calling messages.list fallback")
        try:
            page_token = None
            attempts = 0
            while len(message_ids) < MAX_MESSAGES_PER_PUSH:
                attempts += 1
                params = {"userId": "me", "labelIds": ["INBOX"], "maxResults": MAX_MESSAGES_PER_PUSH}
                if page_token:
                    params["pageToken"] = page_token
                resp = gmail_service.users().messages().list(**params).execute()

                # debug dump
                try:
                    with open("/tmp/gmail_api_debug.json", "a") as fh:
                        fh.write(json.dumps({"kind": "messages.list", "resp": resp, "ts": timezone.now().isoformat()}) + "\n")
                except Exception:
                    logger.debug("Could not write gmail_api_debug.json")

                msgs = resp.get("messages", [])
                logger.debug("messages.list returned %d messages (attempt %d)", len(msgs), attempts)
                for item in msgs:
                    mid = item.get("id")
                    add_id(mid)
                    if len(message_ids) >= MAX_MESSAGES_PER_PUSH:
                        break

                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

                # small guard to avoid runaway paging
                if attempts >= 5:
                    logger.debug("Reached paging attempts limit when listing messages")
                    break

        except Exception as ee:
            logger.exception("Fallback messages.list also failed: %s", ee)

    # final dedup/cap in case of unexpected duplicates
    uniq = []
    for m in message_ids:
        if m not in uniq:
            uniq.append(m)
        if len(uniq) >= MAX_MESSAGES_PER_PUSH:
            break

    logger.debug("Returning %d message ids: %s", len(uniq), uniq)
    return uniq


def fetch_full_messages(gmail_service, message_ids: List[str]) -> List[Dict]:
    """
    Fetch full message objects for given message IDs.
    Returns list of dicts with id, thread_id, subject, from, body, snippet, web_url, raw.
    """
    out = []
    logger.debug("fetch_full_messages: fetching %d ids", len(message_ids))
    if not message_ids:
        return out

    for mid in message_ids:
        try:
            # When mid looks invalid this can raise; catch and log entire exception
            msg = gmail_service.users().messages().get(userId="me", id=mid, format="full").execute()

            # Debug dump first message raw payload (only the first to avoid huge files)
            try:
                with open("/tmp/gmail_api_debug.json", "a") as fh:
                    fh.write(json.dumps({"kind": "message.get", "id": mid, "ts": timezone.now().isoformat(), "headers_present": bool(msg.get("payload", {}).get("headers"))}) + "\n")
            except Exception:
                logger.debug("Could not write gmail_api_debug.json for message.get")

            headers_list = msg.get("payload", {}).get("headers", []) or []
            headers = {h.get("name"): h.get("value") for h in headers_list if isinstance(h, dict)}
            subject = headers.get("Subject", "(No Subject)")
            sender = headers.get("From", "Unknown")
            thread_id = msg.get("threadId")
            snippet = msg.get("snippet", "")
            body = decode_mime_body(msg.get("payload", {}))
            web_url = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}" if thread_id else ""
            out.append({
                "id": mid,
                "thread_id": thread_id,
                "subject": subject,
                "from": sender,
                "body": body,
                "snippet": snippet,
                "web_url": web_url,
                "raw": msg
            })
            logger.debug("Fetched message %s subject=%s", mid, subject)

        except HttpError as he:
            logger.exception("HttpError fetching message %s: %s", mid, he)
            # for HTTP 404 or 410, skip. Continue for other statuses.
            try:
                status = he.resp.status
            except Exception:
                status = None
            if status in (404, 410):
                logger.warning("Message %s missing (status=%s) — skipping", mid, status)
                continue
        except Exception as e:
            logger.exception("Failed to fetch message %s: %s\n%s", mid, e, traceback.format_exc())

    logger.debug("fetch_full_messages returning %d messages", len(out))
    return out

@csrf_exempt
def pubsub_gmail_push(request):
    "Receive Gmail push notifications."

    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    # auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    # if auth_header.startswith("Bearer "):
    #     token = auth_header.split(" ", 1)[1]
    #     try:
    #         expected_audience = None
    #         decoded = id_token.verify_oauth2_token(
    #             token, google_requests.Request(), audience=expected_audience
    #         )
    #         print("Verified push token for sub=%s", decoded.get("sub"))
    #     except Exception as e:
    #         print("Invalid push token: %s", e)
    #         return HttpResponse(status=401)

    try:
        envelope = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        return HttpResponseBadRequest("invalid json")

    message = envelope.get("message")
    if not message:
        return JsonResponse({"ok": True, "info": "no message field"})

    data_b64 = message.get("data")
    if not data_b64:
        return JsonResponse({"ok": True, "info": "empty message"})

    try:
        raw = base64.b64decode(data_b64).decode("utf-8")
        payload = json.loads(raw)
    except Exception as e:
        return HttpResponseBadRequest("bad payload")

    email = payload.get("emailAddress")
    history_id = payload.get("historyId")

    if not email or not history_id:
        return HttpResponseBadRequest("missing emailAddress or historyId")

    user_credential = GoogleCredential.objects.filter(email=email).first()
    if not user_credential:
        logger.warning("No GoogleCredential found for email %s", email)
        return JsonResponse({"ok": False, "error": "no matching credential"}, status=404)

    user = user_credential.user
    telegram_id = getattr(user, "telegram_id", None)

    if not telegram_id:
        logger.warning("User %s (%s) has no telegram_id", user, email)
        return JsonResponse({"ok": True, "info": "no telegram_id"})

    # def handle_update():

    creds = get_credentials_for_user(user)
    try:
        gmail_service = build("gmail", "v1", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Failed to build Drive service: {e}")
    
    user_creds = GoogleCredential.objects.filter(user=user).first()

    latest_history_id = user_creds.latest_history_id

    if latest_history_id and int(history_id) <= int(latest_history_id):
        return JsonResponse({"ok": True, "info": "duplicate or already processed"})

    message_ids = fetch_history_and_message_ids(
        gmail_service, latest_history_id, user_credential
    )

    full_messages = fetch_full_messages(gmail_service, message_ids)


    if not full_messages:
        return JsonResponse({"ok": True, "info": "no new messages"})
    
    message_summaries = []
    for msg in full_messages:
        summary = (
            f"📧 From: {msg['from']}\n"
            f"Subject: {msg['subject']}\n"
            f"Snippet: {msg['snippet']}\n"
            f"Body:\n{msg['body'][:1500]}\n"  
            f"Link: {msg['web_url']}\n"
            "---"
        )
        message_summaries.append(summary)

    all_messages_text = "\n\n".join(message_summaries)



    system_prompt = system_prompt = f"""
    Role and Prime Directive
    You are an autonomous AI Email Assistant for a user named {user.first_name}. Your prime directive is to process incoming emails, take intelligent actions using your tools, and operate without direct user supervision.

    Context: Incoming Emails
    A batch of one or more newly received emails will be provided. Your analysis and subsequent actions will be based solely on this content.

    Standard Operating Procedure (SOP)
    You MUST follow this procedure for each email:

    1.  **Analyze and Categorize:** First, silently analyze each email to determine its primary category. Is it a **Meeting Request**, an **Invoice/Bill**, a **Potential Opportunity** (like a job offer or sales lead), a **Direct Question**, a **Newsletter**, or **Spam**? and label it with an
        appropriate label (If no appropriate lable exists, create a new one).

    2.  **Determine Action:** Based on the category, decide which action(s) to take according to the **Action Matrix** below.

    3.  **Default to No Action:** The most common outcome should be doing nothing. **If an email does not clearly fit a category that requires action, you MUST ignore it.** This is a critical safety instruction.

    4.  **Execute Tools:** If an action is required, use one or more of your available tools to execute it.

    Action Matrix (Category -> Required Action)

    -   **If Category is Meeting Request:**
        -   Use the `create_event` tool to schedule the event on the user's Google Calendar. Extract the title, attendees, date, and time from the email.

    -   **If Category is Invoice/Bill:**
        -   Use the `create_activity` tool to create a task reminding the user to pay it. The task title should include the service/product and amount (e.g., "Pay electricity bill of $75"). Set the due date a few days before the actual due date mentioned in the email.

    -   **If Category is Potential Opportunity (Job, Sales Lead, etc.):**
        -   Use the `create_activity` tool to create a **high-priority** task for the user to review it.
        -   Immediately use the `init_conversation` tool to send a notification to the user with a brief summary of the opportunity and a link to the email.

    -   **If Category is Direct Question or requires a reply:**
        -   If you have enough information, use the `send_gmail_message` tool to draft a reply.
        -   If you need input from {user.first_name} to form the reply, use the `init_conversation` tool to ask them for the necessary information.

    -   **If Category is Newsletter/Spam:**
        -   Take no action. Do not create tasks or notify the user.

    ---
    ### Critical Directives
    -   **Be Conservative:** If you are ever unsure about an email's intent, it is always better to **do nothing** than to take the wrong action.
    -   **Limit User Contact:** Only use the `init_conversation` tool when the Action Matrix explicitly requires it or when you are missing critical information to complete another required action.
    -   **Act Autonomously:** Do not ask for permission. Follow the SOP and Action Matrix directly.
    -   Keep the user in the loop, should you take any significant action, you can simply inform the user of any of the actions taken.
    """

    agent = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    tier = "complete"
    services = ["in_app", "gmail", "calendar"]
    TOOL_SCHEMAS = fetch_schemas(tier=tier, services=services)
    TOOL_REGISTRY = fetch_tools(tier=tier, services=services)
    tools = types.Tool(function_declarations=TOOL_SCHEMAS)

    history = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=all_messages_text)]
        )
    ]
    iter_count = 0
    max_iterations = 20


    while iter_count < max_iterations:
        iter_count += 1

        try: 
            response = agent.models.generate_content(
                model="gemini-2.5-flash",
                contents=history,
                config=types.GenerateContentConfig(
                    tools=[tools],
                    system_instruction=system_prompt
                )
            )

            if response.function_calls:
                for function_call in response.function_calls:
                    tool_name = function_call.name
                    tool_args = {key: value for key, value in function_call.args.items()}
                    tool_args["user_id"] = user.id


                    tool_function = TOOL_REGISTRY.get(tool_name)
                    if not tool_function:
                        tool_result = {"error": f"Tool '{tool_name}' not found."}
                    
                    else:
                        try:
                            tool_result = tool_function(**tool_args)

                        except ValueError as e:
                            tool_result = {
                                "status": "error",
                                "error_type": "VALIDATION_ERROR",
                                "message": "One of the provided arguments has an invalid format.",
                                "details": str(e)
                            }
                            
                        except TypeError as e:
                            tool_result = {
                                "status": "error",
                                "error_type": "ARGUMENT_ERROR",
                                "message": "Missing or incorrect arguments for the tool.",
                                "details": str(e)
                            }
                            
                        except Exception as e:
                            tool_result = {"error": f"An unexpected error occurred: {e}"}

                    if not isinstance(tool_result, dict):
                        tool_result = json.loads(tool_result)
                    function_response_part = types.Part.from_function_response(
                        name=function_call.name,
                        response=tool_result,
                    )
                    function_response_content = types.Content(
                        role='tool', parts=[function_response_part]
                    )
                    history.append(function_response_content)

                    if tool_name == "complete":
                        break

                continue
            else:
                break

        except Exception as e:
            print(f"An error occured: {str(e)}")

    # threading.Thread(target=handle_update, daemon=True).start()
    user_creds.latest_history_id = history_id
    user_creds.save(update_fields=["latest_history_id"])

    return JsonResponse({"ok": True})
