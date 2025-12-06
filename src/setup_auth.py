from gdrive_client import GDriveClient

if __name__ == "__main__":
    print("Initializing Google Drive Client to trigger authentication flow...")
    try:
        client = GDriveClient()
        print("Authentication successful! 'token.json' has been created.")
        print("You can now configure Gemini CLI to use this server.")
    except Exception as e:
        print(f"Authentication failed: {e}")
