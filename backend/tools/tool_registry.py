from .in_house_tools import list_activity, create_activity, edit_activity, delete_activity, search_activities
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
        }
    ]

TOOL_REGISTRY = {
    "list_activity": list_activity,
    "create_activity": create_activity,
    "edit_task": edit_activity,
    "delete_activity": delete_activity,
    "search_activities": search_activities  
}