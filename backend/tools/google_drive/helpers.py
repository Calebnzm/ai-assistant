import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def check_public_link_permission(permissions: List[Dict[str, Any]]) -> bool:
    """
    Return True if any permission object indicates 'anyone with the link'
    with a reader/writer/commenter role.
    """
    if not permissions:
        return False
    try:
        for p in permissions:
            if p.get("type") == "anyone" and p.get("role") in {"reader", "writer", "commenter"}:
                return True
    except Exception as e:
        logger.warning(f"[check_public_link_permission] failed to evaluate permissions: {e}")
    return False


def format_public_sharing_error(file_name: str, file_id: str) -> str:
    """
    Friendly message for files that are not publicly shared.
    """
    return (
        f"❌ Permission Error: '{file_name}' not shared publicly. "
        f"Set 'Anyone with the link' → 'Viewer' in Google Drive sharing. "
        f"File link: https://drive.google.com/file/d/{file_id}/view"
    )


def get_drive_image_url(file_id: str) -> str:
    """
    Return an embeddable Drive image URL for a publicly shared Drive file.
    """
    return f"https://drive.google.com/uc?export=view&id={file_id}"


DRIVE_QUERY_PATTERNS = [
    re.compile(r"\b\w+\s*(=|!=|>|<)\s*['\"].+?['\"]", re.IGNORECASE),   
    re.compile(r"\b\w+\s*(=|!=|>|<)\s*\d+", re.IGNORECASE),          
    re.compile(r"\bcontains\b", re.IGNORECASE),                       
    re.compile(r"\bin\s+parents\b", re.IGNORECASE),                   
    re.compile(r"\bhas\s*\{", re.IGNORECASE),                          
    re.compile(r"\btrashed\s*=\s*(true|false)\b", re.IGNORECASE),
    re.compile(r"\bstarred\s*=\s*(true|false)\b", re.IGNORECASE),
    re.compile(r"[\'\"][^\'\"]+[\'\"]\s+in\s+parents", re.IGNORECASE),
    re.compile(r"\bfullText\s+contains\b", re.IGNORECASE),
    re.compile(r"\bname\s*(=|contains)\b", re.IGNORECASE),
    re.compile(r"\bmimeType\s*(=|!=)\b", re.IGNORECASE),
]


def build_drive_list_params(
    query: str,
    page_size: int,
    drive_id: Optional[str] = None,
    include_items_from_all_drives: bool = True,
    corpora: Optional[str] = None,
    fields: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a dictionary of parameters for Drive `files().list()` calls.

    - query: Drive query string (already formatted)
    - page_size: max results
    - drive_id: optional shared drive id
    - include_items_from_all_drives: set True to include shared drives
    - corpora: optional corpora ('user', 'drive', 'domain', 'allDrives')
    - fields: optional `fields` parameter (defaults to a safe set)

    Returns dict suitable to be passed to `service.files().list(**params)`
    """
    if fields is None:
        fields = "nextPageToken, files(id, name, mimeType, webViewLink, iconLink, modifiedTime, size)"

    params: Dict[str, Any] = {
        "q": query,
        "pageSize": page_size,
        "fields": fields,
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": include_items_from_all_drives,
    }

    if drive_id:
        params["driveId"] = drive_id
        params["corpora"] = corpora if corpora else "drive"
    elif corpora:
        params["corpora"] = corpora

    return params
