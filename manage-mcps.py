#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "rich",
# ]
# ///

"""
Claude Code MCP Management Tool

Manage MCP servers in existing Claude Code projects.

Usage:
    uv run manage-mcps.py                              # Interactive management (current dir)
    uv run manage-mcps.py --project=/path/to/project   # Interactive management (specific dir)
    uv run manage-mcps.py --list                       # List current MCPs
    uv run manage-mcps.py --add=context7,serena
    uv run manage-mcps.py --remove=github
    uv run manage-mcps.py --update                     # Update MCP configurations
"""

import argparse
import json
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

console = Console()

# Same MCP definitions as setup tool
AVAILABLE_MCPS = {
    "firecrawl": {
        "name": "Firecrawl MCP",
        "description": "Web scraping and crawling",
        "npm_package": "firecrawl-mcp",
        "command": "npx",
        "args": ["-y", "firecrawl-mcp"],
        "env_vars": ["FIRECRAWL_API_KEY"]
    },
    "github": {
        "name": "GitHub MCP", 
        "description": "GitHub repository operations", 
        "npm_package": "@modelcontextprotocol/server-github",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env_vars": ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    },
    "elevenlabs": {
        "name": "ElevenLabs MCP",
        "description": "Text-to-speech with ElevenLabs",
        "python_package": "elevenlabs-mcp",
        "command": "uvx",
        "args": ["elevenlabs-mcp"],
        "env_vars": ["ELEVENLABS_API_KEY"]
    },
    "context7": {
        "name": "Context7 MCP",
        "description": "Up-to-date code documentation",
        "npm_package": "@upstash/context7-mcp",
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp"],
        "env_vars": []
    },
    "serena": {
        "name": "Serena MCP",
        "description": "Coding agent toolkit with semantic retrieval",
        "python_package": "git+https://github.com/oraios/serena",
        "command": "uvx",
        "args": ["--from", "git+https://github.com/oraios/serena", "serena-mcp-server"],
        "env_vars": []
    }
}

def find_claude_settings(project_dir: Path = None) -> Path:
    """Find .claude/settings.json in specified directory or current directory."""
    if project_dir is None:
        project_dir = Path.cwd()
    else:
        project_dir = Path(project_dir).resolve()
    
    settings_file = project_dir / ".claude" / "settings.json"
    if settings_file.exists():
        return settings_file
    
    raise FileNotFoundError(f"No .claude/settings.json found in {project_dir}")

# Global variable to store project directory
PROJECT_DIR = None

def load_current_settings() -> dict:
    """Load current Claude settings."""
    try:
        settings_file = find_claude_settings(PROJECT_DIR)
        with open(settings_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError as e:
        console.print(f"❌ {e}", style="red")
        console.print("Make sure you're in a Claude Code project directory or specify --project path", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error reading settings: {e}", style="red")
        sys.exit(1)

def save_settings(settings: dict) -> bool:
    """Save settings back to file."""
    try:
        settings_file = find_claude_settings(PROJECT_DIR)
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        console.print(f"❌ Error saving settings: {e}", style="red")
        return False

def list_current_mcps():
    """List currently installed MCP servers."""
    settings = load_current_settings()
    mcps = settings.get("mcpServers", {})
    
    if not mcps:
        console.print("📦 No MCP servers configured", style="yellow")
        return
    
    table = Table(title="Configured MCP Servers")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Command", style="green")
    table.add_column("Status", style="blue")
    
    for mcp_id, config in mcps.items():
        if mcp_id in AVAILABLE_MCPS:
            name = AVAILABLE_MCPS[mcp_id]["name"]
            status = "✅ Known"
        else:
            name = "Unknown"
            status = "❓ Custom"
        
        command = f"{config['command']} {' '.join(config.get('args', []))}"
        table.add_row(mcp_id, name, command[:50] + "..." if len(command) > 50 else command, status)
    
    console.print(table)

def add_mcps(mcp_ids: list):
    """Add MCP servers to configuration."""
    settings = load_current_settings()
    
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}
    
    added = []
    for mcp_id in mcp_ids:
        if mcp_id not in AVAILABLE_MCPS:
            console.print(f"⚠️  Unknown MCP: {mcp_id}", style="yellow")
            continue
        
        if mcp_id in settings["mcpServers"]:
            console.print(f"⚠️  {mcp_id} already configured", style="yellow")
            continue
        
        mcp_info = AVAILABLE_MCPS[mcp_id]
        settings["mcpServers"][mcp_id] = {
            "command": mcp_info["command"],
            "args": mcp_info["args"]
        }
        
        if mcp_info["env_vars"]:
            settings["mcpServers"][mcp_id]["env"] = {
                var: f"${{{var}}}" for var in mcp_info["env_vars"]
            }
        
        added.append(mcp_id)
        console.print(f"✅ Added {mcp_info['name']}", style="green")
    
    if added and save_settings(settings):
        console.print(f"🎉 Successfully added {len(added)} MCP servers", style="bold green")

def remove_mcps(mcp_ids: list):
    """Remove MCP servers from configuration."""
    settings = load_current_settings()
    mcps = settings.get("mcpServers", {})
    
    removed = []
    for mcp_id in mcp_ids:
        if mcp_id in mcps:
            del mcps[mcp_id]
            removed.append(mcp_id)
            console.print(f"✅ Removed {mcp_id}", style="green")
        else:
            console.print(f"⚠️  {mcp_id} not found", style="yellow")
    
    if removed and save_settings(settings):
        console.print(f"🎉 Successfully removed {len(removed)} MCP servers", style="bold green")

def update_mcps():
    """Update existing MCP configurations to latest format."""
    settings = load_current_settings()
    mcps = settings.get("mcpServers", {})
    
    updated = []
    for mcp_id, config in mcps.items():
        if mcp_id in AVAILABLE_MCPS:
            new_config = AVAILABLE_MCPS[mcp_id]
            old_command = f"{config['command']} {' '.join(config.get('args', []))}"
            new_command = f"{new_config['command']} {' '.join(new_config['args'])}"
            
            if old_command != new_command:
                mcps[mcp_id] = {
                    "command": new_config["command"],
                    "args": new_config["args"]
                }
                
                if new_config["env_vars"]:
                    mcps[mcp_id]["env"] = {
                        var: f"${{{var}}}" for var in new_config["env_vars"]
                    }
                
                updated.append(mcp_id)
                console.print(f"✅ Updated {new_config['name']}", style="green")
    
    if updated and save_settings(settings):
        console.print(f"🎉 Successfully updated {len(updated)} MCP servers", style="bold green")
    elif not updated:
        console.print("✅ All MCP servers are up to date", style="green")

def interactive_mcp_selection():
    """Interactive MCP selection with checkboxes."""
    settings = load_current_settings()
    current_mcps = set(settings.get("mcpServers", {}).keys())
    
    console.print(Panel.fit("MCP Server Selection", style="blue"))
    
    # Show current status
    console.print("\n📦 Current Status:")
    if current_mcps:
        console.print(f"Installed: {', '.join(sorted(current_mcps))}", style="green")
    else:
        console.print("No MCP servers installed", style="yellow")
    
    # Show available options with current status
    console.print("\n🔧 Available MCP Servers:")
    table = Table()
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Status", style="white", no_wrap=True) 
    table.add_column("Name", style="magenta")
    table.add_column("Description", style="green")
    
    available_ids = list(AVAILABLE_MCPS.keys())
    for i, (mcp_id, mcp_info) in enumerate(AVAILABLE_MCPS.items(), 1):
        status = "✅ Installed" if mcp_id in current_mcps else "⬜ Available"
        table.add_row(str(i), status, mcp_info["name"], mcp_info["description"])
    
    console.print(table)
    
    # Get selection
    console.print("\n📝 Selection Options:")
    console.print("• Enter numbers to toggle (e.g., '1,3,5')")
    console.print("• Enter 'all' to install all")
    console.print("• Enter 'none' to remove all")
    console.print("• Enter 'done' to finish")
    
    selected_mcps = current_mcps.copy()
    
    while True:
        current_status = ", ".join(sorted(selected_mcps)) if selected_mcps else "none"
        console.print(f"\n🎯 Currently selected: {current_status}", style="cyan")
        
        selection = Prompt.ask("Your choice", default="done")
        
        if selection.lower() == "done":
            break
        elif selection.lower() == "all":
            selected_mcps = set(AVAILABLE_MCPS.keys())
            console.print("✅ Selected all MCP servers", style="green")
        elif selection.lower() == "none":
            selected_mcps = set()
            console.print("✅ Deselected all MCP servers", style="green")
        else:
            # Parse numbers/IDs
            try:
                selections = [s.strip() for s in selection.split(',')]
                for sel in selections:
                    if sel.isdigit():
                        idx = int(sel) - 1
                        if 0 <= idx < len(available_ids):
                            mcp_id = available_ids[idx]
                            if mcp_id in selected_mcps:
                                selected_mcps.remove(mcp_id)
                                console.print(f"➖ Deselected {AVAILABLE_MCPS[mcp_id]['name']}", style="yellow")
                            else:
                                selected_mcps.add(mcp_id)
                                console.print(f"➕ Selected {AVAILABLE_MCPS[mcp_id]['name']}", style="green")
                    elif sel in AVAILABLE_MCPS:
                        mcp_id = sel
                        if mcp_id in selected_mcps:
                            selected_mcps.remove(mcp_id)
                            console.print(f"➖ Deselected {AVAILABLE_MCPS[mcp_id]['name']}", style="yellow")
                        else:
                            selected_mcps.add(mcp_id)
                            console.print(f"➕ Selected {AVAILABLE_MCPS[mcp_id]['name']}", style="green")
            except (ValueError, IndexError):
                console.print("⚠️  Invalid selection, try again", style="yellow")
    
    # Apply changes
    if selected_mcps != current_mcps:
        to_add = selected_mcps - current_mcps
        to_remove = current_mcps - selected_mcps
        
        if to_remove:
            console.print(f"\n🗑️  Removing: {', '.join(sorted(to_remove))}")
            remove_mcps(list(to_remove))
        
        if to_add:
            console.print(f"\n📦 Adding: {', '.join(sorted(to_add))}")
            add_mcps(list(to_add))
        
        console.print("\n🎉 MCP configuration updated!", style="bold green")
    else:
        console.print("\n✅ No changes made", style="green")

def interactive_management():
    """Interactive MCP management."""
    project_path = PROJECT_DIR or Path.cwd()
    console.print(Panel.fit(f"Claude Code MCP Management\nProject: {project_path}", style="blue"))
    
    while True:
        console.print("\n🔧 Options:")
        console.print("1. Configure MCP servers (interactive selection)")
        console.print("2. List current MCPs")
        console.print("3. Update MCP configurations to latest")
        console.print("4. Exit")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="4")
        
        if choice == "1":
            interactive_mcp_selection()
        elif choice == "2":
            list_current_mcps()
        elif choice == "3":
            update_mcps()
        elif choice == "4":
            break

def main():
    global PROJECT_DIR
    
    parser = argparse.ArgumentParser(
        description="Manage MCP servers in Claude Code projects",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--project", help="Project directory path (default: current directory)")
    parser.add_argument("--list", action="store_true", help="List current MCP servers")
    parser.add_argument("--add", help="Add MCP servers (comma-separated)")
    parser.add_argument("--remove", help="Remove MCP servers (comma-separated)")
    parser.add_argument("--update", action="store_true", help="Update MCP configurations")
    
    args = parser.parse_args()
    
    # Set global project directory
    if args.project:
        PROJECT_DIR = Path(args.project).resolve()
        if not PROJECT_DIR.exists():
            console.print(f"❌ Project directory does not exist: {PROJECT_DIR}", style="red")
            sys.exit(1)
    
    if args.list:
        list_current_mcps()
    elif args.add:
        mcp_ids = [mcp.strip() for mcp in args.add.split(',')]
        add_mcps(mcp_ids)
    elif args.remove:
        mcp_ids = [mcp.strip() for mcp in args.remove.split(',')]
        remove_mcps(mcp_ids)
    elif args.update:
        update_mcps()
    else:
        interactive_management()

if __name__ == "__main__":
    main()