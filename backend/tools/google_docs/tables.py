from typing import Any, Dict, List, Optional, Tuple, Union


def build_table_population_requests(
    table_info: Dict[str, Any],
    data: List[List[str]],
    bold_headers: bool = True
) -> List[Dict[str, Any]]:
    """
    Build batch requests to populate a table with data.

    Args:
        table_info: Table information including 'cells' with cell metadata.
        data: 2D array of strings to insert into the table.
        bold_headers: If True, apply bold to first row.

    Returns:
        List of Google Docs batch requests (dicts).
    """
    requests: List[Dict[str, Any]] = []
    cells = table_info.get("cells", [])

    if not cells:
        return requests

    for row_idx, row_data in enumerate(data):
        if row_idx >= len(cells):
            break

        for col_idx, cell_text in enumerate(row_data):
            if col_idx >= len(cells[row_idx]):
                break

            cell = cells[row_idx][col_idx]

            existing_content = (cell.get("content") or "").strip()
            if not cell_text:
                continue

            insertion_index = cell.get("insertion_index", cell.get("start_index", 0) + 1)

            if existing_content == "" or existing_content == "\n":
                requests.append({
                    "insertText": {
                        "location": {"index": insertion_index},
                        "text": cell_text
                    }
                })

                if bold_headers and row_idx == 0:
                    requests.append({
                        "updateTextStyle": {
                            "range": {
                                "startIndex": insertion_index,
                                "endIndex": insertion_index + len(cell_text)
                            },
                            "textStyle": {"bold": True},
                            "fields": "bold"
                        }
                    })
            else:
                cell_end = max(cell.get("end_index", 0) - 1, insertion_index)
                requests.append({
                    "insertText": {
                        "location": {"index": cell_end},
                        "text": cell_text
                    }
                })

                if bold_headers and row_idx == 0:
                    requests.append({
                        "updateTextStyle": {
                            "range": {
                                "startIndex": cell_end,
                                "endIndex": cell_end + len(cell_text)
                            },
                            "textStyle": {"bold": True},
                            "fields": "bold"
                        }
                    })

    return requests


def calculate_cell_positions(
    table_start_index: int,
    rows: int,
    cols: int,
    existing_table_data: Optional[Dict[str, Any]] = None
) -> List[List[Dict[str, int]]]:
    """
    Calculate (or approximate) positions for each cell in a table.

    If existing_table_data contains 'cells', that is returned as-is; otherwise
    a simple estimate is produced.

    Returns a 2D list of dicts like {'row': r, 'column': c, 'start_index': x, 'end_index': y}
    """
    if existing_table_data and "cells" in existing_table_data:
        return existing_table_data["cells"]

    cells: List[List[Dict[str, int]]] = []
    current_index = table_start_index + 2 

    for r in range(rows):
        row_cells: List[Dict[str, int]] = []
        for c in range(cols):
            cell_start = current_index
            cell_end = current_index + 2
            row_cells.append({
                "row": r,
                "column": c,
                "start_index": cell_start,
                "end_index": cell_end
            })
            current_index = cell_end + 1
        cells.append(row_cells)

    return cells


def format_table_data(raw_data: Union[List[List[str]], List[str], str]) -> List[List[str]]:
    """
    Normalize various input formats into a 2D list of strings for table insertion.

    Supported inputs:
      - 2D list of strings (returned unchanged, coerced to str)
      - 1D list -> converted to single-column table
      - newline-separated string -> split into rows; supports tab- or comma-delimited
      - single string value -> 1x1 table
    """
    if isinstance(raw_data, str):
        lines = [ln for ln in raw_data.strip().splitlines() if ln is not None]
        if "\t" in raw_data:
            return [line.split("\t") for line in lines]
        if "," in raw_data:
            return [line.split(",") for line in lines]
        return [[cell.strip() for cell in line.split()] for line in lines]

    if isinstance(raw_data, list):
        if not raw_data:
            return [[]]
        if isinstance(raw_data[0], list):
            return [[str(cell) for cell in row] for row in raw_data]
        return [[str(cell)] for cell in raw_data]

    return [[str(raw_data)]]


def create_table_with_data(
    index: int,
    data: List[List[str]],
    headers: Optional[List[str]] = None,
    bold_headers: bool = True
) -> List[Dict[str, Any]]:
    """
    Build the initial requests to create a table at the given index with the provided data.

    This function only returns the requests necessary to insert the table (insertTable).
    Filling the table with cell content requires reading the document structure after
    creation to compute accurate insertion indices, then issuing insertion requests
    (use build_table_population_requests for that step).

    Raises:
        ValueError: if provided data is empty or invalid shape.

    Returns:
        List of batchUpdate request dictionaries.
    """
    full_data = data
    if headers:
        full_data = [headers] + data

    full_data = format_table_data(full_data)

    if not full_data or not full_data[0]:
        raise ValueError("Cannot create table with empty data")

    rows = len(full_data)
    cols = len(full_data[0])

    for row in full_data:
        while len(row) < cols:
            row.append("")

    requests: List[Dict[str, Any]] = []
    requests.append({
        "insertTable": {
            "location": {"index": index},
            "rows": rows,
            "columns": cols
        }
    })

    return requests


def build_table_style_requests(
    table_start_index: int,
    style_options: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Build table styling requests (borders, background colors, header background, etc.)

    style_options can include:
      - border_width (number, points)
      - border_color (dict with 'red','green','blue' floats 0..1 or hex unpacked dict)
      - background_color (rgb dict)
      - header_background (rgb dict)
    """
    requests: List[Dict[str, Any]] = []

    table_cell_style: Dict[str, Any] = {}
    fields: List[str] = []

    if "border_width" in style_options:
        bw = {"magnitude": style_options["border_width"], "unit": "PT"}
        table_cell_style["borderTop"] = {"width": bw}
        table_cell_style["borderBottom"] = {"width": bw}
        table_cell_style["borderLeft"] = {"width": bw}
        table_cell_style["borderRight"] = {"width": bw}
        fields.extend(["borderTop", "borderBottom", "borderLeft", "borderRight"])

    if "border_color" in style_options and table_cell_style:
        color = {"color": {"rgbColor": style_options["border_color"]}}
        for side in ("borderTop", "borderBottom", "borderLeft", "borderRight"):
            if side in table_cell_style:
                table_cell_style[side]["color"] = color["color"]

    if "background_color" in style_options:
        table_cell_style["backgroundColor"] = {"color": {"rgbColor": style_options["background_color"]}}
        fields.append("backgroundColor")

    if table_cell_style and fields:
        requests.append({
            "updateTableCellStyle": {
                "tableStartLocation": {"index": table_start_index},
                "tableCellStyle": table_cell_style,
                "fields": ",".join(fields)
            }
        })

    if "header_background" in style_options:
        requests.append({
            "updateTableCellStyle": {
                "tableRange": {
                    "tableCellLocation": {
                        "tableStartLocation": {"index": table_start_index},
                        "rowIndex": 0,
                        "columnIndex": 0
                    },
                    "rowSpan": 1,
                    "columnSpan": 100
                },
                "tableCellStyle": {
                    "backgroundColor": {
                        "color": {"rgbColor": style_options["header_background"]}
                    }
                },
                "fields": "backgroundColor"
            }
        })

    return requests


def extract_table_as_data(table_info: Dict[str, Any]) -> List[List[str]]:
    """
    Convert a table_info structure's 'cells' into a 2D list of strings (cell contents).
    """
    result: List[List[str]] = []
    cells = table_info.get("cells", [])
    for row in cells:
        row_data: List[str] = []
        for cell in row:
            row_data.append((cell.get("content") or "").strip())
        result.append(row_data)
    return result


def find_table_by_content(
    tables: List[Dict[str, Any]],
    search_text: str,
    case_sensitive: bool = False
) -> Optional[int]:
    """
    Return index of first table containing search_text in any cell, or None.
    """
    needle = search_text if case_sensitive else search_text.lower()
    for idx, table in enumerate(tables):
        for row in table.get("cells", []):
            for cell in row:
                content = (cell.get("content") or "")
                hay = content if case_sensitive else content.lower()
                if needle in hay:
                    return idx
    return None


def validate_table_data(data: List[List[str]]) -> Tuple[bool, str]:
    """
    Validate table data shape and limits. Returns (is_valid, message).
    """
    if not data:
        return False, "Data is empty. Use format: [['col1','col2'], ['r1c1','r1c2']]"

    if not isinstance(data, list):
        return False, f"Data must be a list, got {type(data).__name__}."

    if not all(isinstance(row, list) for row in data):
        return False, "Data must be a 2D list (list of lists). Example: [['col1','col2'], ['r1c1','r1c2']]"

    col_counts = [len(row) for row in data]
    if len(set(col_counts)) > 1:
        return False, f"All rows must have same number of columns. Found column counts: {col_counts}"

    rows = len(data)
    cols = col_counts[0] if col_counts else 0

    if rows > 1000:
        return False, f"Too many rows ({rows}). Google Docs limit is 1000 rows."

    if cols > 20:
        return False, f"Too many columns ({cols}). Google Docs limit is 20 columns."

    for r_idx, row in enumerate(data):
        for c_idx, cell in enumerate(row):
            if cell is None:
                return False, f"Cell at row {r_idx}, col {c_idx} is None. Use empty string '' for empty cells."

    return True, f"Valid table data: {rows}x{cols}"
