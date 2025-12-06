"""Spreadsheet-related MCP tools."""
from .main import mcp, get_client
from .managers import search_manager
from utils.errors import handle_http_error, format_error, GDriveError
import csv
import io
import json

try:
    from googleapiclient.errors import HttpError
except ImportError:
    HttpError = Exception


@mcp.tool()
def create_sheet(title: str, data: str) -> str:
    """
    Create a Google Sheet with initial data.
    Args:
        title: Title of the Sheet.
        data: CSV string or list of lists (as JSON string).
    """
    try:
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError:
            reader = csv.reader(io.StringIO(data))
            parsed_data = list(reader)
        
        return get_client().create_sheet(title, parsed_data)
    except HttpError as e:
        return format_error("Create sheet", handle_http_error(e))
    except GDriveError as e:
        return format_error("Create sheet", e)
    except Exception as e:
        return f"Create sheet failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def update_sheet_cell(spreadsheet_id: str, range_name: str, value: str) -> str:
    """
    Update a specific cell or range in a Google Sheet.
    Args:
        spreadsheet_id: The ID of the sheet or its search alias (e.g. "A").
        range_name: The A1 notation range (e.g. "B2", "Sheet1!A1:B2").
        value: Single value OR JSON list of lists for multiple cells.
               To write multiple values to a range, provide a JSON list of lists.
               Example: '[[1, 2], [3, 4]]'
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        
        values = [[value]]
        if value.strip().startswith('[') and range_name.count(':') > 0:
            try:
                values = json.loads(value)
            except json.JSONDecodeError:
                pass
        
        return get_client().update_sheet_values(real_id, range_name, values)
    except HttpError as e:
        return format_error("Update cell", handle_http_error(e, spreadsheet_id))
    except GDriveError as e:
        return format_error("Update cell", e)
    except Exception as e:
        return f"Update cell failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def read_sheet_range(spreadsheet_id: str, range_name: str) -> str:
    """
    Read a specific range of cells from a Google Sheet.
    Returns the data as a formatted string or JSON.
    Args:
        spreadsheet_id: The ID of the sheet or its search alias (e.g. "A").
        range_name: The A1 notation range (e.g. "Sheet1!A1:C10").
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        values = get_client().read_sheet_values(real_id, range_name)
        
        if not values:
            return "No data found in range."
        
        output = io.StringIO()
        writer = csv.writer(output)
        for row in values:
            writer.writerow(row)
        
        table_str = output.getvalue()
        return f"```csv\n{table_str}```"
    except HttpError as e:
        return format_error("Read range", handle_http_error(e, spreadsheet_id))
    except GDriveError as e:
        return format_error("Read range", e)
    except Exception as e:
        return f"Read range failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def append_to_sheet(spreadsheet_id: str, range_name: str, values: str) -> str:
    """
    Append rows to a Google Sheet without overwriting existing data.
    Preserves formulas and references.
    Args:
        spreadsheet_id: The sheet ID or alias.
        range_name: Range like "Sheet1!A1" (start of where to append).
        values: JSON list of lists, e.g. '[["A", "B"], ["C", "D"]]'
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        values_list = json.loads(values)
        return get_client().append_sheet_rows(real_id, range_name, values_list)
    except json.JSONDecodeError:
        return "Append to sheet failed: Values must be a valid JSON list of lists."
    except HttpError as e:
        return format_error("Append to sheet", handle_http_error(e, spreadsheet_id))
    except GDriveError as e:
        return format_error("Append to sheet", e)
    except Exception as e:
        return f"Append to sheet failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def add_sheet_tab(spreadsheet_id: str, tab_name: str) -> str:
    """
    Add a new tab to an existing spreadsheet.
    Does not modify existing tabs, preserving all formulas and data.
    Args:
        spreadsheet_id: The sheet ID or alias.
        tab_name: Name for the new tab.
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        return get_client().add_sheet_tab(real_id, tab_name)
    except HttpError as e:
        return format_error("Add tab", handle_http_error(e, spreadsheet_id))
    except GDriveError as e:
        return format_error("Add tab", e)
    except Exception as e:
        return f"Add tab failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def format_sheet_cells(
    spreadsheet_id: str,
    sheet_id: int,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    bold: bool = False,
    background_color: str = None
) -> str:
    """
    Format cells in a Google Sheet (bold text, background color).
    Args:
        spreadsheet_id: The sheet ID or alias.
        sheet_id: The specific tab/sheet ID (use 0 for first tab).
        start_row, end_row: Row range (0-indexed).
        start_col, end_col: Column range (0-indexed).
        bold: Make text bold.
        background_color: Hex color like '#FF0000'.
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        return get_client().format_sheet_range(
            real_id, sheet_id, start_row, end_row, start_col, end_col, bold, background_color
        )
    except HttpError as e:
        return format_error("Format cells", handle_http_error(e, spreadsheet_id))
    except GDriveError as e:
        return format_error("Format cells", e)
    except Exception as e:
        return f"Format cells failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def protect_sheet_cells(
    spreadsheet_id: str,
    sheet_id: int,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    description: str = 'Protected'
) -> str:
    """
    Protect a range of cells from editing.
    Args:
        spreadsheet_id: The sheet ID or alias.
        sheet_id: The tab ID (0 for first tab).
        start_row, end_row, start_col, end_col: Range (0-indexed).
        description: Reason for protection.
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        return get_client().protect_sheet_range(
            real_id, sheet_id, start_row, end_row, start_col, end_col, description
        )
    except HttpError as e:
        return format_error("Protect cells", handle_http_error(e, spreadsheet_id))
    except GDriveError as e:
        return format_error("Protect cells", e)
    except Exception as e:
        return f"Protect cells failed: Unexpected error ({type(e).__name__}: {e})"
