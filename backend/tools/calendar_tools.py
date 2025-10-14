import logging
import re
import uuid
import json
from typing import List, Optional, Dict, Any, Union, Literal, Tuple

from django.contrib.auth import get_user_model
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from GoogleAuth.utils import get_credentials_for_user

logger = logging.getLogger(__name__)

User = get_user_model()



def _parse_reminders_json(reminders_input: Optional[Union[str, List[Dict[str, Any]]]], function_name: str) -> List[Dict[str, Any]]:
    if not reminders_input:
        return []
    if isinstance(reminders_input, str):
        try:
            reminders = json.loads(reminders_input)
            if not isinstance(reminders, list):
                logger.warning(f"[{function_name}] Reminders must be a JSON array, got {type(reminders).__name__}")
                return []
        except json.JSONDecodeError as e:
            logger.warning(f"[{function_name}] Invalid JSON for reminders: {e}")
            return []
    elif isinstance(reminders_input, list):
        reminders = reminders_input
    else:
        logger.warning(f"[{function_name}] Reminders must be a JSON string or list, got {type(reminders_input).__name__}")
        return []

    if len(reminders) > 5:
        logger.warning(f"[{function_name}] More than 5 reminders provided, truncating to first 5")
        reminders = reminders[:5]

    validated_reminders = []
    for reminder in reminders:
        if not isinstance(reminder, dict) or "method" not in reminder or "minutes" not in reminder:
            logger.warning(f"[{function_name}] Invalid reminder format: {reminder}, skipping")
            continue
        method = reminder["method"].lower()
        if method not in ["popup", "email"]:
            logger.warning(f"[{function_name}] Invalid reminder method '{method}', must be 'popup' or 'email', skipping")
            continue
        minutes = reminder["minutes"]
        if not isinstance(minutes, int) or minutes < 0 or minutes > 40320:
            logger.warning(f"[{function_name}] Invalid reminder minutes '{minutes}', must be integer 0-40320, skipping")
            continue
        validated_reminders.append({"method": method, "minutes": minutes})
    return validated_reminders


def _correct_time_format_for_api(time_str: Optional[str], param_name: str) -> Optional[str]:
    if not time_str:
        return None
    if len(time_str) == 10 and time_str.count("-") == 2:
        try:
            from datetime import datetime
            datetime.strptime(time_str, "%Y-%m-%d")
            return f"{time_str}T00:00:00Z"
        except Exception:
            return time_str
    if len(time_str) == 19 and time_str[10] == "T" and time_str.count(":") == 2 and not (time_str.endswith("Z") or "+" in time_str[10:] or "-" in time_str[10:]):
        return time_str + "Z"
    return time_str


def _extract_drive_file_id(url_or_id: str) -> Optional[str]:
    if not url_or_id:
        return None
    if url_or_id.startswith("http"):
        match = re.search(r"(?:/d/|/file/d/|id=)([a-zA-Z0-9_-]+)", url_or_id)
        return match.group(1) if match else None
    return url_or_id 


def _build_calendar_service_for_user(user_id: int):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ValueError("User not found")
    creds = get_credentials_for_user(user)
    if not creds:
        raise ValueError("No Google credentials for user. Kindly ask the user to authorize from their profile page.")
    try:
        service = build("calendar", "v3", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Failed to build Calendar service: {e}")
    return service, creds



def list_calendars(user_id: int) -> Dict[str, Any]:
    """
    Returns: {"status":"ok","data":{"calendars":[{"id","summary","primary":bool}]}, "meta":{"count":N}}
    """
    try:
        service, _ = _build_calendar_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Calendar service", "details": str(e)}
    try:
        resp = service.calendarList().list().execute()
        items = resp.get("items", []) or []
        results = [{"id": it.get("id"), "summary": it.get("summary"), "primary": bool(it.get("primary", False))} for it in items]
        return {"status": "ok", "data": {"calendars": results}, "meta": {"count": len(results)}}
    except HttpError as e:
        return {"status": "error", "message": "Google Calendar API error listing calendars", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error listing calendars", "details": str(e)}


def get_events(
    user_id: int,
    calendar_id: str = "primary",
    event_id: Optional[str] = None,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 25,
    query: Optional[str] = None,
    detailed: bool = False,
) -> Dict[str, Any]:
    """
    Returns:
      - single event: {"status":"ok","data":{"event": {...}}}
      - multiple events: {"status":"ok","data":{"events":[...]}, "meta": {"count":N}}
    """
    try:
        service, _ = _build_calendar_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Calendar service", "details": str(e)}

    try:
        if event_id:
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            ev = {
                "id": event.get("id"),
                "summary": event.get("summary"),
                "start": event.get("start"),
                "end": event.get("end"),
                "description": event.get("description"),
                "location": event.get("location"),
                "attendees": [a.get("email") for a in (event.get("attendees") or [])],
                "htmlLink": event.get("htmlLink")
            }
            return {"status": "ok", "data": {"event": ev}, "meta": {}}

        formatted_time_min = _correct_time_format_for_api(time_min, "time_min") if time_min else None
        effective_time_min = formatted_time_min or None
        formatted_time_max = _correct_time_format_for_api(time_max, "time_max") if time_max else None

        params = {
            "calendarId": calendar_id,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        if effective_time_min:
            params["timeMin"] = effective_time_min
        if formatted_time_max:
            params["timeMax"] = formatted_time_max
        if query:
            params["q"] = query

        resp = service.events().list(**params).execute()
        items = resp.get("items", []) or []
        events_out = []
        for it in items:
            ev = {
                "id": it.get("id"),
                "summary": it.get("summary"),
                "start": it.get("start"),
                "end": it.get("end"),
                "htmlLink": it.get("htmlLink"),
            }
            if detailed:
                ev.update({
                    "description": it.get("description"),
                    "location": it.get("location"),
                    "attendees": [a.get("email") for a in (it.get("attendees") or [])]
                })
            events_out.append(ev)
        return {"status": "ok", "data": {"events": events_out}, "meta": {"count": len(events_out)}}
    except HttpError as e:
        return {"status": "error", "message": "Google Calendar API error fetching events", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error fetching events", "details": str(e)}


def create_event(
    user_id: int,
    summary: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary",
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    timezone: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    add_google_meet: bool = False,
    reminders: Optional[Union[str, List[Dict[str, Any]]]] = None,
    use_default_reminders: bool = True,
) -> Dict[str, Any]:
    """
    Create event and return created event id and link.
    """
    try:
        service, creds = _build_calendar_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Calendar service", "details": str(e)}

    try:
        event_body: Dict[str, Any] = {
            "summary": summary,
            "start": ({"date": start_time} if "T" not in start_time else {"dateTime": start_time}),
            "end": ({"date": end_time} if "T" not in end_time else {"dateTime": end_time}),
        }
        if location:
            event_body["location"] = location
        if description:
            event_body["description"] = description
        if timezone:
            if "dateTime" in event_body["start"]:
                event_body["start"]["timeZone"] = timezone
            if "dateTime" in event_body["end"]:
                event_body["end"]["timeZone"] = timezone
        if attendees:
            event_body["attendees"] = [{"email": e} for e in attendees]

        if reminders is not None or not use_default_reminders:
            effective_use_default = use_default_reminders and reminders is None
            reminder_data = {"useDefault": effective_use_default}
            if reminders is not None:
                validated = _parse_reminders_json(reminders, "create_event")
                if validated:
                    reminder_data["overrides"] = validated
            event_body["reminders"] = reminder_data

        if add_google_meet:
            request_id = str(uuid.uuid4())
            event_body["conferenceData"] = {
                "createRequest": {
                    "requestId": request_id,
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }

        drive_service = None
        if attachments:
            event_body["attachments"] = []
            try:
                drive_service = build("drive", "v3", credentials=creds)
            except Exception:
                drive_service = None
            for att in attachments:
                file_id = _extract_drive_file_id(att)
                file_url = f"https://drive.google.com/open?id={file_id}" if file_id else att
                title = "Drive Attachment"
                mime_type = "application/octet-stream"
                if drive_service and file_id:
                    try:
                        meta = drive_service.files().get(fileId=file_id, fields="mimeType,name").execute()
                        mime_type = meta.get("mimeType", mime_type)
                        title = meta.get("name", title)
                    except Exception as e:
                        logger.warning(f"Could not fetch drive metadata for {file_id}: {e}")
                event_body["attachments"].append({"fileUrl": file_url, "title": title, "mimeType": mime_type})

            created = service.events().insert(calendarId=calendar_id, body=event_body, supportsAttachments=True, conferenceDataVersion=1 if add_google_meet else 0).execute()
        else:
            created = service.events().insert(calendarId=calendar_id, body=event_body, conferenceDataVersion=1 if add_google_meet else 0).execute()

        ev = {"id": created.get("id"), "summary": created.get("summary"), "htmlLink": created.get("htmlLink")}
        notes = ""
        if add_google_meet and created.get("conferenceData"):
            for ep in created.get("conferenceData", {}).get("entryPoints", []):
                if ep.get("entryPointType") == "video":
                    notes = f"meet:{ep.get('uri')}"
                    break
        return {"status": "ok", "data": {"event": ev}, "meta": {"notes": notes}}
    except HttpError as e:
        return {"status": "error", "message": "Google Calendar API error creating event", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error creating event", "details": str(e)}


def modify_event(
    user_id: int,
    event_id: str,
    calendar_id: str = "primary",
    summary: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    timezone: Optional[str] = None,
    add_google_meet: Optional[bool] = None,
    reminders: Optional[Union[str, List[Dict[str, Any]]]] = None,
    use_default_reminders: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Modify an existing event. Returns updated event id and link.
    """
    try:
        service, _ = _build_calendar_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Calendar service", "details": str(e)}

    try:
        event_body: Dict[str, Any] = {}
        if summary is not None:
            event_body["summary"] = summary
        if start_time is not None:
            event_body["start"] = ({"date": start_time} if "T" not in start_time else {"dateTime": start_time})
            if timezone and "dateTime" in event_body["start"]:
                event_body["start"]["timeZone"] = timezone
        if end_time is not None:
            event_body["end"] = ({"date": end_time} if "T" not in end_time else {"dateTime": end_time})
            if timezone and "dateTime" in event_body["end"]:
                event_body["end"]["timeZone"] = timezone
        if description is not None:
            event_body["description"] = description
        if location is not None:
            event_body["location"] = location
        if attendees is not None:
            event_body["attendees"] = [{"email": e} for e in attendees]

        if reminders is not None or use_default_reminders is not None:
            reminder_data = {}
            if use_default_reminders is not None:
                reminder_data["useDefault"] = use_default_reminders
            else:
                try:
                    existing_event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
                    reminder_data["useDefault"] = existing_event.get("reminders", {}).get("useDefault", True)
                except Exception:
                    reminder_data["useDefault"] = True
            if reminders is not None:
                validated = _parse_reminders_json(reminders, "modify_event")
                if validated:
                    reminder_data["overrides"] = validated
                else:
                    pass
            event_body["reminders"] = reminder_data

        if add_google_meet is not None:
            if add_google_meet:
                request_id = str(uuid.uuid4())
                event_body["conferenceData"] = {"createRequest": {"requestId": request_id, "conferenceSolutionKey": {"type": "hangoutsMeet"}}}
            else:
                event_body["conferenceData"] = {}

        if not event_body:
            return {"status": "error", "message": "No fields provided to modify", "details": ""}

        updated = service.events().patch(calendarId=calendar_id, eventId=event_id, body=event_body, conferenceDataVersion=1).execute()
        ev = {"id": updated.get("id"), "summary": updated.get("summary"), "htmlLink": updated.get("htmlLink")}
        notes = ""
        if add_google_meet:
            for ep in updated.get("conferenceData", {}).get("entryPoints", []):
                if ep.get("entryPointType") == "video":
                    notes = f"meet:{ep.get('uri')}"
                    break
        return {"status": "ok", "data": {"event": ev}, "meta": {"notes": notes}}
    except HttpError as e:
        if getattr(e, "resp", None) and getattr(e.resp, "status", None) == 404:
            return {"status": "error", "message": "Event not found", "details": str(e)}
        return {"status": "error", "message": "Google Calendar API error modifying event", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error modifying event", "details": str(e)}


def delete_event(user_id: int, event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
    """
    Delete an event.
    """
    try:
        service, _ = _build_calendar_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Calendar service", "details": str(e)}
    try:
        try:
            service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        except HttpError as ge:
            if getattr(ge, "resp", None) and getattr(ge.resp, "status", None) == 404:
                return {"status": "error", "message": "Event not found", "details": str(ge)}
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {"status": "ok", "data": {"event_id": event_id}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google Calendar API error deleting event", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error deleting event", "details": str(e)}
