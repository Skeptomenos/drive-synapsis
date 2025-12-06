"""Document-related MCP tools."""
from .main import mcp, get_client
from .managers import search_manager
from utils.errors import handle_http_error, format_error, GDriveError
import json

try:
    from googleapiclient.errors import HttpError
except ImportError:
    HttpError = Exception


@mcp.tool()
def create_google_doc(title: str, content: str) -> str:
    """
    Create a new Google Doc with the given title and text content.
    Args:
        title: The name of the new document.
        content: The initial text content.
    """
    try:
        return get_client().create_doc(title, content)
    except HttpError as e:
        return format_error("Create doc", handle_http_error(e))
    except GDriveError as e:
        return format_error("Create doc", e)
    except Exception as e:
        return f"Create doc failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def read_google_drive_file(name: str, id: str = None) -> str:
    """
    Read the content of a file from Google Drive to SHOW it to the user.
    Use this ONLY when the user asks to "show", "read", or "display" the file content.
    Do NOT use this if the user asks to "download", "save", or "create" a local file.
    Args:
        name: Name of the file to read.
        id: Optional ID. If not provided, searches by name.
    """
    try:
        if id:
            real_id = search_manager.resolve_alias(id)
            return get_client().read_file(real_id)
        else:
            real_id = search_manager.resolve_alias(name)
            return get_client().read_file(real_id)
    except HttpError as e:
        return format_error("Read file", handle_http_error(e, id or name))
    except GDriveError as e:
        return format_error("Read file", e)
    except Exception as e:
        return f"Read file failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def append_to_google_doc(file_id: str, content: str) -> str:
    """
    Append text to the end of a Google Doc.
    Useful for maintaining logs, journals, or meeting notes.
    Args:
        file_id: The ID of the file or its search alias (e.g. "A").
        content: The text to append.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().append_text_to_doc(real_id, content)
    except HttpError as e:
        return format_error("Append to doc", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Append to doc", e)
    except Exception as e:
        return f"Append to doc failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def replace_doc_text(file_id: str, find: str, replace: str, match_case: bool = False) -> str:
    """
    Find and replace text in a Google Doc.
    Useful for bulk updates like changing "TODO" to "DONE".
    Args:
        file_id: The ID of the doc or its search alias.
        find: Text to find.
        replace: Text to replace with.
        match_case: If True, search is case-sensitive.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().replace_text_in_doc(real_id, find, replace, match_case)
    except HttpError as e:
        return format_error("Replace text", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Replace text", e)
    except Exception as e:
        return f"Replace text failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def insert_doc_table(file_id: str, rows: int, cols: int, index: int = 1) -> str:
    """
    Insert a table into a Google Doc.
    Args:
        file_id: The ID of the doc or its search alias.
        rows: Number of rows.
        cols: Number of columns.
        index: Position to insert (1 = start of document).
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().insert_table(real_id, rows, cols, index)
    except HttpError as e:
        return format_error("Insert table", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Insert table", e)
    except Exception as e:
        return f"Insert table failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def get_document_outline(file_id: str) -> str:
    """
    Get the table of contents / outline of a Google Doc.
    Extracts all headings (H1-H6) to help navigate large documents.
    Use this before reading the full document to understand its structure.
    Args:
        file_id: The ID of the document or its search alias (e.g. "A").
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        outline = get_client().get_document_outline(real_id)
        
        if not outline:
            return "No headings found in document."
        
        output = ["Document Outline:"]
        for i, item in enumerate(outline):
            indent = "  " * (item['level'] - 1)
            output.append(f"{i+1}. {indent}[H{item['level']}] {item['text']}")
        
        return "\n".join(output)
    except HttpError as e:
        return format_error("Get outline", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Get outline", e)
    except Exception as e:
        return f"Get outline failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def read_document_section(file_id: str, section_number: int) -> str:
    """
    Read a specific section of a Google Doc by section number.
    First call get_document_outline to see the sections, then use this to read one.
    Args:
        file_id: The ID of the document or its search alias (e.g. "A").
        section_number: The section number (1-based) from the outline.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        outline = get_client().get_document_outline(real_id)
        
        if not outline:
            return "No sections found in document."
        
        if section_number < 1 or section_number > len(outline):
            return f"Invalid section number. Valid range: 1-{len(outline)}"
        
        section = outline[section_number - 1]
        start = section['startIndex']
        end = section['endIndex']
        
        if section_number < len(outline):
            end = outline[section_number]['startIndex']
        
        content = get_client().read_document_section(real_id, start, end)
        return f"## {section['text']}\n\n{content}"
    except HttpError as e:
        return format_error("Read section", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Read section", e)
    except Exception as e:
        return f"Read section failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def post_comment(file_id: str, comment_text: str, quoted_text: str = None) -> str:
    """
    Post a comment on a Google Drive file (Doc, Sheet, etc.).
    Useful for collaboration workflows where AI needs to flag issues or ask questions.
    Args:
        file_id: The ID of the file or its search alias (e.g. "A").
        comment_text: The text of the comment.
        quoted_text: Optional text from the document to anchor the comment to.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().create_comment(real_id, comment_text, quoted_text)
    except HttpError as e:
        return format_error("Post comment", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Post comment", e)
    except Exception as e:
        return f"Post comment failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def reply_to_comment(file_id: str, comment_id: str, reply_text: str) -> str:
    """
    Reply to an existing comment on a Google Drive file.
    First use download_google_doc with include_comments=True to see comment IDs.
    Args:
        file_id: The ID of the file or its search alias (e.g. "A").
        comment_id: The ID of the comment to reply to.
        reply_text: The text of the reply.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().reply_to_comment(real_id, comment_id, reply_text)
    except HttpError as e:
        return format_error("Reply to comment", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Reply to comment", e)
    except Exception as e:
        return f"Reply to comment failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def create_doc_from_template(template_id: str, new_title: str, replacements: str) -> str:
    """
    Create a new Google Doc by copying a template and replacing placeholders.
    Args:
        template_id: The ID of the template file or its search alias (e.g. "A").
        new_title: The title for the new document.
        replacements: A JSON string of replacements, e.g. '{"{{name}}": "Alice", "{{date}}": "2023-01-01"}'.
    """
    try:
        real_id = search_manager.resolve_alias(template_id)
        replacements_dict = json.loads(replacements)
        return get_client().create_from_template(real_id, new_title, replacements_dict)
    except json.JSONDecodeError:
        return "Create from template failed: Invalid JSON for replacements."
    except HttpError as e:
        return format_error("Create from template", handle_http_error(e, template_id))
    except GDriveError as e:
        return format_error("Create from template", e)
    except Exception as e:
        return f"Create from template failed: Unexpected error ({type(e).__name__}: {e})"
