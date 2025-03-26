#!/usr/bin/env python3
"""
Install the PBIXRay MCP Server for Claude Desktop

This script helps you install the PBIXRay MCP server in your Claude Desktop configuration.
"""

import os
import json
import platform
import sys
from pathlib import Path

def main():
    """Install the PBIXRay MCP server for Claude Desktop"""
    # Get the absolute path to the server script
    server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "pbixray_server.py"))
    
    # Determine Claude Desktop config location based on platform
    if platform.system() == "Darwin":  # macOS
        config_path = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
    elif platform.system() == "Windows":
        config_path = os.path.join(os.environ.get("APPDATA", ""), "Claude", "claude_desktop_config.json")
    else:
        print("Unsupported platform. Claude Desktop is only available on macOS and Windows.")
        sys.exit(1)
    
    # Check if server script exists
    if not os.path.exists(server_path):
        print(f"Error: Server script not found at {server_path}")
        sys.exit(1)
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # Load existing config or create new one
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            print(f"Loaded existing Claude Desktop configuration from {config_path}")
        except json.JSONDecodeError:
            print(f"Warning: Existing config at {config_path} is invalid. Creating new config.")
    else:
        print(f"Creating new Claude Desktop configuration at {config_path}")
    
    # Make sure mcpServers section exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Add PBIXRay server
    config["mcpServers"]["pbixray"] = {
        "command": sys.executable,  # Use current Python executable
        "args": [server_path]
    }
    
    # Save updated config
    with open(config_path, "w") as f:
        json.dump(config, indent=2, sort_keys=True, f)
    
    print("\n✅ PBIXRay MCP server has been added to your Claude Desktop configuration!")
    print(f"Configuration saved to: {config_path}")
    print("\nNext steps:")
    print("1. Restart Claude Desktop")
    print("2. You should now see the PBIXRay tools available in Claude")
    print("3. Ask Claude to help you analyze your Power BI files")

if __name__ == "__main__":
    main()
