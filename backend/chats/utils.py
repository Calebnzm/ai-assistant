import requests

MCP_BASE_URL = "http://localhost:8001/mcp"
USER_EMAIL = "calebnzioka2027@gmail.com"

def call_mcp_tool(tool_endpoint: str, params: dict = None):
    """
    Call an MCP tool endpoint for a specific user.
    """
    if params is None:
        params = {}
    # Include the user email to identify the session
    params["user"] = USER_EMAIL
    url = f"{MCP_BASE_URL}/{tool_endpoint}"
    response = requests.get(url, params=params)
    response.raise_for_status()  # Raise error if MCP returns 4xx/5xx
    return response.json()

# --- Gmail Example ---
labels = call_mcp_tool("gmail/list_labels")
print("Gmail Labels:", labels)

# --- Drive Example ---
files = call_mcp_tool("drive/list_files")
print("Drive Files:", files)

# --- Calendar Example ---
events = call_mcp_tool("calendar/list_events", params={"maxResults": 5})
print("Upcoming Events:", events)
