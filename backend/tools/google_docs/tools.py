# gdocs_api.py
from typing import Any, Dict, List, Optional, Tuple
import io
import json

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
from django.contrib.auth import get_user_model

from GoogleAuth.utils import get_credentials_for_user

from .helpers import (
    create_insert_text_request,
    create_delete_range_request,
    create_format_text_request,
    create_find_replace_request,
    create_insert_table_request,
    create_insert_page_break_request,
    create_insert_image_request,
    create_bullet_list_request,
    build_text_style,
    validate_operation,
    extract_office_xml_text
)
from .structures import (
    parse_document_structure,
    find_tables,
    analyze_document_complexity
)
from .tables import extract_table_as_data
from .managers import (
    TableOperationManager,
    HeaderFooterManager,
    ValidationManager,
    BatchOperationManager
)

User = get_user_model()


def _build_docs_drive_services_for_user(user_id: int) -> Tuple[Any, Any, Any]:
    """
    Returns (drive_service, docs_service, creds) or raises ValueError on missing user/creds.
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ValueError("User not found")

    creds = get_credentials_for_user(user)
    if not creds:
        raise ValueError("No Google credentials for user. Ask the user to authorize.")

    try:
        drive_service = build("drive", "v3", credentials=creds)
        docs_service = build("docs", "v1", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Failed to build Google services: {e}")

    return drive_service, docs_service, creds


def search_docs(user_id: int, query: str, page_size: int = 10) -> Dict[str, Any]:
    """
    Search Google Docs by name (Drive listing filtered by mimeType).
    """
    try:
        drive_service, _, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive/Docs services", "details": str(e)}

    try:
        escaped_query = query.replace("'", "\\'")
        resp = drive_service.files().list(
            q=f"name contains '{escaped_query}' and mimeType='application/vnd.google-apps.document' and trashed=false",
            pageSize=page_size,
            fields="files(id, name, createdTime, modifiedTime, webViewLink)"
        ).execute()
        files = resp.get("files", []) or []
        docs = [{"id": f.get("id"), "name": f.get("name"), "createdTime": f.get("createdTime"), "modifiedTime": f.get("modifiedTime"), "webViewLink": f.get("webViewLink")} for f in files]
        return {"status": "ok", "data": {"docs": docs}, "meta": {"count": len(docs)}}
    except HttpError as e:
        return {"status": "error", "message": "Google Drive API error searching docs", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error searching docs", "details": str(e)}


def list_docs_in_folder(user_id: int, folder_id: str = "root", page_size: int = 100) -> Dict[str, Any]:
    try:
        drive_service, _, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive/Docs services", "details": str(e)}

    try:
        resp = drive_service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false",
            pageSize=page_size,
            fields="files(id, name, modifiedTime, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        items = resp.get("files", []) or []
        docs = [{"id": it.get("id"), "name": it.get("name"), "modifiedTime": it.get("modifiedTime"), "webViewLink": it.get("webViewLink")} for it in items]
        return {"status": "ok", "data": {"docs": docs}, "meta": {"count": len(docs)}}
    except HttpError as e:
        return {"status": "error", "message": "Google Drive API error listing docs in folder", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error listing docs", "details": str(e)}


def get_doc_content(user_id: int, document_id: str) -> Dict[str, Any]:
    """
    Returns structured content for a document or Drive file.
    {"status":"ok", "data": {"file": {...}, "content": "..."}}
    """
    try:
        drive_service, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive/Docs services", "details": str(e)}

    try:
        file_metadata = drive_service.files().get(fileId=document_id, fields="id, name, mimeType, webViewLink").execute()
        mime_type = file_metadata.get("mimeType", "")
        file_name = file_metadata.get("name", "Unknown File")
        web_view_link = file_metadata.get("webViewLink", "#")

        content_text = ""

        if mime_type == "application/vnd.google-apps.document":
            doc_data = docs_service.documents().get(documentId=document_id, includeTabsContent=True).execute()

            def extract_text_from_elements(elements, tab_name: Optional[str] = None, depth: int = 0) -> str:
                if depth > 5:
                    return ""
                lines: List[str] = []
                if tab_name:
                    lines.append(f"\n--- TAB: {tab_name} ---\n")
                for element in elements:
                    if "paragraph" in element:
                        paragraph = element.get("paragraph", {})
                        para_elements = paragraph.get("elements", [])
                        current_line = ""
                        for pe in para_elements:
                            tr = pe.get("textRun", {})
                            if tr and "content" in tr:
                                current_line += tr["content"]
                        if current_line.strip():
                            lines.append(current_line)
                    elif "table" in element:
                        table = element.get("table", {})
                        table_rows = table.get("tableRows", [])
                        for row in table_rows:
                            for cell in row.get("tableCells", []):
                                cell_content = cell.get("content", [])
                                cell_text = extract_text_from_elements(cell_content, depth=depth + 1)
                                if cell_text.strip():
                                    lines.append(cell_text)
                return "".join(lines)

            def process_tab_hierarchy(tab: Dict[str, Any], level: int = 0) -> str:
                t_text = ""
                if "documentTab" in tab:
                    tab_title = tab.get("documentTab", {}).get("title", "Untitled Tab")
                    if level > 0:
                        tab_title = ("    " * level) + tab_title
                    tab_body = tab.get("documentTab", {}).get("body", {}).get("content", [])
                    t_text += extract_text_from_elements(tab_body, tab_title)
                for child in tab.get("childTabs", []) or []:
                    t_text += process_tab_hierarchy(child, level + 1)
                return t_text

            parts: List[str] = []
            main_elements = doc_data.get("body", {}).get("content", [])
            main_text = extract_text_from_elements(main_elements)
            if main_text.strip():
                parts.append(main_text)
            for tab in doc_data.get("tabs", []) or []:
                t = process_tab_hierarchy(tab)
                if t.strip():
                    parts.append(t)
            content_text = "".join(parts)

        else:
            request_obj = drive_service.files().get_media(fileId=document_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request_obj)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            file_content_bytes = fh.getvalue()
            office_text = extract_office_xml_text(file_content_bytes, mime_type)
            if office_text:
                content_text = office_text
            else:
                try:
                    content_text = file_content_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    content_text = f"[Binary or unsupported text encoding for mimeType '{mime_type}' - {len(file_content_bytes)} bytes]"

        file_info = {"id": document_id, "name": file_name, "mimeType": mime_type, "webViewLink": web_view_link}
        return {"status": "ok", "data": {"file": file_info, "content": content_text}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google API error fetching document", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error fetching document", "details": str(e)}


def create_doc(user_id: int, title: str, content: str = "") -> Dict[str, Any]:
    try:
        _, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Docs service", "details": str(e)}

    try:
        doc = docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")
        if content:
            requests = [create_insert_text_request(1, content)]
            docs_service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

        link = f"https://docs.google.com/document/d/{doc_id}/edit"
        return {"status": "ok", "data": {"documentId": doc_id, "title": title, "link": link}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google Docs API error creating document", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error creating document", "details": str(e)}


def modify_doc_text(
    user_id: int,
    document_id: str,
    start_index: int,
    end_index: Optional[int] = None,
    text: Optional[str] = None,
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
    underline: Optional[bool] = None,
    font_size: Optional[int] = None,
    font_family: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        _, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Docs service", "details": str(e)}

    try:
        validator = ValidationManager()
        valid, err = validator.validate_document_id(document_id)
        if not valid:
            return {"status": "error", "message": err, "details": ""}

        if text is None and not any([bold is not None, italic is not None, underline is not None, font_size, font_family]):
            return {"status": "error", "message": "Must provide text or formatting parameters", "details": ""}

        if any([bold is not None, italic is not None, underline is not None, font_size, font_family]):
            valid, err = validator.validate_text_formatting_params(bold, italic, underline, font_size, font_family)
            if not valid:
                return {"status": "error", "message": err, "details": ""}

            if end_index is None:
                return {"status": "error", "message": "'end_index' is required when applying formatting", "details": ""}

            valid, err = validator.validate_index_range(start_index, end_index)
            if not valid:
                return {"status": "error", "message": err, "details": ""}

        requests: List[Dict[str, Any]] = []
        operations: List[str] = []

        if text is not None:
            if end_index is not None and end_index > start_index:
                if start_index == 0:
                    requests.append(create_insert_text_request(1, text))
                    adjusted_end = end_index + len(text)
                    requests.append(create_delete_range_request(1 + len(text), adjusted_end))
                    operations.append(f"Replaced text from index {start_index} to {end_index}")
                else:
                    requests.extend([create_delete_range_request(start_index, end_index), create_insert_text_request(start_index, text)])
                    operations.append(f"Replaced text from index {start_index} to {end_index}")
            else:
                actual_index = 1 if start_index == 0 else start_index
                requests.append(create_insert_text_request(actual_index, text))
                operations.append(f"Inserted text at index {start_index}")

        if any([bold is not None, italic is not None, underline is not None, font_size, font_family]):
            format_start = start_index
            format_end = end_index

            if text is not None:
                if end_index is not None and end_index > start_index:
                    format_end = start_index + len(text)
                else:
                    actual_index = 1 if start_index == 0 else start_index
                    format_start = actual_index
                    format_end = actual_index + len(text)

            if format_start == 0:
                format_start = 1
            if format_end is not None and format_end <= format_start:
                format_end = format_start + 1

            fmt_req = create_format_text_request(format_start, format_end, bold, italic, underline, font_size, font_family)
            if fmt_req:
                requests.append(fmt_req)

            fd = []
            if bold is not None:
                fd.append(f"bold={bold}")
            if italic is not None:
                fd.append(f"italic={italic}")
            if underline is not None:
                fd.append(f"underline={underline}")
            if font_size:
                fd.append(f"font_size={font_size}")
            if font_family:
                fd.append(f"font_family={font_family}")
            operations.append(f"Applied formatting ({', '.join(fd)}) to range {format_start}-{format_end}")

        if not requests:
            return {"status": "error", "message": "No operations to perform", "details": ""}

        docs_service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

        link = f"https://docs.google.com/document/d/{document_id}/edit"
        return {"status": "ok", "data": {"summary": "; ".join(operations), "link": link}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google Docs API error modifying document", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error modifying document", "details": str(e)}


def find_and_replace_doc(user_id: int, document_id: str, find_text: str, replace_text: str, match_case: bool = False) -> Dict[str, Any]:
    try:
        _, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Docs service", "details": str(e)}

    try:
        req = [create_find_replace_request(find_text, replace_text, match_case)]
        result = docs_service.documents().batchUpdate(documentId=document_id, body={"requests": req}).execute()
        replacements = 0
        if "replies" in result and result["replies"]:
            rep = result["replies"][0]
            if "replaceAllText" in rep:
                replacements = rep["replaceAllText"].get("occurrencesChanged", 0)
        link = f"https://docs.google.com/document/d/{document_id}/edit"
        return {"status": "ok", "data": {"replacements": replacements, "link": link}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google Docs API error find/replace", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error find/replace", "details": str(e)}


def insert_doc_elements(
    user_id: int,
    document_id: str,
    element_type: str,
    index: int,
    rows: Optional[int] = None,
    columns: Optional[int] = None,
    list_type: Optional[str] = None,
    text: Optional[str] = None
) -> Dict[str, Any]:
    try:
        _, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Docs service", "details": str(e)}

    try:
        if index == 0:
            index = 1

        requests: List[Dict[str, Any]] = []
        description = ""

        if element_type == "table":
            if not rows or not columns:
                return {"status": "error", "message": "rows and columns are required for table insertion", "details": ""}
            requests.append(create_insert_table_request(index, rows, columns))
            description = f"table ({rows}x{columns})"
        elif element_type == "list":
            if not list_type:
                return {"status": "error", "message": "list_type parameter required", "details": ""}
            if not text:
                text = "List item"
            requests.extend([create_insert_text_request(index, text + "\n"), create_bullet_list_request(index, index + len(text), list_type)])
            description = f"{list_type.lower()} list"
        elif element_type == "page_break":
            requests.append(create_insert_page_break_request(index))
            description = "page break"
        else:
            return {"status": "error", "message": f"Unsupported element type '{element_type}'", "details": ""}

        docs_service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
        link = f"https://docs.google.com/document/d/{document_id}/edit"
        return {"status": "ok", "data": {"message": f"Inserted {description} at index {index}", "link": link}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google Docs API error inserting element", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error inserting element", "details": str(e)}


def insert_doc_image(user_id: int, document_id: str, image_source: str, index: int, width: Optional[int] = None, height: Optional[int] = None) -> Dict[str, Any]:
    """
    image_source: either a Drive file ID or a public URL
    """
    try:
        drive_service, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive/Docs services", "details": str(e)}

    try:
        if index == 0:
            index = 1

        is_drive_file = image_source and not (image_source.startswith("http://") or image_source.startswith("https://"))

        if is_drive_file:
            try:
                meta = drive_service.files().get(fileId=image_source, fields="id, name, mimeType").execute()
                mime_type = meta.get("mimeType", "")
                if not mime_type.startswith("image/"):
                    return {"status": "error", "message": f"File {image_source} is not an image (mimeType {mime_type})", "details": ""}
                image_uri = f"https://drive.google.com/uc?id={image_source}"
                source_description = f"Drive file {meta.get('name', image_source)}"
            except HttpError as he:
                return {"status": "error", "message": "Google Drive API error accessing image file", "details": str(he)}
            except Exception as e:
                return {"status": "error", "message": "Unexpected error accessing Drive file", "details": str(e)}
        else:
            image_uri = image_source
            source_description = "URL image"

        req = [create_insert_image_request(index, image_uri, width, height)]
        docs_service.documents().batchUpdate(documentId=document_id, body={"requests": req}).execute()
        link = f"https://docs.google.com/document/d/{document_id}/edit"
        size_info = ""
        if width or height:
            size_info = f" (size: {width or 'auto'}x{height or 'auto'} points)"
        return {"status": "ok", "data": {"message": f"Inserted {source_description}{size_info} at index {index}", "link": link}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google Docs API error inserting image", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error inserting image", "details": str(e)}


def update_doc_headers_footers(user_id: int, document_id: str, section_type: str, content: str, header_footer_type: str = "DEFAULT") -> Dict[str, Any]:
    try:
        _, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Docs service", "details": str(e)}

    try:
        validator = ValidationManager()
        ok, err = validator.validate_document_id(document_id)
        if not ok:
            return {"status": "error", "message": err, "details": ""}

        ok, err = validator.validate_header_footer_params(section_type, header_footer_type)
        if not ok:
            return {"status": "error", "message": err, "details": ""}

        ok, err = validator.validate_text_content(content)
        if not ok:
            return {"status": "error", "message": err, "details": ""}

        header_footer_manager = HeaderFooterManager(docs_service)
        success, message = header_footer_manager.update_header_footer_content(document_id, section_type, content, header_footer_type)
        if success:
            link = f"https://docs.google.com/document/d/{document_id}/edit"
            return {"status": "ok", "data": {"message": message, "link": link}, "meta": {}}
        else:
            return {"status": "error", "message": message, "details": ""}
    except HttpError as e:
        return {"status": "error", "message": "Google Docs API error updating header/footer", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error updating header/footer", "details": str(e)}


def batch_update_doc(user_id: int, document_id: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        _, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Docs service", "details": str(e)}

    try:
        validator = ValidationManager()
        ok, err = validator.validate_document_id(document_id)
        if not ok:
            return {"status": "error", "message": err, "details": ""}

        ok, err = validator.validate_batch_operations(operations)
        if not ok:
            return {"status": "error", "message": err, "details": ""}

        batch_manager = BatchOperationManager(docs_service)
        success, message, metadata = batch_manager.execute_batch_operations(document_id, operations)
        if success:
            link = f"https://docs.google.com/document/d/{document_id}/edit"
            return {"status": "ok", "data": {"message": message, "api_replies": metadata.get("replies_count", 0), "link": link}, "meta": {}}
        else:
            return {"status": "error", "message": message, "details": ""}
    except HttpError as e:
        return {"status": "error", "message": "Google Docs API error performing batch update", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error performing batch update", "details": str(e)}


def inspect_doc_structure(user_id: int, document_id: str, detailed: bool = False) -> Dict[str, Any]:
    try:
        _, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Docs service", "details": str(e)}

    try:
        doc = docs_service.documents().get(documentId=document_id).execute()
        if detailed:
            structure = parse_document_structure(doc)
            result = {
                "title": structure["title"],
                "total_length": structure["total_length"],
                "statistics": {
                    "elements": len(structure["body"]),
                    "tables": len(structure["tables"]),
                    "paragraphs": sum(1 for e in structure["body"] if e.get("type") == "paragraph"),
                    "has_headers": bool(structure["headers"]),
                    "has_footers": bool(structure["footers"])
                },
                "elements": []
            }
            for element in structure["body"]:
                elem_summary = {
                    "type": element["type"],
                    "start_index": element["start_index"],
                    "end_index": element["end_index"]
                }
                if element["type"] == "table":
                    elem_summary["rows"] = element["rows"]
                    elem_summary["columns"] = element["columns"]
                    elem_summary["cell_count"] = len(element.get("cells", []))
                elif element["type"] == "paragraph":
                    elem_summary["text_preview"] = element.get("text", "")[:100]
                result["elements"].append(elem_summary)
            if structure["tables"]:
                result["tables"] = []
                for i, table in enumerate(structure["tables"]):
                    table_data = extract_table_as_data(table)
                    result["tables"].append({
                        "index": i,
                        "position": {"start": table["start_index"], "end": table["end_index"]},
                        "dimensions": {"rows": table["rows"], "columns": table["columns"]},
                        "preview": table_data[:3] if table_data else []
                    })
        else:
            result = analyze_document_complexity(doc)
            tables = find_tables(doc)
            if tables:
                result["table_details"] = []
                for i, table in enumerate(tables):
                    result["table_details"].append({
                        "index": i,
                        "rows": table["rows"],
                        "columns": table["columns"],
                        "start_index": table["start_index"],
                        "end_index": table["end_index"]
                    })

        link = f"https://docs.google.com/document/d/{document_id}/edit"
        return {"status": "ok", "data": {"structure": result, "link": link}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google Docs API error inspecting document", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error inspecting document", "details": str(e)}


def create_table_with_data(user_id: int, document_id: str, table_data: List[List[str]], index: int, bold_headers: bool = True) -> Dict[str, Any]:
    try:
        _, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Docs service", "details": str(e)}

    try:
        validator = ValidationManager()
        ok, err = validator.validate_document_id(document_id)
        if not ok:
            return {"status": "error", "message": err, "details": ""}

        ok, err = validator.validate_table_data(table_data)
        if not ok:
            return {"status": "error", "message": err, "details": ""}

        ok, err = validator.validate_index(index, "Index")
        if not ok:
            return {"status": "error", "message": err, "details": ""}

        table_manager = TableOperationManager(docs_service)
        success, message, metadata = table_manager.create_and_populate_table(document_id, table_data, index, bold_headers)
        if not success and "must be less than the end index" in message:
            # Retry with index-1
            success, message, metadata = table_manager.create_and_populate_table(document_id, table_data, index - 1, bold_headers)

        if success:
            link = f"https://docs.google.com/document/d/{document_id}/edit"
            return {"status": "ok", "data": {"message": message, "rows": metadata.get("rows", 0), "columns": metadata.get("columns", 0), "index": index, "link": link}, "meta": {}}
        else:
            return {"status": "error", "message": message, "details": ""}
    except HttpError as e:
        return {"status": "error", "message": "Google Docs API error creating table", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error creating table", "details": str(e)}


def debug_table_structure(user_id: int, document_id: str, table_index: int = 0) -> Dict[str, Any]:
    try:
        _, docs_service, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Docs service", "details": str(e)}

    try:
        doc = docs_service.documents().get(documentId=document_id).execute()
        tables = find_tables(doc)
        if table_index >= len(tables):
            return {"status": "error", "message": f"Table index {table_index} not found. Document has {len(tables)} table(s).", "details": ""}

        table_info = tables[table_index]
        debug_info = {
            "table_index": table_index,
            "dimensions": f"{table_info['rows']}x{table_info['columns']}",
            "table_range": f"[{table_info['start_index']}-{table_info['end_index']}]",
            "cells": []
        }
        for r_idx, row in enumerate(table_info["cells"]):
            row_info = []
            for c_idx, cell in enumerate(row):
                cell_debug = {
                    "position": f"({r_idx},{c_idx})",
                    "range": f"[{cell['start_index']}-{cell['end_index']}]",
                    "insertion_index": cell.get("insertion_index", "N/A"),
                    "current_content": repr(cell.get("content", "")),
                    "content_elements_count": len(cell.get("content_elements", []))
                }
                row_info.append(cell_debug)
            debug_info["cells"].append(row_info)

        link = f"https://docs.google.com/document/d/{document_id}/edit"
        return {"status": "ok", "data": {"debug": debug_info, "link": link}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google Docs API error debugging table", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error debugging table", "details": str(e)}


def export_doc_to_pdf(user_id: int, document_id: str, pdf_filename: Optional[str] = None, folder_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Export Google Doc to PDF and upload to Drive (drive_service required).
    """
    try:
        drive_service, _, _ = _build_docs_drive_services_for_user(user_id)
    except Exception as e:
        return {"status": "error", "message": "Failed to init Drive service", "details": str(e)}

    try:
        meta = drive_service.files().get(fileId=document_id, fields="id, name, mimeType, webViewLink").execute()
    except HttpError as e:
        return {"status": "error", "message": "Google Drive API error getting file metadata", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error getting file metadata", "details": str(e)}

    mime_type = meta.get("mimeType", "")
    original_name = meta.get("name", "Unknown Document")
    web_view_link = meta.get("webViewLink", "#")

    if mime_type != "application/vnd.google-apps.document":
        return {"status": "error", "message": f"File '{original_name}' is not a Google Doc (mimeType: {mime_type})", "details": ""}

    try:
        request_obj = drive_service.files().export_media(fileId=document_id, mimeType="application/pdf")
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_obj)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        pdf_content = fh.getvalue()
        pdf_size = len(pdf_content)
    except HttpError as e:
        return {"status": "error", "message": "Google Drive API error exporting to PDF", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error exporting to PDF", "details": str(e)}

    if not pdf_filename:
        pdf_filename = f"{original_name}_PDF.pdf"
    elif not pdf_filename.lower().endswith(".pdf"):
        pdf_filename += ".pdf"

    try:
        fh.seek(0)
        media = MediaIoBaseUpload(fh, mimetype="application/pdf", resumable=True)
        file_meta = {"name": pdf_filename, "mimeType": "application/pdf"}
        if folder_id:
            file_meta["parents"] = [folder_id]

        uploaded = drive_service.files().create(body=file_meta, media_body=media, fields="id, name, webViewLink, parents", supportsAllDrives=True).execute()
        pdf_file_id = uploaded.get("id")
        pdf_web_link = uploaded.get("webViewLink", "#")
        pdf_parents = uploaded.get("parents", [])
        folder_info = ""
        if folder_id:
            folder_info = f" in folder {folder_id}"
        elif pdf_parents:
            folder_info = f" in folder {pdf_parents[0]}"

        return {"status": "ok", "data": {"pdf_file_id": pdf_file_id, "pdf_webLink": pdf_web_link, "pdf_size": pdf_size, "folder_info": folder_info, "original_link": web_view_link}, "meta": {}}
    except HttpError as e:
        return {"status": "error", "message": "Google Drive API error uploading PDF", "details": str(e)}
    except Exception as e:
        return {"status": "error", "message": "Unexpected error uploading PDF", "details": str(e)}


