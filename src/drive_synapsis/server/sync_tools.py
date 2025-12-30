"""Sync-related MCP tools for local file synchronization."""

from .main import mcp, get_client
from .managers import search_manager, sync_manager
from ..utils.errors import (
    handle_http_error,
    format_error,
    GDriveError,
    LinkNotFoundError,
    LocalFileNotFoundError,
    SyncConflictError,
)
from collections import deque
import difflib
import re
import os

try:
    from googleapiclient.errors import HttpError
except ImportError:
    HttpError = Exception


@mcp.tool()
def link_local_file(local_path: str, file_id: str) -> str:
    """
    Link a local file to a Google Drive file ID for synchronization.
    Args:
        local_path: The relative path to the local file (e.g. "docs/notes.md").
        file_id: The Google Drive file ID or its search alias (e.g. "A").
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        version = get_client().get_file_version(real_id)
        abs_path = os.path.abspath(local_path)
        sync_manager.file_map[abs_path] = {
            "id": real_id,
            "last_synced_version": version,
        }
        sync_manager._save_map()
        return f"Linked {local_path} to {real_id} (Version {version})"
    except HttpError as e:
        return format_error("Link file", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Link file", e)
    except Exception as e:
        return f"Link file failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def update_google_doc(
    local_path: str, force: bool = False, dry_run: bool = True
) -> str:
    """
    Upload content from a local file to its linked Google Doc.
    SAFETY: Defaults to dry_run=True. Usage must explicitly set dry_run=False to apply changes.
    Args:
        local_path: Path to the local file.
        force: If True, overwrite even if the remote file has changed since last sync.
        dry_run: If True (default), return a diff of changes instead of updating. Set to False to apply.
    """
    try:
        link = sync_manager.get_link(local_path)
        if not link:
            raise LinkNotFoundError(local_path)

        file_id = link["id"]
        known_version = link.get("last_synced_version", 0)

        current_remote_version = get_client().get_file_version(file_id)

        if not force and not dry_run and current_remote_version > known_version:
            raise SyncConflictError(
                f"Remote file (v{current_remote_version}) is newer than last synced (v{known_version}). Use force=True to overwrite.",
                known_version,
                current_remote_version,
                file_id,
            )

        if not os.path.exists(local_path):
            raise LocalFileNotFoundError(local_path)

        with open(local_path, "r") as f:
            content = f.read()

        if dry_run:
            remote_content = get_client().download_doc(file_id, "markdown")

            diff = difflib.unified_diff(
                remote_content.splitlines(),
                content.splitlines(),
                fromfile=f"Remote (v{current_remote_version})",
                tofile="Local (Proposed)",
                lineterm="",
            )
            diff_text = "\n".join(diff)
            if not diff_text:
                return "No changes detected."
            return f"DRY RUN (No changes made):\n\n```diff\n{diff_text}\n```"

        is_tab_update = ":" in file_id

        if is_tab_update:
            real_file_id, tab_id = file_id.split(":", 1)
            get_client().update_tab_content(real_file_id, tab_id, content)

            new_version = get_client().get_file_version(real_file_id)
            sync_manager.update_version(local_path, new_version)
            return (
                f"Successfully updated Tab in Google Doc (new version: {new_version})"
            )

        doc_struct = get_client().get_doc_structure(file_id)
        tabs = doc_struct.get("tabs", [])
        if len(tabs) > 1 and not force:
            return (
                f"BLOCKED: Target document has {len(tabs)} tabs. "
                "Updating it with this file will OVERWRITE all tabs. "
                "Use force=True to proceed, or edit the individual Tab text files."
            )

        def link_replacer(match):
            rel_path = match.group(1)
            base_dir = os.path.dirname(os.path.abspath(local_path))
            abs_target = os.path.normpath(os.path.join(base_dir, rel_path))

            for lpath, data in sync_manager.file_map.items():
                if os.path.abspath(lpath) == abs_target:
                    fid = data["id"]
                    if ":" in fid:
                        fid = fid.split(":")[0]
                    return f"(https://docs.google.com/document/d/{fid})"
            return match.group(0)

        pattern = r"\(((?:\.\.|\./|[\w\s-]+/)[^\)]+\.(?:md|txt|doc))\)"
        content = re.sub(pattern, link_replacer, content)

        get_client().update_doc(file_id, content)

        new_version = get_client().get_file_version(file_id)
        sync_manager.update_version(local_path, new_version)

        return f"Successfully updated Google Doc (new version: {new_version})"

    except (LinkNotFoundError, LocalFileNotFoundError, SyncConflictError) as e:
        return format_error("Update doc", e)
    except HttpError as e:
        return format_error("Update doc", handle_http_error(e))
    except GDriveError as e:
        return format_error("Update doc", e)
    except Exception as e:
        return f"Update doc failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def download_google_doc(
    local_path: str,
    format: str = "markdown",
    include_comments: bool = False,
    rewrite_links: bool = True,
    dry_run: bool = True,
) -> str:
    """
    Download content from a linked Google Doc and SAVE it to a local file.
    SAFETY: Defaults to dry_run=True. Usage must explicitly set dry_run=False to apply changes.
    Args:
        local_path: Path to the local file.
        format: Output format ('markdown', 'html', 'pdf', 'docx').
        include_comments: If True, append comments to the end.
        rewrite_links: If True, rewrite internal doc links to local file links.
        dry_run: If True (default), return a diff of changes (for text/markdown) or preview. Set False to save.
    """
    try:
        link = sync_manager.get_link(local_path)
        if not link:
            raise LinkNotFoundError(local_path)

        file_id = link["id"]

        content = get_client().download_doc(file_id, format)

        if include_comments and format == "markdown":
            comments = get_client().get_file_comments(file_id)
            if comments:
                content += "\n\n---\n## Comments\n\n"
                for c in comments:
                    author = c.get("author", {}).get("displayName", "Unknown")
                    text = c.get("content", "")
                    quoted = c.get("quotedFileContent", {}).get("value", "")

                    content += f"**{author}**: {text}\n"
                    if quoted:
                        content += f"> _{quoted}_\n"
                    content += f"_Comment ID: {c.get('id')}_\n\n"

                    for reply in c.get("replies", []):
                        r_author = reply.get("author", {}).get("displayName", "Unknown")
                        r_text = reply.get("content", "")
                        content += f"  - **{r_author}** (reply): {r_text}\n"
                    content += "\n"

        if rewrite_links and format == "markdown":

            def replace_callback(match):
                url = match.group(2)
                if "docs.google.com/document/d/" in url:
                    doc_id = url.split("/d/")[1].split("/")[0]

                    for lpath, data in sync_manager.file_map.items():
                        fid = data["id"]
                        if ":" in fid:
                            fid = fid.split(":")[0]
                        if fid == doc_id:
                            current_dir = os.path.dirname(os.path.abspath(local_path))
                            target_abs = os.path.abspath(lpath)
                            rel_path = os.path.relpath(target_abs, current_dir)
                            return f"[{match.group(1)}]({rel_path})"
                return match.group(0)

            link_pattern = r"\[([^\]]+)\]\((https?://[^\)]+)\)"
            content = re.sub(link_pattern, replace_callback, content)

        if dry_run:
            if format in ("markdown", "html"):
                if os.path.exists(local_path):
                    with open(local_path, "r", encoding="utf-8") as f:
                        local_content = f.read()

                    diff = difflib.unified_diff(
                        local_content.splitlines(),
                        content.splitlines(),
                        fromfile="Local (Current)",
                        tofile="Remote (Proposed)",
                        lineterm="",
                    )
                    diff_text = "\n".join(diff)
                    if not diff_text:
                        return "No changes detected."
                    return f"DRY RUN (No changes made):\n\n```diff\n{diff_text}\n```"
                else:
                    preview = content[:500] + "..." if len(content) > 500 else content
                    return f"DRY RUN: Would create new file with content:\n\n{preview}"
            else:
                return f"DRY RUN: Would save {format.upper()} file to {local_path}"

        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)

        mode = "wb" if format in ("pdf", "docx", "xlsx") else "w"
        with open(local_path, mode) as f:
            if mode == "wb":
                f.write(
                    content if isinstance(content, bytes) else content.encode("utf-8")
                )
            else:
                f.write(content)

        new_version = get_client().get_file_version(file_id)
        sync_manager.update_version(local_path, new_version)

        return (
            f"Successfully downloaded to {local_path} (synced at version {new_version})"
        )

    except LinkNotFoundError as e:
        return format_error("Download doc", e)
    except HttpError as e:
        return format_error("Download doc", handle_http_error(e))
    except GDriveError as e:
        return format_error("Download doc", e)
    except Exception as e:
        return f"Download doc failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def upload_folder(local_path: str, parent_folder_id: str = None) -> str:
    """
    Recursively upload a local folder to Google Drive using BFS traversal.
    More robust than recursion - handles deep trees and reports errors gracefully.
    """
    try:
        if not os.path.exists(local_path) or not os.path.isdir(local_path):
            return f"Upload folder failed: {local_path} is not a directory."

        dir_name = os.path.basename(os.path.normpath(local_path))
        folder_metadata = {
            "name": dir_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_folder_id:
            folder_metadata["parents"] = [parent_folder_id]

        root_folder = (
            get_client()
            .drive_service.files()
            .create(body=folder_metadata, fields="id")
            .execute()
        )
        root_id = root_folder.get("id")

        queue = deque()

        for item in os.listdir(local_path):
            item_path = os.path.join(local_path, item)
            queue.append((item_path, root_id))

        uploaded_files = 0
        created_folders = 1
        errors = []

        while queue:
            current_path, current_parent_id = queue.popleft()

            if os.path.isdir(current_path):
                try:
                    sub_dir_name = os.path.basename(current_path)
                    sub_folder_meta = {
                        "name": sub_dir_name,
                        "mimeType": "application/vnd.google-apps.folder",
                        "parents": [current_parent_id],
                    }
                    sub_folder = (
                        get_client()
                        .drive_service.files()
                        .create(body=sub_folder_meta, fields="id")
                        .execute()
                    )
                    sub_folder_id = sub_folder.get("id")
                    created_folders += 1

                    for item in os.listdir(current_path):
                        queue.append((os.path.join(current_path, item), sub_folder_id))
                except HttpError as e:
                    err = handle_http_error(e)
                    errors.append(f"Folder {current_path}: {err.message}")
                except Exception as e:
                    errors.append(f"Folder {current_path}: {str(e)}")
            else:
                try:
                    result = get_client().upload_file(current_path, current_parent_id)
                    sync_manager.link_file(current_path, result["id"])
                    uploaded_files += 1
                except HttpError as e:
                    err = handle_http_error(e)
                    errors.append(f"File {current_path}: {err.message}")
                except Exception as e:
                    errors.append(f"File {current_path}: {str(e)}")

        summary = (
            f"Created {created_folders} folders and uploaded {uploaded_files} files."
        )
        if errors:
            summary += f"\n\n{len(errors)} errors:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                summary += f"\n... and {len(errors) - 10} more"

        return summary

    except HttpError as e:
        return format_error("Upload folder", handle_http_error(e))
    except GDriveError as e:
        return format_error("Upload folder", e)
    except Exception as e:
        return f"Upload folder failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def mirror_drive_folder(
    local_parent_dir: str, folder_query: str, recursive: bool = True
) -> str:
    """
    Recursively download a Google Drive folder to a local directory.
    Maintains directory structure and links downloaded files for future sync.
    Args:
        local_parent_dir: The local directory to download into. Created if missing.
        folder_query: The Name or ID of the Drive folder.
        recursive: Whether to download subfolders.
    """
    try:
        folder_id = search_manager.resolve_alias(folder_query)

        if len(folder_query) > 10:
            folder_meta = get_client().get_file_metadata(folder_id)
            folder_name = folder_meta.get("name", "Downloaded")
        else:
            folder_id_result = get_client().get_folder_id(folder_query)
            if folder_id_result:
                folder_id = folder_id_result
                folder_name = folder_query
            else:
                folder_meta = get_client().get_file_metadata(folder_id)
                folder_name = folder_meta.get("name", "Downloaded")

        local_base = os.path.join(local_parent_dir, folder_name)
        os.makedirs(local_base, exist_ok=True)

        downloaded_files = 0
        created_folders = 1
        errors = []

        def _process_folder(f_id, current_local_path):
            nonlocal downloaded_files, created_folders, errors

            items = get_client().list_folder_contents(f_id)

            for item in items:
                item_name = item["name"]
                item_id = item["id"]
                mime_type = item.get("mimeType", "")

                if mime_type == "application/vnd.google-apps.folder":
                    if recursive:
                        sub_path = os.path.join(current_local_path, item_name)
                        os.makedirs(sub_path, exist_ok=True)
                        created_folders += 1
                        _process_folder(item_id, sub_path)
                else:
                    try:
                        if "google-apps" in mime_type:
                            content = get_client().download_doc(item_id, "markdown")
                            file_name = item_name + ".md"
                        else:
                            content = get_client().download_doc(item_id, "html")
                            file_name = item_name

                        local_file_path = os.path.join(current_local_path, file_name)
                        with open(local_file_path, "w", encoding="utf-8") as f:
                            f.write(content)

                        abs_path = os.path.abspath(local_file_path)
                        sync_manager.file_map[abs_path] = {
                            "id": item_id,
                            "last_synced_version": get_client().get_file_version(
                                item_id
                            ),
                        }
                        downloaded_files += 1
                    except HttpError as e:
                        err = handle_http_error(e, item_id)
                        errors.append(f"{item_name}: {err.message}")
                    except Exception as e:
                        errors.append(f"{item_name}: {str(e)}")

        _process_folder(folder_id, local_base)
        sync_manager._save_map()

        summary = f"Downloaded {downloaded_files} files into {created_folders} folders at {local_base}."
        if errors:
            summary += f"\n\n{len(errors)} errors:\n" + "\n".join(errors[:5])

        return summary

    except HttpError as e:
        return format_error("Mirror folder", handle_http_error(e))
    except GDriveError as e:
        return format_error("Mirror folder", e)
    except Exception as e:
        return f"Mirror folder failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def download_doc_tabs(local_dir: str, file_id: str) -> str:
    """
    Download a Google Doc using "Hybrid Split-Sync".
    Creates a folder containing:
    1. _Full_Export.md: The entire doc as Markdown (High Fidelity).
    2. [TabName].md: Raw text content of each individual tab.
    Args:
        local_dir: Local directory to save files into.
        file_id: The Google Drive file ID or its search alias (e.g. "A").
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        os.makedirs(local_dir, exist_ok=True)

        full_content = get_client().download_doc(real_id, "markdown")
        full_export_path = os.path.join(local_dir, "_Full_Export.md")
        with open(full_export_path, "w") as f:
            f.write(full_content)

        doc_structure = get_client().get_doc_structure(real_id)
        tabs = doc_structure.get("tabs", [])

        extracted_count = 0

        if not tabs:
            body = doc_structure.get("body", {}).get("content", [])
            text = get_client().extract_text_from_element(body)
            main_path = os.path.join(local_dir, "Main.txt")
            with open(main_path, "w") as f:
                f.write(text)
            extracted_count = 1
        else:
            for tab in tabs:
                tab_props = tab.get("tabProperties", {})
                title = tab_props.get("title", "Untitled Tab")
                safe_title = "".join(
                    [c for c in title if c.isalpha() or c.isdigit() or c in " ._-"]
                ).strip()

                doc_tab = tab.get("documentTab", {})
                body = doc_tab.get("body", {}).get("content", [])

                text = get_client().extract_text_from_element(body)

                tab_path = os.path.join(local_dir, f"{safe_title}.txt")
                with open(tab_path, "w") as f:
                    f.write(text)

                tab_id = tab_props.get("tabId")
                if tab_id:
                    sync_manager.link_file(tab_path, f"{real_id}:{tab_id}")

                extracted_count += 1

        sync_manager.link_file(local_dir, real_id)
        sync_manager.link_file(full_export_path, real_id)

        return f"Hybrid Sync Complete in '{local_dir}'. Saved _Full_Export.md and {extracted_count} tab files."

    except HttpError as e:
        return format_error("Download tabs", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Download tabs", e)
    except Exception as e:
        return f"Download tabs failed: Unexpected error ({type(e).__name__}: {e})"
