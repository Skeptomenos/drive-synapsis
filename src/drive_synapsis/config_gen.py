"""Configuration generator for Drive Synapsis MCP Server.

Generates client-specific configuration JSON for various AI assistants:
- Claude Desktop / Claude Code
- VS Code (Copilot, Continue, etc.)
- Gemini CLI / OpenCode
"""
import json
import os
import shutil
import sys
from pathlib import Path


def get_uv_path() -> str:
    """Find the uv executable path."""
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path
    # Common locations
    common_paths = [
        os.path.expanduser("~/.local/bin/uv"),
        os.path.expanduser("~/.cargo/bin/uv"),
        "/usr/local/bin/uv",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return "uv"  # Fallback, user will need to adjust


def get_package_dir() -> Path:
    """Get the drive_synapsis package directory."""
    # This file is in drive_synapsis/config_gen.py
    return Path(__file__).parent


def get_project_root() -> Path:
    """Get the project root directory (where pyproject.toml is)."""
    # Package is in src/drive_synapsis, so root is ../../
    return get_package_dir().parent.parent


def generate_claude_config() -> dict:
    """Generate configuration for Claude Desktop/Code.
    
    Claude uses a settings.json format with mcpServers key.
    """
    uv_path = get_uv_path()
    project_root = str(get_project_root())
    
    return {
        "mcpServers": {
            "drive-synapsis": {
                "command": uv_path,
                "args": ["run", "--directory", project_root, "drive-synapsis"],
                "env": {}
            }
        }
    }


def generate_vscode_config() -> dict:
    """Generate configuration for VS Code extensions (Copilot, Continue, etc.).
    
    VS Code extensions typically use a similar format to Claude.
    """
    uv_path = get_uv_path()
    project_root = str(get_project_root())
    
    return {
        "mcpServers": {
            "drive-synapsis": {
                "command": uv_path,
                "args": ["run", "--directory", project_root, "drive-synapsis"]
            }
        }
    }


def generate_gemini_config() -> dict:
    """Generate configuration for Gemini CLI.
    
    Gemini CLI uses settings.json with mcpServers in stdio format.
    """
    uv_path = get_uv_path()
    project_root = str(get_project_root())
    
    return {
        "mcpServers": [
            {
                "name": "drive-synapsis",
                "command": uv_path,
                "args": ["run", "--directory", project_root, "drive-synapsis"]
            }
        ]
    }


def print_separator():
    """Print a visual separator."""
    print("=" * 60)


def main():
    """Main entry point for drive-synapsis-config command."""
    print("\n🔧 Drive Synapsis - Configuration Generator\n")
    
    # Detect environment
    uv_path = get_uv_path()
    project_root = get_project_root()
    
    print(f"📁 Project directory: {project_root}")
    print(f"🔨 UV executable: {uv_path}")
    print()
    
    # Check if credentials exist
    client_secret = project_root / "client_secret.json"
    token_file = project_root / "token.json"
    
    if not client_secret.exists():
        print("⚠️  WARNING: client_secret.json not found!")
        print("   You need to set up Google Cloud credentials first.")
        print("   See README.md for BYOK (Bring Your Own Keys) instructions.\n")
    else:
        print("✅ client_secret.json found")
        
    if token_file.exists():
        print("✅ token.json found (already authenticated)")
    else:
        print("ℹ️  token.json not found (will authenticate on first run)")
    print()
    
    print_separator()
    print("📋 CLAUDE DESKTOP / CLAUDE CODE")
    print_separator()
    print("Add to: ~/.claude/settings.json (or Claude Desktop config)")
    print()
    print(json.dumps(generate_claude_config(), indent=2))
    print()
    
    print_separator()
    print("📋 VS CODE (Copilot, Continue, etc.)")
    print_separator()
    print("Add to your VS Code extension's MCP configuration")
    print()
    print(json.dumps(generate_vscode_config(), indent=2))
    print()
    
    print_separator()
    print("📋 GEMINI CLI / OPENCODE")
    print_separator()
    print("Add to: ~/.gemini/settings.json")
    print()
    print(json.dumps(generate_gemini_config(), indent=2))
    print()
    
    print_separator()
    print("💡 QUICK TEST")
    print_separator()
    print("To verify the server works, run:")
    print(f"  {uv_path} run drive-synapsis")
    print()
    print("The server should start and wait for MCP connections.")
    print("Press Ctrl+C to stop.\n")


if __name__ == "__main__":
    main()
