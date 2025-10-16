import logging
import io
import re
from typing import List, Optional, Dict, Any

from django.contrib.auth import get_user_model
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import httpx

from GoogleAuth.utils import get_credentials_for_user
from .helpers import DRIVE_QUERY_PATTERNS, build_drive_list_params, check_public_link_permission, get_drive_image_url
from tools.core_utils import extract_office_xml_text 

User = get_user_model()


def _extract_drive_file_id(url_or_id: str) -> Optional[str]:
    if not url_or_id:
        return None
    if url_or_id.startswith("http"):
        match = re.search(r"(?:/d/|/file/d/|id=)([a-zA-Z0-9_-]+)", url_or_id)
        return match.group(1) if match else None
    return url_or_id


def _build_drive_service_for_user(user_id: int):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ValueError("User not found")
    creds = get_credentials_for_user(user)
    if not creds:
        raise ValueError("No Google credentials for user. Kindly ask the user to authorize from their profile page.")
    try:
        service = build("drive", "v3", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Failed to build Drive service: {e}")
    return service, creds


def search_drive_files(
    user_id: int,
    query: str,
    page_size: int = 10,
    drive_id: Optional[str] = None,
    include_items_from_all_drives: bool = True,
    corpora: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns: {"status":"ok","data":{"files":[{id,name,mimeType,size,modifiedTime,webViewLink}]}, "meta":{"count":N}}
    """
    try:
        service, _ = _build_drive_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive service", "details": str(e)}

    try:
        is_structured = any(p.search(query) for p in DRIVE_QUERY_PATTERNS)
        if is_structured:
            final_query = query
        else:
            escaped = query.replace("'", "\\'")
            final_query = f"fullText contains '{escaped}'"

        list_params = build_drive_list_params(
            query=final_query,
            page_size=page_size,
            drive_id=drive_id,
            include_items_from_all_drives=include_items_from_all_drives,
            corpora=corpora,
        )

        resp = service.files().list(**list_params).execute()
        files = resp.get("files", []) or []

        files_out = [
            {
                "id": f.get("id"),
                "name": f.get("name"),
                "mimeType": f.get("mimeType"),
                "size": f.get("size"),
                "modifiedTime": f.get("modifiedTime"),
                "webViewLink": f.get("webViewLink"),
            }
            for f in files
        ]

        return {"status": "ok", "data": {"files": files_out}, "meta": {"count": len(files_out)}}
    except HttpError as e:
        return {"status": "error", "message": "Google Drive API error searching files", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error searching Drive files", "details": str(e)}


def get_drive_file_content(user_id: int, file_id: str) -> Dict[str, Any]:
    """
    Returns: {"status":"ok","data":{"file":{id,name,mimeType,webViewLink}, "content": "..."}, "meta":{}}
    """
    try:
        service, _ = _build_drive_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive service", "details": str(e)}

    try:
        meta = service.files().get(fileId=file_id, fields="id,name,mimeType,webViewLink", supportsAllDrives=True).execute()
        mime_type = meta.get("mimeType", "")
        file_name = meta.get("name", "Unknown File")

        export_map = {
            "application/vnd.google-apps.document": "text/plain",
            "application/vnd.google-apps.spreadsheet": "text/csv",
            "application/vnd.google-apps.presentation": "text/plain",
        }
        export_mime = export_map.get(mime_type)

        if export_mime:
            request_obj = service.files().export_media(fileId=file_id, mimeType=export_mime)
        else:
            request_obj = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_obj)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        content_bytes = fh.getvalue()

        office_mime_types = {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        if mime_type in office_mime_types:
            office_text = extract_office_xml_text(content_bytes, mime_type)
            if office_text:
                body_text = office_text
            else:
                try:
                    body_text = content_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    body_text = f"[Binary or unsupported encoding for mimeType '{mime_type}' - {len(content_bytes)} bytes]"
        else:
            try:
                body_text = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                body_text = f"[Binary or unsupported encoding for mimeType '{mime_type}' - {len(content_bytes)} bytes]"

        data = {
            "file": {
                "id": meta.get("id"),
                "name": file_name,
                "mimeType": mime_type,
                "webViewLink": meta.get("webViewLink"),
            },
            "content": body_text,
        }
        return {"status": "ok", "data": data, "meta": {}}
    except HttpError as e:
        if getattr(e, "resp", None) and getattr(e.resp, "status", None) == 404:
            return {"status": "error", "message": "File not found", "details": str(e)}
        return {"status": "error", "message": "Google Drive API error fetching file content", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error fetching file content", "details": str(e)}


def list_drive_items(
    user_id: int,
    folder_id: str = "root",
    page_size: int = 100,
    drive_id: Optional[str] = None,
    include_items_from_all_drives: bool = True,
    corpora: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns: {"status":"ok","data":{"items":[{id,name,mimeType,size,modifiedTime,webViewLink}]}, "meta":{"count":N}}
    """
    try:
        service, _ = _build_drive_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive service", "details": str(e)}

    try:
        query = f"'{folder_id}' in parents and trashed=false"
        list_params = build_drive_list_params(
            query=query,
            page_size=page_size,
            drive_id=drive_id,
            include_items_from_all_drives=include_items_from_all_drives,
            corpora=corpora,
        )
        resp = service.files().list(**list_params).execute()
        files = resp.get("files", []) or []

        items = [
            {
                "id": f.get("id"),
                "name": f.get("name"),
                "mimeType": f.get("mimeType"),
                "size": f.get("size"),
                "modifiedTime": f.get("modifiedTime"),
                "webViewLink": f.get("webViewLink"),
            }
            for f in files
        ]
        return {"status": "ok", "data": {"items": items}, "meta": {"count": len(items)}}
    except HttpError as e:
        return {"status": "error", "message": "Google Drive API error listing items", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error listing drive items", "details": str(e)}


def create_drive_file(
    user_id: int,
    file_name: str,
    content: Optional[str] = None,
    folder_id: str = "root",
    mime_type: str = "text/plain",
    fileUrl: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns: {"status":"ok","data":{"file":{id,name,webViewLink}}}
    """
    try:
        service, _ = _build_drive_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive service", "details": str(e)}

    try:
        if not content and not fileUrl:
            return {"status": "error", "message": "You must provide either 'content' or 'fileUrl'."}

        file_bytes = None
        if fileUrl:
            extracted = _extract_drive_file_id(fileUrl)
            if extracted and fileUrl.startswith("http"):
                try:
                    r = httpx.get(fileUrl, timeout=30.0)
                    if r.status_code != 200:
                        return {"status": "error", "message": f"Failed to fetch file from URL: {fileUrl}", "details": {"status_code": r.status_code}}
                    file_bytes = r.content
                    ct = r.headers.get("Content-Type")
                    if ct and ct != "application/octet-stream":
                        mime_type = ct
                except Exception as e:
                    return {"status": "error", "message": "Failed to fetch fileUrl content", "details": str(e)}
            else:
                if extracted:
                    try:
                        fh = io.BytesIO()
                        req = service.files().get_media(fileId=extracted)
                        downloader = MediaIoBaseDownload(fh, req)
                        done = False
                        while not done:
                            _, done = downloader.next_chunk()
                        file_bytes = fh.getvalue()
                    except Exception as e:
                        return {"status": "error", "message": "Failed to download drive file by id", "details": str(e)}
                else:
                    return {"status": "error", "message": "fileUrl provided but could not fetch content or extract id", "details": fileUrl}

        if content is not None and file_bytes is None:
            file_bytes = content.encode("utf-8")

        media = io.BytesIO(file_bytes)

        metadata = {"name": file_name, "parents": [folder_id], "mimeType": mime_type}

        created = service.files().create(
            body=metadata,
            media_body=MediaIoBaseUpload(media, mimetype=mime_type, resumable=True),
            fields="id,name,webViewLink",
            supportsAllDrives=True,
        ).execute()

        file_info = {"id": created.get("id"), "name": created.get("name"), "webViewLink": created.get("webViewLink")}
        return {"status": "ok", "data": {"file": file_info}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google Drive API error creating file", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error creating drive file", "details": str(e)}


def get_drive_file_permissions(user_id: int, file_id: str) -> Dict[str, Any]:
    """
    Returns:
      {"status":"ok","data":{"file":{...}, "owners":[...], "sharingUser":..., "permissions":[...]}, "meta":{}}
    """
    try:
        service, _ = _build_drive_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive service", "details": str(e)}

    try:
        fields = "id,name,mimeType,size,modifiedTime,owners,permissions,webViewLink,webContentLink,shared,sharingUser,viewersCanCopyContent"
        meta = service.files().get(fileId=file_id, fields=fields, supportsAllDrives=True).execute()

        permissions = meta.get("permissions", []) or []
        owners = meta.get("owners", []) or []
        sharing_user = meta.get("sharingUser")

        perms_out = []
        for p in permissions:
            perms_out.append({
                "id": p.get("id"),
                "type": p.get("type"),
                "role": p.get("role"),
                "emailAddress": p.get("emailAddress"),
                "domain": p.get("domain"),
                "allowFileDiscovery": p.get("allowFileDiscovery"),
            })

        data = {
            "file": {
                "id": meta.get("id"),
                "name": meta.get("name"),
                "mimeType": meta.get("mimeType"),
                "size": meta.get("size"),
                "modifiedTime": meta.get("modifiedTime"),
                "webViewLink": meta.get("webViewLink"),
                "webContentLink": meta.get("webContentLink"),
                "shared": meta.get("shared", False),
            },
            "owners": [{"displayName": o.get("displayName"), "emailAddress": o.get("emailAddress")} for o in owners],
            "sharingUser": {"displayName": sharing_user.get("displayName"), "emailAddress": sharing_user.get("emailAddress")} if sharing_user else None,
            "permissions": perms_out,
            "has_public_link": check_public_link_permission(permissions),
        }

        message = "File is shared publicly (anyone with link)." if data["has_public_link"] else "File is not shared publicly."
        return {"status": "ok", "data": data, "meta": {}, "message": message}
    except HttpError as e:
        if getattr(e, "resp", None) and getattr(e.resp, "status", None) == 404:
            return {"status": "error", "message": "File not found", "details": str(e)}
        return {"status": "error", "message": "Google Drive API error fetching file metadata/permissions", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error fetching file permissions", "details": str(e)}


def check_drive_file_public_access(user_id: int, file_name: str) -> Dict[str, Any]:
    """
    Returns:
      {"status":"ok","data":{"found_files":[...],"checked_file":{...},"has_public_link":bool,"insert_doc_image_url": "..."}}
    """
    try:
        service, _ = _build_drive_service_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive service", "details": str(e)}

    try:
        escaped = file_name.replace("'", "\\'")
        q = f"name = '{escaped}'"

        params = {
            "q": q,
            "pageSize": 10,
            "fields": "files(id,name,mimeType,webViewLink)",
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True,
        }

        resp = service.files().list(**params).execute()
        files = resp.get("files", []) or []
        if not files:
            return {"status": "ok", "data": {"files": []}, "meta": {"count": 0}, "message": f"No file found with name '{file_name}'."}

        found_files = [{"id": f.get("id"), "name": f.get("name"), "mimeType": f.get("mimeType")} for f in files]

        file_id = files[0].get("id")
        meta = service.files().get(fileId=file_id, fields="id,name,mimeType,permissions,webViewLink,webContentLink,shared", supportsAllDrives=True).execute()

        permissions = meta.get("permissions", []) or []
        has_public = check_public_link_permission(permissions)

        data = {
            "found_files": found_files,
            "checked_file": {
                "id": meta.get("id"),
                "name": meta.get("name"),
                "mimeType": meta.get("mimeType"),
                "shared": meta.get("shared", False),
                "webViewLink": meta.get("webViewLink"),
                "webContentLink": meta.get("webContentLink"),
            },
            "has_public_link": has_public,
        }

        if has_public:
            data["insert_doc_image_url"] = get_drive_image_url(file_id)
            message = f"PUBLIC - '{meta.get('name')}' is publicly accessible."
        else:
            message = f"NOT PUBLIC - '{meta.get('name')}' is not publicly accessible."

        return {"status": "ok", "data": data, "meta": {}, "message": message}
    except HttpError as e:
        return {"status": "error", "message": "Google Drive API error searching/checking file", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error checking drive file public access", "details": str(e)}
