from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload, MediaFileUpload
from auth import get_creds
from html_converter import convert_html_to_markdown
from utils.constants import (
    DEFAULT_SHEET_RANGE,
    DEFAULT_SNIPPET_LENGTH,
    DEFAULT_MAX_WORKERS,
    EXPORT_MIME_TYPES,
)
from typing import Optional, Any
import io
import json
import concurrent.futures
import os


class GDriveClient:
    """Client for interacting with Google Drive, Docs, and Sheets APIs."""
    
    def __init__(self) -> None:
        """Initialize the client with authenticated Google API services."""
        self.creds = get_creds()
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)
        self.sheets_service = build('sheets', 'v4', credentials=self.creds)

    def search_files(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search for files using Drive Query Language.
        
        Args:
            query: Search string to match against file names and content.
            limit: Maximum number of results to return.
            
        Returns:
            List of file metadata dictionaries.
        """
        # Construct query. Ensure not trashed.
        drive_query = f"(name contains '{query}' or fullText contains '{query}') and trashed = false"
        
        results = self.drive_service.files().list(
            q=drive_query,
            pageSize=limit,
            fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime, parents)"
        ).execute()
        
        return results.get('files', [])

    def search_files_advanced(
        self,
        query: str,
        file_type: Optional[str] = None,
        modified_after: Optional[str] = None,
        owner: str = 'me',
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Advanced search with filters.
        Args:
            query: Search query.
            file_type: 'doc', 'sheet', 'folder', 'pdf', etc.
            modified_after: ISO date string (e.g. '2024-01-01').
            owner: 'me' or 'anyone'.
            limit: Max results.
        """
        # Build query parts
        query_parts = [f"(name contains '{query}' or fullText contains '{query}')"]
        query_parts.append("trashed = false")
        
        # File type filter
        if file_type:
            mime_map = {
                'doc': 'application/vnd.google-apps.document',
                'sheet': 'application/vnd.google-apps.spreadsheet',
                'folder': 'application/vnd.google-apps.folder',
                'pdf': 'application/pdf',
                'image': 'image/',
            }
            if file_type in mime_map:
                mime = mime_map[file_type]
                if file_type == 'image':
                    query_parts.append(f"mimeType contains '{mime}'")
                else:
                    query_parts.append(f"mimeType = '{mime}'")
        
        # Modified after filter
        if modified_after:
            query_parts.append(f"modifiedTime > '{modified_after}T00:00:00'")
        
        # Owner filter
        if owner == 'me':
            query_parts.append("'me' in owners")
        
        drive_query = ' and '.join(query_parts)
        
        results = self.drive_service.files().list(
            q=drive_query,
            pageSize=limit,
            fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime, parents)"
        ).execute()
        
        return results.get('files', [])

    def search_in_folder(self, folder_id: str, query: str, limit: int = 10):
        """
        Search for files within a specific folder.
        """
        drive_query = f"'{folder_id}' in parents and (name contains '{query}' or fullText contains '{query}') and trashed = false"
        
        results = self.drive_service.files().list(
            q=drive_query,
            pageSize=limit,
            fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime)"
        ).execute()
        
        return results.get('files', [])

    def get_folder_id(self, folder_name: str) -> str:
        """
        Find a folder ID by exact name match.
        """
        query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false"
        results = self.drive_service.files().list(q=query, pageSize=1, fields="files(id)").execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None

    def list_folder_contents(self, folder_id: str) -> list:
        """
        List all children of a folder (non-recursive).
        Returns list of files with name, id, mimeType.
        """
        query = f"'{folder_id}' in parents and trashed = false"
        results = []
        page_token = None
        while True:
            response = self.drive_service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token
            ).execute()
            results.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        return results

    def get_file_comments(self, file_id: str) -> list:
        """
        Fetch all comments for a file.
        Returns a list of comment objects with content, author, and quoted content context.
        """
        try:
            # comments.list returns a list of comments
            # fields=* is heavy, so we select what we need
            fields = "comments(id, content, author(displayName), createdTime, quotedFileContent, replies(content, author(displayName), createdTime))"
            results = self.drive_service.comments().list(
                fileId=file_id, 
                fields=fields,
                pageSize=100 
            ).execute()
            return results.get('comments', [])
        except Exception as e:
            # If comments are disabled or error occurs, return empty list or re-raise
            # Often rate limits or permissions issue.
            print(f"Warning: Could not fetch comments for {file_id}: {e}")
            return []

    def create_comment(self, file_id: str, content: str, quoted_text: str = None) -> str:
        """
        Create a new comment on a file.
        Args:
            file_id: The ID of the file.
            content: The comment text.
            quoted_text: Optional text to anchor the comment to (for Docs).
        """
        try:
            comment_body = {
                'content': content
            }
            
            # If quoted text is provided, try to anchor it
            if quoted_text:
                comment_body['quotedFileContent'] = {
                    'mimeType': 'text/plain',
                    'value': quoted_text
                }
            
            result = self.drive_service.comments().create(
                fileId=file_id,
                body=comment_body,
                fields='id,content,createdTime'
            ).execute()
            
            return f"Comment created (ID: {result.get('id')}) at {result.get('createdTime')}"
        except Exception as e:
            return f"Error creating comment: {str(e)}"

    def reply_to_comment(self, file_id: str, comment_id: str, content: str) -> str:
        """
        Reply to an existing comment.
        Args:
            file_id: The ID of the file.
            comment_id: The ID of the comment to reply to.
            content: The reply text.
        """
        try:
            reply_body = {
                'content': content
            }
            
            result = self.drive_service.replies().create(
                fileId=file_id,
                commentId=comment_id,
                body=reply_body,
                fields='id,content,createdTime'
            ).execute()
            
            return f"Reply created (ID: {result.get('id')}) at {result.get('createdTime')}"
        except Exception as e:
            return f"Error creating reply: {str(e)}"


    def get_doc_structure(self, file_id: str) -> dict:
        """
        Fetch the full document structure including tabs.
        Returns the raw JSON resource.
        """
        return self.docs_service.documents().get(documentId=file_id).execute()

    def extract_text_from_element(self, element: list) -> str:
        """
        Recursively extract text from a Google Doc Content Element List.
        """
        text = ""
        for item in element:
            if 'paragraph' in item:
                for elem in item['paragraph']['elements']:
                    if 'textRun' in elem:
                        text += elem['textRun']['content']
            elif 'table' in item:
                # Naive table text extraction
                for row in item['table']['tableRows']:
                    for cell in row['tableCells']:
                        text += self.extract_text_from_element(cell['content']) + " | "
                    text += "\n"
            elif 'sectionBreak' in item:
                pass # Ignore section breaks
        return text

    def get_document_outline(self, file_id: str) -> list[dict]:
        """
        Extract the document outline (headings H1-H6) for navigation.
        Returns a list of dicts with 'level', 'text', 'startIndex', 'endIndex'.
        """
        doc = self.get_doc_structure(file_id)
        outline = []
        
        # For multi-tab docs, we'll only process the first tab for simplicity
        # or process all tabs and mark them
        tabs = doc.get('tabs', [])
        if tabs:
            # Process first tab
            content_list = tabs[0].get('documentTab', {}).get('body', {}).get('content', [])
        else:
            # Legacy single-tab doc
            content_list = doc.get('body', {}).get('content', [])
        
        for item in content_list:
            if 'paragraph' in item:
                para = item['paragraph']
                style = para.get('paragraphStyle', {})
                heading_id = style.get('namedStyleType', '')
                
                # Check if it's a heading
                if heading_id.startswith('HEADING_'):
                    level = int(heading_id.split('_')[1]) if heading_id.split('_')[1].isdigit() else 0
                    
                    # Extract text
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
        """
        Read content between two indices in a document.
        Useful for reading a specific section after getting the outline.
        """
        doc = self.get_doc_structure(file_id)
        
        # Get content list
        tabs = doc.get('tabs', [])
        if tabs:
            content_list = tabs[0].get('documentTab', {}).get('body', {}).get('content', [])
        else:
            content_list = doc.get('body', {}).get('content', [])
        
        # Filter items within range
        section_items = []
        for item in content_list:
            item_start = item.get('startIndex', 0)
            item_end = item.get('endIndex', 0)
            
            # Include if overlaps with our range
            if item_start < end_index and item_end > start_index:
                section_items.append(item)
        
        # Extract text
        return self.extract_text_from_element(section_items)

    def read_file(self, file_id: str):
        """
        Read file content. Exports Docs to Markdown, Sheets to CSV.
        """
        # 1. Get metadata to check mimeType
        file_meta = self.drive_service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
        mime_type = file_meta.get('mimeType')
        
        content = None
        
        if mime_type == 'application/vnd.google-apps.document':
            # Export to Markdown
            request = self.drive_service.files().export_media(
                fileId=file_id, mimeType='text/markdown')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            content = fh.getvalue().decode('utf-8')
            
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            # Export to CSV (only first sheet usually)
            request = self.drive_service.files().export_media(
                fileId=file_id, mimeType='text/csv')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            content = fh.getvalue().decode('utf-8')
            
        else:
            # Try plain text or binary
            # For PoC we might just say unsupported or try text/plain export
             return f"[UNSUPPORTED MIME TYPE: {mime_type}]"

        return f"# File: {file_meta.get('name')}\n\n{content}"
    def create_doc(self, title: str, text: str):
        """
        Two-step creation:
        1. Create empty file wrapper.
        2. Insert text via Docs API.
        """
        # Step 1: Create Container
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document'
        }
        file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        file_id = file.get('id')
        
        # Step 2: Content Injection
        # Note: Index 1 is the start of the body for a new doc.
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1,
                    },
                    'text': text
                }
            }
        ]
        
        self.docs_service.documents().batchUpdate(
            documentId=file_id, body={'requests': requests}).execute()
            
        return f"Document created successfully. ID: {file_id}"


    def create_sheet(self, title: str, data: list[list[str]]):
        """
        Create a sheet and upload initial data.
        data example: [['Header1', 'Header2'], ['Val1', 'Val2']]
        """
        # Step 1: Create Container
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }
        file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        file_id = file.get('id')
        
        # Step 2: Update Values
        body = {
            'values': data
        }
        result = self.sheets_service.spreadsheets().values().update(
            spreadsheetId=file_id, range="A1",
            valueInputOption="USER_ENTERED", body=body).execute()
            
        return f"Sheet created successfully. ID: {file_id}"

    def update_sheet_values(self, spreadsheet_id: str, range_name: str, values: list[list[str]]):
        """
        Update values in a Google Sheet.
        Args:
            spreadsheet_id: The ID of the sheet.
            range_name: The A1 notation of the values to update.
            values: A list of lists of values to write.
        """
        body = {
            'values': values
        }
        result = self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption="USER_ENTERED", body=body).execute()
        return f"Updated {result.get('updatedCells')} cells in range {range_name}."

    def read_sheet_values(self, spreadsheet_id: str, range_name: str) -> list[list[str]]:
        """
        Read values from a specific range in a Google Sheet.
        Returns a list of lists.
        """
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        return result.get('values', [])

    def append_sheet_rows(self, spreadsheet_id: str, range_name: str, values: list[list[str]]):
        """
        Append rows to the end of a range (doesn't overwrite).
        """
        body = {'values': values}
        result = self.sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        return f"Appended {result.get('updates', {}).get('updatedRows', 0)} rows."

    def insert_sheet_rows(self, spreadsheet_id: str, sheet_id: int, start_index: int, row_count: int):
        """
        Insert blank rows at a specific position.
        """
        requests = [{
            'insertDimension': {
                'range': {
                    'sheetId': sheet_id,
                    'dimension': 'ROWS',
                    'startIndex': start_index,
                    'endIndex': start_index + row_count
                }
            }
        }]
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        return f"Inserted {row_count} rows at index {start_index}."

    def add_sheet_tab(self, spreadsheet_id: str, tab_name: str):
        """
        Add a new tab to an existing spreadsheet.
        """
        requests = [{
            'addSheet': {
                'properties': {
                    'title': tab_name
                }
            }
        }]
        result = self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        new_sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']
        return f"Added tab '{tab_name}' (Sheet ID: {new_sheet_id})."

    def format_sheet_range(self, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, bold: bool = False, background_color: str = None) -> str:
        """
        Apply formatting to a range in a spreadsheet.
        Args:
            sheet_id: The sheet ID (not spreadsheet ID).
            background_color: Hex color like '#FF0000' or None.
        """
        requests = []
        
        # Build cell format
        cell_format = {}
        if bold:
            cell_format['textFormat'] = {'bold': True}
        if background_color:
            # Convert hex to RGB
            color_hex = background_color.lstrip('#')
            r = int(color_hex[0:2], 16) / 255.0
            g = int(color_hex[2:4], 16) / 255.0
            b = int(color_hex[4:6], 16) / 255.0
            cell_format['backgroundColor'] = {'red': r, 'green': g, 'blue': b}
        
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': start_row,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col
                },
                'cell': {'userEnteredFormat': cell_format},
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        })
        
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        return f"Formatted range (rows {start_row}-{end_row}, cols {start_col}-{end_col})"

    def protect_sheet_range(self, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, description: str = 'Protected range') -> str:
        """
        Protect a range from editing.
        """
        requests = [{
            'addProtectedRange': {
                'protectedRange': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': start_row,
                        'endRowIndex': end_row,
                        'startColumnIndex': start_col,
                        'endColumnIndex': end_col
                    },
                    'description': description,
                    'warningOnly': True
                }
            }
        }]
        
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        return f"Protected range: {description}"

    def move_file(self, file_id: str, new_folder_id: str) -> str:
        """
        Move a file to a different folder.
        """
        # Get current parents
        file = self.drive_service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents', []))
        
        # Move to new folder
        self.drive_service.files().update(
            fileId=file_id,
            addParents=new_folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        
        return f"Moved file to folder {new_folder_id}"

    def rename_file(self, file_id: str, new_name: str) -> str:
        """
        Rename a file without changing its location or content.
        """
        self.drive_service.files().update(
            fileId=file_id,
            body={'name': new_name}
        ).execute()
        
        return f"Renamed to '{new_name}'"

    def delete_file(self, file_id: str, permanent: bool = False) -> str:
        """
        Delete a file. By default moves to trash (recoverable).
        """
        if permanent:
            self.drive_service.files().delete(fileId=file_id).execute()
            return "Permanently deleted"
        else:
            self.drive_service.files().update(
                fileId=file_id,
                body={'trashed': True}
            ).execute()
            return "Moved to trash (recoverable via Drive UI)"

    def copy_file(self, file_id: str, new_name: str, folder_id: str = None) -> dict:
        """
        Create a copy of a file with a new name.
        """
        body = {'name': new_name}
        if folder_id:
            body['parents'] = [folder_id]
        
        result = self.drive_service.files().copy(
            fileId=file_id,
            body=body,
            fields='id, name, webViewLink'
        ).execute()
        
        return result

    def get_file_metadata(self, file_id: str) -> dict:
        """
        Get comprehensive metadata about a file.
        """
        return self.drive_service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, size, createdTime, modifiedTime, owners, parents, starred, trashed, webViewLink'
        ).execute()

    def star_file(self, file_id: str, starred: bool = True) -> str:
        """
        Star or unstar a file for quick access.
        """
        self.drive_service.files().update(
            fileId=file_id,
            body={'starred': starred}
        ).execute()
        
        return f"File {'starred' if starred else 'unstarred'}"

    def share_file(self, file_id: str, email: str, role: str = 'reader') -> str:
        """
        Share a file with a user via email.
        Args:
            file_id: The file ID.
            email: Email address of the user.
            role: 'reader', 'writer', or 'commenter'.
        """
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }
        
        self.drive_service.permissions().create(
            fileId=file_id,
            body=permission,
            sendNotificationEmail=True
        ).execute()
        
        return f"Shared with {email} as {role}"

    def make_file_public(self, file_id: str) -> str:
        """
        Make a file publicly accessible (anyone with link can view).
        Returns the shareable link.
        """
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        
        self.drive_service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()
        
        # Get the web view link
        file_meta = self.drive_service.files().get(
            fileId=file_id,
            fields='webViewLink'
        ).execute()
        
        return f"Public link: {file_meta.get('webViewLink')}"

    def revoke_access(self, file_id: str, email: str) -> str:
        """
        Remove a user's access to a file.
        """
        # List permissions to find the permission ID for this email
        permissions = self.drive_service.permissions().list(
            fileId=file_id,
            fields='permissions(id, emailAddress)'
        ).execute()
        
        for perm in permissions.get('permissions', []):
            if perm.get('emailAddress') == email:
                self.drive_service.permissions().delete(
                    fileId=file_id,
                    permissionId=perm['id']
                ).execute()
                return f"Revoked access for {email}"
        
        return f"No permission found for {email}"

    def list_permissions(self, file_id: str) -> list[dict]:
        """
        List all users who have access to a file.
        """
        result = self.drive_service.permissions().list(
            fileId=file_id,
            fields='permissions(id, emailAddress, role, type)'
        ).execute()
        
        return result.get('permissions', [])

    def replace_text_in_doc(self, file_id: str, find: str, replace: str, match_case: bool = False) -> str:
        """
        Find and replace text in a Google Doc.
        """
        requests = [{
            'replaceAllText': {
                'containsText': {
                    'text': find,
                    'matchCase': match_case
                },
                'replaceText': replace
            }
        }]
        
        result = self.docs_service.documents().batchUpdate(
            documentId=file_id,
            body={'requests': requests}
        ).execute()
        
        # Count replacements
        replacements = result.get('replies', [{}])[0].get('replaceAllText', {}).get('occurrencesChanged', 0)
        return f"Replaced {replacements} occurrence(s) of '{find}' with '{replace}'"

    def insert_table(self, file_id: str, rows: int, cols: int, index: int = 1) -> str:
        """
        Insert a table into a Google Doc at a specific index.
        """
        requests = [{
            'insertTable': {
                'rows': rows,
                'columns': cols,
                'location': {
                    'index': index
                }
            }
        }]
        
        self.docs_service.documents().batchUpdate(
            documentId=file_id,
            body={'requests': requests}
        ).execute()
        
        return f"Inserted {rows}x{cols} table at index {index}"

    def set_file_description(self, file_id: str, description: str) -> str:
        """
        Set or update a file's description.
        """
        self.drive_service.files().update(
            fileId=file_id,
            body={'description': description}
        ).execute()
        
        return f"Updated description"
    def get_file_version(self, file_id: str) -> int:
        """
        Get the current version of the file from Drive metadata.
        """
        file_meta = self.drive_service.files().get(
            fileId=file_id, fields="version").execute()
        return int(file_meta.get('version', 0))

    def update_doc(self, file_id: str, content: str):
        """
        Overwrite Google Doc content with new Markdown content.
        Uses MediaIoBaseUpload with text/markdown mimeType to trigger conversion.
        """

        # Prepare content
        fh = io.BytesIO(content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='text/markdown', resumable=True)

        # Update file
        # Explicitly set the target mimeType to ensure it acts as a conversion
        body = {'mimeType': 'application/vnd.google-apps.document'}
        
        self.drive_service.files().update(
            fileId=file_id,
            body=body,
            media_body=media,
        ).execute()

    def upload_file(self, local_path: str, parent_id: str = None) -> dict:
        """
        Upload any file to Drive.
        """
        
        name = os.path.basename(local_path)
        file_metadata = {'name': name}
        if parent_id:
            file_metadata['parents'] = [parent_id]
            
        media = MediaFileUpload(local_path, resumable=True)
        
        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        return file

    def update_file_media(self, file_id: str, local_path: str):
        """
        Update the content of an existing file (binary/text).
        """
        
        media = MediaFileUpload(local_path, resumable=True)
        
        self.drive_service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()

    def update_tab_content(self, file_id: str, tab_id: str, text: str):
        """
        Replace the content of a specific tab with plain text.
        Strategy: Select All -> Delete -> Insert Text.
        """
        # 1. Get tab bounds to ensure we delete everything
        # Note: We can't easily "Select All" without knowing the length, so we just use a large range 
        # or fetch the doc structure first. Fetching is safer.
        doc = self.docs_service.documents().get(documentId=file_id).execute()
        
        tabs = doc.get('tabs', [])
        target_tab = next((t for t in tabs if t['tabProperties']['tabId'] == tab_id), None)
        
        if not target_tab:
            # Maybe it's the default tab (legacy)? 
            # If tab_id is empty or 'default', we might target the main body.
            # But the caller should have provided a valid ID.
            raise ValueError(f"Tab ID {tab_id} not found in document.")
            
        content_list = target_tab.get('documentTab', {}).get('body', {}).get('content', [])
        if not content_list:
            end_index = 1
        else:
            # The last element is always a section break or similar, causing end_index to be the doc length
            end_index = content_list[-1].get('endIndex') - 1
            
        requests = [
            # 1. Delete existing content (Index 1 to End)
             {
                'deleteContentRange': {
                    'range': {
                         'segmentId': tab_id,
                         'startIndex': 1,
                         'endIndex': max(1, end_index) 
                    }
                }
            },
            # 2. Insert new text
            {
                'insertText': {
                    'location': {
                        'segmentId': tab_id,
                        'index': 1,
                    },
                    'text': text
                }
            }
        ]
        
        # Optimize: If file is empty (end_index <= 1), skip delete
        if end_index <= 1:
            requests = [requests[1]]

        self.docs_service.documents().batchUpdate(
            documentId=file_id, body={'requests': requests}).execute()
        
        return f"Updated tab {tab_id} in document {file_id}"

    def append_text_to_doc(self, file_id: str, text: str):
        """
        Append text to the end of a Google Doc.
        """
        # 1. Get document bounds
        doc = self.docs_service.documents().get(documentId=file_id).execute()
        content_list = doc.get('body').get('content')
        end_index = content_list[-1].get('endIndex') - 1 # Insert before the final newline

        # 2. Insert text
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': end_index,
                    },
                    'text': text
                }
            }
        ]
        
        self.docs_service.documents().batchUpdate(
            documentId=file_id, body={'requests': requests}).execute()
        
        return f"Appended text to document {file_id}"

    def create_from_template(self, template_id: str, title: str, replacements: dict):
        """
        Create a new doc by copying a template and replacing variables.
        """
        # 1. Copy Template
        copy_body = {'name': title}
        new_file = self.drive_service.files().copy(
            fileId=template_id, body=copy_body).execute()
        new_file_id = new_file.get('id')

        # 2. Perform Replacements
        requests = []
        for key, value in replacements.items():
            requests.append({
                'replaceAllText': {
                    'containsText': {
                        'text': key,
                        'matchCase': True
                    },
                    'replaceText': value
                }
            })
            
        if requests:
            self.docs_service.documents().batchUpdate(
                documentId=new_file_id, body={'requests': requests}).execute()
                
        return f"Created document '{title}' from template. ID: {new_file_id}"

    def _download_media(self, file_id, mime_type, encoding=None):
        """
        Helper for media download.
        """
        request = self.drive_service.files().export_media(
            fileId=file_id, mimeType=mime_type)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        if encoding:
            return fh.getvalue().decode(encoding)
        return fh.getvalue()

    def download_doc(self, file_id: str, format_type: str = 'markdown'):
        """
        Download Google Doc/Sheet content in specified format.
        Supported formats:
        - markdown (default, via HTML conversion)
        - html
        - pdf
        - docx
        - csv (sheets only)
        - xlsx (sheets only)
        - json (sheets only -> list of dicts)
        """
        # Map simple format names to MIME types
        mime_map = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'html': 'text/html',
            'rtf': 'application/rtf',
            'odt': 'application/vnd.oasis.opendocument.text',
            'markdown': 'text/markdown', # Special case, treated as text/markdown for GDoc or processed manually
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'json': 'application/json' # Special case for Sheets
        }

        target_mime = mime_map.get(format_type.lower())
        if not target_mime:
            raise ValueError(f"Unsupported format: {format_type}")
        
        # Get metadata to check source type
        file_meta = self.drive_service.files().get(fileId=file_id, fields="mimeType, name").execute()
        source_mime = file_meta.get('mimeType')

        # Special Case: Markdown via HTML (to fix Smart Chip Concatenation bugs)
        if format_type == 'markdown' and source_mime == 'application/vnd.google-apps.document':
            # Download as HTML first
            html_content = self._download_media(file_id, 'text/html', 'utf-8')
            if not html_content: return ""

            # Convert to Markdown using our custom parser
            return convert_html_to_markdown(html_content)

        # Special Case: JSON for Sheets
        if format_type == 'json' and source_mime == 'application/vnd.google-apps.spreadsheet':
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=file_id, range=DEFAULT_SHEET_RANGE).execute()
            values = result.get('values', [])
            if not values:
                return "[]"
            headers = values[0]
            data = []
            for row in values[1:]:
                # Zip headers with row data
                item = {h: (row[i] if i < len(row) else "") for i, h in enumerate(headers)}
                data.append(item)
            return json.dumps(data, indent=2)

        return self._download_media(file_id, target_mime, encoding='utf-8')


    def get_file_snippet(self, file_id: str, length: int = DEFAULT_SNIPPET_LENGTH) -> str:
        """
        Get a short snippet of the file content.
        """
        try:
            content = self.read_file(file_id)
            # Remove the header line we added in read_file if it exists
            if content.startswith("# File:"):
                # Find the double newline after the header
                parts = content.split('\n\n', 1)
                if len(parts) > 1:
                    content = parts[1]
            
            # Simple truncation
            snippet = content[:length].replace('\n', ' ').strip()
            if len(content) > length:
                snippet += "..."
            return snippet
        except Exception:
            return ""

    def batch_get_snippets(self, files: list, max_workers: int = DEFAULT_MAX_WORKERS) -> dict:
        """
        Fetch snippets for multiple files in parallel.
        Returns a dict of {file_id: snippet}.
        """
        snippets = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a map of future -> file_id
            future_to_id = {
                executor.submit(self.get_file_snippet, f['id']): f['id'] 
                for f in files
            }
            
            for future in concurrent.futures.as_completed(future_to_id):
                file_id = future_to_id[future]
                try:
                    snippets[file_id] = future.result()
                except Exception:
                    snippets[file_id] = ""
                    
        return snippets

