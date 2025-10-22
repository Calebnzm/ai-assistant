from .in_house_tools import list_activity, create_activity, edit_activity, delete_activity, search_activities, bot_send_message, complete
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

from .google_docs.tools import (
    search_docs,
    get_doc_content,
    list_docs_in_folder,
    create_doc,
    modify_doc_text,
    find_and_replace_doc,
    insert_doc_elements,
    insert_doc_image,
    update_doc_headers_footers,
    batch_update_doc,
    inspect_doc_structure,
    create_table_with_data,
    debug_table_structure,
    export_doc_to_pdf
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
from typing import List, Dict, Callable, Any



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

        {
            "name": "list_calendars",
            "description": "List calendars the user has access to. Returns id, summary, primary flag and timezone.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },

        {
            "name": "get_events",
            "description": "Get events from a calendar. Provide either event_id (single event) or time_min/time_max and optional query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (default 'primary')."
                    },
                    "event_id": {
                        "type": "string",
                        "description": "Specific event ID to fetch (when provided, time range and query are ignored)."
                    },
                    "time_min": {
                        "type": "string",
                        "description": "Start of time range (RFC3339 or YYYY-MM-DD)."
                    },
                    "time_max": {
                        "type": "string",
                        "description": "End of time range (RFC3339 or YYYY-MM-DD)."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max number of events to return (default 25)."
                    },
                    "query": {
                        "type": "string",
                        "description": "Keyword to search within events (summary/description/location)."
                    },
                    "detailed": {
                        "type": "boolean",
                        "description": "Whether to return detailed event fields (description, attendees, raw)."
                    }
                },
                "required": []
            }
        },

        {
            "name": "create_event",
            "description": "Create an event. Required: summary, start_time, end_time. Accepts attendees, reminders, attachments, timezone, and optional Google Meet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (default 'primary')."
                    },
                    "summary": {
                        "type": "string",
                        "description": "Event title."
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time (RFC3339 like 2023-10-27T10:00:00Z or YYYY-MM-DD for all-day)."
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time (RFC3339 or YYYY-MM-DD for all-day)."
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description."
                    },
                    "location": {
                        "type": "string",
                        "description": "Event location."
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses."
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (e.g., 'America/New_York')."
                    },
                    "attachments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Drive URLs or file IDs to attach (optional)."
                    },
                    "add_google_meet": {
                        "type": "boolean",
                        "description": "If true, add a Google Meet conference."
                    },
                    "reminders": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "method": {
                                    "type": "string",
                                    "enum": ["popup", "email"],
                                    "description": "Reminder method: 'popup' or 'email'."
                                },
                                "minutes": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 40320,
                                    "description": "Minutes before the event."
                                }
                            },
                            "required": ["method", "minutes"]
                        },
                        "description": "List of reminder objects. Each: {method:'popup'|'email', minutes:int}. Max 5 recommended."
                    },
                    "use_default_reminders": {
                        "type": "boolean",
                        "description": "Whether to use calendar default reminders (true/false)."
                    }
                },
                "required": ["summary", "start_time", "end_time"]
            }
        },

        {
            "name": "modify_event",
            "description": "Modify event fields. Provide event_id and any fields to update (summary, start_time, end_time, etc).",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "ID of the event to modify."
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (default 'primary')."
                    },
                    "summary": {
                        "type": "string",
                        "description": "New event title."
                    },
                    "start_time": {
                        "type": "string",
                        "description": "New start time (RFC3339 or YYYY-MM-DD)."
                    },
                    "end_time": {
                        "type": "string",
                        "description": "New end time (RFC3339 or YYYY-MM-DD)."
                    },
                    "description": {
                        "type": "string",
                        "description": "New description."
                    },
                    "location": {
                        "type": "string",
                        "description": "New location."
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses (replaces existing if provided)."
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone to apply to provided dateTimes."
                    },
                    "add_google_meet": {
                        "type": "boolean",
                        "description": "True to add meet, false to remove, omit to leave unchanged."
                    },
                    "reminders": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "method": {
                                    "type": "string",
                                    "enum": ["popup", "email"],
                                    "description": "Reminder method: 'popup' or 'email'."
                                },
                                "minutes": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 40320,
                                    "description": "Minutes before the event."
                                }
                            },
                            "required": ["method", "minutes"]
                        },
                        "description": "List of reminder objects to replace existing reminders."
                    },
                    "use_default_reminders": {
                        "type": "boolean",
                        "description": "Whether to use calendar default reminders (true/false)."
                    }
                },
                "required": ["event_id"]
            }
        },

        {
            "name": "delete_event",
            "description": "Delete an event. Provide event_id and optional calendar_id (default 'primary').",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "ID of the event to delete."
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (default 'primary')."
                    }
                },
                "required": ["event_id"]
            }
        },

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

        {
            "name": "search_docs",
            "description": "Search Google Docs by name (Drive query). Returns list of docs with id, name, createdTime, modifiedTime and webViewLink.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Substring to search in document name."},
                    "page_size": {"type": "integer", "description": "Maximum number of documents to return (default 10)."},
                },
                "required": ["query"]
            }
        },

        {
            "name": "get_doc_content",
            "description": "Get document content by ID. Supports native Google Docs (via Docs API) and Office files stored in Drive (downloads and extracts text). Returns content with a header including file metadata and webViewLink.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Drive/Docs file ID to fetch content for."}
                },
                "required": ["document_id"]
            }
        },

        {
            "name": "list_docs_in_folder",
            "description": "List Google Docs within a specific Drive folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_id": {"type": "string", "description": "Folder ID to list (default 'root')."},
                    "page_size": {"type": "integer", "description": "Maximum number of docs to return (default 100)."}
                },
                "required": []
            }
        },

        {
            "name": "create_doc",
            "description": "Create a new Google Doc. Optionally provide initial content to insert.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title for the new document."},
                    "content": {"type": "string", "description": "Optional initial content (text) to insert into the new document."}
                },
                "required": ["title"]
            }
        },

        {
            "name": "modify_doc_text",
            "description": "Insert or replace text and/or apply formatting in a Google Doc. Can do insert, replace, and apply text style (bold/italic/underline/font size/family).",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to modify."},
                    "start_index": {"type": "integer", "description": "Start index for operation (0-based)."},
                    "end_index": {"type": "integer", "description": "End index for replacement/formatting (required for formatting or replace operations)."},
                    "text": {"type": "string", "description": "Text to insert or replace with."},
                    "bold": {"type": "boolean", "description": "Set bold on range/inserted text."},
                    "italic": {"type": "boolean", "description": "Set italic on range/inserted text."},
                    "underline": {"type": "boolean", "description": "Set underline on range/inserted text."},
                    "font_size": {"type": "integer", "description": "Font size in points."},
                    "font_family": {"type": "string", "description": "Font family name (e.g., 'Arial')."}
                },
                "required": ["document_id", "start_index"]
            }
        },

        {
            "name": "find_and_replace_doc",
            "description": "Find and replace text across a Google Doc using replaceAllText.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to operate on."},
                    "find_text": {"type": "string", "description": "Text to find."},
                    "replace_text": {"type": "string", "description": "Text to replace with."},
                    "match_case": {"type": "boolean", "description": "Whether to match case exactly (default false)."}
                },
                "required": ["document_id", "find_text", "replace_text"]
            }
        },

        {
            "name": "insert_doc_elements",
            "description": "Insert structural elements into a document: table, list, or page break. For tables provide rows and columns. For lists provide list_type and optional text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to update."},
                    "element_type": {"type": "string", "description": "Element type: 'table', 'list', or 'page_break'."},
                    "index": {"type": "integer", "description": "Insertion index (0-based; use inspect_doc_structure to get safe index)."},
                    "rows": {"type": "integer", "description": "Number of rows (required for 'table')."},
                    "columns": {"type": "integer", "description": "Number of columns (required for 'table')."},
                    "list_type": {"type": "string", "description": "List type ('UNORDERED' or 'ORDERED' - required for 'list')."},
                    "text": {"type": "string", "description": "Initial text for list item(s)."}
                },
                "required": ["document_id", "element_type", "index"]
            }
        },

        {
            "name": "insert_doc_image",
            "description": "Insert an image into a document from a Drive file ID or a public URL. If a Drive ID is provided the file will be validated to be an image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to update."},
                    "image_source": {"type": "string", "description": "Drive file ID or public image URL."},
                    "index": {"type": "integer", "description": "Insertion index (0-based)."},
                    "width": {"type": "integer", "description": "Optional width in points."},
                    "height": {"type": "integer", "description": "Optional height in points."}
                },
                "required": ["document_id", "image_source", "index"]
            }
        },

        {
            "name": "update_doc_headers_footers",
            "description": "Update header or footer content in a Google Doc. Supports types: DEFAULT, FIRST_PAGE_ONLY, EVEN_PAGE.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to modify."},
                    "section_type": {"type": "string", "description": "Either 'header' or 'footer'."},
                    "content": {"type": "string", "description": "Text content to set in header/footer."},
                    "header_footer_type": {"type": "string", "description": "Header/footer type ('DEFAULT', 'FIRST_PAGE_ONLY', 'EVEN_PAGE')."}
                },
                "required": ["document_id", "section_type", "content"]
            }
        },

        {
            "name": "batch_update_doc",
            "description": "Execute multiple document operations in a single atomic batch. Operations are validated and translated to Docs API requests by the batch manager.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to update."},
                    "operations": {"type": "array", "items": {"type": "object"}, "description": "List of operation objects (insert_text, delete_text, replace_text, format_text, insert_table, insert_page_break, find_replace)."}
                },
                "required": ["document_id", "operations"]
            }
        },

        {
            "name": "inspect_doc_structure",
            "description": "Analyze document structure to find safe insertion points, table positions and document statistics. Use this before creating tables to get 'total_length'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to inspect."},
                    "detailed": {"type": "boolean", "description": "Return detailed parsed structure (headers, footers, element list) if true."}
                },
                "required": ["document_id"]
            }
        },

        {
            "name": "create_table_with_data",
            "description": "Create a table at a safe index and populate it with the provided 2D list of strings. MANDATORY: call inspect_doc_structure first and use its 'total_length' value for index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to update."},
                    "table_data": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "2D list of strings: first row may be headers."},
                    "index": {"type": "integer", "description": "Safe insertion index (use inspect_doc_structure)."},
                    "bold_headers": {"type": "boolean", "description": "Whether to bold the first row (default true)."}
                },
                "required": ["document_id", "table_data", "index"]
            }
        },

        {
            "name": "debug_table_structure",
            "description": "Return detailed structure of a specific table (dimensions, each cell's indices, insertion indices and current content). Useful for debugging table population issues.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to inspect."},
                    "table_index": {"type": "integer", "description": "Which table to debug (0 = first)."}
                },
                "required": ["document_id"]
            }
        },

        {
            "name": "export_doc_to_pdf",
            "description": "Export a native Google Doc to PDF and save the resulting PDF to Drive (optionally into a given folder). Returns created PDF file id and web link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to export."},
                    "pdf_filename": {"type": "string", "description": "Optional filename for the PDF (will get .pdf if not present)."},
                    "folder_id": {"type": "string", "description": "Optional Drive folder ID to save the PDF into."}
                },
                "required": ["document_id"]
            }
        },
        {
            "name": "init_conversation",
            "description": "Initiates a conversation with the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message text to send to the user via Telegram."
                    }
                },
                "required": ["message"]
            }
        },
        {
            "name": "complete",
            "description":"Call this tool when you complete your task.",
            "parameters": {
                "type": "object",
                "properties":{},
                "required" : []
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
    "search_docs": search_docs,
    "get_doc_content": get_doc_content,
    "list_docs_in_folder": list_docs_in_folder,
    "create_doc": create_doc,
    "modify_doc_text": modify_doc_text,
    "find_and_replace_doc": find_and_replace_doc,
    "insert_doc_elements": insert_doc_elements,
    "insert_doc_image": insert_doc_image,
    "update_doc_headers_footers": update_doc_headers_footers,
    "batch_update_doc": batch_update_doc,
    "inspect_doc_structure": inspect_doc_structure,
    "create_table_with_data": create_table_with_data,
    "debug_table_structure": debug_table_structure,
    "export_doc_to_pdf": export_doc_to_pdf,
    "init_conversation": bot_send_message,
    "complete": complete
}



TOOL_CONFIG = {
    "core": {
        "in_app": [
            "create_activity",
            "list_activity",
            "edit_activity",
            "delete_activity",
            "search_activities",
        ],
        "gmail": [
            "search_gmail_messages", 
            "send_gmail_message",
            "get_gmail_message_content"
        ],
        "calendar": [
            "get_events", 
            "create_event"
        ],
        "google_drive": [
            "search_drive_files",
            "get_drive_file_content"
        ],
        "google_docs": [
            "search_docs", 
            "create_doc", 
            "get_doc_content"
        ],
    },
    "complete": {
        "in_app": [
            "create_activity",
            "list_activity",
            "edit_activity",
            "delete_activity",
            "search_activities",
            "init_conversation",
            "complete"
        ],
        "gmail": [
            "search_gmail_messages",
            "send_gmail_message",
            "get_gmail_message_content",
            "draft_gmail_message",
            "modify_gmail_message_labels",
            "list_gmail_labels",
            "get_gmail_messages_content_batch",
            "get_gmail_thread_content",
            "get_gmail_threads_content_batch",
            "manage_gmail_label",
            "batch_modify_gmail_message_labels",
        ],
        "calendar": [
            "get_events",
            "create_event",
            "modify_event",
            "delete_event",
            "list_calendars"
        ],
        "google_drive": [
            "search_drive_files",
            "get_drive_file_content",
            "create_drive_file",
            "list_drive_items",
            "get_drive_file_permissions",
            "check_drive_file_public_access",
        ],
        "google_docs": [
            "search_docs",
            "create_doc",
            "get_doc_content",
            "modify_doc_text",
            "find_and_replace_doc",
            "export_doc_to_pdf",
            "list_docs_in_folder",
            "insert_doc_elements",
            "insert_doc_image",
            "update_doc_headers_footers",
            "batch_update_doc",
            "inspect_doc_structure",
            "create_table_with_data",
            "debug_table_structure",
        ],
    }
}

def get_tool_names(tier: str, services: List[str]) -> List[str]:
    "Gets the list of tool names based on the tier and services."
    if tier not in TOOL_CONFIG:
        raise ValueError(f"Invalid tier: {tier}. Available tiers are {list(TOOL_CONFIG.keys())}")

    selected_tool_names = set()
    tier_config = TOOL_CONFIG[tier]

    for service in services:
        if service in tier_config:
            selected_tool_names.update(tier_config[service])
    
    return list(selected_tool_names)


def fetch_tools(tier: str, services: List[str]) -> Dict[str, Callable]:
    "Fetches the actual tool functions from the TOOL_REGISTRY."
    tool_names = get_tool_names(tier, services)
    return {name: TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY}


def fetch_schemas(tier: str, services: List[str]) -> List[Dict[str, Any]]:
    "Fetches the tool schemas from the TOOL_SCHEMAS list."
    tool_names = get_tool_names(tier, services)
    return [schema for schema in TOOL_SCHEMAS if schema['name'] in tool_names]