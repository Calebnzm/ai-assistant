import logging
from typing import List, Dict, Any, Tuple

from tools.google_docs.helpers import create_insert_table_request
from tools.google_docs.structures import find_tables
from tools.google_docs.tables import validate_table_data

logger = logging.getLogger(__name__)


class TableOperationManager:
    """
    High-level manager for Google Docs table operations.
    """

    def __init__(self, service):
        self.service = service

    def create_and_populate_table(
        self,
        document_id: str,
        table_data: List[List[str]],
        index: int,
        bold_headers: bool = True
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Creates a table and populates it with data in a reliable multi-step process.
        Returns (success, message, metadata)
        """
        logger.debug(
            f"Creating table at index {index}, dimensions: {len(table_data)}x"
            f"{len(table_data[0]) if table_data and len(table_data) > 0 else 0}"
        )

        is_valid, error_msg = validate_table_data(table_data)
        if not is_valid:
            return False, f"Invalid table data: {error_msg}", {}

        rows = len(table_data)
        cols = len(table_data[0])

        try:
            self._create_empty_table(document_id, index, rows, cols)

            fresh_tables = self._get_document_tables(document_id)
            if not fresh_tables:
                return False, "Could not find table after creation", {}

            population_count = self._populate_table_cells(document_id, table_data, bold_headers)

            metadata = {
                'rows': rows,
                'columns': cols,
                'populated_cells': population_count,
                'table_index': len(fresh_tables) - 1
            }

            return True, f"Successfully created {rows}x{cols} table and populated {population_count} cells", metadata

        except Exception as e:
            logger.error(f"Failed to create and populate table: {str(e)}")
            return False, f"Table creation failed: {str(e)}", {}

    def _create_empty_table(
        self,
        document_id: str,
        index: int,
        rows: int,
        cols: int
    ) -> None:
        """Create an empty table at the specified index."""
        logger.debug(f"Creating {rows}x{cols} table at index {index}")
        self.service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': [create_insert_table_request(index, rows, cols)]}
        ).execute()

    def _get_document_tables(self, document_id: str) -> List[Dict[str, Any]]:
        """Get fresh document structure and extract table information."""
        doc = self.service.documents().get(documentId=document_id).execute()
        return find_tables(doc)

    def _populate_table_cells(
        self,
        document_id: str,
        table_data: List[List[str]],
        bold_headers: bool
    ) -> int:
        """
        Populate table cells with data, refreshing structure before each insertion.
        """
        population_count = 0

        for row_idx, row_data in enumerate(table_data):
            logger.debug(f"Processing row {row_idx}: {len(row_data)} cells")
            for col_idx, cell_text in enumerate(row_data):
                if not cell_text:
                    continue

                try:
                    success = self._populate_single_cell(
                        document_id, row_idx, col_idx, cell_text, bold_headers and row_idx == 0
                    )

                    if success:
                        population_count += 1
                        logger.debug(f"Populated cell ({row_idx},{col_idx})")
                    else:
                        logger.warning(f"Failed to populate cell ({row_idx},{col_idx})")

                except Exception as e:
                    logger.error(f"Error populating cell ({row_idx},{col_idx}): {str(e)}")

        return population_count

    def _populate_single_cell(
        self,
        document_id: str,
        row_idx: int,
        col_idx: int,
        cell_text: str,
        apply_bold: bool = False
    ) -> bool:
        """
        Populate a single cell with text, with optional bold formatting.
        Returns True if successful, False otherwise.
        """
        try:
            tables = self._get_document_tables(document_id)
            if not tables:
                return False

            table = tables[-1]
            cells = table.get('cells', [])

            if row_idx >= len(cells) or col_idx >= len(cells[row_idx]):
                logger.error(f"Cell ({row_idx},{col_idx}) out of bounds")
                return False

            cell = cells[row_idx][col_idx]
            insertion_index = cell.get('insertion_index')

            if not insertion_index:
                logger.warning(f"No insertion_index for cell ({row_idx},{col_idx})")
                return False

            self.service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': [{
                    'insertText': {
                        'location': {'index': insertion_index},
                        'text': cell_text
                    }
                }]}
            ).execute()

            if apply_bold:
                self._apply_bold_formatting(document_id, insertion_index, insertion_index + len(cell_text))

            return True

        except Exception as e:
            logger.error(f"Failed to populate single cell: {str(e)}")
            return False

    def _apply_bold_formatting(self, document_id: str, start_index: int, end_index: int) -> None:
        """Apply bold formatting to a text range."""
        self.service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': [{
                'updateTextStyle': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': end_index
                    },
                    'textStyle': {'bold': True},
                    'fields': 'bold'
                }
            }]}
        ).execute()

    def populate_existing_table(
        self,
        document_id: str,
        table_index: int,
        table_data: List[List[str]],
        clear_existing: bool = False
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Populate an existing table with data.
        Returns (success, message, metadata)
        """
        try:
            tables = self._get_document_tables(document_id)
            if table_index >= len(tables):
                return False, f"Table index {table_index} not found. Document has {len(tables)} tables", {}

            table_info = tables[table_index]

            table_rows = table_info['rows']
            table_cols = table_info['columns']
            data_rows = len(table_data)
            data_cols = len(table_data[0]) if table_data else 0

            if data_rows > table_rows or data_cols > table_cols:
                return False, f"Data ({data_rows}x{data_cols}) exceeds table dimensions ({table_rows}x{table_cols})", {}

            population_count = self._populate_existing_table_cells(document_id, table_index, table_data)

            metadata = {
                'table_index': table_index,
                'populated_cells': population_count,
                'table_dimensions': f"{table_rows}x{table_cols}",
                'data_dimensions': f"{data_rows}x{data_cols}"
            }

            return True, f"Successfully populated {population_count} cells in existing table", metadata

        except Exception as e:
            return False, f"Failed to populate existing table: {str(e)}", {}

    def _populate_existing_table_cells(
        self,
        document_id: str,
        table_index: int,
        table_data: List[List[str]]
    ) -> int:
        """Populate cells in an existing table."""
        population_count = 0

        for row_idx, row_data in enumerate(table_data):
            for col_idx, cell_text in enumerate(row_data):
                if not cell_text:
                    continue

                tables = self._get_document_tables(document_id)
                if table_index >= len(tables):
                    break

                table = tables[table_index]
                cells = table.get('cells', [])

                if row_idx >= len(cells) or col_idx >= len(cells[row_idx]):
                    continue

                cell = cells[row_idx][col_idx]
                cell_end = cell['end_index'] - 1

                try:
                    self.service.documents().batchUpdate(
                        documentId=document_id,
                        body={'requests': [{
                            'insertText': {
                                'location': {'index': cell_end},
                                'text': cell_text
                            }
                        }]}
                    ).execute()
                    population_count += 1

                except Exception as e:
                    logger.error(f"Failed to populate existing cell ({row_idx},{col_idx}): {str(e)}")

        return population_count
