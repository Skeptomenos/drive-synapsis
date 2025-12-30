from drive_synapsis.client import GDriveClient
import time
import json


def test_features():
    print("Initializing Client...")
    try:
        client = GDriveClient()
    except Exception as e:
        print(f"Failed to auth: {e}")
        return

    timestamp = int(time.time())

    # 1. Test Smart Markdown Update
    print("\n--- Test 1: Smart Markdown Update ---")
    title = f"Test Doc {timestamp}"
    print(f"Creating doc: {title}")
    # We can use our create_doc helper (which creates empty + inserts text)
    # But to test UPGRADE, let's create it, then UPDATE it.
    res = client.create_doc(title, "Initial text")
    doc_id = res.split("ID: ")[1].strip()
    print(f"Created ID: {doc_id}")

    markdown_content = """
# Header 1
## Header 2
*   Bullet 1
*   **Bold Item**
    """
    print("Updating with Markdown...")
    client.update_doc(doc_id, markdown_content)
    print("Update complete. Fetching snippet to verify...")
    snippet = client.get_file_snippet(doc_id)
    print(f"Snippet: {snippet}")
    # Note: Snippet might be plain text, so we might not see "bolding" here,
    # but we should see the text content without the markdown ### chars if conversion worked?
    # Actually, if conversion works, "# Header 1" becomes "Header 1" with Title style.
    # If it failed (plain text), it would still read "# Header 1".

    if "# Header 1" not in snippet and "Header 1" in snippet:
        print("SUCCESS: Markdown chars likely converted.")
    else:
        print("NOTICE: Markdown chars might still be present or snippet format issues.")

    # 2. Test Append
    print("\n--- Test 2: Append Text ---")
    append_text = f"\n\n[Log Entry {timestamp}] Appended text."
    print(f"Appending: {append_text.strip()}")
    client.append_text_to_doc(doc_id, append_text)

    snippet_after = client.get_file_snippet(doc_id)
    print(f"Snippet after append: {snippet_after}")

    if f"[Log Entry {timestamp}]" in snippet_after:
        print("SUCCESS: Appended text found.")
    else:
        print("FAILURE: Appended text not found in snippet.")

    # 3. Test Template
    print("\n--- Test 3: Template Creation ---")
    # We'll use the doc we just made as a template.
    # It has content "Header 1..." and "[Log Entry...]".
    # Let's add a placeholder to it first?
    p_holder = "{{name}}"
    client.append_text_to_doc(doc_id, f"\nHello {p_holder}!")

    template_title = f"Derived Doc {timestamp}"
    replacements = {"{{name}}": "WorldMap"}

    print(f"Creating from template ID {doc_id} with replacements: {replacements}")
    res_tmpl = client.create_from_template(doc_id, template_title, replacements)
    new_id = res_tmpl.split("ID: ")[1].strip()

    snippet_tmpl = client.get_file_snippet(new_id)
    print(f"New Doc Snippet: {snippet_tmpl}")

    if "Hello WorldMap!" in snippet_tmpl:
        print("SUCCESS: Placeholder replaced.")
    else:
        print("FAILURE: Placeholder not replaced.")


if __name__ == "__main__":
    test_features()
