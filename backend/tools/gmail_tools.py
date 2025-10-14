import logging
import base64
import time
from typing import Optional, List, Dict, Literal, Tuple

from email.mime.text import MIMEText

from django.contrib.auth import get_user_model

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from GoogleAuth.utils import get_credentials_for_user

logger = logging.getLogger(__name__)

GMAIL_BATCH_SIZE = 25
GMAIL_REQUEST_DELAY = 0.1
HTML_BODY_TRUNCATE_LIMIT = 20000

User = get_user_model()



def _decode_base64url(data: str) -> str:
    if not data:
        return ""
    missing_padding = len(data) % 4
    if missing_padding:
        data += "=" * (4 - missing_padding)
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    except Exception:
        try:
            return base64.b64decode(data).decode("utf-8", errors="replace")
        except Exception:
            return ""


def _extract_message_bodies(payload: dict) -> Dict[str, str]:
    text_body = ""
    html_body = ""
    parts = payload.get("parts") or [payload]
    queue = list(parts)
    while queue:
        part = queue.pop(0)
        mime_type = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data")
        if body_data:
            try:
                decoded = _decode_base64url(body_data)
                if mime_type == "text/plain" and not text_body:
                    text_body = decoded
                elif mime_type == "text/html" and not html_body:
                    html_body = decoded
            except Exception as e:
                logger.warning(f"Failed to decode part: {e}")
        if part.get("parts"):
            queue.extend(part.get("parts", []))

    if payload.get("body", {}).get("data"):
        try:
            decoded = _decode_base64url(payload["body"]["data"])
            mime_type = payload.get("mimeType", "")
            if mime_type == "text/plain" and not text_body:
                text_body = decoded
            elif mime_type == "text/html" and not html_body:
                html_body = decoded
        except Exception as e:
            logger.warning(f"Failed to decode main payload body: {e}")

    return {"text": text_body, "html": html_body}


def _format_body_content(text_body: str, html_body: str) -> str:
    if text_body and text_body.strip():
        return text_body
    if html_body and html_body.strip():
        if len(html_body) > HTML_BODY_TRUNCATE_LIMIT:
            html_body = html_body[:HTML_BODY_TRUNCATE_LIMIT] + "\n\n[HTML content truncated...]"
        return f"[HTML Content Converted]\n{html_body}"
    return "[No readable content found]"


def _extract_headers(payload: dict, header_names: List[str]) -> Dict[str, str]:
    headers = {}
    for h in payload.get("headers", []):
        name = h.get("name", "")
        if name in header_names:
            headers[name] = h.get("value", "")
    return headers


def _prepare_gmail_message(
    subject: str,
    body: str,
    to: Optional[str] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    thread_id: Optional[str] = None,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    reply_subject = subject
    if in_reply_to and not subject.lower().startswith("re:"):
        reply_subject = f"Re: {subject}"

    message = MIMEText(body)
    message["subject"] = reply_subject
    if to:
        message["to"] = to
    if cc:
        message["cc"] = cc
    if bcc:
        message["bcc"] = bcc
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
    if references:
        message["References"] = references

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return raw_message, thread_id


def _generate_gmail_web_url(item_id: str, account_index: int = 0) -> str:
    return f"https://mail.google.com/mail/u/{account_index}/#all/{item_id}"


def _build_gmail_service_for_user(user_id: int):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ValueError("User not found")
    creds = get_credentials_for_user(user)
    if not creds:
        raise ValueError("No Google credentials for user. Kindly ask the user to authenticate and authorize via the profile page.")
    try:
        service = build("gmail", "v1", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Failed to build Gmail service: {e}")
    return service



def search_gmail_messages(user_id: int, query: str, page_size: int = 10) -> Dict:
    """
    Returns:
      {"status":"ok","data":{"messages":[{id,threadId,subject,from,snippet,web_url}]}, "meta":{"count":N}}
    """
    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}

    try:
        resp = service.users().messages().list(userId="me", q=query, maxResults=page_size).execute()
        messages = resp.get("messages") or []
    except HttpError as e:
        return {"status": "error", "message": "Gmail API error listing messages", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error listing messages", "details": str(e)}

    results = []
    for m in messages:
        mid = m.get("id")
        try:
            meta = service.users().messages().get(userId="me", id=mid, format="metadata", metadataHeaders=["Subject", "From"]).execute()
            headers = {h["name"]: h["value"] for h in meta.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "")
            sender = headers.get("From", "")
            snippet = meta.get("snippet", "") or ""
        except Exception:
            subject = ""
            sender = ""
            snippet = m.get("snippet", "") or ""
        results.append({
            "id": mid,
            "threadId": m.get("threadId"),
            "subject": subject,
            "from": sender,
            "snippet": snippet,
            "web_url": _generate_gmail_web_url(mid) if mid else None
        })

    return {"status": "ok", "data": {"messages": results}, "meta": {"count": len(results)}}


def get_gmail_message_content(user_id: int, message_id: str) -> Dict:
    """
    Returns:
      {"status":"ok","data":{"message": {id, subject, from, date, body, web_url}}, "meta": {}}
    """
    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}

    try:
        meta = service.users().messages().get(userId="me", id=message_id, format="metadata", metadataHeaders=["Subject", "From", "Date"]).execute()
        headers = {h["name"]: h["value"] for h in meta.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "(no subject)")
        sender = headers.get("From", "(unknown sender)")
        date_hdr = headers.get("Date", "")

        full = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        payload = full.get("payload", {})
        bodies = _extract_message_bodies(payload)
        body_data = _format_body_content(bodies.get("text", ""), bodies.get("html", ""))

        message_obj = {
            "id": message_id,
            "subject": subject,
            "from": sender,
            "date": date_hdr,
            "body": body_data,
            "web_url": _generate_gmail_web_url(message_id)
        }
        return {"status": "ok", "data": {"message": message_obj}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Gmail API error fetching message", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error fetching message", "details": str(e)}


def get_gmail_messages_content_batch(user_id: int, message_ids: List[str], format: Literal["full", "metadata"] = "full") -> Dict:
    """
    Returns:
      {"status":"ok","data":{"messages":[{id,subject,from,body,web_url}]}, "meta":{"count":N}}
    """
    logger.info(f"[get_gmail_messages_content_batch] user_id={user_id}, count={len(message_ids)}")
    if not message_ids:
        return {"status": "error", "message": "No message IDs provided", "details": ""}

    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}

    output_messages = []
    for chunk_start in range(0, len(message_ids), GMAIL_BATCH_SIZE):
        chunk = message_ids[chunk_start: chunk_start + GMAIL_BATCH_SIZE]
        results: Dict[str, Dict] = {}

        try:
            def _batch_cb(request_id, response, exception):
                results[request_id] = {"data": response, "error": exception}

            batch = service.new_batch_http_request(callback=_batch_cb)
            for mid in chunk:
                if format == "metadata":
                    req = service.users().messages().get(userId="me", id=mid, format="metadata", metadataHeaders=["Subject", "From"])
                else:
                    req = service.users().messages().get(userId="me", id=mid, format="full")
                batch.add(req, request_id=mid)
            batch.execute()
        except Exception as batch_error:
            logger.warning(f"Batch failed ({batch_error}), falling back to sequential")
            for mid in chunk:
                try:
                    if format == "metadata":
                        msg = service.users().messages().get(userId="me", id=mid, format="metadata", metadataHeaders=["Subject", "From"]).execute()
                    else:
                        msg = service.users().messages().get(userId="me", id=mid, format="full").execute()
                    results[mid] = {"data": msg, "error": None}
                except Exception as e:
                    results[mid] = {"data": None, "error": e}
                time.sleep(GMAIL_REQUEST_DELAY)

        for mid in chunk:
            entry = results.get(mid, {"data": None, "error": "No result"})
            if entry["error"]:
                output_messages.append({"id": mid, "error": str(entry["error"])})
                continue
            message = entry["data"]
            if not message:
                output_messages.append({"id": mid, "error": "No data returned"})
                continue

            payload = message.get("payload", {})
            if format == "metadata":
                headers = _extract_headers(payload, ["Subject", "From"])
                subject = headers.get("Subject", "(no subject)")
                sender = headers.get("From", "(unknown sender)")
                output_messages.append({
                    "id": mid,
                    "subject": subject,
                    "from": sender,
                    "body": None,
                    "web_url": _generate_gmail_web_url(mid)
                })
            else:
                headers = _extract_headers(payload, ["Subject", "From"])
                subject = headers.get("Subject", "(no subject)")
                sender = headers.get("From", "(unknown sender)")
                bodies = _extract_message_bodies(payload)
                body_data = _format_body_content(bodies.get("text", ""), bodies.get("html", ""))
                output_messages.append({
                    "id": mid,
                    "subject": subject,
                    "from": sender,
                    "body": body_data,
                    "web_url": _generate_gmail_web_url(mid)
                })

    return {"status": "ok", "data": {"messages": output_messages}, "meta": {"count": len(output_messages)}}


def send_gmail_message(user_id: int, to: str, subject: str, body: str, cc: Optional[str] = None, bcc: Optional[str] = None,
                       thread_id: Optional[str] = None, in_reply_to: Optional[str] = None, references: Optional[str] = None) -> Dict:
    logger.info(f"[send_gmail_message] user_id={user_id}, to={to}, subject={subject}")
    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}

    raw_message, thread_final = _prepare_gmail_message(subject=subject, body=body, to=to, cc=cc, bcc=bcc, thread_id=thread_id, in_reply_to=in_reply_to, references=references)
    send_body = {"raw": raw_message}
    if thread_final:
        send_body["threadId"] = thread_final

    try:
        sent = service.users().messages().send(userId="me", body=send_body).execute()
        message_id = sent.get("id")
        return {"status": "ok", "data": {"message_id": message_id}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Gmail API error sending message", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error sending message", "details": str(e)}


def draft_gmail_message(user_id: int, subject: str, body: str, to: Optional[str] = None, cc: Optional[str] = None, bcc: Optional[str] = None,
                        thread_id: Optional[str] = None, in_reply_to: Optional[str] = None, references: Optional[str] = None) -> Dict:
    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}

    raw_message, thread_final = _prepare_gmail_message(subject=subject, body=body, to=to, cc=cc, bcc=bcc, thread_id=thread_id, in_reply_to=in_reply_to, references=references)
    draft_body = {"message": {"raw": raw_message}}
    if thread_final:
        draft_body["message"]["threadId"] = thread_final

    try:
        created = service.users().drafts().create(userId="me", body=draft_body).execute()
        draft_id = created.get("id")
        return {"status": "ok", "data": {"draft_id": draft_id}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Gmail API error creating draft", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error creating draft", "details": str(e)}


def _format_thread_content(thread_data: dict, thread_id: str) -> Dict:
    messages = thread_data.get("messages", [])
    first_message = messages[0] if messages else None
    first_headers = {h["name"]: h["value"] for h in first_message.get("payload", {}).get("headers", [])} if first_message else {}
    thread_subject = first_headers.get("Subject", "(no subject)")
    out_messages = []
    for message in messages:
        headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
        sender = headers.get("From", "(unknown sender)")
        date = headers.get("Date", "(unknown date)")
        subject = headers.get("Subject", "(no subject)")
        payload = message.get("payload", {})
        bodies = _extract_message_bodies(payload)
        body_data = _format_body_content(bodies.get("text", ""), bodies.get("html", ""))
        out_messages.append({
            "id": message.get("id"),
            "from": sender,
            "date": date,
            "subject": subject,
            "body": body_data
        })
    return {"thread_id": thread_id, "subject": thread_subject, "messages": out_messages}


def get_gmail_thread_content(user_id: int, thread_id: str) -> Dict:
    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}
    try:
        thread_resp = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
        thread_obj = _format_thread_content(thread_resp, thread_id)
        return {"status": "ok", "data": {"thread": thread_obj}, "meta": {"count": len(thread_obj.get("messages", []))}}
    except HttpError as e:
        return {"status": "error", "message": "Gmail API error fetching thread", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error fetching thread", "details": str(e)}


def get_gmail_threads_content_batch(user_id: int, thread_ids: List[str]) -> Dict:
    if not thread_ids:
        return {"status": "error", "message": "No thread IDs provided", "details": ""}

    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}

    output_threads = []
    for chunk_start in range(0, len(thread_ids), GMAIL_BATCH_SIZE):
        chunk = thread_ids[chunk_start: chunk_start + GMAIL_BATCH_SIZE]
        results: Dict[str, Dict] = {}

        try:
            def _batch_cb(request_id, response, exception):
                results[request_id] = {"data": response, "error": exception}

            batch = service.new_batch_http_request(callback=_batch_cb)
            for tid in chunk:
                req = service.users().threads().get(userId="me", id=tid, format="full")
                batch.add(req, request_id=tid)
            batch.execute()
        except Exception as batch_error:
            logger.warning(f"Batch failed ({batch_error}), falling back to sequential")
            for tid in chunk:
                try:
                    thread = service.users().threads().get(userId="me", id=tid, format="full").execute()
                    results[tid] = {"data": thread, "error": None}
                except Exception as e:
                    results[tid] = {"data": None, "error": e}
                time.sleep(GMAIL_REQUEST_DELAY)

        for tid in chunk:
            entry = results.get(tid, {"data": None, "error": "No result"})
            if entry["error"]:
                output_threads.append({"thread_id": tid, "error": str(entry["error"])})
                continue
            thread = entry["data"]
            if not thread:
                output_threads.append({"thread_id": tid, "error": "No data returned"})
                continue
            formatted = _format_thread_content(thread, tid)
            output_threads.append(formatted)

    return {"status": "ok", "data": {"threads": output_threads}, "meta": {"count": len(output_threads)}}


def list_gmail_labels(user_id: int) -> Dict:
    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}

    try:
        resp = service.users().labels().list(userId="me").execute()
        labels = resp.get("labels", []) or []
        labels_out = []
        for l in labels:
            labels_out.append({"id": l.get("id"), "name": l.get("name"), "type": l.get("type", "user")})
        return {"status": "ok", "data": {"labels": labels_out}, "meta": {"count": len(labels_out)}}
    except HttpError as e:
        return {"status": "error", "message": "Gmail API error listing labels", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error listing labels", "details": str(e)}


def manage_gmail_label(user_id: int, action: Literal["create", "update", "delete"], name: Optional[str] = None,
                       label_id: Optional[str] = None,
                       label_list_visibility: Literal["labelShow", "labelHide"] = "labelShow",
                       message_list_visibility: Literal["show", "hide"] = "show") -> Dict:
    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}

    try:
        if action == "create":
            if not name:
                return {"status": "error", "message": "Label name required for create", "details": ""}
            body = {"name": name, "labelListVisibility": label_list_visibility, "messageListVisibility": message_list_visibility}
            created = service.users().labels().create(userId="me", body=body).execute()
            return {"status": "ok", "data": {"label": {"id": created.get("id"), "name": created.get("name")}}, "meta": {}}

        elif action == "update":
            if not label_id:
                return {"status": "error", "message": "Label ID required for update", "details": ""}
            current = service.users().labels().get(userId="me", id=label_id).execute()
            body = {
                "id": label_id,
                "name": name if name is not None else current.get("name"),
                "labelListVisibility": label_list_visibility,
                "messageListVisibility": message_list_visibility,
            }
            updated = service.users().labels().update(userId="me", id=label_id, body=body).execute()
            return {"status": "ok", "data": {"label": {"id": updated.get("id"), "name": updated.get("name")}}, "meta": {}}

        elif action == "delete":
            if not label_id:
                return {"status": "error", "message": "Label ID required for delete", "details": ""}
            label = service.users().labels().get(userId="me", id=label_id).execute()
            label_name = label.get("name")
            service.users().labels().delete(userId="me", id=label_id).execute()
            return {"status": "ok", "data": {"label": {"id": label_id, "name": label_name}}, "meta": {"notes": "deleted"}}
        else:
            return {"status": "error", "message": "Unsupported action", "details": ""}
    except HttpError as e:
        return {"status": "error", "message": "Gmail API error managing label", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error managing label", "details": str(e)}


def modify_gmail_message_labels(user_id: int, message_id: str, add_label_ids: List[str] = None, remove_label_ids: List[str] = None) -> Dict:
    if not add_label_ids and not remove_label_ids:
        return {"status": "error", "message": "At least one of add_label_ids or remove_label_ids must be provided", "details": ""}

    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}

    body = {}
    if add_label_ids:
        body["addLabelIds"] = add_label_ids
    if remove_label_ids:
        body["removeLabelIds"] = remove_label_ids

    try:
        service.users().messages().modify(userId="me", id=message_id, body=body).execute()
        return {"status": "ok", "data": {"updated": {"message_id": message_id, "added": add_label_ids or [], "removed": remove_label_ids or []}}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Gmail API error modifying message labels", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error modifying message labels", "details": str(e)}


def batch_modify_gmail_message_labels(user_id: int, message_ids: List[str], add_label_ids: List[str] = None, remove_label_ids: List[str] = None) -> Dict:
    if not message_ids:
        return {"status": "error", "message": "No message IDs provided", "details": ""}
    if not add_label_ids and not remove_label_ids:
        return {"status": "error", "message": "At least one of add_label_ids or remove_label_ids required", "details": ""}

    try:
        service = _build_gmail_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to initialize Gmail service", "details": str(e)}

    body = {"ids": message_ids}
    if add_label_ids:
        body["addLabelIds"] = add_label_ids
    if remove_label_ids:
        body["removeLabelIds"] = remove_label_ids

    try:
        service.users().messages().batchModify(userId="me", body=body).execute()
        return {"status": "ok", "data": {"updated_items": {"message_count": len(message_ids), "added": add_label_ids or [], "removed": remove_label_ids or []}}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Gmail API error batch modifying labels", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error batch modifying labels", "details": str(e)}
