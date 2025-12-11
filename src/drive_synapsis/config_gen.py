"""Interactive Configuration Wizard for Drive Synapsis MCP Server."""
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Try imports
try:
    from drive_synapsis.auth import get_creds, CREDENTIALS_DIR
except ImportError:
    # Fallback for direct execution if package not installed
    sys.path.append(str(Path(__file__).parent.parent))
    from drive_synapsis.auth import get_creds, CREDENTIALS_DIR

# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}")

def print_success(text: str):
    print(f"{Colors.GREEN}✔ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}✖ {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")

def get_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default."""
    if default:
        user_input = input(f"{Colors.BOLD}{prompt}{Colors.ENDC} [{default}]: ")
        return user_input.strip() or default
    return input(f"{Colors.BOLD}{prompt}{Colors.ENDC}: ").strip()

def confirm(prompt: str, default: bool = True) -> bool:
    """Ask for confirmation."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{Colors.BOLD}{prompt}{Colors.ENDC} [{default_str}]: ").strip().lower()
    if not response:
        return default
    return response.startswith('y')

def get_uv_path() -> str:
    """Find the uv executable path."""
    uv_path = shutil.which("uv")
    if uv_path:
        return os.path.abspath(uv_path)
    
    # Common locations check
    common_paths = [
        os.path.expanduser("~/.local/bin/uv"),
        os.path.expanduser("~/.cargo/bin/uv"),
        "/usr/local/bin/uv",
        "/opt/homebrew/bin/uv"
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return "uv"

def get_project_root() -> str:
    """Get absolute path to project root."""
    return str(Path(__file__).parent.parent.parent.resolve())

def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print_warning(f"Could not parse {path}. Starting with empty config.")
        return {}

def save_json(path: Path, data: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print_success(f"Updated {path}")

# --- Setup Steps ---

def setup_credentials():
    print_header("1. Credential Setup")
    
    # Ensure dir exists (it should via auth.py import, but double check)
    creds_dir = Path(CREDENTIALS_DIR)
    creds_dir.mkdir(parents=True, exist_ok=True)
    
    client_secret = creds_dir / "client_secret.json"
    token_file = creds_dir / "token.json"
    
    # 1. Client Secret
    if client_secret.exists():
        print_success("client_secret.json found.")
    else:
        print_warning(f"client_secret.json NOT found in {creds_dir}")
        print_info("You need to download 'client_secret.json' from Google Cloud Console.")
        
        while True:
            path_str = get_input("Path to your downloaded client_secret.json (or 'skip')")
            if path_str.lower() == 'skip':
                print_warning("Skipping credential setup. Server will not work without it.")
                return
            
            # Remove quotes if user dragged & dropped
            path_str = path_str.strip("'\"")
            src_path = Path(path_str).expanduser()
            
            if src_path.exists() and src_path.is_file():
                try:
                    shutil.copy(src_path, client_secret)
                    print_success(f"Copied credentials to {client_secret}")
                    break
                except Exception as e:
                    print_error(f"Failed to copy file: {e}")
            else:
                print_error(f"File not found at {src_path}. Please try again.")

    # 2. Token Generation (Auth)
    if token_file.exists():
        print_success("token.json found (Authenticated).")
        if confirm("Do you want to re-authenticate?", default=False):
             token_file.unlink()
        else:
            return

    if client_secret.exists():
        print_info("Ready to authenticate with Google.")
        print_info("A browser window will open. Please sign in.")
        if confirm("Start authentication now?"):
            try:
                get_creds() # Triggers flow
                print_success("Authentication successful! token.json created.")
            except Exception as e:
                print_error(f"Authentication failed: {e}")

def configure_clients(uv_path: str, project_root: str):
    print_header("2. Client Configuration")
    
    print("Which AI clients do you want to configure?")
    print("1. Claude Code (~/.claude.json)")
    print("2. Gemini CLI (~/.gemini/settings.json)")
    print("3. OpenCode (Global ~/.config/opencode/opencode.json OR Local ./opencode.json)")
    print("4. All of the above (OpenCode defaults to Global)")
    print("5. Skip")
    
    choice = get_input("Selection (comma separated, e.g., '1,2')")
    
    if choice == '5' or choice.lower() == 'skip':
        return

    selections = choice.split(',')
    if '4' in selections:
        selections = ['1', '2', '3']
        
    for sel in selections:
        sel = sel.strip()
        if sel == '1':
            _setup_claude(uv_path, project_root)
        elif sel == '2':
            _setup_gemini(uv_path, project_root)
        elif sel == '3':
            _setup_opencode(uv_path, project_root)

def _setup_claude(uv_path: str, project_root: str):
    config_path = Path.home() / ".claude.json"
    print_info(f"Configuring Claude Code at {config_path}")
    
    config = load_json(config_path)
    if "mcpServers" not in config:
        config["mcpServers"] = {}
        
    config["mcpServers"]["drive-synapsis"] = {
        "command": uv_path,
        "args": ["run", "--directory", project_root, "drive-synapsis"],
        "env": {}
    }
    
    if confirm(f"Write config to {config_path}?"):
        save_json(config_path, config)
    else:
        print(json.dumps(config, indent=2))

def _setup_gemini(uv_path: str, project_root: str):
    config_path = Path.home() / ".gemini" / "settings.json"
    print_info(f"Configuring Gemini CLI at {config_path}")
    
    config = load_json(config_path)
    if "mcpServers" not in config:
        config["mcpServers"] = {}
        
    # Gemini CLI usually uses list for mcpServers in some versions, but docs say object.
    # Docs: "mcpServers": { "serverName": { ... } }
    # Existing config might be a list (older versions). We will assume Object per docs.
    
    if isinstance(config.get("mcpServers"), list):
        print_warning("Your Gemini config uses a list for 'mcpServers'. Converting to object not supported automatically to avoid breaking.")
        print_info("Please manually add:")
        print(json.dumps({
            "name": "drive-synapsis",
            "command": uv_path,
            "args": ["run", "--directory", project_root, "drive-synapsis"]
        }, indent=2))
        return

    config["mcpServers"]["drive-synapsis"] = {
        "command": uv_path,
        "args": ["run", "--directory", project_root, "drive-synapsis"]
    }
    
    if confirm(f"Write config to {config_path}?"):
        save_json(config_path, config)
    else:
        print(json.dumps(config, indent=2))

def _setup_opencode(uv_path: str, project_root: str):
    print("\n--- OpenCode Configuration ---")
    print("1. Global (~/.config/opencode/opencode.json)")
    print("2. Local (./opencode.json)")
    
    choice = get_input("Choose location", default="1")
    
    if choice == '1':
        config_path = Path.home() / ".config" / "opencode" / "opencode.json"
    else:
        config_path = Path.cwd() / "opencode.json"

    print_info(f"Configuring OpenCode at {config_path}")
    
    config = load_json(config_path)
    if "mcp" not in config:
        config["mcp"] = {}
        
    config["mcp"]["drive-synapsis"] = {
        "type": "local",
        "command": [uv_path, "run", "--directory", project_root, "drive-synapsis"],
        "enabled": True
    }
    
    if confirm(f"Write config to {config_path}?"):
        save_json(config_path, config)
    else:
        print(json.dumps(config, indent=2))

def main():
    print_header("Drive Synapsis Setup Wizard")
    print_info(f"Project Root: {get_project_root()}")
    
    uv_path = get_uv_path()
    if uv_path == "uv":
        print_warning("Could not locate absolute path for 'uv'. Using 'uv' command directly.")
    
    try:
        setup_credentials()
        print()
        configure_clients(uv_path, get_project_root())
        
        print_header("Setup Complete!")
        print_success("You are ready to use Drive Synapsis.")
        print_info(f"Try running: {uv_path} run drive-synapsis")
        
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()