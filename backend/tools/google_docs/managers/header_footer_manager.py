import logging
from typing import Any, Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class HeaderFooterManager:
    """
    High-level manager for Google Docs header and footer operations.
    """

    def __init__(self, service):
        self.service = service

    def update_header_footer_content(
        self,
        document_id: str,
        section_type: str,
        content: str,
        header_footer_type: str = "DEFAULT"
    ) -> Tuple[bool, str]:
        """
        Updates header or footer content in a document.
        Returns (success, message)
        """
        logger.info(f"Updating {section_type} in document {document_id}")

        if section_type not in ["header", "footer"]:
            return False, "section_type must be 'header' or 'footer'"

        if header_footer_type not in ["DEFAULT", "FIRST_PAGE_ONLY", "EVEN_PAGE"]:
            return False, "header_footer_type must be 'DEFAULT', 'FIRST_PAGE_ONLY', or 'EVEN_PAGE'"

        try:
            doc = self._get_document(document_id)

            target_section, section_id = self._find_target_section(doc, section_type, header_footer_type)

            if not target_section:
                return False, f"No {section_type} found in document. Please create a {section_type} first in Google Docs."

            success = self._replace_section_content(document_id, target_section, content)

            if success:
                return True, f"Updated {section_type} content in document {document_id}"
            else:
                return False, f"Could not find content structure in {section_type} to update"

        except Exception as e:
            logger.error(f"Failed to update {section_type}: {str(e)}")
            return False, f"Failed to update {section_type}: {str(e)}"

    def _get_document(self, document_id: str) -> dict:
        """Get the full document data."""
        return self.service.documents().get(documentId=document_id).execute()

    def _find_target_section(
        self,
        doc: dict,
        section_type: str,
        header_footer_type: str
    ) -> Tuple[Optional[dict], Optional[str]]:
        if section_type == "header":
            sections = doc.get('headers', {})
        else:
            sections = doc.get('footers', {})

        for section_id, section_data in sections.items():
            if 'type' in section_data and section_data['type'] == header_footer_type:
                return section_data, section_id

        target_patterns = {
            "DEFAULT": ["default", "kix"],
            "FIRST_PAGE": ["first", "firstpage"],
            "EVEN_PAGE": ["even", "evenpage"],
            "FIRST_PAGE_ONLY": ["first", "firstpage"]
        }

        patterns = target_patterns.get(header_footer_type, [])
        for pattern in patterns:
            for section_id, section_data in sections.items():
                if pattern.lower() in section_id.lower():
                    return section_data, section_id

        for section_id, section_data in sections.items():
            return section_data, section_id

        return None, None

    def _replace_section_content(
        self,
        document_id: str,
        section: dict,
        new_content: str
    ) -> bool:
        content_elements = section.get('content', [])
        if not content_elements:
            return False

        first_para = self._find_first_paragraph(content_elements)
        if not first_para:
            return False

        start_index = first_para.get('startIndex', 0)
        end_index = first_para.get('endIndex', 0)

        requests = []

        if end_index > start_index:
            requests.append({
                'deleteContentRange': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': end_index - 1
                    }
                }
            })

        requests.append({
            'insertText': {
                'location': {'index': start_index},
                'text': new_content
            }
        })

        try:
            self.service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to replace section content: {str(e)}")
            return False

    def _find_first_paragraph(self, content_elements: list) -> Optional[dict]:
        for element in content_elements:
            if 'paragraph' in element:
                return element
        return None

    def get_header_footer_info(self, document_id: str) -> dict:
        try:
            doc = self._get_document(document_id)

            headers_info = {}
            for header_id, header_data in doc.get('headers', {}).items():
                headers_info[header_id] = self._extract_section_info(header_data)

            footers_info = {}
            for footer_id, footer_data in doc.get('footers', {}).items():
                footers_info[footer_id] = self._extract_section_info(footer_data)

            return {
                'headers': headers_info,
                'footers': footers_info,
                'has_headers': bool(headers_info),
                'has_footers': bool(footers_info)
            }

        except Exception as e:
            logger.error(f"Failed to get header/footer info: {str(e)}")
            return {'error': str(e)}

    def _extract_section_info(self, section_data: dict) -> dict:
        content_elements = section_data.get('content', [])

        text_content = ""
        for element in content_elements:
            if 'paragraph' in element:
                para = element['paragraph']
                for para_element in para.get('elements', []):
                    if 'textRun' in para_element:
                        text_content += para_element['textRun'].get('content', '')

        return {
            'content_preview': text_content[:100] if text_content else "(empty)",
            'element_count': len(content_elements),
            'start_index': content_elements[0].get('startIndex', 0) if content_elements else 0,
            'end_index': content_elements[-1].get('endIndex', 0) if content_elements else 0
        }

    def create_header_footer(self, document_id: str, section_type: str, header_footer_type: str = "DEFAULT") -> Tuple[bool, str]:
        if section_type not in ["header", "footer"]:
            return False, "section_type must be 'header' or 'footer'"

        type_mapping = {
            "DEFAULT": "DEFAULT",
            "FIRST_PAGE": "FIRST_PAGE",
            "EVEN_PAGE": "EVEN_PAGE",
            "FIRST_PAGE_ONLY": "FIRST_PAGE"
        }

        api_type = type_mapping.get(header_footer_type, header_footer_type)
        if api_type not in ["DEFAULT", "FIRST_PAGE", "EVEN_PAGE"]:
            return False, "header_footer_type must be 'DEFAULT', 'FIRST_PAGE', or 'EVEN_PAGE'"

        try:
            request = {'type': api_type}
            batch_request = {'createHeader': request} if section_type == "header" else {'createFooter': request}

            self.service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': [batch_request]}
            ).execute()

            return True, f"Successfully created {section_type} with type {api_type}"

        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                return False, f"A {section_type} of type {api_type} already exists in the document"
            return False, f"Failed to create {section_type}: {error_msg}"
