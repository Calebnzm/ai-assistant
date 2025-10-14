from .in_house_tools import list_activity, create_activity, edit_activity, delete_activity, search_activities
from .gmail_tools import search_gmail_messages, get_gmail_message_content, get_gmail_messages_content_batch, get_gmail_thread_content, get_gmail_threads_content_batch, list_gmail_labels, manage_gmail_label, modify_gmail_message_labels, batch_modify_gmail_message_labels, send_gmail_message, draft_gmail_message
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
    "draft_gmail_message": draft_gmail_message
}