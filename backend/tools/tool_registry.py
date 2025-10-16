from .in_house_tools import list_activity, create_activity, edit_activity, delete_activity, search_activities
from .gmail_tools import (
    search_gmail_messages,
    get_gmail_message_content,
    get_gmail_messages_content_batch,
    get_gmail_thread_content,
    get_gmail_threads_content_batch,
    list_gmail_labels,
    manage_gmail_label,
    modify_gmail_message_labels,
    batch_modify_gmail_message_labels,
    send_gmail_message,
    draft_gmail_message,
)
from .calendar_tools import create_event, modify_event, delete_event, list_calendars, get_events
from .google_drive.tools import (
    search_drive_files,
    get_drive_file_content,
    list_drive_items,
    create_drive_file,
    get_drive_file_permissions,
    check_drive_file_public_access,
)
from google.generativeai import types

TOOL_SCHEMAS = [
        {
            "name": "list_activity",
            "description":"Retrieves a list of tasks that were created or are due within a specific range. Dates must be in YYYY-MM-DD format.",
            "parameters": {
                "type": "object",
                "properties":{
                    "start_date_str": { "type": "string", "description": "The start date of the range, formatted as YYYY-MM-DD."},
                    "end_date_str": { "type": "string", "description": "The end date of the range, formatted as YYYY-MM-DD."}
                },
                "required" : ["start_date_str", "end_date_str"]
            }
        },
        {
            "name": "delete_activity",
            "description":"Deletes a specific activity",
            "parameters": {
                "type": "object",
                "properties":{
                    "task_id": {"type": "integer", "description": "The unique ID of the task to edit."},
                },
                "required" : ["task_id"]
            }
        },
        {
            "name": "search_activities",
            "description":"Searches for an activity based on a search phrase",
            "parameters": {
                "type": "object",
                "properties":{
                    "search_phrase": {"type": "string", "description": "The search phrase to search the activity with"},
                },
                "required" : ["search_phrase"]
            }
        },
        { 
            "name": "edit_activity",
            "description": "Edits an existing task. The user must provide the task ID and one or more fields to update.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The unique ID of the task to edit."},
                    "title": {"type": "string", "description": "The new title for the activity."},
                    "description": {"type": "string", "description": "The new description for the activity."},
                    "type": {"type": "string", "description": "The new type for the activity.", "enum": ["project", "task", "habit"]},
                    "priority": {"type": "string", "description": "The new priority for the activity.", "enum": ["low", "medium", "high"]},
                    "due_date": {"type": "string", "description": "The new due date, formatted as 'YYYY-MM-DD'."},
                    "tags": {"type": "string", "description": "The new list of tags for the activity."}
                },
                "required": ["task_id"] 
            }
        },
        {
            "name": "create_activity",
            "description": "Creates a new activity for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title for the activity. It should be descriptive. To be understood at a glance."},
                    "description": {"type": "string", "description": "Should contain the details of what should be done or accomplished for the activity"},
                    "type": {"type": "string", "description": "The type of the activity. Should be either 'project', 'task', or 'habit', based on the nature of the activity.", "enum": ["project", "task", "habit"] },
                    "priority": {"type": "string", "description": "Should be either 'high', 'medium' or 'low'. Reflecting the importance of the activity", "enum": ["low", "medium", "high"] },
                    "due_date_str": {"type": "string", "description": "Should be a date string of the format: 'YYYY-MM-DD' representing when the activity should be completed"},
                    "tags": {
                        "type": "string",
                        "description": "A list of comma seperated themes for the activity. Each tag should be a single word.",
                    }
                },
                "required": ["title", "description", "type", "priority", "due_date_str", "tags"]
            }
        },
        {
            "name": "search_gmail_messages",
            "description": "Search the user's Gmail using Gmail query syntax and return a small list of message metadata (id, threadId, subject, from, snippet, web_url).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Gmail search query (Gmail search operators allowed)."},
                    "page_size": {"type": "integer", "description": "Max number of messages to return (default 10)."}
                },
                "required": ["query"]
            }
        },

        {
            "name": "get_gmail_message_content",
            "description": "Fetch subject, sender and a readable body (text/plain fallback to HTML) for a single Gmail message id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Gmail message ID."}
                },
                "required": ["message_id"]
            }
        },
        {
            "name": "get_gmail_messages_content_batch",
            "description": "Retrieve contents for multiple Gmail message IDs. Returns array of {id, subject, from, body, web_url}.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Gmail message IDs (max 25 recommended)."
                    },
                    "format": {"type":"string","enum":["full","metadata"],"description":"'full' includes body; 'metadata' only headers."}
                },
                "required": ["message_ids"]
            }
        },

        {
            "name": "get_gmail_thread_content",
            "description": "Retrieve the whole conversation thread for a given Gmail thread ID. Returns ordered messages with headers and bodies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string"}
                },
                "required": ["thread_id"]
            }
        },
        {
            "name": "get_gmail_threads_content_batch",
            "description": "Retrieve multiple Gmail threads in batch. Returns array of thread objects (id, subject, messages[]).",
            "parameters": {
                "type": "object",
                "properties": {
                    "thread_ids": {"type":"array","items":{"type":"string"}}
                },
                "required": ["thread_ids"]
            }
        },

        {
            "name": "list_gmail_labels",
            "description": "List all Gmail labels (system and user) with id and name.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },

        {
            "name": "manage_gmail_label",
            "description": "Create, update or delete a Gmail label.",
            "parameters": {
                "type":"object",
                "properties":{
                    "action": {"type":"string","enum":["create","update","delete"]},
                    "name": {"type":"string"},
                    "label_id": {"type":"string"},
                    "label_list_visibility": {"type":"string","enum":["labelShow","labelHide"]},
                    "message_list_visibility": {"type":"string","enum":["show","hide"]}
                },
                "required": ["action"]
            }
        },

        {
            "name": "modify_gmail_message_labels",
            "description": "Add/remove labels on a single Gmail message.",
            "parameters": {
                "type":"object",
                "properties": {
                    "message_id": {"type":"string"},
                    "add_label_ids": {"type":"array","items":{"type":"string"}},
                    "remove_label_ids": {"type":"array","items":{"type":"string"}}
                },
                "required": ["message_id"]
            }
        },

        {
            "name": "batch_modify_gmail_message_labels",
            "description": "Add/remove labels on many Gmail messages at once.",
            "parameters": {
                "type":"object",
                "properties": {
                    "message_ids": {"type":"array","items":{"type":"string"}},
                    "add_label_ids": {"type":"array","items":{"type":"string"}},
                    "remove_label_ids": {"type":"array","items":{"type":"string"}}
                },
                "required": ["message_ids"]
            }
        },

        {
            "name": "send_gmail_message",
            "description": "Send an email from the user's Gmail account (supports replies/threading). Returns sent message id.",
            "parameters": {
                "type":"object",
                "properties": {
                    "to": {"type":"string"},
                    "subject": {"type":"string"},
                    "body": {"type":"string"},
                    "cc": {"type":"string"},
                    "bcc": {"type":"string"},
                    "thread_id": {"type":"string"},
                    "in_reply_to": {"type":"string"},
                    "references": {"type":"string"}
                },
                "required": ["to","subject","body"]
            }
        },

        {
            "name": "draft_gmail_message",
            "description": "Create a draft in the user's Gmail account. Returns draft id.",
            "parameters": {
                "type":"object",
                "properties": {
                    "subject": {"type":"string"},
                    "body": {"type":"string"},
                    "to": {"type":"string"},
                    "cc": {"type":"string"},
                    "bcc": {"type":"string"},
                    "thread_id": {"type":"string"},
                    "in_reply_to": {"type":"string"},
                    "references": {"type":"string"}
                },
                "required": ["subject","body"]
            }
        },

        # {
        #     "name": "list_calendars",
        #     "description": "List calendars the user has access to. Returns id, summary, primary flag and timezone.",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {},
        #         "required": []
        #     }
        # },

        # {
        #     "name": "get_events",
        #     "description": "Get events from a calendar. Provide either event_id (single event) or time_min/time_max and optional query.",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "calendar_id": {
        #                 "type": "string",
        #                 "description": "Calendar ID (default 'primary')."
        #             },
        #             "event_id": {
        #                 "type": "string",
        #                 "description": "Specific event ID to fetch (when provided, time range and query are ignored)."
        #             },
        #             "time_min": {
        #                 "type": "string",
        #                 "description": "Start of time range (RFC3339 or YYYY-MM-DD)."
        #             },
        #             "time_max": {
        #                 "type": "string",
        #                 "description": "End of time range (RFC3339 or YYYY-MM-DD)."
        #             },
        #             "max_results": {
        #                 "type": "integer",
        #                 "description": "Max number of events to return (default 25)."
        #             },
        #             "query": {
        #                 "type": "string",
        #                 "description": "Keyword to search within events (summary/description/location)."
        #             },
        #             "detailed": {
        #                 "type": "boolean",
        #                 "description": "Whether to return detailed event fields (description, attendees, raw)."
        #             }
        #         },
        #         "required": []
        #     }
        # },

        # {
        #     "name": "create_event",
        #     "description": "Create an event. Required: summary, start_time, end_time. Accepts attendees, reminders, attachments, timezone, and optional Google Meet.",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "calendar_id": {
        #                 "type": "string",
        #                 "description": "Calendar ID (default 'primary')."
        #             },
        #             "summary": {
        #                 "type": "string",
        #                 "description": "Event title."
        #             },
        #             "start_time": {
        #                 "type": "string",
        #                 "description": "Start time (RFC3339 like 2023-10-27T10:00:00Z or YYYY-MM-DD for all-day)."
        #             },
        #             "end_time": {
        #                 "type": "string",
        #                 "description": "End time (RFC3339 or YYYY-MM-DD for all-day)."
        #             },
        #             "description": {
        #                 "type": "string",
        #                 "description": "Event description."
        #             },
        #             "location": {
        #                 "type": "string",
        #                 "description": "Event location."
        #             },
        #             "attendees": {
        #                 "type": "array",
        #                 "items": {"type": "string"},
        #                 "description": "List of attendee email addresses."
        #             },
        #             "timezone": {
        #                 "type": "string",
        #                 "description": "Timezone (e.g., 'America/New_York')."
        #             },
        #             "attachments": {
        #                 "type": "array",
        #                 "items": {"type": "string"},
        #                 "description": "Drive URLs or file IDs to attach (optional)."
        #             },
        #             "add_google_meet": {
        #                 "type": "boolean",
        #                 "description": "If true, add a Google Meet conference."
        #             },
        #             "reminders": {
        #                 "type": "array",
        #                 "items": {
        #                     "type": "object",
        #                     "properties": {
        #                         "method": {
        #                             "type": "string",
        #                             "enum": ["popup", "email"],
        #                             "description": "Reminder method: 'popup' or 'email'."
        #                         },
        #                         "minutes": {
        #                             "type": "integer",
        #                             "minimum": 0,
        #                             "maximum": 40320,
        #                             "description": "Minutes before the event."
        #                         }
        #                     },
        #                     "required": ["method", "minutes"]
        #                 },
        #                 "description": "List of reminder objects. Each: {method:'popup'|'email', minutes:int}. Max 5 recommended."
        #             },
        #             "use_default_reminders": {
        #                 "type": "boolean",
        #                 "description": "Whether to use calendar default reminders (true/false)."
        #             }
        #         },
        #         "required": ["summary", "start_time", "end_time"]
        #     }
        # },

        # {
        #     "name": "modify_event",
        #     "description": "Modify event fields. Provide event_id and any fields to update (summary, start_time, end_time, etc).",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "event_id": {
        #                 "type": "string",
        #                 "description": "ID of the event to modify."
        #             },
        #             "calendar_id": {
        #                 "type": "string",
        #                 "description": "Calendar ID (default 'primary')."
        #             },
        #             "summary": {
        #                 "type": "string",
        #                 "description": "New event title."
        #             },
        #             "start_time": {
        #                 "type": "string",
        #                 "description": "New start time (RFC3339 or YYYY-MM-DD)."
        #             },
        #             "end_time": {
        #                 "type": "string",
        #                 "description": "New end time (RFC3339 or YYYY-MM-DD)."
        #             },
        #             "description": {
        #                 "type": "string",
        #                 "description": "New description."
        #             },
        #             "location": {
        #                 "type": "string",
        #                 "description": "New location."
        #             },
        #             "attendees": {
        #                 "type": "array",
        #                 "items": {"type": "string"},
        #                 "description": "List of attendee email addresses (replaces existing if provided)."
        #             },
        #             "timezone": {
        #                 "type": "string",
        #                 "description": "Timezone to apply to provided dateTimes."
        #             },
        #             "add_google_meet": {
        #                 "type": "boolean",
        #                 "description": "True to add meet, false to remove, omit to leave unchanged."
        #             },
        #             "reminders": {
        #                 "type": "array",
        #                 "items": {
        #                     "type": "object",
        #                     "properties": {
        #                         "method": {
        #                             "type": "string",
        #                             "enum": ["popup", "email"],
        #                             "description": "Reminder method: 'popup' or 'email'."
        #                         },
        #                         "minutes": {
        #                             "type": "integer",
        #                             "minimum": 0,
        #                             "maximum": 40320,
        #                             "description": "Minutes before the event."
        #                         }
        #                     },
        #                     "required": ["method", "minutes"]
        #                 },
        #                 "description": "List of reminder objects to replace existing reminders."
        #             },
        #             "use_default_reminders": {
        #                 "type": "boolean",
        #                 "description": "Whether to use calendar default reminders (true/false)."
        #             }
        #         },
        #         "required": ["event_id"]
        #     }
        # },

        # {
        #     "name": "delete_event",
        #     "description": "Delete an event. Provide event_id and optional calendar_id (default 'primary').",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "event_id": {
        #                 "type": "string",
        #                 "description": "ID of the event to delete."
        #             },
        #             "calendar_id": {
        #                 "type": "string",
        #                 "description": "Calendar ID (default 'primary')."
        #             }
        #         },
        #         "required": ["event_id"]
        #     }
        # },

        {
            "name": "search_drive_files",
            "description": "Search files and folders in Google Drive using Drive query syntax or free text (wrapped in fullText). Returns list of files with id, name, mimeType, modifiedTime and webViewLink.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Drive query or free-text search (will be wrapped in fullText contains if needed)."},
                    "page_size": {"type": "integer", "description": "Maximum number of files to return (default 10)."},
                    "drive_id": {"type": "string", "description": "Optional shared drive ID to scope search to."},
                    "include_items_from_all_drives": {"type": "boolean", "description": "Whether to include items from all drives/shared drives."},
                    "corpora": {"type": "string", "description": "Optional corpora parameter ('user','drive','domain','allDrives')."}
                },
                "required": ["query"]
            }
        },

        {
            "name": "get_drive_file_content",
            "description": "Get file content by Drive file ID. Exports native Google files, extracts Office files, or downloads raw bytes and attempts UTF-8 decode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "Drive file ID to fetch content for."}
                },
                "required": ["file_id"]
            }
        },

        {
            "name": "list_drive_items",
            "description": "List items in a folder (supports shared drives).",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_id": {"type": "string", "description": "Folder ID to list (default 'root')."},
                    "page_size": {"type": "integer", "description": "Maximum items to return (default 100)."},
                    "drive_id": {"type": "string", "description": "Optional shared drive ID to scope listing."},
                    "include_items_from_all_drives": {"type": "boolean", "description": "Whether to include items from all drives/shared drives."},
                    "corpora": {"type": "string", "description": "Optional corpora parameter ('user','drive','domain','allDrives')."}
                },
                "required": []
            }
        },

        {
            "name": "create_drive_file",
            "description": "Create a file in Drive. Provide file_name and either content or fileUrl (server validates presence of content/fileUrl). Returns created file id and web link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "Name for the new file."},
                    "content": {"type": "string", "description": "Optional file content as text."},
                    "folder_id": {"type": "string", "description": "Parent folder ID (default 'root')."},
                    "mime_type": {"type": "string", "description": "MIME type of file (default 'text/plain')."},
                    "fileUrl": {"type": "string", "description": "Optional URL to fetch file contents from."}
                },
                "required": ["file_name"]
            }
        },

        {
            "name": "get_drive_file_permissions",
            "description": "Get a file's metadata and permissions, returning structured details about sharing and URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "Drive file ID."}
                },
                "required": ["file_id"]
            }
        },

        {
            "name": "check_drive_file_public_access",
            "description": "Search for file by name and check if 'Anyone with the link' public access is enabled.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "Name of the file to search for."}
                },
                "required": ["file_name"]
            }
        },
    ]

TOOL_REGISTRY = {
    "list_activity": list_activity,
    "create_activity": create_activity,
    "edit_activity": edit_activity,
    "delete_activity": delete_activity,
    "search_activities": search_activities,
    "search_gmail_messages": search_gmail_messages,
    "get_gmail_message_content": get_gmail_message_content,
    "get_gmail_messages_content_batch": get_gmail_messages_content_batch,
    "get_gmail_thread_content": get_gmail_thread_content,
    "get_gmail_threads_content_batch": get_gmail_threads_content_batch,
    "list_gmail_labels": list_gmail_labels,
    "manage_gmail_label": manage_gmail_label,
    "modify_gmail_message_labels": modify_gmail_message_labels,
    "batch_modify_gmail_message_labels": batch_modify_gmail_message_labels,
    "send_gmail_message": send_gmail_message,
    "draft_gmail_message": draft_gmail_message,
    "list_calendars": list_calendars,
    "get_events": get_events,
    "create_event": create_event,
    "modify_event": modify_event,
    "delete_event": delete_event,
    "search_drive_files": search_drive_files,
    "get_drive_file_content": get_drive_file_content,
    "list_drive_items": list_drive_items,
    "create_drive_file": create_drive_file,
    "get_drive_file_permissions": get_drive_file_permissions,
    "check_drive_file_public_access": check_drive_file_public_access,
}