"""Spreadsheet operations mixin for GDriveClient."""
from typing import Optional


class SheetsMixin:
    """Mixin providing spreadsheet-related operations."""
    
    def create_sheet(self, title: str, data: list[list[str]]) -> str:
        """Create a sheet and upload initial data.
        
        Args:
            title: Sheet title.
            data: Initial data as list of lists.
            
        Returns:
            Success message with sheet ID.
        """
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }
        file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        file_id = file.get('id')
        
        body = {'values': data}
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=file_id, range="A1",
            valueInputOption="USER_ENTERED", body=body
        ).execute()
            
        return f"Sheet created successfully. ID: {file_id}"

    def update_sheet_values(self, spreadsheet_id: str, range_name: str, values: list[list[str]]) -> str:
        """Update values in a Google Sheet.
        
        Args:
            spreadsheet_id: The sheet ID.
            range_name: The A1 notation range.
            values: Values to write.
            
        Returns:
            Success message with cell count.
        """
        body = {'values': values}
        result = self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption="USER_ENTERED", body=body
        ).execute()
        return f"Updated {result.get('updatedCells')} cells in range {range_name}."

    def read_sheet_values(self, spreadsheet_id: str, range_name: str) -> list[list[str]]:
        """Read values from a specific range in a Google Sheet.
        
        Args:
            spreadsheet_id: The sheet ID.
            range_name: The A1 notation range.
            
        Returns:
            List of lists with cell values.
        """
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        return result.get('values', [])

    def append_sheet_rows(self, spreadsheet_id: str, range_name: str, values: list[list[str]]) -> str:
        """Append rows to the end of a range.
        
        Args:
            spreadsheet_id: The sheet ID.
            range_name: The A1 notation range.
            values: Rows to append.
            
        Returns:
            Success message with row count.
        """
        body = {'values': values}
        result = self.sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        return f"Appended {result.get('updates', {}).get('updatedRows', 0)} rows."

    def insert_sheet_rows(self, spreadsheet_id: str, sheet_id: int, start_index: int, row_count: int) -> str:
        """Insert blank rows at a specific position.
        
        Args:
            spreadsheet_id: The spreadsheet ID.
            sheet_id: The sheet/tab ID.
            start_index: Starting row index.
            row_count: Number of rows to insert.
            
        Returns:
            Success message.
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

    def add_sheet_tab(self, spreadsheet_id: str, tab_name: str) -> str:
        """Add a new tab to an existing spreadsheet.
        
        Args:
            spreadsheet_id: The spreadsheet ID.
            tab_name: Name for the new tab.
            
        Returns:
            Success message with tab ID.
        """
        requests = [{
            'addSheet': {
                'properties': {'title': tab_name}
            }
        }]
        result = self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        new_sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']
        return f"Added tab '{tab_name}' (Sheet ID: {new_sheet_id})."

    def format_sheet_range(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        bold: bool = False,
        background_color: Optional[str] = None
    ) -> str:
        """Apply formatting to a range in a spreadsheet.
        
        Args:
            spreadsheet_id: The spreadsheet ID.
            sheet_id: The sheet/tab ID.
            start_row, end_row: Row range (0-indexed).
            start_col, end_col: Column range (0-indexed).
            bold: Make text bold.
            background_color: Hex color like '#FF0000'.
            
        Returns:
            Success message.
        """
        cell_format = {}
        if bold:
            cell_format['textFormat'] = {'bold': True}
        if background_color:
            color_hex = background_color.lstrip('#')
            r = int(color_hex[0:2], 16) / 255.0
            g = int(color_hex[2:4], 16) / 255.0
            b = int(color_hex[4:6], 16) / 255.0
            cell_format['backgroundColor'] = {'red': r, 'green': g, 'blue': b}
        
        requests = [{
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
        }]
        
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        return f"Formatted range (rows {start_row}-{end_row}, cols {start_col}-{end_col})"

    def protect_sheet_range(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        description: str = 'Protected range'
    ) -> str:
        """Protect a range from editing.
        
        Args:
            spreadsheet_id: The spreadsheet ID.
            sheet_id: The sheet/tab ID.
            start_row, end_row, start_col, end_col: Range (0-indexed).
            description: Reason for protection.
            
        Returns:
            Success message.
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
