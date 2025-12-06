from gdrive_client import GDriveClient
import time

def test_sheets():
    client = GDriveClient()
    
    print("1. Creating Test Sheet...")
    res = client.create_sheet("MCP Test Sheet", [['Header1', 'Header2'], ['Initial', 'Value']])
    # Extract ID from "Sheet created successfully. ID: XXXXX"
    sheet_id = res.split("ID: ")[1].strip()
    print(f"   Created ID: {sheet_id}")
    
    print("2. Updating Cell B2...")
    res = client.update_sheet_values(sheet_id, "B2", [['Updated Value']])
    print(f"   {res}")
    
    print("3. Reading Range A1:B2...")
    data = client.read_sheet_values(sheet_id, "A1:B2")
    print(f"   Data: {data}")
    
    assert data[1][1] == 'Updated Value'
    print("SUCCESS: Sheet updated and read correctly.")

if __name__ == "__main__":
    test_sheets()
