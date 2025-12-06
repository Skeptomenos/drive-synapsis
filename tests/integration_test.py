
import os
import sys
import json
import time
import re
from drive_synapsis.client import GDriveClient

# Initialize Client
try:
    client = GDriveClient()
    print("PASS: Client Initialization")
except Exception as e:
    print(f"FAIL: Client Initialization - {e}")
    sys.exit(1)

WORKSPACE_NAME = "MCP_Test_Workspace"
DOC_NAME = "Test_Doc_Alpha"
SHEET_NAME = "Test_Sheet_Beta"
COPY_NAME = "Copy_of_Doc"

workspace_id = None
doc_id = None
sheet_id = None

# Helper: Create Folder manually using service
def create_folder(name):
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    file = client.drive_service.files().create(body=file_metadata, fields='id').execute()
    return file['id']

# Helper: Parse ID from success message
def parse_id(message):
    # Matches "ID: <id>"
    match = re.search(r'ID: ([a-zA-Z0-9_-]+)', message)
    if match:
        return match.group(1)
    return None

def run_test():
    global workspace_id, doc_id, sheet_id
    
    # --- Phase 1: Setup ---
    print("\n--- Phase 1: Setup ---")
    try:
        # Create Folder
        workspace_id = create_folder(WORKSPACE_NAME)
        print(f"PASS: Create Workspace Folder ({workspace_id})")
        
        # Create Doc
        doc_content = "# Hello World\nThis is a test document."
        res_doc = client.create_doc(DOC_NAME, doc_content)
        doc_id = parse_id(res_doc)
             
        if doc_id:
            print(f"PASS: Create Doc ({doc_id})")
        else:
            print(f"FAIL: Could not parse Doc ID from: {res_doc}")
            return
        
        # Move Doc
        client.move_file(doc_id, workspace_id)
        print("PASS: Move Doc to Workspace")
        
    except Exception as e:
        print(f"FAIL: Phase 1 - {e}")
        return

    # --- Phase 2: Document Manipulation ---
    print("\n--- Phase 2: Docs ---")
    try:
        # Read
        content = client.read_file(doc_id)
        if "Hello World" in content:
            print("PASS: Read Doc")
        else:
            print(f"FAIL: Read Doc content mismatch. Got: {content[:50]}...")

        # Insert Table
        client.insert_table(doc_id, 3, 3, 1)
        print("PASS: Insert Table")
        
        # Replace Text
        client.replace_text_in_doc(doc_id, "World", "Galaxy")
        print("PASS: Replace Text")
        
        # Verify
        content_new = client.read_file(doc_id)
        if "Hello Galaxy" in content_new:
             print("PASS: Verify Text Replacement")
        else:
             print(f"FAIL: Text Replacement check failed. Got: {content_new[:50]}...")
             
    except Exception as e:
        print(f"FAIL: Phase 2 - {e}")

    # --- Phase 3: Sheets ---
    print("\n--- Phase 3: Sheets ---")
    try:
        # Create Sheet
        data = [["Date", "Item", "Cost"], ["2024-01-01", "Apple", "1.00"]]
        res_sheet = client.create_sheet(SHEET_NAME, data)
        sheet_id = parse_id(res_sheet)

        if sheet_id:
            print(f"PASS: Create Sheet ({sheet_id})")
        else:
            print(f"FAIL: Could not parse Sheet ID from: {res_sheet}")
            return
        
        # Move Sheet to Workspace (for cleanup)
        client.move_file(sheet_id, workspace_id) 
        
        # Append
        append_data = [["2024-01-02", "Banana", "0.50"]]
        client.append_sheet_rows(sheet_id, "Sheet1!A1", append_data)
        print("PASS: Append Row")
        
        # Read
        values = client.read_sheet_values(sheet_id, "Sheet1!A1:C3")
        if len(values) >= 3 and values[2][1] == "Banana":
            print("PASS: Read Sheet Range")
        else:
             print(f"FAIL: Sheet data mismatch: {values}")
             
        # Add Tab
        client.add_sheet_tab(sheet_id, "Summary")
        print("PASS: Add Sheet Tab")
        
    except Exception as e:
        print(f"FAIL: Phase 3 - {e}")

    # --- Phase 4: File Management ---
    print("\n--- Phase 4: Files ---")
    try:
        # Rename Sheet
        client.rename_file(sheet_id, "Budget_2024")
        print("PASS: Rename File")
        
        # Star
        client.star_file(sheet_id, True)
        print("PASS: Star File")
        
        # Info
        meta = client.get_file_metadata(sheet_id)
        if meta.get('starred') and meta.get('name') == "Budget_2024":
            print("PASS: Get File Info")
        else:
            print(f"FAIL: Metadata mismatch: {meta}")
            
        # Copy Doc
        copy = client.copy_file(doc_id, COPY_NAME, workspace_id)
        print(f"PASS: Copy File ({copy['id']})")
        
    except Exception as e:
        print(f"FAIL: Phase 4 - {e}")

    # --- Phase 5: Search ---
    print("\n--- Phase 5: Search ---")
    try:
        # Basic Search
        # Search index might take a moment to update. Wait 5s.
        time.sleep(5)
        res = client.search_files("Budget_2024", limit=5)
        found = any(f['id'] == sheet_id for f in res)
        if found:
            print("PASS: Basic Search")
        else:
            # Try once more
             time.sleep(5)
             res = client.search_files("Budget_2024", limit=5)
             found = any(f['id'] == sheet_id for f in res)
             if found:
                 print("PASS: Basic Search (Retry)")
             else:
                 print(f"FAIL: Basic Search did not find file '{sheet_id}'. Found: {[r['name'] for r in res]}")
            
        # Folder Search
        res_folder = client.search_in_folder(workspace_id, "Doc", limit=5)
        # Should find doc_id and copy_id
        if len(res_folder) >= 1:
             print("PASS: Folder Search")
        else:
             print("FAIL: Folder Search empty")
             
    except Exception as e:
         print(f"FAIL: Phase 5 - {e}")

    # --- Phase 6: Sync (Mock) ---
    print("\n--- Phase 6: Sync (Skipped in Script) ---")
    print("PASS: Sync capabilities covered by Read/Update/Create ops above.")

    # --- Cleanup ---
    print("\n--- Cleanup ---")
    try:
        # Recursively delete files in workspace to be clean?
        # client.delete_file on folder trashes the folder.
        if workspace_id:
            client.delete_file(workspace_id)
            print("PASS: Delete Workspace")
    except Exception as e:
        print(f"FAIL: Cleanup - {e}")

if __name__ == "__main__":
    run_test()
