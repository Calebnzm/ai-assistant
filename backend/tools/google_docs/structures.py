from typing import Any, Dict, List, Optional, Tuple


def parse_document_structure(doc_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse full document structure into a dictionary with:
      - title, body (list of elements), tables (list), headers, footers, total_length
    """
    structure: Dict[str, Any] = {
        "title": doc_data.get("title", ""),
        "body": [],
        "tables": [],
        "headers": {},
        "footers": {},
        "total_length": 0
    }

    body = doc_data.get("body", {}) or {}
    content = body.get("content", []) or []

    for element in content:
        info = _parse_element(element)
        if info:
            structure["body"].append(info)
            if info.get("type") == "table":
                structure["tables"].append(info)

    if structure["body"]:
        last = structure["body"][-1]
        structure["total_length"] = last.get("end_index", 0)

    for header_id, header_data in (doc_data.get("headers") or {}).items():
        structure["headers"][header_id] = _parse_segment(header_data)

    for footer_id, footer_data in (doc_data.get("footers") or {}).items():
        structure["footers"][footer_id] = _parse_segment(footer_data)

    return structure


def _parse_element(element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a single document element into a normalized dict.
    """
    element_info: Dict[str, Any] = {
        "start_index": element.get("startIndex", 0),
        "end_index": element.get("endIndex", 0)
    }

    if "paragraph" in element:
        paragraph = element["paragraph"]
        element_info["type"] = "paragraph"
        element_info["text"] = _extract_paragraph_text(paragraph)
        element_info["style"] = paragraph.get("paragraphStyle", {})
    elif "table" in element:
        table = element["table"]
        rows = len(table.get("tableRows", []))
        cols = 0
        if rows > 0:
            cols = len(table.get("tableRows", [{}])[0].get("tableCells", []))
        element_info["type"] = "table"
        element_info["rows"] = rows
        element_info["columns"] = cols
        element_info["cells"] = _parse_table_cells(table)
        element_info["table_style"] = table.get("tableStyle", {})
    elif "sectionBreak" in element:
        element_info["type"] = "section_break"
        element_info["section_style"] = element["sectionBreak"].get("sectionStyle", {})
    elif "tableOfContents" in element:
        element_info["type"] = "table_of_contents"
    else:
        return None

    return element_info


def _parse_table_cells(table: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
    """
    Parse a table element and return a 2D list of cell metadata dictionaries:
    each cell dict contains: row, column, start_index, end_index, insertion_index, content, content_elements
    """
    cells: List[List[Dict[str, Any]]] = []
    for r_idx, row in enumerate(table.get("tableRows", [])):
        row_cells: List[Dict[str, Any]] = []
        for c_idx, cell in enumerate(row.get("tableCells", [])):
            insertion_index = cell.get("startIndex", 0) + 1
            content_elements = cell.get("content", []) or []

            for element in content_elements:
                if "paragraph" in element:
                    para = element["paragraph"]
                    para_elems = para.get("elements", []) or []
                    if para_elems:
                        first = para_elems[0]
                        if "startIndex" in first:
                            insertion_index = first["startIndex"]
                            break

            cell_info: Dict[str, Any] = {
                "row": r_idx,
                "column": c_idx,
                "start_index": cell.get("startIndex", 0),
                "end_index": cell.get("endIndex", 0),
                "insertion_index": insertion_index,
                "content": _extract_cell_text(cell),
                "content_elements": content_elements
            }
            row_cells.append(cell_info)
        cells.append(row_cells)
    return cells


def _extract_paragraph_text(paragraph: Dict[str, Any]) -> str:
    parts: List[str] = []
    for element in paragraph.get("elements", []) or []:
        if "textRun" in element:
            parts.append(element["textRun"].get("content", ""))
    return "".join(parts)


def _extract_cell_text(cell: Dict[str, Any]) -> str:
    parts: List[str] = []
    for element in cell.get("content", []) or []:
        if "paragraph" in element:
            parts.append(_extract_paragraph_text(element["paragraph"]))
    return "".join(parts)


def _parse_segment(segment_data: Dict[str, Any]) -> Dict[str, Any]:
    content = segment_data.get("content", []) or []
    start = content[0].get("startIndex", 0) if content else 0
    end = content[-1].get("endIndex", 0) if content else 0
    return {"content": content, "start_index": start, "end_index": end}


def find_tables(doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return a list of tables discovered in the document, each with:
      index, start_index, end_index, rows, columns, cells (2D list)
    """
    tables: List[Dict[str, Any]] = []
    structure = parse_document_structure(doc_data)
    for idx, table_info in enumerate(structure.get("tables", [])):
        tables.append({
            "index": idx,
            "start_index": table_info.get("start_index"),
            "end_index": table_info.get("end_index"),
            "rows": table_info.get("rows"),
            "columns": table_info.get("columns"),
            "cells": table_info.get("cells")
        })
    return tables


def get_table_cell_indices(doc_data: Dict[str, Any], table_index: int = 0) -> Optional[List[List[Tuple[int, int]]]]:
    """
    Return 2D list of (start_index, end_index) for each cell in table_index,
    or None when the table index is invalid.
    """
    tables = find_tables(doc_data)
    if table_index >= len(tables):
        return None

    table = tables[table_index]
    result: List[List[Tuple[int, int]]] = []
    for row in table.get("cells", []):
        row_indices: List[Tuple[int, int]] = []
        for cell in row:
            cell_content_elements = cell.get("content_elements", []) or []
            placed = False
            if cell_content_elements:
                for element in cell_content_elements:
                    if "paragraph" in element:
                        para = element["paragraph"]
                        elems = para.get("elements", []) or []
                        if elems:
                            first_text = elems[0]
                            if "textRun" in first_text:
                                start_idx = first_text.get("startIndex", cell.get("start_index", 0) + 1)
                                end_idx = first_text.get("endIndex", start_idx + 1)
                                row_indices.append((start_idx, end_idx))
                                placed = True
                                break
            if not placed:
                content_start = cell.get("start_index", 0) + 1
                content_end = max(cell.get("end_index", 0) - 1, content_start)
                row_indices.append((content_start, content_end))
        result.append(row_indices)
    return result


def find_element_at_index(doc_data: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
    """
    Return the parsed element that contains the given index.
    If it's a table, also returns 'containing_cell' with row/column info.
    """
    structure = parse_document_structure(doc_data)
    for element in structure.get("body", []):
        if element.get("start_index", 0) <= index < element.get("end_index", 0):
            copy = dict(element)
            if element.get("type") == "table" and "cells" in element:
                for r_idx, row in enumerate(element["cells"]):
                    for c_idx, cell in enumerate(row):
                        if cell.get("start_index", 0) <= index < cell.get("end_index", 0):
                            copy["containing_cell"] = {
                                "row": r_idx,
                                "column": c_idx,
                                "cell_start": cell.get("start_index"),
                                "cell_end": cell.get("end_index")
                            }
                            break
            return copy
    return None


def get_next_paragraph_index(doc_data: Dict[str, Any], after_index: int = 0) -> int:
    """
    Find the start_index of the next paragraph element after 'after_index';
    otherwise return end of document (total_length - 1) or 1 as a fallback.
    """
    structure = parse_document_structure(doc_data)
    for element in structure.get("body", []):
        if element.get("type") == "paragraph" and element.get("start_index", 0) > after_index:
            return element.get("start_index", 1)
    total = structure.get("total_length", 0)
    return total - 1 if total > 0 else 1


def analyze_document_complexity(doc_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return statistics about the document: counts of elements, tables, paragraphs,
    section breaks, total_length, headers/footers presence and some table stats.
    """
    structure = parse_document_structure(doc_data)
    stats: Dict[str, Any] = {
        "total_elements": len(structure.get("body", [])),
        "tables": len(structure.get("tables", [])),
        "paragraphs": sum(1 for e in structure.get("body", []) if e.get("type") == "paragraph"),
        "section_breaks": sum(1 for e in structure.get("body", []) if e.get("type") == "section_break"),
        "total_length": structure.get("total_length", 0),
        "has_headers": bool(structure.get("headers")),
        "has_footers": bool(structure.get("footers"))
    }

    if structure.get("tables"):
        total_cells = sum(t.get("rows", 0) * t.get("columns", 0) for t in structure.get("tables", []))
        stats["total_table_cells"] = total_cells
        stats["largest_table"] = max((t.get("rows", 0) * t.get("columns", 0) for t in structure.get("tables", [])), default=0)

    return stats
