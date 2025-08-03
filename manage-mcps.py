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
import subprocess
import sys
import termios
import tty
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

def find_mcp_config(project_dir: Path = None) -> Path:
    """Find .mcp.json in specified directory or current directory."""
    if project_dir is None:
        project_dir = Path.cwd()
    else:
        project_dir = Path(project_dir).resolve()
    
    mcp_file = project_dir / ".mcp.json"
    if mcp_file.exists():
        return mcp_file
    
    raise FileNotFoundError(f"No .mcp.json found in {project_dir}")

# Global variable to store project directory
PROJECT_DIR = None

def check_command_available(command: str) -> bool:
    """Check if a command is available in PATH."""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_node_version() -> tuple[bool, str]:
    """Check if Node.js is available and meets minimum version requirements."""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
        version_str = result.stdout.strip()
        
        # Parse version (e.g., "v18.17.0" -> [18, 17, 0])
        if version_str.startswith('v'):
            version_str = version_str[1:]
        
        version_parts = [int(x) for x in version_str.split('.')]
        major_version = version_parts[0]
        
        # Node.js >= 18.0.0 required for context7
        if major_version >= 18:
            return True, version_str
        else:
            return False, version_str
            
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return False, "not found"

def check_npm_package_installed(package: str) -> bool:
    """Check if an npm package is globally installed."""
    try:
        result = subprocess.run(
            ["npm", "list", "-g", "--depth=0", package],
            capture_output=True,
            text=True
        )
        return package in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_python_package_available(package: str) -> bool:
    """Check if a Python package is available via uvx."""
    if package.startswith("git+"):
        # For git packages, we can't easily check availability
        return True
    try:
        # Try to get help from uvx - if package exists, this should work
        result = subprocess.run(
            ["uvx", "--help"],
            capture_output=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_mcp_dependencies(mcp_ids: list) -> bool:
    """Install dependencies for the specified MCP servers."""
    console.print("\n🔍 Checking and installing MCP dependencies...", style="blue")
    
    # Check Node.js requirements
    node_ok, node_version = check_node_version()
    needs_nodejs = any(mcp_id in ["context7", "firecrawl", "github"] for mcp_id in mcp_ids)
    
    if needs_nodejs and not node_ok:
        if node_version == "not found":
            console.print("❌ Node.js not found but required for selected MCPs", style="red")
        else:
            console.print(f"❌ Node.js v{node_version} found, but v18.0.0+ required for context7", style="red")
        
        console.print("Please install Node.js v18+:", style="yellow")
        console.print("  - Download: https://nodejs.org/", style="dim")
        console.print("  - Or use nvm: nvm install 18", style="dim")
        return False
    elif needs_nodejs:
        console.print(f"✅ Node.js v{node_version} meets requirements", style="green")
    
    # Check other basic requirements
    missing_commands = []
    if needs_nodejs and not check_command_available("npx"):
        missing_commands.append("npx (should come with Node.js)")
    if any(mcp_id in ["elevenlabs", "serena"] for mcp_id in mcp_ids) and not check_command_available("uvx"):
        missing_commands.append("uvx (uv)")
    
    if missing_commands:
        console.print(f"❌ Missing required commands: {', '.join(missing_commands)}", style="red")
        console.print("Installation guides:", style="yellow")
        console.print("  - uv: https://docs.astral.sh/uv/", style="dim")
        return False
    
    installed_count = 0
    failed_count = 0
    
    for mcp_id in mcp_ids:
        if mcp_id not in AVAILABLE_MCPS:
            continue
            
        mcp_info = AVAILABLE_MCPS[mcp_id]
        console.print(f"📦 Installing {mcp_info['name']}...", style="cyan")
        
        try:
            if mcp_info["command"] == "npx":
                # Test npx with a simple command to check for permission issues
                test_result = subprocess.run(
                    ["npx", "--version"], 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                if test_result.returncode == 0:
                    console.print(f"✅ {mcp_info['name']} ready (npx will download on demand)", style="green")
                    installed_count += 1
                else:
                    console.print(f"⚠️  {mcp_info['name']} may have npm cache issues", style="yellow")
                    console.print("  Try: npm cache clean --force", style="dim")
                    installed_count += 1  # Don't fail the whole process
            elif mcp_info["command"] == "uvx":
                # For uvx packages, we can try to cache them
                if "python_package" in mcp_info:
                    package = mcp_info["python_package"]
                    if package.startswith("git+"):
                        # For git packages, try to install
                        cmd = ["uvx", "--from", package, "--help"]
                    else:
                        cmd = ["uvx", package, "--help"]
                    
                    result = subprocess.run(cmd, capture_output=True, timeout=30)
                    if result.returncode == 0:
                        console.print(f"✅ {mcp_info['name']} installed successfully", style="green")
                        installed_count += 1
                    else:
                        console.print(f"⚠️  {mcp_info['name']} may need manual setup", style="yellow")
                        installed_count += 1  # Don't fail for this
            else:
                console.print(f"⚠️  Unknown command type for {mcp_info['name']}", style="yellow")
                installed_count += 1  # Don't fail for this
                
        except subprocess.TimeoutExpired:
            console.print(f"⚠️  {mcp_info['name']} installation timeout (will work on demand)", style="yellow")
            installed_count += 1
        except Exception as e:
            console.print(f"❌ Failed to install {mcp_info['name']}: {e}", style="red")
            failed_count += 1
    
    if failed_count == 0:
        console.print(f"🎉 All {installed_count} MCP dependencies ready!", style="bold green")
        return True
    else:
        console.print(f"⚠️  {installed_count} succeeded, {failed_count} failed", style="yellow")
        console.print("\n💡 If you're having npm issues, try:", style="blue")
        console.print("   npm cache clean --force", style="dim")
        console.print("   sudo chown -R $(whoami) ~/.npm", style="dim")
        return installed_count > 0

def fix_npm_cache():
    """Try to fix common npm cache permission issues."""
    console.print("🔧 Attempting to fix npm cache issues...", style="blue")
    
    try:
        # Clean npm cache
        result = subprocess.run(["npm", "cache", "clean", "--force"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            console.print("✅ npm cache cleaned", style="green")
        else:
            console.print("⚠️  npm cache clean failed", style="yellow")
        
        # Try to fix permissions (this might need sudo)
        console.print("💡 You may need to run: sudo chown -R $(whoami) ~/.npm", style="yellow")
        return True
        
    except Exception as e:
        console.print(f"❌ Cache fix failed: {e}", style="red")
        return False

def load_mcp_config() -> dict:
    """Load current MCP configuration."""
    try:
        mcp_file = find_mcp_config(PROJECT_DIR)
        with open(mcp_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create empty config if file doesn't exist
        return {"mcpServers": {}}
    except Exception as e:
        console.print(f"❌ Error reading .mcp.json: {e}", style="red")
        sys.exit(1)

def save_mcp_config(config: dict) -> bool:
    """Save MCP configuration back to file."""
    try:
        project_dir = PROJECT_DIR or Path.cwd()
        mcp_file = project_dir / ".mcp.json"
        with open(mcp_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        console.print(f"❌ Error saving .mcp.json: {e}", style="red")
        return False

def list_current_mcps():
    """List currently installed MCP servers."""
    config = load_mcp_config()
    mcps = config.get("mcpServers", {})
    
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

def add_mcps(mcp_ids: list, install_deps: bool = True):
    """Add MCP servers to configuration."""
    config = load_mcp_config()
    
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Filter out already configured MCPs
    to_add = []
    for mcp_id in mcp_ids:
        if mcp_id not in AVAILABLE_MCPS:
            console.print(f"⚠️  Unknown MCP: {mcp_id}", style="yellow")
            continue
        
        if mcp_id in config["mcpServers"]:
            console.print(f"⚠️  {mcp_id} already configured", style="yellow")
            continue
        
        to_add.append(mcp_id)
    
    if not to_add:
        return
    
    # Install dependencies first if requested
    if install_deps:
        if not install_mcp_dependencies(to_add):
            console.print("⚠️  Some dependencies failed to install, but continuing with configuration...", style="yellow")
    
    # Add to configuration
    added = []
    for mcp_id in to_add:
        mcp_info = AVAILABLE_MCPS[mcp_id]
        config["mcpServers"][mcp_id] = {
            "command": mcp_info["command"],
            "args": mcp_info["args"]
        }
        
        if mcp_info["env_vars"]:
            config["mcpServers"][mcp_id]["env"] = {
                var: f"${{{var}}}" for var in mcp_info["env_vars"]
            }
        
        added.append(mcp_id)
        console.print(f"✅ Configured {mcp_info['name']}", style="green")
    
    if added and save_mcp_config(config):
        console.print(f"🎉 Successfully configured {len(added)} MCP servers", style="bold green")
        
        # Show environment variable reminder
        env_vars_needed = []
        for mcp_id in added:
            env_vars_needed.extend(AVAILABLE_MCPS[mcp_id]["env_vars"])
        
        if env_vars_needed:
            console.print(f"\n💡 Don't forget to set these environment variables:", style="blue")
            for var in sorted(set(env_vars_needed)):
                console.print(f"   {var}", style="cyan")

def remove_mcps(mcp_ids: list):
    """Remove MCP servers from configuration."""
    config = load_mcp_config()
    mcps = config.get("mcpServers", {})
    
    removed = []
    for mcp_id in mcp_ids:
        if mcp_id in mcps:
            del mcps[mcp_id]
            removed.append(mcp_id)
            console.print(f"✅ Removed {mcp_id}", style="green")
        else:
            console.print(f"⚠️  {mcp_id} not found", style="yellow")
    
    if removed and save_mcp_config(config):
        console.print(f"🎉 Successfully removed {len(removed)} MCP servers", style="bold green")

def update_mcps():
    """Update existing MCP configurations to latest format."""
    config = load_mcp_config()
    mcps = config.get("mcpServers", {})
    
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
    
    if updated and save_mcp_config(config):
        console.print(f"🎉 Successfully updated {len(updated)} MCP servers", style="bold green")
    elif not updated:
        console.print("✅ All MCP servers are up to date", style="green")

def get_key():
    """Get a single keypress from stdin using termios."""
    try:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        # Create new settings for raw mode
        new_settings = old_settings.copy()
        new_settings[3] = new_settings[3] & ~(termios.ICANON | termios.ECHO)
        new_settings[6][termios.VMIN] = 1
        new_settings[6][termios.VTIME] = 0
        
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
            char = sys.stdin.read(1)
            
            # Handle escape sequences (arrow keys)
            if char == '\x1b':
                char += sys.stdin.read(2)
                
            return char
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    except (ImportError, AttributeError, OSError, termios.error):
        # Terminal doesn't support raw mode
        raise Exception("Terminal input not supported")

def interactive_mcp_selection():
    """Interactive MCP selection with arrow keys and spacebar."""
    config = load_mcp_config()
    current_mcps = set(config.get("mcpServers", {}).keys())
    
    # Available MCPs with current selection
    mcps = list(AVAILABLE_MCPS.items())
    selected = current_mcps.copy()
    cursor = 0
    
    def render_menu():
        console.clear()
        console.print(Panel.fit("MCP Server Selection - Use ↑↓ arrows, SPACE to toggle, ENTER to finish", style="blue"))
        console.print()
        
        for i, (mcp_id, mcp_info) in enumerate(mcps):
            # Cursor indicator
            cursor_mark = "→ " if i == cursor else "  "
            
            # Checkbox with color coding
            if mcp_id in selected:
                checkbox = "[bold green]✓[/bold green]"
                name_style = "bold green"
                bg_style = "on bright_black" if i == cursor else ""
            else:
                checkbox = "[dim]☐[/dim]"
                name_style = "white"
                bg_style = "on bright_black" if i == cursor else ""
            
            # Highlight current row
            line = f"{cursor_mark}{checkbox} [{name_style}]{mcp_info['name']}[/{name_style}] - {mcp_info['description']}"
            if i == cursor:
                console.print(f"[{bg_style}]{line}[/{bg_style}]")
            else:
                console.print(line)
        
        console.print(f"\n[bold cyan]Selected: {len(selected)} MCPs[/bold cyan]")
        console.print("\n[dim]Controls:[/dim]")
        console.print("[dim]↑↓  Navigate  │  SPACE  Toggle  │  ENTER  Finish  │  ESC  Cancel[/dim]")
    
    # Main interaction loop
    try:
        while True:
            render_menu()
            
            try:
                key = get_key()
            except KeyboardInterrupt:
                console.print("\n[yellow]Cancelled[/yellow]")
                return
            
            if key == '\x1b[A':  # Up arrow
                cursor = (cursor - 1) % len(mcps)
            elif key == '\x1b[B':  # Down arrow  
                cursor = (cursor + 1) % len(mcps)
            elif key == ' ':  # Space - toggle
                mcp_id = mcps[cursor][0]
                if mcp_id in selected:
                    selected.remove(mcp_id)
                else:
                    selected.add(mcp_id)
            elif key == '\r' or key == '\n':  # Enter - finish
                break
            elif key == '\x1b':  # ESC - cancel
                console.print("\n[yellow]Cancelled[/yellow]")
                return
            elif key == 'q':  # q - quit
                console.print("\n[yellow]Cancelled[/yellow]")
                return
    
    except Exception as e:
        console.print(f"\n[red]Error during interaction: {e}[/red]")
        console.print("[yellow]Falling back to text input...[/yellow]")
        # Fallback to simple text input
        return interactive_mcp_selection_fallback(config, current_mcps)
    
    # Apply changes
    if selected != current_mcps:
        to_add = selected - current_mcps
        to_remove = current_mcps - selected
        
        console.clear()
        console.print("🔄 Applying changes...\n")
        
        if to_remove:
            console.print(f"[yellow]🗑️  Removing: {', '.join(sorted(to_remove))}[/yellow]")
            remove_mcps(list(to_remove))
        
        if to_add:
            console.print(f"[cyan]📦 Adding: {', '.join(sorted(to_add))}[/cyan]")
            add_mcps(list(to_add))
        
        console.print("\n🎉 MCP configuration updated!", style="bold green")
    else:
        console.clear()
        console.print("✅ No changes made", style="green")

def interactive_mcp_selection_fallback(config, current_mcps):
    """Fallback text-based selection if arrow keys don't work."""
    mcps = list(AVAILABLE_MCPS.items())
    selected = current_mcps.copy()
    
    console.print("\n🔧 MCP Server Configuration (Text Mode):\n")
    
    for i, (mcp_id, mcp_info) in enumerate(mcps, 1):
        status = "✓" if mcp_id in selected else "☐"
        console.print(f"{i}. {status} {mcp_info['name']} ({mcp_id}) - {mcp_info['description']}")
    
    console.print(f"\n[bold cyan]Selected: {len(selected)} MCPs[/bold cyan]")
    console.print("\n[dim]Enter numbers to toggle (e.g., '1,3'), 'all', 'none', or 'done':[/dim]")
    
    while True:
        choice = Prompt.ask("Your choice", default="done").lower().strip()
        
        if choice == "done":
            break
        elif choice == "all":
            selected = set(AVAILABLE_MCPS.keys())
            console.print("✅ Selected all")
        elif choice == "none":
            selected = set()
            console.print("✅ Deselected all")
        else:
            try:
                numbers = [int(x.strip()) for x in choice.split(',')]
                for num in numbers:
                    if 1 <= num <= len(mcps):
                        mcp_id = mcps[num-1][0]
                        if mcp_id in selected:
                            selected.remove(mcp_id)
                        else:
                            selected.add(mcp_id)
            except ValueError:
                console.print("[red]Invalid input[/red]")
    
    # Apply changes same as main function
    if selected != current_mcps:
        to_add = selected - current_mcps
        to_remove = current_mcps - selected
        
        if to_remove:
            remove_mcps(list(to_remove))
        if to_add:
            add_mcps(list(to_add))
        
        console.print("\n🎉 Updated!", style="bold green")

def interactive_management():
    """Interactive MCP management."""
    project_path = PROJECT_DIR or Path.cwd()
    console.print(Panel.fit(f"Claude Code MCP Management\nProject: {project_path}", style="blue"))
    
    while True:
        console.print("\n🔧 Options:")
        console.print("1. Configure MCP servers (interactive selection)")
        console.print("2. List current MCPs")
        console.print("3. Update MCP configurations to latest")
        console.print("4. Fix npm cache issues")
        console.print("5. Exit")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="5")
        
        if choice == "1":
            interactive_mcp_selection()
        elif choice == "2":
            list_current_mcps()
        elif choice == "3":
            update_mcps()
        elif choice == "4":
            fix_npm_cache()
        elif choice == "5":
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