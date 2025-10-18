import io
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

def build_text_style(
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
    underline: Optional[bool] = None,
    font_size: Optional[int] = None,
    font_family: Optional[str] = None
) -> Tuple[Dict[str, Any], List[str]]:
    text_style: Dict[str, Any] = {}
    fields: List[str] = []
    if bold is not None:
        text_style["bold"] = bold
        fields.append("bold")
    if italic is not None:
        text_style["italic"] = italic
        fields.append("italic")
    if underline is not None:
        text_style["underline"] = underline
        fields.append("underline")
    if font_size is not None:
        text_style["fontSize"] = {"magnitude": font_size, "unit": "PT"}
        fields.append("fontSize")
    if font_family is not None:
        text_style["weightedFontFamily"] = {"fontFamily": font_family}
        fields.append("weightedFontFamily")
    return text_style, fields


def create_insert_text_request(index: int, text: str) -> Dict[str, Any]:
    return {"insertText": {"location": {"index": index}, "text": text}}


def create_insert_text_segment_request(index: int, text: str, segment_id: str) -> Dict[str, Any]:
    return {"insertText": {"location": {"segmentId": segment_id, "index": index}, "text": text}}


def create_delete_range_request(start_index: int, end_index: int) -> Dict[str, Any]:
    return {"deleteContentRange": {"range": {"startIndex": start_index, "endIndex": end_index}}}


def create_format_text_request(
    start_index: int,
    end_index: int,
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
    underline: Optional[bool] = None,
    font_size: Optional[int] = None,
    font_family: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    text_style, fields = build_text_style(bold, italic, underline, font_size, font_family)
    if not text_style:
        return None
    return {"updateTextStyle": {"range": {"startIndex": start_index, "endIndex": end_index}, "textStyle": text_style, "fields": ",".join(fields)}}


def create_find_replace_request(find_text: str, replace_text: str, match_case: bool = False) -> Dict[str, Any]:
    return {"replaceAllText": {"containsText": {"text": find_text, "matchCase": match_case}, "replaceText": replace_text}}


def create_insert_table_request(index: int, rows: int, columns: int) -> Dict[str, Any]:
    return {"insertTable": {"location": {"index": index}, "rows": rows, "columns": columns}}


def create_insert_page_break_request(index: int) -> Dict[str, Any]:
    return {"insertPageBreak": {"location": {"index": index}}}


def create_insert_image_request(index: int, image_uri: str, width: Optional[int] = None, height: Optional[int] = None) -> Dict[str, Any]:
    request = {"insertInlineImage": {"location": {"index": index}, "uri": image_uri}}
    object_size: Dict[str, Any] = {}
    if width is not None:
        object_size["width"] = {"magnitude": width, "unit": "PT"}
    if height is not None:
        object_size["height"] = {"magnitude": height, "unit": "PT"}
    if object_size:
        request["insertInlineImage"]["objectSize"] = object_size
    return request


def create_bullet_list_request(start_index: int, end_index: int, list_type: str = "UNORDERED") -> Dict[str, Any]:
    bullet_preset = "BULLET_DISC_CIRCLE_SQUARE" if list_type == "UNORDERED" else "NUMBERED_DECIMAL_ALPHA_ROMAN"
    return {"createParagraphBullets": {"range": {"startIndex": start_index, "endIndex": end_index}, "bulletPreset": bullet_preset}}


def validate_operation(operation: Dict[str, Any]) -> Tuple[bool, str]:
    op_type = operation.get("type")
    if not op_type:
        return False, "Missing 'type' field"
    required_fields = {
        "insert_text": ["index", "text"],
        "delete_text": ["start_index", "end_index"],
        "replace_text": ["start_index", "end_index", "text"],
        "format_text": ["start_index", "end_index"],
        "insert_table": ["index", "rows", "columns"],
        "insert_page_break": ["index"],
        "find_replace": ["find_text", "replace_text"]
    }
    if op_type not in required_fields:
        return False, f"Unsupported operation type: {op_type}"
    for f in required_fields[op_type]:
        if f not in operation:
            return False, f"Missing required field: {f}"
    return True, ""


def extract_office_xml_text(file_bytes: bytes, mime_type: str) -> Optional[str]:
    """
    Attempt to pull readable text from OOXML files using zipfile + ElementTree.
    Returns joined text or None if nothing meaningful found.
    """
    ns_excel_main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            targets: List[str] = []
            shared_strings: List[str] = []

            if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                targets = ["word/document.xml"]
            elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                targets = [n for n in zf.namelist() if n.startswith("ppt/slides/slide")]
            elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                targets = [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and "drawing" not in n]
                try:
                    shared_xml = zf.read("xl/sharedStrings.xml")
                    root = ET.fromstring(shared_xml)
                    for si in root.findall(f"{{{ns_excel_main}}}si"):
                        parts: List[str] = []
                        for t in si.findall(f".//{{{ns_excel_main}}}t"):
                            if t.text:
                                parts.append(t.text)
                        shared_strings.append("".join(parts))
                except KeyError:
                    pass
                except ET.ParseError:
                    pass

            else:
                return None

            pieces: List[str] = []
            for member in targets:
                try:
                    xml_content = zf.read(member)
                    root = ET.fromstring(xml_content)
                    member_texts: List[str] = []
                    if mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                        for cell in root.findall(f".//{{{ns_excel_main}}}c"):
                            v = cell.find(f"{{{ns_excel_main}}}v")
                            if v is None or v.text is None:
                                continue
                            cell_t = cell.get("t")
                            if cell_t == "s":
                                try:
                                    idx = int(v.text)
                                    if 0 <= idx < len(shared_strings):
                                        member_texts.append(shared_strings[idx])
                                except Exception:
                                    pass
                            else:
                                member_texts.append(v.text)
                    else:
                        for el in root.iter():
                            if el.tag.endswith("}t") and el.text:
                                txt = el.text.strip()
                                if txt:
                                    member_texts.append(txt)
                    if member_texts:
                        pieces.append(" ".join(member_texts))
                except ET.ParseError:
                    continue
                except KeyError:
                    continue
                except Exception:
                    continue

            if not pieces:
                return None
            text = "\n\n".join(pieces).strip()
            return text or None
    except zipfile.BadZipFile:
        return None
    except Exception:
        return None
