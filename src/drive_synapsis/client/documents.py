"""Document operations mixin for GDriveClient."""
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from ..html_converter import convert_html_to_markdown
from ..utils.constants import DEFAULT_SHEET_RANGE, EXPORT_MIME_TYPES
from typing import Any, Optional
import io
import json


class DocumentsMixin:
    """Mixin providing document-related operations."""
    
    def get_doc_structure(self, file_id: str) -> dict[str, Any]:
        """Fetch the full document structure including tabs.
        
        Args:
            file_id: The document ID.
            
        Returns:
            Raw JSON resource from Docs API.
        """
        return self.docs_service.documents().get(documentId=file_id).execute()

    def extract_text_from_element(self, element: list) -> str:
        """Recursively extract text from a Google Doc Content Element List.
        
        Args:
            element: List of content elements.
            
        Returns:
            Extracted text string.
        """
        text = ""
        for item in element:
            if 'paragraph' in item:
                for elem in item['paragraph']['elements']:
                    if 'textRun' in elem:
                        text += elem['textRun']['content']
            elif 'table' in item:
                for row in item['table']['tableRows']:
                    for cell in row['tableCells']:
                        text += self.extract_text_from_element(cell['content']) + " | "
                    text += "\n"
            elif 'sectionBreak' in item:
                pass
        return text

    def get_document_outline(self, file_id: str) -> list[dict[str, Any]]:
        """Extract the document outline (headings H1-H6).
        
        Args:
            file_id: The document ID.
            
        Returns:
            List of dicts with 'level', 'text', 'startIndex', 'endIndex'.
        """
        doc = self.get_doc_structure(file_id)
        outline = []
        
        tabs = doc.get('tabs', [])
        if tabs:
            content_list = tabs[0].get('documentTab', {}).get('body', {}).get('content', [])
        else:
            content_list = doc.get('body', {}).get('content', [])
        
        for item in content_list:
            if 'paragraph' in item:
                para = item['paragraph']
                style = para.get('paragraphStyle', {})
                heading_id = style.get('namedStyleType', '')
                
                if heading_id.startswith('HEADING_'):
                    level = int(heading_id.split('_')[1]) if heading_id.split('_')[1].isdigit() else 0
                    
                    text = ""
                    for elem in para.get('elements', []):
                        if 'textRun' in elem:
                            text += elem['textRun']['content']
                    
                    text = text.strip()
                    if text:
                        outline.append({
                            'level': level,
                            'text': text,
                            'startIndex': item.get('startIndex'),
                            'endIndex': item.get('endIndex')
                        })
        
        return outline

    def read_document_section(self, file_id: str, start_index: int, end_index: int) -> str:
        """Read content between two indices in a document.
        
        Args:
            file_id: The document ID.
            start_index: Starting index.
            end_index: Ending index.
            
        Returns:
            Extracted text from the section.
        """
        doc = self.get_doc_structure(file_id)
        
        tabs = doc.get('tabs', [])
        if tabs:
            content_list = tabs[0].get('documentTab', {}).get('body', {}).get('content', [])
        else:
            content_list = doc.get('body', {}).get('content', [])
        
        section_items = []
        for item in content_list:
            item_start = item.get('startIndex', 0)
            item_end = item.get('endIndex', 0)
            if item_start < end_index and item_end > start_index:
                section_items.append(item)
        
        return self.extract_text_from_element(section_items)

    def read_file(self, file_id: str) -> str:
        """Read file content. Exports Docs to Markdown, Sheets to CSV.
        
        Args:
            file_id: The file ID.
            
        Returns:
            File content as string with header.
        """
        file_meta = self.drive_service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
        mime_type = file_meta.get('mimeType')
        
        content = None
        
        if mime_type == 'application/vnd.google-apps.document':
            request = self.drive_service.files().export_media(fileId=file_id, mimeType='text/markdown')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            content = fh.getvalue().decode('utf-8')
            
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            request = self.drive_service.files().export_media(fileId=file_id, mimeType='text/csv')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            content = fh.getvalue().decode('utf-8')
            
        else:
            return f"[UNSUPPORTED MIME TYPE: {mime_type}]"

        return f"# File: {file_meta.get('name')}\n\n{content}"

    def create_doc(self, title: str, text: str) -> str:
        """Create a new Google Doc with content.
        
        Args:
            title: Document title.
            text: Initial text content.
            
        Returns:
            Success message with document ID.
        """
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document'
        }
        file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        file_id = file.get('id')
        
        requests = [{
            'insertText': {
                'location': {'index': 1},
                'text': text
            }
        }]
        
        self.docs_service.documents().batchUpdate(
            documentId=file_id, body={'requests': requests}
        ).execute()
            
        return f"Document created successfully. ID: {file_id}"

    def update_doc(self, file_id: str, content: str) -> None:
        """Overwrite Google Doc content with Markdown.
        
        Args:
            file_id: The document ID.
            content: Markdown content.
        """
        fh = io.BytesIO(content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='text/markdown', resumable=True)
        body = {'mimeType': 'application/vnd.google-apps.document'}
        
        self.drive_service.files().update(
            fileId=file_id,
            body=body,
            media_body=media,
        ).execute()

    def update_tab_content(self, file_id: str, tab_id: str, text: str) -> str:
        """Replace the content of a specific tab with plain text.
        
        Args:
            file_id: The document ID.
            tab_id: The tab ID.
            text: New text content.
            
        Returns:
            Success message.
        """
        doc = self.docs_service.documents().get(documentId=file_id).execute()
        
        tabs = doc.get('tabs', [])
        target_tab = next((t for t in tabs if t['tabProperties']['tabId'] == tab_id), None)
        
        if not target_tab:
            raise ValueError(f"Tab ID {tab_id} not found in document.")
            
        content_list = target_tab.get('documentTab', {}).get('body', {}).get('content', [])
        if not content_list:
            end_index = 1
        else:
            end_index = content_list[-1].get('endIndex') - 1
            
        requests = [
            {
                'deleteContentRange': {
                    'range': {
                        'segmentId': tab_id,
                        'startIndex': 1,
                        'endIndex': max(1, end_index) 
                    }
                }
            },
            {
                'insertText': {
                    'location': {'segmentId': tab_id, 'index': 1},
                    'text': text
                }
            }
        ]
        
        if end_index <= 1:
            requests = [requests[1]]

        self.docs_service.documents().batchUpdate(
            documentId=file_id, body={'requests': requests}
        ).execute()
        
        return f"Updated tab {tab_id} in document {file_id}"

    def append_text_to_doc(self, file_id: str, text: str) -> str:
        """Append text to the end of a Google Doc.
        
        Args:
            file_id: The document ID.
            text: Text to append.
            
        Returns:
            Success message.
        """
        doc = self.docs_service.documents().get(documentId=file_id).execute()
        content_list = doc.get('body').get('content')
        end_index = content_list[-1].get('endIndex') - 1

        requests = [{
            'insertText': {
                'location': {'index': end_index},
                'text': text
            }
        }]
        
        self.docs_service.documents().batchUpdate(
            documentId=file_id, body={'requests': requests}
        ).execute()
        
        return f"Appended text to document {file_id}"

    def replace_text_in_doc(self, file_id: str, find: str, replace: str, match_case: bool = False) -> str:
        """Find and replace text in a Google Doc.
        
        Args:
            file_id: The document ID.
            find: Text to find.
            replace: Replacement text.
            match_case: Whether search is case-sensitive.
            
        Returns:
            Message with replacement count.
        """
        requests = [{
            'replaceAllText': {
                'containsText': {'text': find, 'matchCase': match_case},
                'replaceText': replace
            }
        }]
        
        result = self.docs_service.documents().batchUpdate(
            documentId=file_id, body={'requests': requests}
        ).execute()
        
        replacements = result.get('replies', [{}])[0].get('replaceAllText', {}).get('occurrencesChanged', 0)
        return f"Replaced {replacements} occurrence(s) of '{find}' with '{replace}'"

    def insert_table(self, file_id: str, rows: int, cols: int, index: int = 1) -> str:
        """Insert a table into a Google Doc.
        
        Args:
            file_id: The document ID.
            rows: Number of rows.
            cols: Number of columns.
            index: Position to insert.
            
        Returns:
            Success message.
        """
        requests = [{
            'insertTable': {
                'rows': rows,
                'columns': cols,
                'location': {'index': index}
            }
        }]
        
        self.docs_service.documents().batchUpdate(
            documentId=file_id, body={'requests': requests}
        ).execute()
        
        return f"Inserted {rows}x{cols} table at index {index}"

    def create_from_template(self, template_id: str, title: str, replacements: dict) -> str:
        """Create a new doc from a template with replacements.
        
        Args:
            template_id: The template document ID.
            title: New document title.
            replacements: Dict of placeholder -> value.
            
        Returns:
            Success message with new document ID.
        """
        copy_body = {'name': title}
        new_file = self.drive_service.files().copy(fileId=template_id, body=copy_body).execute()
        new_file_id = new_file.get('id')

        requests = []
        for key, value in replacements.items():
            requests.append({
                'replaceAllText': {
                    'containsText': {'text': key, 'matchCase': True},
                    'replaceText': value
                }
            })
            
        if requests:
            self.docs_service.documents().batchUpdate(
                documentId=new_file_id, body={'requests': requests}
            ).execute()
                
        return f"Created document '{title}' from template. ID: {new_file_id}"

    def _download_media(self, file_id: str, mime_type: str, encoding: Optional[str] = None):
        """Helper for media download.
        
        Args:
            file_id: The file ID.
            mime_type: Target MIME type.
            encoding: Optional encoding for text.
            
        Returns:
            Bytes or decoded string.
        """
        request = self.drive_service.files().export_media(fileId=file_id, mimeType=mime_type)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        if encoding:
            return fh.getvalue().decode(encoding)
        return fh.getvalue()

    def download_doc(self, file_id: str, format_type: str = 'markdown') -> str:
        """Download Google Doc/Sheet content in specified format.
        
        Args:
            file_id: The file ID.
            format_type: 'markdown', 'html', 'pdf', 'docx', 'csv', 'xlsx', 'json'.
            
        Returns:
            Content in requested format.
        """
        mime_map = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'html': 'text/html',
            'rtf': 'application/rtf',
            'odt': 'application/vnd.oasis.opendocument.text',
            'markdown': 'text/markdown',
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'json': 'application/json'
        }

        target_mime = mime_map.get(format_type.lower())
        if not target_mime:
            raise ValueError(f"Unsupported format: {format_type}")
        
        file_meta = self.drive_service.files().get(fileId=file_id, fields="mimeType, name").execute()
        source_mime = file_meta.get('mimeType')

        # Special Case: Markdown via HTML
        if format_type == 'markdown' and source_mime == 'application/vnd.google-apps.document':
            html_content = self._download_media(file_id, 'text/html', 'utf-8')
            if not html_content:
                return ""
            return convert_html_to_markdown(html_content)

        # Special Case: JSON for Sheets
        if format_type == 'json' and source_mime == 'application/vnd.google-apps.spreadsheet':
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=file_id, range=DEFAULT_SHEET_RANGE
            ).execute()
            values = result.get('values', [])
            if not values:
                return "[]"
            headers = values[0]
            data = []
            for row in values[1:]:
                item = {h: (row[i] if i < len(row) else "") for i, h in enumerate(headers)}
                data.append(item)
            return json.dumps(data, indent=2)

        return self._download_media(file_id, target_mime, encoding='utf-8')
